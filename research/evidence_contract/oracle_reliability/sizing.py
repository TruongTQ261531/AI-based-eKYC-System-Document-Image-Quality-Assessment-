"""Deterministic planning sensitivity, NOT a final sample size or achieved power.

Equal cluster sizes, exchangeable nonnegative ICC and nondifferential missingness
are assumptions. Effective-N Wilson widths are planning approximations, not CIs
for clustered observed data. Paired normal power has no small-cluster correction.
"""
import argparse
from itertools import product
import json
from math import isfinite, sqrt
from pathlib import Path
from statistics import NormalDist

from ..reviewer_tools.strict import digest, loads, need
from ..task55.data import EC, save_new

NORMAL=NormalDist()


def probability(value):
    need(type(value) in (int,float) and isfinite(value) and 0<=value<=1,'Probability in [0,1] required')


def design_effect(m,rho):
    need(type(m) is int and m>=1,'Positive integer cases per ID required');probability(rho)
    return 1+(m-1)*rho


def effective_n(ids,m,rho,fraction=1):
    need(type(ids) is int and ids>=0,'Nonnegative physical ID count required');probability(fraction)
    return ids*m*fraction/design_effect(m,rho)


def wilson(p,n,alpha=.05):
    probability(p);probability(alpha);need(0<alpha<1 and isfinite(n) and n>=0,'Alpha/size')
    if n==0:return dict(low=None,high=None,width=None)
    z=NORMAL.inv_cdf(1-alpha/2);denominator=1+z*z/n
    center=(p+z*z/(2*n))/denominator
    half=z*sqrt(p*(1-p)/n+z*z/(4*n*n))/denominator
    low=0.0 if p==0 else max(0.0,center-half)
    high=1.0 if p==1 else min(1.0,center+half)
    return dict(low=low,high=high,width=high-low)


def required_ids(p,m,rho,fraction,width,alpha=.05,cap=100000):
    probability(fraction);probability(width);need(width>0 and type(cap) is int and cap>=1,'Width/cap')
    if fraction==0:return None
    enough=lambda k:wilson(p,effective_n(k,m,rho,fraction),alpha)['width']<=width
    if not enough(cap):return None
    lo,hi=1,cap
    while lo<hi:
        mid=(lo+hi)//2
        if enough(mid):hi=mid
        else:lo=mid+1
    return lo


def paired_normal_power(n,p10,p01,alpha=.05):
    probability(p10);probability(p01);probability(alpha)
    need(p10+p01<=1 and 0<alpha<1 and isfinite(n) and n>=0,'Discordance/alpha/size')
    delta=p10-p01;variance=p10+p01-delta*delta
    if n==0 or variance<=0:return None
    signal=delta*sqrt(n/variance);critical=NORMAL.inv_cdf(1-alpha/2)
    return NORMAL.cdf(-critical-signal)+1-NORMAL.cdf(critical-signal)


def paired_required_ids(m,rho,fraction,p10,p01,target,alpha=.05,cap=100000):
    probability(target);probability(fraction);need(0<target<1,'Power target')
    if fraction==0 or p10==p01:return None
    def enough(k):
        value=paired_normal_power(effective_n(k,m,rho,fraction),p10,p01,alpha)
        return value is not None and value>=target
    if not enough(cap):return None
    lo,hi=1,cap
    while lo<hi:
        mid=(lo+hi)//2
        if enough(mid):hi=mid
        else:lo=mid+1
    return lo


def scenario(ids,m,rho,fault,ref_defect,label,abstain,assumptions):
    for p in (fault,ref_defect,label,abstain):probability(p)
    # The same full-cluster design effect is retained after denominator thinning.
    # This is conservative under the stated homogeneous, nondifferential model;
    # it is not a correction for informative missingness or unequal clusters.
    rate_definitions={
        'decision_coverage_all':(1-abstain,1),
        'abstention_all':(abstain,1),
        'sensitivity_all_labeled_faults':(assumptions['illustrative_expected_sensitivity'],fault*label),
        'FAR_all_labeled_nonfaults':(assumptions['illustrative_expected_far'],(1-fault)*label),
        'selective_risk':(assumptions['illustrative_selective_risk'],label*(1-abstain)),
        'FAR_reference_defect_subset':(assumptions['illustrative_expected_far'],(1-fault)*label*ref_defect)}
    result={};alpha=assumptions['alpha'];width=assumptions['illustrative_ci_full_width']
    for metric,(p,fraction) in rate_definitions.items():
        n=effective_n(ids,m,rho,fraction)
        result[metric]=dict(expected_denominator=ids*m*fraction,denominator_fraction=fraction,effective_n=n,
            planning_interval=wilson(p,n,alpha),illustrative_ids_for_width=required_ids(p,m,rho,fraction,width,alpha))
    paired=assumptions['illustrative_paired_discordance'];p10=paired['baseline_only_false_alarm'];p01=paired['checked_only_false_alarm']
    q=(1-fault)*label*ref_defect
    inputs=dict(physical_ids=ids,cases_per_id=m,icc=rho,fault_prevalence=fault,reference_defect_prevalence=ref_defect,
                label_availability=label,abstention=abstain)
    return dict(scenario_id=digest(inputs),inputs=inputs,design_effect=design_effect(m,rho),metrics=result,
        paired_false_alarm_contrast=dict(expected_difference=p10-p01,denominator_fraction=q,
            normal_approx_power=paired_normal_power(effective_n(ids,m,rho,q),p10,p01,alpha),
            illustrative_ids_for_normal_power=paired_required_ids(m,rho,q,p10,p01,assumptions['illustrative_normal_power_target'],alpha)),
        warnings=['ILLUSTRATIVE_NOT_APPROVED','UNKNOWN_HETEROGENEITY_AND_MISSINGNESS',
                  'NO_SMALL_CLUSTER_OR_RARE_EVENT_CORRECTION','NO_TEMPLATE_GENERALIZATION']+
                 (['FEWER_THAN_30_CLUSTERS'] if ids<30 else []))


def run(output):
    output=Path(output).resolve();need(output.is_relative_to((EC/'execution').resolve()) and not output.exists(),'Fresh execution destination required')
    assumptions=loads(Path(__file__).with_name('sizing_assumptions.json').read_bytes())
    need(all(v is None or v is False for v in assumptions['owner_decisions'].values()),'This run only supports unresolved owner design')
    need(assumptions['illustrative_invalid_rate']==0,'Nonzero invalidity requires an explicit denominator model amendment')
    names=('physical_ids','cases_per_id','icc','fault_prevalence','reference_defect_prevalence','label_availability','abstention')
    rows=[scenario(*values,assumptions) for values in product(*(assumptions[n] for n in names))]
    summary=dict(schema='oracle-sizing-sensitivity/1',status='PLANNING_ONLY',scenario_count=len(rows),scenarios=rows,
        assumptions_sha256=digest(assumptions),owner_decisions=assumptions['owner_decisions'],new_observations=0,
        cohort_selected=False,models_trained=0,model_calls=0,scientific_go=False,
        endpoint_assumptions='Marginal endpoint precision illustrations, not a jointly simulated confusion matrix')
    save_new(output/'sizing.json',summary);save_new(output/'assumptions.json',assumptions)
    selected=[row for row in rows if row['inputs']['physical_ids']==100 and row['inputs']['cases_per_id']==6
              and row['inputs']['fault_prevalence']==.05 and row['inputs']['label_availability']==.9 and row['inputs']['abstention']==.2]
    lines=['# Planning sensitivity: illustrative, not an approved N','','Full grid: '+str(len(rows))+' scenarios. All decisions remain pending.',
        '','Shown: 100 IDs, 6 cases/ID, 5% faults, 90% labels, 20% abstention. Width target 0.20 is illustrative.',
        '','| ICC | Ref defects | Coverage width | Sensitivity width | IDs for sensitivity width | IDs for paired 80% normal power |',
        '|---:|---:|---:|---:|---:|---:|']
    for row in selected:
        metric=row['metrics'];lines.append('| '+ ' | '.join([str(row['inputs']['icc']),str(row['inputs']['reference_defect_prevalence']),
            f"{metric['decision_coverage_all']['planning_interval']['width']:.3f}",f"{metric['sensitivity_all_labeled_faults']['planning_interval']['width']:.3f}",
            str(metric['sensitivity_all_labeled_faults']['illustrative_ids_for_width']),
            str(row['paired_false_alarm_contrast']['illustrative_ids_for_normal_power'])])+' |')
    lines+=['','These are equal-cluster/effective-N approximations, not measured power or defensible final sample sizes.',
        'A large result may exceed the available corpus; it is not a request to acquire that many IDs.',
        'Rare events, informative missingness, template dependence and unequal clusters require a revised design/simulation before lock.','']
    (output/'TABLES.md').write_text('\n'.join(lines),encoding='utf-8')
    return dict(status='PASS_PLANNING_CALCULATION',scenarios=len(rows),cohort_selected=False,scientific_go=False)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True,type=Path)
    print(json.dumps(run(parser.parse_args().output),indent=2))
