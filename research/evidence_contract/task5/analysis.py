"""Replay-only development comparisons. Never constructs a predictor."""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import replace
import time

from . import baselines
from .pilot import EC, READERS, paths, read, verify_lock, readonly_cached
from ..normalized_output import ReaderSpec
from ..runner import InputRequest, Runner, sha_file, write_once
from ..source_graph import EvidenceGraph, digest
from ..smoke_task4 import _report_from_dict
from ..evaluator import observe_fields, summarize, rate


def _method_summary(rows, method):
    selected = [(r, r['checks'][method]) for r in rows]
    alarms = [(r, c) for r, c in selected if c['alarm']]
    return dict(scheduled_contract_key_evaluations=len(selected),
        unique_contract_output_packs=len({r['evaluation_id'] for r in rows}),
        verdicts=dict(Counter(c['verdict'] for _, c in selected)), alarms=len(alarms),
        confirmed_violations=sum(c['confirmed'] for _, c in selected), confirmed_software_defects=0,
        independent_gold_labels=0, false_alarms=None, alarm_precision=rate(0,0), alarm_recall=rate(0,0), false_alarm_rate=rate(0,0),
        alarms_on_validator_invalid_attempts=sum(r['validity']=='INVALID_TEST' for r,c in alarms),
        alarms_on_validator_unknown_attempts=sum(r['validity']=='INCONCLUSIVE' for r,c in alarms),
        candidate_taxonomy=dict(Counter(category for _,c in alarms for category in c['categories'])),
        validity=dict(Counter(r['validity'] for r in rows)),
        original_already_wrong_or_unverified=sum('original_already_wrong' in c['reason'] for _,c in selected),
        decision_coverage=rate(sum(c['verdict'] in ('PASS','CANDIDATE_VIOLATION','CONFIRMED_VIOLATION') for _,c in selected),len(selected)),
        unit='scheduled contract-key packs; repeated seeds/views are not independent documents')


def evaluate_run(run, label):
    local, public = paths(run)
    verify_lock(local,public)
    packs=read(local/'scoring.json')['packs']
    inputs={r['pixel_sha256']:InputRequest(**r) for r in read(local/'inputs.json')['inputs']}
    outputs, all_events, event_hashes, event_snapshots, workers = {}, [], {}, {}, {}
    for reader in READERS:
        spec=ReaderSpec(**read(local/reader/(reader+'.spec.json')))
        runner=Runner(spec,local/reader)  # No loader, no infer() call.
        old_path=EC/'local/smoke_02'/reader
        old=Runner(spec,old_path) if (old_path/(reader+'.spec.json')).exists() and read(old_path/(reader+'.spec.json'))==spec.to_dict() else None
        logs=[runner.events]+([old.events] if old else [])
        for log in logs:
            if log.path.exists():
                event_hashes[str(log.path)]=sha_file(log.path)
                event_snapshots[str(log.path.relative_to(EC))]=log.read()
                all_events.extend(log.read())
        for key, request in inputs.items():
            value=readonly_cached(runner,request)
            if value is None and old:
                value=readonly_cached(old,request)
            if value is None:
                raise ValueError('Missing cached output; scoring cannot call a model')
            if value.output_origin != 'actual_model':
                raise ValueError('Injected control output cannot enter real-model pilot analysis')
            outputs[(reader,key)]=value
        workers[reader]=read(public/('fresh_'+reader+'.json'))
    rows, a_decisions= [], defaultdict(list)
    visible_fields,full_fields=defaultdict(list),defaultdict(list)
    per_arm_costs=defaultdict(lambda:dict(logical_requests=0,native_latency_seconds=0.,native_cpu_seconds=0.))
    start,cpu=time.perf_counter(),time.process_time()
    for raw in packs:
        graph=EvidenceGraph.from_dict(raw['graph'])
        report=_report_from_dict(raw['pair']['validation'])
        for reader in READERS:
            before=outputs[(reader,report.before_pixel_sha256)]
            after=outputs[(reader,report.after_pixel_sha256)]
            checks=baselines.run_checks(graph,report,before,after)
            values={name:baselines.unpack(value) for name,value in checks.items()}
            row=dict(pack_id=raw['pack_id'],arm=raw['arm'],selection_seed=raw['selection_seed'],stratum=raw['stratum'],
                reader=reader,contract_id=report.mutation.contract_id,key=baselines.key_for(report),
                output_origin=after.output_origin,
                graph_sha256=graph.sha256,mutation_sha256=report.mutation_sha256,
                evaluation_id=checks['A'].decision_sha256, physical_id_sha256=digest(graph.physical_id),
                original_pixel_sha256=report.before_pixel_sha256,followup_pixel_sha256=report.after_pixel_sha256,
                source_kinds=sorted({s.kind for f in graph.fields for s in f.realizations}),
                validity=report.status.value,validity_reasons=report.reasons,checks=values)
            rows.append(row)
            if raw['stratum']=='primary':
                arm=raw['arm']
                a_decisions[arm].append(checks['A'])
                visible_fields[arm].extend(observe_fields(graph,before))
                full_fields[arm].extend(observe_fields(graph,before))
                if report.after_graph:
                    visible_fields[arm].extend(observe_fields(report.after_graph,after))
                full=replace(graph,input_pixel_sha256=after.input_pixel_sha256,
                             width=report.mutation.output_size[0],height=report.mutation.output_size[1],input_file_sha256=None)
                full_fields[arm].extend(replace(f,reference_basis='full_reference_inaccessible_fields_included') for f in observe_fields(full,after))
    oracle_wall,oracle_cpu=time.perf_counter()-start,time.process_time()-cpu
    # Price the identical logical request quota even when physical raw results
    # were shared/reused. No quota bonus for cache hits or duplicate seed views.
    for arm in ('A','B1'):
        for seed in (42,31415):
            block=[r for r in packs if r['arm']==arm and r['selection_seed']==seed and r['stratum']=='primary']
            pixels={v for r in block for v in (r['pair']['original_pixel_sha256'],r['pair']['input_pixel_sha256'])}
            assert len(pixels)==10
            for reader in READERS:
                for pixel in pixels:
                    output=outputs[(reader,pixel)]
                    per_arm_costs[arm]['logical_requests']+=1
                    per_arm_costs[arm]['native_latency_seconds']+=output.latency_seconds
                    per_arm_costs[arm]['native_cpu_seconds']+=output.cpu_seconds
    methods=list(rows[0]['checks'])
    report=dict(schema='task5-development-comparison/1',scope='exploratory fixtures/development only; no independent failure gold',
        primary={},diagnostics={},models={},comparisons={},resources={r:workers[r]['resources'] for r in READERS},
        proposal_and_selection=read(public/'preparation.json'),new_actual_model_calls=sum(workers[r]['new_inference_calls'] for r in READERS),
        new_calls_during_scoring=0,historical_cache_uses=sum(x['provenance']=='TASK4_read_only_cache' for r in READERS for x in workers[r]['provenance']),
        oracle_wall_seconds=oracle_wall,oracle_cpu_seconds=oracle_cpu,per_arm_charged_costs=dict(per_arm_costs),
        annotation_person_minutes=None,confirmed_real_model_failures=0,confirmed_software_defects=0,
        false_alarms=None,inference_event_hashes=event_hashes,
        unique_physical_ids=len({r['physical_id_sha256'] for r in rows}),
        actual_unique_input_reader_outputs=len(outputs),
        synthetic_output_injections_in_real_model_results=0,
        late_model_or_prompt_changes=False)
    for arm in ('A','B1'):
        subset=[r for r in rows if r['arm']==arm]
        report['primary'][arm]={method:_method_summary(subset,method) for method in methods}
        report['comparisons'][arm]=dict(
            A_alarm_not_B0=sum(r['checks']['A']['alarm'] and not r['checks']['B0']['alarm'] for r in subset),
            A_alarm_not_B2=sum(r['checks']['A']['alarm'] and not r['checks']['B2']['alarm'] for r in subset),
            A_alarm_not_B3=sum(r['checks']['A']['alarm'] and not r['checks']['B3']['alarm'] for r in subset),
            B3_alarm_not_A=sum(r['checks']['B3']['alarm'] and not r['checks']['A']['alarm'] for r in subset),
            A_flat_verdict_agreement=rate(sum(r['checks']['A']['verdict']==r['checks']['A_flat']['verdict'] for r in subset),len(subset)),
            A_no_validator_verdict_agreement=rate(sum(r['checks']['A']['verdict']==r['checks']['A_no_validator']['verdict'] for r in subset),len(subset)),
            C3_A_alarms=sum(r['contract_id']=='C3' and r['checks']['A']['alarm'] for r in subset),
            C3_A_alarm_not_B3=sum(r['contract_id']=='C3' and r['checks']['A']['alarm'] and not r['checks']['B3']['alarm'] for r in subset))
        report['primary'][arm]['visible_field_metrics']=summarize([],visible_fields[arm],[],include_groups=False)
        report['primary'][arm]['full_reference_field_metrics']=summarize([],full_fields[arm],[],include_groups=False)
        ids={x for d in a_decisions[arm] for x in (d.before_call_id,d.after_call_id)}
        events=[e for e in all_events if e.get('call_id') in ids or e['event'].startswith('model_load_')]
        report['primary'][arm]['A_evaluator_deduplicated']=summarize(a_decisions[arm],visible_fields[arm],events,new_run_ids=set())
    for name in sorted({r['stratum'] for r in rows if r['stratum']!='primary'}):
        subset=[r for r in rows if r['stratum']==name]
        report['diagnostics'][name]={method:_method_summary(subset,method) for method in methods}
    for reader in READERS:
        report['models'][reader]={arm:{method:_method_summary([r for r in rows if r['reader']==reader and r['arm']==arm],method)
                                             for method in methods} for arm in ('A','B1','shared_diagnostic')}
    report['by_contract']={arm:{contract:{method:_method_summary([r for r in rows if r['arm']==arm and r['contract_id']==contract],method)
                                                      for method in methods} for contract in ('C1','C2','C3','C4')}
                              for arm in ('A','B1','shared_diagnostic')}
    for path,expected in event_hashes.items():
        if sha_file(path)!=expected:
            raise ValueError('Scoring modified an inference event log')
    report['all_inference_logs_unchanged_by_scoring']=True
    report['code_sha256']=read(public/'pilot_lock.json')['code_sha256']
    # Performance timings differ across replays; the semantic payload is compared separately.
    report['semantic_payload_sha256']=digest(dict(rows=rows,
        comparisons=report['comparisons'],primary={arm:{m:report['primary'][arm][m] for m in methods} for arm in ('A','B1')},
        diagnostics=report['diagnostics']))
    write_once(public/(label+'.checks.json'),dict(rows=rows))
    write_once(public/(label+'.events.json'),event_snapshots)
    write_once(public/(label+'.json'),report)
    print(__import__('json').dumps(dict(label=label,new_calls=report['new_actual_model_calls'],scoring_calls=0,
        comparisons=report['comparisons'],A=report['primary']['A']['A']['verdicts'],B1=report['primary']['B1']['A']['verdicts'])),flush=True)
