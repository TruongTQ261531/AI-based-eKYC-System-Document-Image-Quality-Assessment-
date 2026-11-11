"""Bounded development pilot. No checkpoint, historical log or test set writes."""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict
import json
from pathlib import Path
import subprocess
import sys
import time

from ..runner import InputRequest, Runner, sha_file, write_once
from ..normalized_output import ReaderSpec, normalize
from ..source_graph import digest, pixel_sha256

EC = Path(__file__).resolve().parents[1]
ROOT = EC.parents[1]
READERS = ("rapid_v4", "rapid_latin_v5", "partial_42")
CAP = 120


def paths(run):
    if not run or not all(c.isalnum() or c in "_-" for c in run):
        raise ValueError("Expected an opaque development run ID")
    return EC / "local" / ("task5_" + run), EC / "execution/task5_pilot" / run


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def code_hashes():
    files = list((EC / "task5").glob("*.py"))
    files += [EC / name for name in ("contracts.py", "source_graph.py", "validity.py", "generator.py", "oracle.py",
                                     "evaluator.py", "normalized_output.py", "reader_adapters.py", "runner.py")]
    return {p.relative_to(ROOT).as_posix(): sha_file(p) for p in sorted(files)}


def verify_lock(local, public):
    lock = read(public / "pilot_lock.json")
    for filename, expected in lock["manifests"].items():
        if sha_file(local / filename) != expected:
            raise ValueError("Pilot manifest changed: " + filename)
    if lock["code_sha256"] != code_hashes() or sha_file(EC / "BASELINE_PROTOCOL.md") != lock["protocol_sha256"]:
        raise ValueError("Pilot code/protocol changed after lock; no silent inference rerun")
    if sha_file(EC / 'ABLATION_PLAN.md') != lock['ablation_plan_sha256']:
        raise ValueError('Ablation plan changed after development lock')
    return lock


def prepare(run):
    from . import planning
    from ..generator import png_bytes
    local, public = paths(run)
    if local.exists() or public.exists():
        raise FileExistsError("Keep old pilot artifacts; select a new run ID only after inspecting them")
    local.mkdir(parents=True)
    public.mkdir(parents=True)
    wall, cpu = time.perf_counter(), time.process_time()
    panel = planning.approved_panel()
    candidate_pool = planning.pools(panel)
    pool_seconds = time.perf_counter() - wall
    selected, ledger, timing = [], [], []
    for arm in ("A", "B1"):
        seen = set()
        for index, seed in enumerate(planning.SEEDS):
            start, start_cpu = time.perf_counter(), time.process_time()
            pairs, choices = planning.select(candidate_pool, arm=arm, seed=seed, seed_index=index, seen=seen)
            selected.extend((arm, seed, "primary", p) for p in pairs)
            ledger.extend(choices)
            timing.append(dict(arm=arm, seed=seed, wall_seconds=time.perf_counter() - start,
                               cpu_seconds=time.process_time() - start_cpu))
    for seed in planning.SEEDS:
        a = [r for r in ledger if r["arm"] == "A" and r["seed"] == seed]
        b = [r for r in ledger if r["arm"] == "B1" and r["seed"] == seed]
        assert [(r['case'],r['family'],r['area_bin'],r['domain_sha256'],r['domain_size']) for r in a] == [
               (r['case'],r['family'],r['area_bin'],r['domain_sha256'],r['domain_size']) for r in b]
    selected.extend(("shared_diagnostic", 42, name, pair) for name, pair in planning.diagnostics())
    (local / "inputs").mkdir()
    requests, records = {}, []
    for arm, seed, stratum, pair in selected:
        for image in (pair.original, pair.followup):
            checksum = pixel_sha256(image)
            path = local / "inputs" / (checksum + ".png")
            if checksum not in requests:
                with path.open("xb") as stream:
                    stream.write(png_bytes(image))
                requests[checksum] = InputRequest(str(path), sha_file(path), checksum, pair.graph.role, pair.graph.data_policy)
        metadata = pair.metadata()
        records.append(dict(pack_id=digest([arm, seed, stratum, metadata['case_id']]),
                            arm=arm, selection_seed=seed, stratum=stratum,
                            graph=pair.graph.to_dict(), pair=metadata))
    if len(requests) * len(READERS) > CAP:
        raise ValueError("Prepared union exceeds fixed actual-call cap")
    write_once(local / "inputs.json", dict(schema="pixels-only-inputs/1", inputs=[asdict(requests[k]) for k in sorted(requests)]))
    write_once(local / "scoring.json", dict(packs=records))
    write_once(local / "candidate_pool.json", [dict(c.public(), graph=c.pair.graph.to_dict(),
        transformation=c.pair.mutation.to_dict(), validation=c.pair.validation.to_dict()) for c in candidate_pool])
    prepared = dict(role="fixture/development_only", fictional_only=True,
        pool_proposals=len(candidate_pool), pool_statuses=dict(Counter(c.pair.validation.status.value for c in candidate_pool)),
        admissible_candidates=sum(c.eligible for c in candidate_pool),
        pool_auxiliary_C3_validations=sum(c.bundle_ni_validity is not None for c in candidate_pool),
        pool_generation_wall_seconds=pool_seconds, preparation_wall_seconds=time.perf_counter()-wall,
        preparation_cpu_seconds=time.process_time()-cpu, selection_times=timing,
        seeds=planning.SEEDS, selected_pair_records=len(records),
        selected_pair_counts=dict(Counter(r['arm'] for r in records)),
        unique_images=len(requests), physical_ids=len({r['graph']['physical_id'] for r in records}),
        primary_physical_ids=3, primary_pairs_per_arm=20, primary_logical_requests_per_arm=60,
        planned_union_image_reader_requests=len(requests)*len(READERS), new_actual_call_cap=CAP,
        selection=ledger, candidate_audit=[c.public() for c in candidate_pool],
        selected_validity=dict(Counter(r['pair']['validation']['status'] for r in records)),
        expected_false_alarm_gold_available=False, annotation_person_minutes=None,
        graph_annotation_cost='reused authored fixture annotations; person-time unknown, not zero',
        production_or_confirmatory_inputs=0, model_training=False)
    write_once(public / "preparation.json", prepared)
    lock = dict(schema="task5-development-lock/1", scope="exploratory development only; not confirmatory",
                readers=READERS, seeds=planning.SEEDS, actual_call_cap=CAP,
                manifests={f:sha_file(local/f) for f in ('inputs.json','scoring.json','candidate_pool.json')},
                code_sha256=code_hashes(), protocol_sha256=sha_file(EC/'BASELINE_PROTOCOL.md'),
                ablation_plan_sha256=sha_file(EC/'ABLATION_PLAN.md'),
                selection_sha256=digest(ledger), independent_model_failure_gold=False)
    write_once(public / "pilot_lock.json", lock)
    print(json.dumps({k: prepared[k] for k in ('pool_proposals','selected_pair_counts','selected_validity','unique_images','physical_ids','planned_union_image_reader_requests')}),flush=True)


def readonly_cached(runner, request):
    """Never create an old lock file or append to a historical event log."""
    key = runner.key(request)
    path = runner.store / "raw" / (key + ".json")
    if not path.exists():
        return None
    request.load()
    native, call_id, _ = runner._cached(path, key, request)
    return normalize(runner.spec, native, input_file_sha256=request.file_sha256,
        input_pixel_sha256=request.pixel_sha256, cache_key=key, call_id=call_id, access_mode="replay")


def worker(run, reader, mode):
    from .resources import ResourceMonitor
    from ..reader_adapters import specification, load_predictor
    local, public = paths(run)
    lock = verify_lock(local, public)
    monitor = ResourceMonitor(gpu=reader=='partial_42').start()
    spec = specification(reader)
    store = local / reader
    spec_path = store / (reader + '.spec.json')
    if spec_path.exists():
        if read(spec_path) != spec.to_dict():
            raise ValueError("Reader spec changed")
    else:
        if mode != 'fresh':
            raise ValueError("Resume requires a stored reader spec")
        write_once(spec_path, spec.to_dict())
    runner = Runner(spec, store, load_predictor if mode=='fresh' else None)
    old_store = EC / 'local/smoke_02' / reader
    old_spec_path = old_store / (reader+'.spec.json')
    old = Runner(spec, old_store) if old_spec_path.exists() and read(old_spec_path)==spec.to_dict() else None
    old_log_sha = sha_file(old.events.path) if old else None
    events_before = runner.events.read()
    outputs, origin, actual_new_outputs = [], [], []
    for raw in read(local/'inputs.json')['inputs']:
        request = InputRequest(**raw)
        cached = None
        if not (store/'raw'/(runner.key(request)+'.json')).exists() and old:
            cached = readonly_cached(old, request)
        if cached is not None:
            output, provenance = cached, 'TASK4_read_only_cache'
        else:
            if mode != 'fresh' and not (store/'raw'/(runner.key(request)+'.json')).exists():
                raise ValueError("Resume is missing raw output; automatic inference forbidden")
            begins = sum(e['event']=='inference_begin' for e in runner.events.read())
            if begins >= lock['actual_call_cap']//len(READERS) and not (store/'raw'/(runner.key(request)+'.json')).exists():
                raise RuntimeError("Fixed per-backend inference cap reached")
            output = runner.infer(request, replay=mode=='replay')
            provenance = 'TASK5_new' if output.access_mode=='fresh' else 'TASK5_cache'
            if output.access_mode=='fresh':
                actual_new_outputs.append(output)
        outputs.append(output)
        origin.append(dict(input_pixel_sha256=output.input_pixel_sha256, call_id=output.call_id, provenance=provenance))
    resources = monitor.finish(actual_new_outputs)
    events_after = runner.events.read()
    if old and old_log_sha != sha_file(old.events.path):
        raise ValueError("Historical TASK4 event log changed")
    summary = dict(reader=spec.to_dict(), mode=mode, run_id=runner.run_id,
        outputs=[o.public() for o in outputs], provenance=origin,
        new_inference_calls=sum(e['event']=='inference_begin' for e in events_after[len(events_before):]),
        new_model_loads=sum(e['event']=='model_load_begin' for e in events_after[len(events_before):]),
        cache_or_historical_outputs=sum(r['provenance']!='TASK5_new' for r in origin),
        event_log_sha256=sha_file(runner.events.path) if runner.events.path.exists() else None,
        historical_event_log_sha256=old_log_sha, historical_log_unchanged=True,
        resources={k:v for k,v in resources.items() if k not in ('samples','gpu_samples')},
        inference_receives='pixels_only; input manifest has no GT',
        worker_code_sha256=sha_file(__file__))
    write_once(local/(mode+'_'+reader+'.resources.json'),resources)
    write_once(public/(mode+'_'+reader+'.json'),summary)
    print(json.dumps(dict(reader=reader,mode=mode,outputs=len(outputs),new_calls=summary['new_inference_calls'],
                          new_loads=summary['new_model_loads'],provenance=dict(Counter(r['provenance'] for r in origin)))),flush=True)


def execute(run, mode):
    from research.vlm_setup import environment
    local, public = paths(run)
    verify_lock(local, public)
    env = environment()
    env.update(HF_HOME=str(local/'runtime/hf'),HF_HUB_CACHE=str(local/'runtime/hf/hub'),
               TORCH_HOME=str(local/'runtime/torch'),TORCH_EXTENSIONS_DIR=str(local/'runtime/extensions'),PYTHONDONTWRITEBYTECODE='1')
    for reader in READERS:
        log = local/(mode+'_'+reader+'.log')
        if log.exists():
            raise FileExistsError('Inspect old process log; no silent retry/overwrite')
        command=[sys.executable,'-B','-m','research.evidence_contract.task5.pilot','worker','--run',run,'--reader',reader,'--mode',mode]
        print(json.dumps(dict(mode=mode,reader=reader,state='starting')),flush=True)
        start=time.perf_counter()
        with log.open('xb') as stream:
            process=subprocess.run(command,cwd=ROOT,env=env,stdout=stream,stderr=subprocess.STDOUT,check=False)
        write_once(public/(mode+'_'+reader+'.process.json'),dict(mode=mode,reader=reader,command=command,
            elapsed_seconds=time.perf_counter()-start,exit_code=process.returncode,stdout_sha256=sha_file(log)))
        print(json.dumps(dict(mode=mode,reader=reader,exit_code=process.returncode)),flush=True)
        if process.returncode:
            raise RuntimeError('Worker failed: preserve log and audit before any retry')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('prepare','fresh','resume','replay','worker','evaluate'))
    parser.add_argument('--run',default='pilot_01')
    parser.add_argument('--reader',choices=READERS)
    parser.add_argument('--mode',choices=('fresh','resume','replay'),default='fresh')
    parser.add_argument('--label',default='evaluation')
    args=parser.parse_args()
    if args.action=='prepare':prepare(args.run)
    elif args.action=='worker':worker(args.run,args.reader,args.mode)
    elif args.action=='evaluate':
        from .analysis import evaluate_run
        evaluate_run(args.run,args.label)
    else:execute(args.run,args.action)


if __name__=='__main__':main()
