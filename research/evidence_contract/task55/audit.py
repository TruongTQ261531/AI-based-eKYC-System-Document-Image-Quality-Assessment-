"""Disaggregate and replay frozen oracle decisions. No model inference."""
from __future__ import annotations

import ast
from collections import Counter,defaultdict
import random
import statistics
import time

from .data import EC,ROOT,OUT,PUBLIC,FrozenPilot,read,save_new,digest,sha
from ..task5 import baselines


def comparison(rows):
    pairs=Counter((r['checks']['A']['verdict'],r['checks']['B3']['verdict']) for r in rows)
    return dict(n=len(rows),verdict_agreement=sum(r['checks']['A']['verdict']==r['checks']['B3']['verdict'] for r in rows),
        alarm_agreement=sum(r['checks']['A']['alarm']==r['checks']['B3']['alarm'] for r in rows),
        A_flat_verdict_agreement=sum(r['checks']['A']['verdict']==r['checks']['A_flat']['verdict'] for r in rows),
        A_alarms=sum(r['checks']['A']['alarm'] for r in rows),B3_alarms=sum(r['checks']['B3']['alarm'] for r in rows),
        A_exclusive_alarms=sum(r['checks']['A']['alarm'] and not r['checks']['B3']['alarm'] for r in rows),
        original_wrong_exclusions=sum('original_already_wrong' in r['checks']['A']['reason'] for r in rows),
        confusion=[dict(A=a,B3=b,n=n) for (a,b),n in sorted(pairs.items())])


def function_map(path):
    tree=ast.parse(path.read_text(encoding='utf-8'))
    result={}
    for node in ast.walk(tree):
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
            calls=[]
            for sub in ast.walk(node):
                if isinstance(sub,ast.Call):
                    try:calls.append(ast.unparse(sub.func))
                    except ValueError:pass
            result[node.name]=dict(line=node.lineno,end_line=node.end_lineno,calls=sorted(set(calls)))
    return result


def run(label):
    pilot=FrozenPilot();primary=[r for r in pilot.rows if r['stratum']=='primary']
    instances=list(pilot.instances());row_map={(r['pack_id'],r['reader']):r for r in pilot.rows}
    enriched=[];recomputed=[]
    for raw,graph,report,before,after in instances:
        row=dict(row_map[(raw['pack_id'],after.reader_id)])
        key=baselines.key_for(report);original=graph.field(key)
        field=report.after_graph.field(key) if report.after_graph else None
        row.update(perturbation=report.mutation.kind,operator=report.mutation.operator,
            evaluated_source_kinds=sorted({s.kind for s in original.realizations}),
            remaining_supported_source_kinds=sorted({s.kind for s in field.supported_sources()}) if field else [],
            source_multiplicity='multiple' if len(original.realizations)>1 else 'single',
            field_key=key,after_field_state=field.state().value if field else 'NO_GRAPH',
            coverage=original.coverage,source_count=len(original.realizations))
        actual={m:baselines.unpack(v) for m,v in baselines.run_checks(graph,report,before,after).items()}
        if actual!=row['checks']:raise ValueError('Frozen method replay differs from TASK5')
        enriched.append(row);recomputed.append(dict(pack_id=raw['pack_id'],reader=after.reader_id,checks=actual))
    groups={}
    for dimension,getter in (
        ('contract',lambda r:[r['contract_id']]),('arm',lambda r:[r['arm']]),('reader',lambda r:[r['reader']]),
        ('field',lambda r:[r['field_key']]),('source',lambda r:r['evaluated_source_kinds']),
        ('remaining_source',lambda r:r['remaining_supported_source_kinds'] or ['none_or_unknown']),
        ('multiplicity',lambda r:[r['source_multiplicity']]),('operator',lambda r:[r['operator']]),
        ('perturbation',lambda r:[r['perturbation']])):
        buckets=defaultdict(list)
        for row in enriched:
            if row['stratum']=='primary':
                for name in getter(row):buckets[name].append(row)
        groups[dimension]={key:comparison(value) for key,value in sorted(buckets.items())}
    code={name:function_map(EC/name) for name in ('contracts.py','oracle.py','source_graph.py','validity.py','task5/baselines.py')}
    # Alternating paired order; same cached packs, no extraction or validation calls.
    timing=[]
    for seed in (42,31415,20261106):
        order=list(range(len(instances)));rng=random.Random(seed);rng.shuffle(order)
        samples={'A':[],'B3':[]};status={'A':[],'B3':[]}
        for index in order:
            raw,graph,report,before,after=instances[index]
            names=['A','B3'];rng.shuffle(names)
            for name in names:
                function=baselines.proposed if name=='A' else baselines.visible_reference
                start=time.perf_counter_ns();result=function(graph,report,before,after)
                elapsed=time.perf_counter_ns()-start
                samples[name].append(elapsed)
                status[name].append((index,baselines.unpack(result)['verdict']))
        timing.append(dict(seed=seed,cached_pack_count=len(order),model_calls=0,
            methods={name:dict(total_seconds=sum(value)/1e9,median_call_ms=statistics.median(value)/1e6,
                p95_call_ms=sorted(value)[int(.95*(len(value)-1))]/1e6,
                status_sha256=digest(sorted(status[name]))) for name,value in samples.items()}))
    artifacts=[]
    for p in sorted((EC/'execution/task5_pilot').rglob('*')):
        if p.is_file():
            data=p.read_bytes()
            if p.suffix=='.json':read(p)
            elif p.suffix in ('.log','.md','.xml','.py'):data.decode('utf-8-sig',errors='replace')
            artifacts.append(dict(path=p.relative_to(ROOT).as_posix(),bytes=len(data),sha256=sha(p)))
    pilot.assert_read_only()
    result=dict(task='TASK5.5',scope='reanalysis of development outputs only',model_calls=0,
        primary=comparison(primary),diagnostic=comparison([r for r in pilot.rows if r['stratum']!='primary']),
        groups=groups,source_group_policy='evaluated field sources, not all sources anywhere on card; groups overlap',
        baseline_identity_correction='120/120 is A vs A_flat; A vs B3 is 78/120 verdict and 79/120 alarm agreement',
        frozen_replay_matches_all_methods=True,reader_outputs_verified=len(pilot.outputs),
        independent_gold_labels_created=0,confirmed_real_failures=0,
        sharing=dict(A_and_B3=['contracts.assessment','Field.state/supported_sources','normalized/value precision',
            'same ValidationReport','same normalized reader outputs','same extraction policy and semantic key'],
            A_flat_calls_B3=True,A_flat_independent_reimplementation=False,confidence_threshold=None),
        function_maps=code,timing=timing,
        timing_scope='implemented oracle calls incl A provenance/hash/diagnostics vs simpler B3; not matched tracing overhead or independent statistical samples',
        artifact_inventory=artifacts,log_hashes=pilot.log_hashes,
        rows=enriched,unchanged_frozen_artifacts=True)
    save_new(OUT/(label+'.json'),result)
    print(__import__('json').dumps(dict(primary=result['primary'],reader_outputs=len(pilot.outputs),model_calls=0,artifacts_checked=len(artifacts))),flush=True)


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--label',default='audit_run_01');args=parser.parse_args()
    if not args.label or not all(c.isalnum() or c in '_-' for c in args.label):raise ValueError('Invalid label')
    run(args.label)
