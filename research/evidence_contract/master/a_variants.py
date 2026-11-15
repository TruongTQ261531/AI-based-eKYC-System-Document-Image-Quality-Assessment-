"""Exploratory, post-pilot A variants on frozen outputs. Original A is untouched.

The dual lane reuses B3 for pointwise checking and A for relations. It is an
engineering composition, explicitly not a new detector outperforming B3.
The change-union alternative exposes the trade-off from adding B2 signals.
No new model calls, training, reference labels or confirmatory inputs are used.
"""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import json

from ..task55 import ifv_sampling,ifv
from ..task55.data import EC,OUT,FrozenPilot,read,sha,save_new,digest
from .ifv_report import method_summary,sealed_results
from .ifv_analysis import from_sealed
from .intake import EXECUTION

VARIANTS=('A_frozen','A_change_union','A_dual','A_reference_gate','B3','A_flat')


def decision(verdict,reason):
    return dict(verdict=verdict,alarm=verdict=='CANDIDATE_VIOLATION',reason=reason)


def lanes(row,*,reference_approved=False):
    checks=row['checks'];a=deepcopy(checks['A']);b2=checks['B2'];b3=deepcopy(checks['B3'])
    if row['validity']!='VALID':
        verdict='INVALID_TEST' if row['validity']=='INVALID_TEST' else 'INCONCLUSIVE'
        union=decision(verdict,'common_mutation_gate')
    elif a['alarm'] or b2['alarm']:
        union=decision('CANDIDATE_VIOLATION','A_or_graph_free_output_change')
    elif a['verdict']=='PASS' and b2['verdict']=='PASS':
        union=decision('PASS','both_signals_pass')
    else:
        union=decision('INCONCLUSIVE','one_signal_cannot_decide')
    gated=deepcopy(b3) if reference_approved else decision('INCONCLUSIVE','independent_reference_pending')
    return dict(A_frozen=dict(pointwise=a,relation=deepcopy(a)),
        A_change_union=dict(pointwise=union,relation=deepcopy(a)),
        A_dual=dict(pointwise=deepcopy(b3),relation=deepcopy(a)),
        A_reference_gate=dict(pointwise=gated,relation=deepcopy(a) if reference_approved else deepcopy(gated)),
        B3=dict(pointwise=deepcopy(b3),relation=deepcopy(b3)),
        A_flat=dict(pointwise=deepcopy(checks['A_flat']),relation=deepcopy(checks['A_flat'])))


def evaluate_panel(links,labels):
    result={}
    for endpoint in ('pointwise','relation'):
        result[endpoint]={}
        for name in VARIANTS:
            cases=[]
            for key,case in links.items():
                row=case['row']
                if row['stratum']!='primary':continue
                derived=lanes(row)[name][endpoint]
                augmented=dict(row,checks=dict(row['checks'],variant=derived))
                cases.append((augmented,labels[key][endpoint]))
            result[endpoint][name]=method_summary(cases,'variant')
    return result


def run(plan_path,submission,destination):
    plan=read(plan_path)
    if plan['scope']!='POST_PILOT_EXPLORATORY' or plan['variants']!=list(VARIANTS):
        raise ValueError('Use the declared development plan')
    if plan['independent_reference_approved'] is not False or plan['model_call_budget']!=0:
        raise ValueError('This run neither invents reference approval nor calls a model')
    # Every output and old scorer binding is independently rechecked before reuse.
    pilot=FrozenPilot();frame=read(ifv_sampling.SAMPLE)
    ifv.bound_manifest(frame,'sample_id')
    audit,details=from_sealed(submission)
    packet=read(submission.parents[2]/'packet.json')
    links=read(ifv.JOINS/(submission.parents[2].name+'.json'))
    labels=read(submission.parent/'labels.json');withheld=deepcopy(labels)
    for row in details:
        if row['coherence_flags']:withheld[row['case_id']]=dict(pointwise='INCONCLUSIVE',relation='INCONCLUSIVE')
    if len(pilot.rows)!=132 or len(frame['frame'])!=120 or len(links)!=46:
        raise ValueError('Scheduled or deduplicated evaluation set changed')
    all_cases=[]
    for raw in pilot.rows:
        all_cases.append(dict(evaluation_id=raw['evaluation_id'],stratum=raw['stratum'],
            reader=raw['reader'],contract=raw['contract_id'],row_sha256=digest(raw),variants=lanes(raw)))
    panels=dict(original=evaluate_panel(links,labels),withholding_sensitivity=evaluate_panel(links,withheld))
    agreements={name:sum(lanes(c['row'])[name]['pointwise']['alarm']==c['row']['checks']['B3']['alarm']
        for c in frame['frame']) for name in VARIANTS}
    relation_unchanged=all(lanes(r)['A_dual']['relation']==r['checks']['A'] and
        lanes(r)['A_change_union']['relation']==r['checks']['A'] for r in pilot.rows)
    report=dict(schema='A-development-variants/1',scope=plan['scope'],plan_sha256=sha(plan_path),
        source_sha256=sha(__file__),scheduled_comparisons=len(pilot.rows),deduplicated_comparisons=len(frame['frame']),
        review_comparisons=len(links),primary_review_comparisons=42,primary_physical_ids=3,
        scheduled_readers=dict(Counter(r['reader'] for r in pilot.rows)),variants=list(VARIANTS),
        dual_field_matches_B3_all_cases=all(lanes(r)['A_dual']['pointwise']==r['checks']['B3'] for r in pilot.rows),
        relation_lane_preserved=relation_unchanged,pointwise_alarm_agreement_with_B3=agreements,
        panels=panels,independent_reference_approved=False,
        meaning='Dual lane repairs endpoint visibility by composing existing B3 and A; it does not establish new fault-discovery superiority.',
        actual_reviewers=1,adjudicated=False,confirmatory=False,model_calls=0,training_steps=0,
        case_digest=digest(all_cases))
    assert report['dual_field_matches_B3_all_cases'] and relation_unchanged
    pilot.assert_read_only()
    save_new(destination/'variant_cases.json',all_cases)
    save_new(destination/'variant_results.json',report)
    lines=['# A development variants — exploratory', '',
        'Post-pilot analysis on unchanged outputs and one-author labels. Original A is frozen.',
        'A_dual uses B3 for the field lane and A for the relation lane; this is not a superiority result.', '',
        '| Panel | Variant | Pointwise TP/FP/FN/TN | Coverage | Relation TP/FP/FN/TN |',
        '|---|---|---|---|---|']
    for panel,results in panels.items():
        for name in VARIANTS:
            counts=['/'.join(str(results[e][name]['confusion'][k]) for k in ('TP','FP','FN','TN'))
                    for e in ('pointwise','relation')]
            coverage=results['pointwise'][name]['decision_coverage_on_reviewed']
            lines.append('| '+' | '.join([panel,name,counts[0],f"{coverage['numerator']}/{coverage['denominator']}",counts[1]])+' |')
    lines.extend(['','The reference-gate control has no approved independent references and therefore abstains; its low alarm count is not an accuracy improvement.',
        'No external reviewers, C2 evidence or population confidence were manufactured. New reference and a locked study remain necessary.', ''])
    with (destination/'variant_results.md').open('x',encoding='utf-8') as stream:stream.write('\n'.join(lines))
    return report


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--plan',type=Path,required=True)
    parser.add_argument('--submission',type=Path,required=True)
    parser.add_argument('--destination',type=Path,required=True)
    args=parser.parse_args()
    report=run(args.plan,args.submission.resolve(),args.destination)
    print(json.dumps(dict(status='EXPLORATORY_COMPLETE',scheduled=report['scheduled_comparisons'],
        dual_matches_B3=report['dual_field_matches_B3_all_cases'],model_calls=0)))
