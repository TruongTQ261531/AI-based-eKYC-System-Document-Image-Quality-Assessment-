"""Authored policy expectations and invariants; none are human/model evidence."""
from copy import deepcopy
from dataclasses import replace
from itertools import permutations, product

import pytest

from research.evidence_contract.oracle_reliability import policy as p
from research.evidence_contract.oracle_reliability.controls import make_controls, inputs, LINE1, LINE2


@pytest.mark.parametrize('case', make_controls(), ids=lambda c:c['name'])
def test_authored_policy_outcomes_and_equal_information_flat(case):
    args=inputs(case);before=deepcopy(args[0]);result=p.evaluate(*args)
    assert [result[e]['state'] for e in p.ENDPOINTS]==case['expected']
    assert args[0]==before
    flat=p.evaluate(*args,flat=True)
    assert [(result[e]['state'],result[e]['grade']) for e in p.ENDPOINTS]==[(flat[e]['state'],flat[e]['grade']) for e in p.ENDPOINTS]
    strict=p.evaluate(*args,minimum_grade=2)
    for endpoint in ('pointwise','relation'):
        if strict[endpoint]['state'] in {'FAULT','NO_FAULT'}:
            assert strict[endpoint]['state']==result[endpoint]['state']
    assert result['independent_gold'] is False and result['software_fault_confirmed'] is False


def test_permutations_and_unknown_source_cannot_increase_certainty():
    reference,*_=inputs(make_controls()[0]);template=reference['after']['sources'][0];checks=0
    for size in range(4):
        for states in product(('SUPPORTED','REMOVED','UNKNOWN'),repeat=size):
            for complete in (False,True):
                sources=[dict(deepcopy(template),source_id=str(i),state=state) for i,state in enumerate(states)]
                frame=dict(reference['after'],sources=sources,inventory_complete=complete)
                expected=p.resolve(frame,'id_number','identifier')
                for order in permutations(sources):
                    assert p.resolve(dict(frame,sources=list(order)),'id_number','identifier')==expected;checks+=1
                extra=dict(deepcopy(template),source_id='new_unknown',state='UNKNOWN')
                assert p.resolve(dict(frame,sources=sources+[extra]),'id_number','identifier')['state']=='UNKNOWN'
    assert checks==368  # 2 * (1 + 3*1! + 9*2! + 27*3!)


def test_c1_cannot_drop_an_inventory_record_to_claim_complete_removal():
    case=next(c for c in make_controls() if c['name']=='C1_complete_emitted')
    ref=case['reference_payload'];ref['before']['sources'].append(dict(deepcopy(ref['before']['sources'][0]),source_id='missing'))
    assert p.evaluate(*inputs(case))['pointwise']['state']=='UNKNOWN'


def test_literal_td3_known_check_digits_and_field_precision():
    mrz=dict(line1=LINE1,line2=LINE2)
    assert p.check_digit('L898902C3')=='6'
    assert p.td3_value(mrz,'id_number','identifier')[0]==('identifier','L898902C3')
    assert p.td3_value(mrz,'dob','date_yymmdd')[0]==('date_yymmdd',74,8,12)
    assert p.td3_value(mrz,'dob','date_full')[0] is None
    assert p.td3_value(mrz,'full_name','text')[0] is None
    for index in list(range(10))+list(range(13,20))+list(range(21,44)):
        old=LINE2[index];new='1' if old!='1' else '2'
        # Some substitutions differ by a multiple of 10: checksums are NOT cryptographic proof.
        if (0 if old=='<' else '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'.index(old))%10==int(new):
            new='3'
        changed=LINE2[:index]+new+LINE2[index+1:]
        assert p.td3_value(dict(line1=LINE1,line2=changed),'id_number','identifier')[0] is None


def test_typed_values_and_ambiguous_century():
    assert p.canonical('ĐẶNG  VĂN','text')==p.canonical('đặng văn','text')
    assert p.canonical('O01','identifier')!=p.canonical('001','identifier')
    assert p.canonical('2024-02-29','date_full')==p.canonical('29/02/2024','date_full')
    assert p.canonical('000229','date_yymmdd') is None
    assert p.canonical('000228','date_yymmdd')==('date_yymmdd',0,2,28)
    assert p.canonical('990101','date_yymmdd')!=p.canonical('1999-01-01','date_full')


def test_approval_binding_is_external_to_validator_and_exact_to_revision():
    case=next(c for c in make_controls() if c['name']=='reference_unapproved')
    ref,ctx,before,after=inputs(case)
    assert p.evaluate(ref,ctx,before,after)['pointwise']['state']=='UNKNOWN'
    assert p.evaluate(ref,ctx,before,after,approved_external_ids={ref['reference_id']})['pointwise']['state']=='FAULT'
    case['reference_payload']['provenance']+=' amended';amended,*_=inputs(case)
    assert p.evaluate(amended,ctx,before,after,approved_external_ids={ref['reference_id']})['pointwise']['state']=='UNKNOWN'
    assert not p.evaluate(ref,ctx,before,after,approved_external_ids=True)['reference_accepted']
    for broken in (replace(after,input_pixel_sha256='f'*64),replace(after,reader_fingerprint='f'*64)):
        assert all(p.evaluate(ref,ctx,before,broken)[e]['state']=='INVALID_TEST' for e in p.ENDPOINTS)


@pytest.mark.parametrize('malformed',[None,[],{},True,{'schema':[]},'not a reference'])
def test_malformed_reference_fails_closed(malformed):
    _,ctx,before,after=inputs(make_controls()[0])
    assert p.evaluate(malformed,ctx,before,after)['pointwise']['state']=='UNKNOWN'


def test_shared_poisoned_reference_is_a_retained_counterexample_not_a_success_claim():
    case=next(c for c in make_controls() if c['name']=='shared_wrong_reference')
    assert case['truth'][0] is False
    assert p.evaluate(*inputs(case))['pointwise']['state']=='FAULT'
    assert p.evaluate(*inputs(case),flat=True)['pointwise']['state']=='FAULT'
