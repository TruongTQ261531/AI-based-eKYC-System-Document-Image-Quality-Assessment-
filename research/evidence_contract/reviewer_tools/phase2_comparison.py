"""Interim phase-2 agreement on organizer-verified joins; no adjudication/gold.

Each person's own sealed phase-1 evidence feeds the frozen label guards upstream.
Raw categorical answers and derived endpoint labels are reported separately.
"""
from collections import Counter

from .strict import digest, need, sha_value
from ..task55 import ifv
from ..task55.agreement import nominal

RAW=('test_validity','before_reading','after_reading','absence_check')
ENDPOINTS=('pointwise','relation')
KNOWN={'CONFIRMED_FAULT','NO_FAULT'}
DIAGNOSTIC_STRATA=frozenset({'invalid_mrz_backup','incomplete_target_erasure',
                           'shared_context_loss','limited_source_universe'})


def build_view(export,links,labels,reviewer_code,*,synthetic=False):
    need(export.get('mode')==('unit_injected' if synthetic else 'human_entered'),'Evidence domain mismatch')
    need(isinstance(reviewer_code,str) and reviewer_code.strip(),'Reviewer code required')
    need(not synthetic or reviewer_code.startswith('SYNTHETIC_'),'Synthetic identity required')
    items={i['case_id']:i for i in export['items']}
    need(len(items)==len(export['items']) and set(items)==set(links)==set(labels),'Complete unique case join required')
    rows={}
    for cid,item in items.items():
        link=links[cid];identity=link['identity_sha256'];sha_value(identity)
        need(identity not in rows,'Duplicate canonical comparison identity')
        row=link['row'];sha_value(row['physical_id_sha256'])
        need(row['stratum']=='primary' or row['stratum'] in DIAGNOSTIC_STRATA,'Unknown stratum')
        need(set(labels[cid])==set(ENDPOINTS) and all(v in ifv.STATUSES for v in labels[cid].values()),'Unknown endpoint labels')
        need(item['test_validity'] in ('valid','invalid','uncertain') and
             item['before_reading'] in ifv.READINGS and item['after_reading'] in ifv.READINGS and
             item['absence_check'] in ('all_sources_removed','not_established','not_applicable'),'Invalid raw category')
        rows[identity]=dict(pair_binding_sha256=digest(row),stratum=row['stratum'],contract=row['contract_id'],
            field=row['field_key'],cluster=row['physical_id_sha256'],raw={k:item[k] for k in RAW},derived=labels[cid])
    return dict(schema='phase2-comparison-view/1',reviewer_code=reviewer_code,
        mode='SYNTHETIC' if synthetic else 'HUMAN_SUBMITTED_UNVERIFIED',export_sha256=digest(export),
        join_sha256=digest(links),rows=rows)


def table(pairs):
    n=len(pairs);matched=sum(a==b for a,b in pairs);metrics=nominal(pairs)
    return dict(compared=n,matched=matched,disagreed=n-matched,
        exact_agreement=matched/n if n else None,cohen_kappa=metrics['cohen_kappa'],
        kappa_unavailable_reason='no_common_rows_or_no_expected_disagreement' if metrics['cohen_kappa'] is None else None,
        contingencies=[dict(first=a,second=b,count=count) for (a,b),count in sorted(Counter(pairs).items())])


def compare(first,second):
    need(first['reviewer_code'].strip().casefold()!=second['reviewer_code'].strip().casefold(),'One reviewer cannot count twice')
    need(first['mode']==second['mode'],'Mixed evidence domains')
    a,b=first['rows'],second['rows'];need(set(a)==set(b),'Different frames: do not silently intersect/drop rows')
    for key in a:
        need(all(a[key][k]==b[key][k] for k in ('pair_binding_sha256','stratum','contract','field','cluster')),
             'Canonical identity has inconsistent image/output/sample binding')
    views={}
    for stratum in ('all','primary','diagnostic'):
        ids=sorted(k for k in a if stratum=='all' or a[k]['stratum']==stratum or
                   (stratum=='diagnostic' and a[k]['stratum'] in DIAGNOSTIC_STRATA))
        raw={dim:table([(a[k]['raw'][dim],b[k]['raw'][dim]) for k in ids]) for dim in RAW}
        derived={dim:table([(a[k]['derived'][dim],b[k]['derived'][dim]) for k in ids]) for dim in ENDPOINTS}
        overlap={}
        for dim in ENDPOINTS:
            pairs=[(a[k]['derived'][dim],b[k]['derived'][dim]) for k in ids]
            both=[(x,y) for x,y in pairs if x in KNOWN and y in KNOWN]
            overlap[dim]=dict(first_binary=sum(x in KNOWN for x,y in pairs),second_binary=sum(y in KNOWN for x,y in pairs),
                both_binary=len(both),binary_matched=sum(x==y for x,y in both),binary_opposed=sum(x!=y for x,y in both),
                first_only_binary=sum(x in KNOWN and y not in KNOWN for x,y in pairs),
                second_only_binary=sum(y in KNOWN and x not in KNOWN for x,y in pairs),
                neither_binary=sum(x not in KNOWN and y not in KNOWN for x,y in pairs))
        views[stratum]=dict(cases=len(ids),physical_instances=len({a[k]['cluster'] for k in ids}),raw=raw,derived=derived,
            binary_overlap=overlap,all_raw_dimensions_matched=sum(a[k]['raw']==b[k]['raw'] for k in ids),
            both_endpoint_labels_matched=sum(a[k]['derived']==b[k]['derived'] for k in ids))
    differences=[]
    for key in sorted(a):
        dimensions=[kind+'.'+dim for kind,dims in (('raw',RAW),('derived',ENDPOINTS)) for dim in dims if a[key][kind][dim]!=b[key][kind][dim]]
        if dimensions:differences.append(dict(identity=key,dimensions=dimensions,first=a[key],second=b[key]))
    result=dict(schema='phase2-interim-agreement/1',status='INTERIM_TWO_REVIEWERS_UNADJUDICATED',
        scope='Descriptive paired agreement; not truth/accuracy or independent population reliability',
        first=first['reviewer_code'],second=second['reviewer_code'],mode=first['mode'],
        views=views,any_dimension_disagreement_cases=len(differences),round_status='OPEN',
        adjudicated_cases=0,independent_gold_created=False,independence_verified=False,
        ci=None,p_value=None,labels_pooled=False,model_calls=0,
        provenance=dict(first_view_sha256=digest(first),second_view_sha256=digest(second)))
    return result,differences
