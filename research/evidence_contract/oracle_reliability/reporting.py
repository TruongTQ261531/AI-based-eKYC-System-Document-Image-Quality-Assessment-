"""Descriptive oracle metrics. Abstention is not a correct binary decision."""
from collections import Counter

DECIDED = {'FAULT', 'NO_FAULT', 'STRUCTURAL_ERROR'}


def rate(n, d):
    return dict(numerator=n,denominator=d,value=n/d if d else None)


def cells_from_rows(rows):
    """Collapse observations before public release; no raw reviewer items or IDs."""
    counts=Counter()
    for row in rows:
        for method,lanes in row['methods'].items():
            for endpoint,decision in lanes.items():
                counts[(row['dataset'],row['partition'],row['contract'],row['cluster'],method,endpoint,
                        row['truth'][endpoint],decision['state'],decision['reason'])]+=1
    names=('dataset','partition','contract','cluster','method','endpoint','truth','state','reason')
    return [dict(zip(names,key),count=count) for key,count in sorted(counts.items(),key=lambda v:str(v[0]))]


def summarize(cells):
    total=sum(c['count'] for c in cells);known=decided=decided_known=errors=abstained_faults=0
    confusion=Counter(TP=0,FP=0,FN=0,TN=0);decided_confusion=Counter(TP=0,FP=0,FN=0,TN=0)
    alarms=Counter(total=0,labeled_fault=0,labeled_no_fault=0,unresolved=0)
    statuses=Counter();unknown=Counter()
    for c in cells:
        n=c['count'];state=c['state'];truth=c['truth'];is_decided=state in DECIDED
        alarm=state in {'FAULT','STRUCTURAL_ERROR'};statuses[state]+=n;decided+=n*is_decided
        if state not in DECIDED:unknown[c['reason']]+=n
        if alarm:
            alarms['total']+=n;alarms['unresolved' if truth is None else 'labeled_fault' if truth else 'labeled_no_fault']+=n
        if truth is None:continue
        known+=n;key=('TP' if alarm else 'FN') if truth else ('FP' if alarm else 'TN');confusion[key]+=n
        if is_decided:
            decided_known+=n;decided_confusion[key]+=n;errors+=n*(alarm!=truth)
        else:abstained_faults+=n*(truth is True)
    return dict(rows=total,labeled_rows=known,alarm_detection_confusion=dict(confusion),decided_confusion=dict(decided_confusion),
                decision_coverage_all=rate(decided,total),decision_coverage_labeled=rate(decided_known,known),
                sensitivity_all_labeled_faults=rate(confusion['TP'],confusion['TP']+confusion['FN']),
                FAR_all_labeled_nonfaults=rate(confusion['FP'],confusion['FP']+confusion['TN']),
                selective_risk=rate(errors,decided_known),abstained_labeled_faults=abstained_faults,
                alarm_accounting=dict(alarms),status_counts=dict(statuses),abstention_reasons=dict(unknown))


def report(cells):
    result={}
    for dataset in sorted({c['dataset'] for c in cells}):
        result[dataset]={}
        for partition in sorted({c['partition'] for c in cells if c['dataset']==dataset}):
            panel=[c for c in cells if c['dataset']==dataset and c['partition']==partition]
            views={'all':panel}
            for axis in ('contract','cluster'):
                for value in sorted({c[axis] for c in panel}):views[axis+':'+value]=[c for c in panel if c[axis]==value]
            result[dataset][partition]={}
            for view,subset in views.items():
                result[dataset][partition][view]={}
                for method in sorted({c['method'] for c in subset}):
                    result[dataset][partition][view][method]={endpoint:summarize([c for c in subset if c['method']==method and c['endpoint']==endpoint])
                        for endpoint in sorted({c['endpoint'] for c in subset if c['method']==method})}
    return result
