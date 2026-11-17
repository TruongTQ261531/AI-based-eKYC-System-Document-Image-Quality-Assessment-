"""Independent stdlib arithmetic audit of public aggregates, without private joins.

This checks accounting, not the truth of a review. The separate private replay
verifies provenance and the exact paired frame.
"""
from collections import Counter
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent


def need(condition,message):
    if not condition:raise ValueError(message)


def equal(actual,expected):
    need(actual==expected if expected is None or not isinstance(expected,float)
         else isinstance(actual,(int,float)) and math.isclose(actual,expected,rel_tol=1e-12,abs_tol=1e-12),
         'Arithmetic mismatch')


def rate(value,n,d):
    equal(value['numerator'],n);equal(value['denominator'],d)
    equal(value['value'],n/d if d else None)


def verify_table(value):
    cells={}
    for c in value['contingencies']:
        key=(c['first'],c['second'])
        need(key not in cells and type(c['count']) is int and c['count']>0,'Invalid contingency cell')
        cells[key]=c['count']
    n=sum(cells.values());matched=sum(v for (a,b),v in cells.items() if a==b)
    equal(value['compared'],n);equal(value['matched'],matched);equal(value['disagreed'],n-matched)
    equal(value['exact_agreement'],matched/n if n else None)
    left=Counter();right=Counter()
    for (a,b),count in cells.items():left[a]+=count;right[b]+=count
    expected_n=sum(left[k]*right[k] for k in left)
    denominator=n*n-expected_n
    kappa=float(Fraction(matched*n-expected_n,denominator)) if denominator else None
    equal(value['cohen_kappa'],kappa)
    need((value['kappa_unavailable_reason'] is None)==(kappa is not None),'Kappa NA reason mismatch')
    return Counter(cells)


def verify_method(value):
    c=value['confusion'];s=value['status'];a=value['alarms_by_status']
    need(all(type(v) is int and v>=0 for group in (c,s,a) for v in group.values()),'Invalid count')
    tp,fp,fn,tn=(c[k] for k in ('TP','FP','FN','TN'))
    equal(value['labeled_cases'],tp+fp+fn+tn)
    equal(s.get('CONFIRMED_FAULT',0),tp+fn);equal(s.get('NO_FAULT',0),fp+tn)
    equal(a.get('CONFIRMED_FAULT',0),tp);equal(a.get('NO_FAULT',0),fp)
    need(all(count<=s.get(k,0) for k,count in a.items()),'Alarm count exceeds stratum')
    rate(value['precision'],tp,tp+fp);rate(value['sensitivity_on_reviewed'],tp,tp+fn)
    rate(value['false_alarm_rate_on_reviewed'],fp,fp+tn)
    rate(value['invalid_alarm_rate'],a.get('INVALID_TEST',0),s.get('INVALID_TEST',0))
    coverage=value['decision_coverage_on_reviewed'];need(0<=coverage['numerator']<=tp+fp+fn+tn,'Invalid coverage')
    rate(coverage,coverage['numerator'],tp+fp+fn+tn)
    need(value['population_recall'] is None,'No population inference permitted')


def methods(node):
    if isinstance(node,dict):
        if 'confusion' in node:yield node
        else:
            for child in node.values():yield from methods(child)
    elif isinstance(node,list):
        for child in node:yield from methods(child)


def verify():
    names=('phase2_agreement.json','r02_descriptive.json','r02_postreview_analysis.json','r02_primary_status_by_contract.json')
    values={name:json.loads((HERE/name).read_text(encoding='utf-8')) for name in names}
    agreement=values[names[0]];description=values[names[1]];analysis=values[names[2]];contracts=values[names[3]]
    need(agreement['round_status']=='OPEN' and agreement['adjudicated_cases']==0 and not agreement['labels_pooled'],'Unexpected adjudication')
    need(agreement['ci'] is agreement['p_value'] is None,'Unexpected inference')
    need(description['results']==analysis['original'],'Descriptive/analysis divergence')
    tables={};n_tables=0
    for stratum,view in agreement['views'].items():
        for kind in ('raw','derived'):
            for dim,t in view[kind].items():
                tables[stratum,kind,dim]=verify_table(t);equal(t['compared'],view['cases']);n_tables+=1
    for kind,dim in ((k,d) for k in ('raw','derived') for d in agreement['views']['all'][k]):
        equal(tables['all',kind,dim],tables['primary',kind,dim]+tables['diagnostic',kind,dim])
    n_methods=0
    for panel in (description['results'],analysis['original'],analysis['sensitivity']['results']):
        for value in methods(panel):verify_method(value);n_methods+=1
    for endpoint in ('pointwise','relation'):
        overall=analysis['original'][endpoint]['overall']
        status=overall['A']['status'];equal(sum(status.values()),42)
        equal(sum(analysis['original'][endpoint]['diagnostics'].values()),4)
        second=Counter()
        for (a,b),n in tables['primary','derived',endpoint].items():second[b]+=n
        equal(dict(second),status)
        by_contract=Counter()
        for contract,counts in contracts.items():
            equal(counts[endpoint],analysis['original'][endpoint]['by_contract'][contract]['A']['status'])
            by_contract.update(counts[endpoint])
        equal(dict(by_contract),status)
        rate(analysis['original_label_coverage'][endpoint],status.get('CONFIRMED_FAULT',0)+status.get('NO_FAULT',0),42)
        for method,value in analysis['all_alarm_accounting'][endpoint].items():
            alarms=overall[method]['alarms_by_status']
            equal(value['status_counts'],alarms);total=sum(alarms.values());equal(value['total_alarms'],total)
            tp=alarms.get('CONFIRMED_FAULT',0);fp=alarms.get('NO_FAULT',0)
            equal(value['labeled_fault_alarms'],tp);equal(value['labeled_no_fault_alarms'],fp)
            equal(value['unresolved_alarms'],total-tp-fp)
            rate(value['verified_fault_fraction_of_all_alarms'],tp,total);rate(value['conditional_precision'],tp,tp+fp)
    return dict(status='PASS',scope='Independent aggregate arithmetic only; not reference truth or provenance',
        agreement_tables=n_tables,method_summary_panels=n_methods,alarm_panels=12,
        reviewed_cases=46,primary_cases=42,round_status='OPEN',labels_pooled=False,
        aggregate_sha256={name:hashlib.sha256((HERE/name).read_bytes()).hexdigest() for name in names})


if __name__=='__main__':
    result=verify()
    if len(sys.argv)>1:
        with (HERE/sys.argv[1]).open('x',encoding='utf-8',newline='\n') as stream:
            stream.write(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,indent=2))
