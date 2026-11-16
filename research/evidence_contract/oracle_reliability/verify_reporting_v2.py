"""Independent supplement arithmetic; does not import the report generator."""
import hashlib
import json
from pathlib import Path
import sys

from .verify import fraction, need, recalculate


def verify(source,report):
    raw=Path(source).read_bytes();cells=json.loads(raw);result=json.loads(Path(report).read_bytes())
    need(hashlib.sha256(raw).hexdigest()==result['input_sha256'],'Source hash')
    need(result['source_cells']==len(cells),'Cell count')
    need(result['confirmatory'] is False and result['new_observations']==result['labels_changed']==result['model_calls']==result['training_runs']==0,'Scope')
    expected=set()
    for c in cells:
        need(type(c['count']) is int and c['count']>0,'Count')
        need(c['truth'] is None or type(c['truth']) is bool,'Truth')
        for view in ('all','contract:'+c['contract'],'cluster:'+c['cluster']):
            expected.add((c['dataset'],c['partition'],view,c['method'],c['endpoint']))
    observed=set()
    for group in result['groups']:
        key=tuple(group[k] for k in ('dataset','partition','view','method','endpoint'))
        need(key not in observed,'Duplicate group');observed.add(key)
        ds,part,view,method,endpoint=key
        pool=[c for c in cells if (c['dataset'],c['partition'],c['method'],c['endpoint'])==(ds,part,method,endpoint)]
        if view!='all':
            axis,value=view.split(':',1);need(axis in ('contract','cluster'),'View');pool=[c for c in pool if c[axis]==value]
        base=recalculate(pool);n=base['rows']
        count=lambda state:sum(c['count'] for c in pool if c['state']==state)
        extra=dict(abstention_unknown=fraction(count('UNKNOWN'),n),invalid_test=fraction(count('INVALID_TEST'),n),
            combined_deferral=fraction(count('UNKNOWN')+count('INVALID_TEST'),n),
            structural_error=fraction(count('STRUCTURAL_ERROR'),n),truth_availability=fraction(base['labeled_rows'],n))
        need(group['metrics']==dict(base=base,rates=extra,unresolved_truth_rows=n-base['labeled_rows']),'Accounting differs')
        need(base['decision_coverage_all']['numerator']+extra['combined_deferral']['numerator']==n,'Decision partition')
    need(observed==expected and len(observed)==result['metric_groups'],'Missing/extra groups')
    return dict(status='PASS',groups=len(observed),cells=len(cells),new_labels=0,scope='Independent arithmetic, not independent truth')


if __name__=='__main__':print(json.dumps(verify(*sys.argv[1:]),indent=2))
