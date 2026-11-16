"""Standalone stdlib arithmetic and file-integrity verifier, not a truth oracle.

Does not import policy/reporting or private reviewer data. Public contingency
cells suffice for arithmetic; organizer-only replay verifies the private joins.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def need(value,message):
    if not value:raise ValueError(message)


def fraction(n,d):
    return {'numerator':n,'denominator':d,'value':n/d if d else None}


def recalculate(cells):
    counts={k:0 for k in ('TP','FP','FN','TN')};binary=dict(counts)
    status=Counter();reasons=Counter();alarm={'total':0,'labeled_fault':0,'labeled_no_fault':0,'unresolved':0}
    n=k=d=dk=mistakes=missed_abstain=0
    for row in cells:
        weight=row['count'];truth=row['truth'];state=row['state']
        n+=weight;status[state]+=weight;emit=state in ('FAULT','STRUCTURAL_ERROR')
        decides=state in ('FAULT','NO_FAULT','STRUCTURAL_ERROR');d+=weight*decides
        if not decides:reasons[row['reason']]+=weight
        if emit:
            alarm['total']+=weight
            alarm['unresolved' if truth is None else 'labeled_fault' if truth else 'labeled_no_fault']+=weight
        if truth is None:continue
        k+=weight
        category={True:{True:'TP',False:'FN'},False:{True:'FP',False:'TN'}}[truth][emit]
        counts[category]+=weight
        if decides:
            dk+=weight;binary[category]+=weight;mistakes+=weight*(truth!=emit)
        elif truth:missed_abstain+=weight
    return dict(rows=n,labeled_rows=k,alarm_detection_confusion=counts,decided_confusion=binary,
                decision_coverage_all=fraction(d,n),decision_coverage_labeled=fraction(dk,k),
                sensitivity_all_labeled_faults=fraction(counts['TP'],counts['TP']+counts['FN']),
                FAR_all_labeled_nonfaults=fraction(counts['FP'],counts['FP']+counts['TN']),
                selective_risk=fraction(mistakes,dk),abstained_labeled_faults=missed_abstain,
                alarm_accounting=alarm,status_counts=dict(status),abstention_reasons=dict(reasons))


def verify(folder):
    folder=Path(folder).resolve();manifest=read(folder/'manifest.json')
    need(set(manifest['files'])=={'control_cases.json','aggregate_cells.json','results.json'},'Unexpected artifact manifest')
    for name,expected in manifest['files'].items():
        need(hashlib.sha256((folder/name).read_bytes()).hexdigest()==expected,'File hash mismatch: '+name)
    result=read(folder/'results.json');cells=read(folder/'aggregate_cells.json');controls=read(folder/'control_cases.json')
    need(result['model_calls']==0 and result['training_runs']==0 and result['confirmatory'] is False,'Scope overclaim')
    need(len(controls)==result['control_cases']==len({c['comparison_id'] for c in controls}),'Control identity duplication')
    for c in controls:
        need(c['origin']=='oracle_unit_injected' and c['physical_ids']==0,'Control mislabeled as real evidence')
        payload={k:v for k,v in c.items() if k in {'context','reference_payload','before_raw','after_raw','actual_origin_probe','tamper_after_seal'}}
        raw=json.dumps(payload,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf-8')
        need(hashlib.sha256(raw).hexdigest()==c['comparison_id'],'Control identity content changed')
        need(c['expected']==[c['methods']['B_tier1'][e]['state'] for e in ('pointwise','relation','structure')],'Expected/observed mismatch')
        for tier in (1,2):
            for e in ('pointwise','relation','structure'):
                need(c['methods']['B_tier'+str(tier)][e]['state']==c['methods']['flat_tier'+str(tier)][e]['state'],'Parity mismatch')
    for row in cells:
        need(type(row['count']) is int and row['count']>0,'Invalid contingency count')
        need(row['truth'] is None or type(row['truth']) is bool,'Invalid truth category')
        need(row['state'] in {'FAULT','NO_FAULT','UNKNOWN','INVALID_TEST','STRUCTURAL_ERROR'},'Invalid decision category')
    projected=Counter()
    for control in controls:
        truth=dict(zip(('pointwise','relation','structure'),control['truth']))
        for method,lanes in control['methods'].items():
            for endpoint,lane in lanes.items():
                projected[(control['context']['contract'],method,endpoint,truth[endpoint],lane['state'],lane['reason'])]+=1
    published=Counter()
    for cell in cells:
        if cell['dataset']=='symbolic_controls':
            need(cell['partition']=='development' and cell['cluster']=='symbolic_not_physical','Symbolic cohort relabeled')
            published[(cell['contract'],cell['method'],cell['endpoint'],cell['truth'],cell['state'],cell['reason'])]+=cell['count']
    need(projected==published,'Control outputs do not match aggregate cells')
    recomputed={};groups=0
    for dataset in sorted({c['dataset'] for c in cells}):
        recomputed[dataset]={}
        for partition in sorted({c['partition'] for c in cells if c['dataset']==dataset}):
            pool=[c for c in cells if c['dataset']==dataset and c['partition']==partition]
            views={'all':pool}
            for field in ('contract','cluster'):
                for value in sorted({c[field] for c in pool}):views[field+':'+value]=[c for c in pool if c[field]==value]
            recomputed[dataset][partition]={}
            for view,subset in views.items():
                recomputed[dataset][partition][view]={}
                for method in sorted({c['method'] for c in subset}):
                    recomputed[dataset][partition][view][method]={}
                    for endpoint in sorted({c['endpoint'] for c in subset if c['method']==method}):
                        matching=[c for c in subset if c['method']==method and c['endpoint']==endpoint]
                        recomputed[dataset][partition][view][method][endpoint]=recalculate(matching);groups+=1
    need(recomputed==result['results'],'Report arithmetic or grouping differs')
    for dataset,partitions in recomputed.items():
        for partition,views in partitions.items():
            sizes={r['rows'] for lanes in views['all'].values() for r in lanes.values()}
            expected=len(controls) if dataset=='symbolic_controls' else 42 if partition=='primary' else 4
            need(sizes=={expected},'Paired methods have unequal denominators')
    return dict(status='PASS',metric_groups=groups,control_cases=len(controls),public_contingency_cells=len(cells),
                private_labels_reproduced=False,policy_reexecuted=False,scope='File integrity and independent arithmetic only')


if __name__=='__main__':
    print(json.dumps(verify(sys.argv[1]),indent=2))
