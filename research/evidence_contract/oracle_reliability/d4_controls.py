"""Small predeclared D4 controls extending, never replacing, the frozen 58.

Truth is authored for these symbolic examples and is not passed to either arm.
The original tier-2 expectations come from the frozen published run, not a new
call to the implementation under test.
"""
from copy import deepcopy
from dataclasses import replace
import json

from . import controls,policy
from ..task55.data import EC,read

OLD=EC/'execution/master_01/oracle_reliability_20261116/run_02/control_cases.json'


def cases():
    old={c['name']:c for c in read(OLD)};result=[]
    changed={'TD3_bad_checksum':['FAULT','FAULT','NO_FAULT'],
             'TD3_missing_literal':['FAULT','FAULT','NO_FAULT'],
             'TD3_wrong_value':['FAULT','UNKNOWN','NO_FAULT'],
             'TD3_invalid_date':['FAULT','FAULT','NO_FAULT']}
    for c in controls.make_controls():
        c=deepcopy(c)
        c.pop('expected')  # Explicit per-arm/per-tier expectations below replace this legacy shorthand.
        c['expected_by_tier']={str(t):dict(checked_v2=[old[c['name']]['methods']['B_tier'+str(t)][e]['state'] for e in policy.ENDPOINTS],
            mrz_metadata_asserted=changed.get(c['name'],[old[c['name']]['methods']['B_tier'+str(t)][e]['state'] for e in policy.ENDPOINTS])) for t in (1,2)}
        c['family']='literal_mrz_intervention' if c['name'] in changed else 'frozen_guard_regression'
        c['output_tamper']=None;result.append(c)
    seed=next(c for c in result if c['name']=='TD3_id_number')
    def add(name,checked,asserted=None,truth=(None,None,False),family='common_guard'):
        c=deepcopy(seed);c.update(name=name,family=family,truth=list(truth))
        c['expected_by_tier']={str(t):dict(checked_v2=list(checked),mrz_metadata_asserted=list(asserted if asserted is not None else checked)) for t in (1,2)}
        result.append(c);return c
    n=('NO_FAULT','NO_FAULT','NO_FAULT');u=('UNKNOWN','UNKNOWN','NO_FAULT');f=('FAULT','FAULT','NO_FAULT')
    c=add('valid_MRZ_correct_output',n,truth=(False,False,False),family='valid_reference_parity');c['after_raw']=c['before_raw']
    c=add('literal_checksum_defect_correct_output',u,n,truth=(False,False,False),family='literal_mrz_intervention')
    c['reference_payload']['after']['sources'][1]['mrz']['line2']=controls.LINE2[:9]+'7'+controls.LINE2[10:];c['after_raw']=c['before_raw']
    c=add('declared_wrong_MRZ_value_false_alarm',u,('FAULT','UNKNOWN','NO_FAULT'),truth=(False,False,False),family='literal_mrz_intervention')
    c['reference_payload']['after']['sources'][1]['value']='POISON';c['after_raw']=c['before_raw']
    c=add('declared_wrong_value_matches_faulty_output',u,('NO_FAULT','UNKNOWN','NO_FAULT'),truth=(True,True,False),family='literal_mrz_intervention')
    c['reference_payload']['after']['sources'][1]['value']='WRONG'
    c=add('MRZ_format_defect_faulty_output',u,f,truth=(True,True,False),family='literal_mrz_intervention')
    c['reference_payload']['after']['sources'][1]['mrz']['line1']='not a TD3 literal'
    c=add('C2_backup_lost_after_mutation',u)
    c['reference_payload']['after']['sources'][1]['state']='UNKNOWN'
    c=add('C2_backup_not_supported_before',('FAULT','UNKNOWN','NO_FAULT'))
    c['reference_payload']['before']['sources'][1]['conditions']['context_present']=False
    c=add('YYMMDD_value_cannot_supply_full_date',u)
    c['context']['key']='dob';c['reference_payload'].update(field_key='dob',value_kind='date_full')
    for side in ('before','after'):
        for s in c['reference_payload'][side]['sources']:s.update(semantic_key='dob',value='740812')
    c['before_raw']=c['after_raw']='{"dob":"1974-08-12"}'
    for name,change in [('output_before_pixel','before_pixel'),('output_after_pixel','after_pixel'),
                        ('reader_mismatch','reader'),('origin_mismatch','origin')]:
        c=add(name,('INVALID_TEST',)*3);c['output_tamper']=change
    # A self-consistent wrong MRZ + matching wrong body still fools both arms.
    c=add('correlated_wrong_body_and_valid_MRZ',('FAULT','FAULT','NO_FAULT'),truth=(False,False,False),family='correlated_wrong_reference')
    number='X12345678';line=number+policy.check_digit(number)+controls.LINE2[10:43]
    line+=policy.check_digit(line[:10]+line[13:20]+line[21:43])
    for side in ('before','after'):
        for s in c['reference_payload'][side]['sources']:
            s['value']=number
            if s['kind']=='mrz':s['mrz']['line2']=line
    c['after_raw']=c['before_raw']
    c=add('reference_missing',u);c['reference_missing']=True
    return result


def inputs(case):
    ref,ctx,before,after=controls.inputs(case)
    if case.get('reference_missing'):ref=None
    tamper=case['output_tamper']
    if tamper=='before_pixel':before=replace(before,input_pixel_sha256='f'*64)
    if tamper=='after_pixel':after=replace(after,input_pixel_sha256='f'*64)
    if tamper=='reader':after=replace(after,reader_fingerprint='f'*64)
    if tamper=='origin':after=replace(after,output_origin='actual_model')
    return ref,ctx,before,after
