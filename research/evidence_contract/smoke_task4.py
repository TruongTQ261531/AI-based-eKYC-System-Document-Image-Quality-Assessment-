"""Fixed four-input development fixture smoke. Never a benchmark/test-set run.

prepare is separate from reader workers so rendering dependencies do not share
GPU/RAM with Vintern. evaluate/replay never call a predictor factory.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, replace
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
EC = Path(__file__).resolve().parent
READERS = ("rapid_v4", "rapid_latin_v5", "partial_42")


def _paths(run):
    if not run or not all(c.isalnum() or c in "_-" for c in run):
        raise ValueError("Expected an opaque run name")
    return EC / "local" / run, EC / "execution/task4_runner" / run


def prepare(run):
    from .fixtures import backup_fixture
    from .generator import generate, plan, png_bytes
    from .runner import InputRequest, write_once, sha_file
    from .source_graph import pixel_sha256
    local, public = _paths(run)
    local.mkdir(parents=True, exist_ok=False)
    public.mkdir(parents=True, exist_ok=False)
    image, graph, a, b = backup_fixture()
    inputs_dir = local / "inputs"
    inputs_dir.mkdir()
    original_path = inputs_dir / (pixel_sha256(image) + ".png")
    with original_path.open("xb") as stream:
        stream.write(png_bytes(image))
    graph = replace(graph, input_file_sha256=sha_file(original_path))
    all_mask = plan(graph, "all_sources_mask", target_key=a, seed=42)
    mutations = [all_mask, plan(graph, "single_source_mask", target_key=a, seed=42),
                 replace(all_mask, contract_id="C3", kind="pair_a_mask", retained_key=b),
                 plan(graph, "geometry_translate", target_key=a, seed=42)]
    pairs = [generate(image, graph, m) for m in mutations]
    requests = {}
    def add(pixels):
        pixel_hash = pixel_sha256(pixels)
        path = inputs_dir / (pixel_hash + ".png")
        if not path.exists():
            with path.open("xb") as stream:
                stream.write(png_bytes(pixels))
        requests[pixel_hash] = InputRequest(str(path), sha_file(path), pixel_hash, "fixture", "fictional")
        return pixel_hash
    add(image)
    for pair in pairs:
        add(pair.followup)
    if len(requests) != 4:
        raise ValueError("This fixed smoke must have exactly four unique image inputs")
    input_manifest = dict(schema="pixels-only-inputs/1", inputs=[asdict(requests[k]) for k in sorted(requests)])
    write_once(local / "inputs.json", input_manifest)
    write_once(local / "scoring.json", dict(graph=graph.to_dict(), pairs=[p.metadata() for p in pairs]))
    summary = dict(schema="task4-smoke-preparation/1", timestamp_utc=datetime.now(timezone.utc).isoformat(),
        role="fixture", data_policy="fictional", seeds=[42], physical_ids=1, unique_originals=1,
        unique_images=len(requests), generated_pairs=len(pairs), scheduled_readers=list(READERS),
        planned_image_reader_invocations=len(READERS) * len(requests),
        contract_validity=[dict(contract=p.mutation.contract_id, validity=p.validation.status.value,
                                reasons=p.validation.reasons, graph_sha256=p.graph.sha256,
                                mutation_sha256=p.mutation.sha256,
                                original_pixel_sha256=p.validation.before_pixel_sha256,
                                followup_pixel_sha256=p.validation.after_pixel_sha256) for p in pairs],
        inputs_manifest_sha256=sha_file(local / "inputs.json"), scoring_manifest_sha256=sha_file(local / "scoring.json"),
        output_injections=False, human_readability_labels=False, confirmatory_test_opened=False)
    write_once(public / "preparation.json", summary)
    if any(p.validation.status.value != "VALID" for p in pairs):
        raise ValueError("Fixture mutation invalid; no reader run is allowed")
    print(json.dumps(dict(prepared=run, images=len(requests), pairs=len(pairs), planned_calls=12)), flush=True)


def execute(run, mode):
    """Standard-library orchestrator: one frozen worker at a time."""
    from .runner import write_once, sha_file
    from research.vlm_setup import environment
    local, public = _paths(run)
    preparation = json.loads((public / "preparation.json").read_text(encoding="utf-8"))
    if sha_file(local / "inputs.json") != preparation["inputs_manifest_sha256"]:
        raise ValueError("Smoke inputs changed after preparation")
    if any(p["validity"] != "VALID" for p in preparation["contract_validity"]):
        raise ValueError("Not an admissible fixture smoke")
    env = environment()
    env.update(HF_HOME=str(local / "runtime/hf"), HF_HUB_CACHE=str(local / "runtime/hf/hub"),
               TORCH_HOME=str(local / "runtime/torch"), TORCH_EXTENSIONS_DIR=str(local / "runtime/extensions"),
               PYTHONDONTWRITEBYTECODE="1")
    exits = []
    for reader in READERS:
        summary = public / (mode + "_" + reader + ".json")
        log = local / (mode + "_" + reader + ".log")
        if summary.exists() or log.exists():
            raise FileExistsError("Process artifacts already exist; inspect them, do not silently rerun")
        command = [sys.executable, "-B", "-m", "research.evidence_contract.runner", "--reader", reader,
                   "--inputs", str(local / "inputs.json"), "--store", str(local / reader), "--summary", str(summary)]
        if mode == "replay":
            command.append("--replay")
        start = time.perf_counter()
        print(json.dumps(dict(mode=mode, reader=reader, state="starting")), flush=True)
        with log.open("xb") as stream:
            process = subprocess.run(command, cwd=ROOT, env=env, stdout=stream, stderr=subprocess.STDOUT, check=False)
        result = dict(mode=mode, reader=reader, exit_code=process.returncode,
                      elapsed_seconds=time.perf_counter() - start, command=command,
                      stdout_log_sha256=sha_file(log), stdout_log_public=False)
        write_once(public / (mode + "_" + reader + ".process.json"), result)
        exits.append(result)
        print(json.dumps(dict(mode=mode, reader=reader, exit_code=process.returncode)), flush=True)
    if any(r["exit_code"] for r in exits):
        raise RuntimeError("Some smoke workers failed. Keep their logs and inspect; no automatic retry")


def _report_from_dict(raw):
    from .source_graph import EvidenceGraph
    from .validity import Mutation, ValidationReport, Validity
    mutation = dict(raw["mutation"])
    for key in ("hidden_source_ids", "output_size", "fill", "expected_source_state", "homography", "mask_geometry"):
        mutation[key] = tuple(mutation[key])
    return ValidationReport(Validity(raw["status"]), tuple(raw["reasons"]), raw["graph_sha256"],
        raw["mutation_sha256"], raw["before_pixel_sha256"], raw["after_pixel_sha256"], Mutation(**mutation),
        EvidenceGraph.from_dict(raw["after_graph"]) if raw["after_graph"] else None,
        raw["measurements"], tuple(raw.get("review_required", ())),
        EvidenceGraph.from_dict(raw["reference_before_graph"]) if raw.get("reference_before_graph") else None)


def evaluate_run(run, label):
    from .evaluator import summarize, observe_fields, missing_fields
    from .normalized_output import ReaderSpec
    from .oracle import evaluate
    from .runner import Runner, InputRequest, write_once, sha_file
    from .source_graph import EvidenceGraph, digest
    local, public = _paths(run)
    preparation = json.loads((public / "preparation.json").read_text(encoding="utf-8"))
    if sha_file(local / "scoring.json") != preparation["scoring_manifest_sha256"]:
        raise ValueError("Scoring reference changed")
    manifest = json.loads((local / "inputs.json").read_text(encoding="utf-8"))
    if sha_file(local / "inputs.json") != preparation["inputs_manifest_sha256"]:
        raise ValueError("Input manifest changed")
    requests = {row["pixel_sha256"]: InputRequest(**row) for row in manifest["inputs"]}
    source = json.loads((local / "scoring.json").read_text(encoding="utf-8"))
    graph = EvidenceGraph.from_dict(source["graph"])
    reports = [_report_from_dict(pair["validation"]) for pair in source["pairs"]]
    decisions, observations, event_rows, hashes, missing = [], [], [], {}, []
    fresh_ids = set()
    for reader in READERS:
        spec = ReaderSpec(**json.loads((local / reader / (reader + ".spec.json")).read_text(encoding="utf-8")))
        runner = Runner(spec, local / reader)  # No loader. Cannot call a model.
        event_before = sha_file(runner.events.path)
        outputs = {key: runner.infer(request, replay=True) for key, request in requests.items()}
        for report in reports:
            before = outputs[report.before_pixel_sha256]
            after = outputs[report.after_pixel_sha256]
            decisions.append(evaluate(graph, report, before, after))
            observations.extend(observe_fields(graph, before))
            if report.after_graph:
                observations.extend(observe_fields(report.after_graph, after))
                missing.append(dict(reader=reader, pair=digest([graph.sha256, report.mutation_sha256]),
                                    **missing_fields(report.after_graph, after)))
        event_after = sha_file(runner.events.path)
        if event_before != event_after:
            raise ValueError("Scoring replay changed the inference event log")
        hashes[reader] = event_after
        event_rows.extend(runner.events.read())
        fresh_ids.add(json.loads((public / ("fresh_" + reader + ".json")).read_text(encoding="utf-8"))["run_id"])
    process_runs = [json.loads((public / ("fresh_" + r + ".process.json")).read_text(encoding="utf-8")) for r in READERS]
    # This action only rescores stored calls; "new" refers to this analysis, not the old fresh run.
    score = summarize(decisions, observations, event_rows, new_run_ids=set(), process_runs=process_runs)
    score["originating_fresh_run_ids"] = sorted(fresh_ids)
    score["new_actual_model_invocations_during_scoring"] = 0
    score["scope"] = "TASK4 wiring smoke only: one fictional physical ID, no independent failure labels"
    score["event_log_sha256"] = hashes
    score["decisions"] = [d.to_dict() for d in decisions]
    score["missing_fields_scoring_join"] = missing
    score["scorer_code_sha256"] = {name: sha_file(EC / name) for name in (
        "oracle.py", "evaluator.py", "normalized_output.py", "smoke_task4.py")}
    # Public aggregate output contains no field/reference strings, OCR boxes or face embeddings.
    write_once(public / (label + ".json"), score)
    print(json.dumps(dict(evaluation=label, model_calls=score['budget']['image_reader_invocations'],
                          candidate=score['candidate_violation_count'], verified=score['verified_failure_count'],
                          verdicts=score['verdict_counts'])), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "fresh", "resume", "replay", "evaluate"))
    parser.add_argument("--run", default="smoke_01")
    parser.add_argument("--label", default="evaluation")
    args = parser.parse_args()
    if args.action == "prepare":
        prepare(args.run)
    elif args.action == "evaluate":
        evaluate_run(args.run, args.label)
    else:
        execute(args.run, args.action)


if __name__ == "__main__":
    main()
