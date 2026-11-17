from copy import deepcopy
import pytest

from research.evidence_contract.reviewer_tools import phase2_comparison as p
from research.evidence_contract.reviewer_tools.strict import digest


def fixture(code,*,reverse=False):
    export=dict(mode='unit_injected',items=[]);links={};labels={}
    for i in range(3):
        cid=code+'-'+str(i);truth='CONFIRMED_FAULT' if i==0 else 'INCONCLUSIVE'
        export['items'].append(dict(case_id=cid,test_validity='valid',before_reading='correct',
            after_reading='wrong_value' if i==0 else 'uncertain',absence_check='not_applicable'))
        links[cid]=dict(identity_sha256=digest(['PAIR',i]),row=dict(stratum='limited_source_universe' if i==2 else 'primary',
            contract_id='C2',field_key='id_number',physical_id_sha256=digest('ONE_SYNTHETIC_ID')))
        labels[cid]=dict(pointwise=truth,relation='INCONCLUSIVE')
    if reverse:export['items'].reverse()
    return export,links,labels


def test_private_identity_join_handles_different_case_ids_and_order():
    first=p.build_view(*fixture('SYNTHETIC_A'),'SYNTHETIC_A',synthetic=True)
    second=p.build_view(*fixture('SYNTHETIC_B',reverse=True),'SYNTHETIC_B',synthetic=True)
    result,details=p.compare(first,second)
    assert result['views']['all']['all_raw_dimensions_matched']==3 and not details
    assert result['views']['primary']['physical_instances']==1
    assert result['views']['all']['derived']['relation']['cohen_kappa'] is None
    assert result['round_status']=='OPEN' and result['adjudicated_cases']==0 and result['labels_pooled'] is False


def test_raw_agreement_does_not_imply_endpoint_truth_agreement_or_majority():
    first=p.build_view(*fixture('SYNTHETIC_A'),'SYNTHETIC_A',synthetic=True)
    args=list(fixture('SYNTHETIC_B'));args[2]['SYNTHETIC_B-0']['pointwise']='INCONCLUSIVE'
    second=p.build_view(*args,'SYNTHETIC_B',synthetic=True)
    before=deepcopy((first,second));result,details=p.compare(first,second)
    assert (first,second)==before and len(details)==1
    assert result['views']['all']['raw']['after_reading']['matched']==3
    assert result['views']['all']['derived']['pointwise']['matched']==2
    assert result['views']['all']['binary_overlap']['pointwise']['first_only_binary']==1
    assert not result['independent_gold_created']


@pytest.mark.parametrize('change',['same_reviewer','different_frame','changed_binding','duplicate_identity','mixed_domain','bad_label','unknown_stratum'])
def test_join_and_domain_fail_closed(change):
    first=p.build_view(*fixture('SYNTHETIC_A'),'SYNTHETIC_A',synthetic=True)
    args=list(fixture('SYNTHETIC_B'))
    if change=='duplicate_identity':args[1]['SYNTHETIC_B-1']['identity_sha256']=args[1]['SYNTHETIC_B-0']['identity_sha256']
    if change=='bad_label':args[2]['SYNTHETIC_B-0']['pointwise']='GOLD'
    if change=='unknown_stratum':args[1]['SYNTHETIC_B-0']['row']['stratum']='unrecognized'
    with pytest.raises(ValueError):
        second=p.build_view(*args,'SYNTHETIC_B',synthetic=True)
        if change=='same_reviewer':second['reviewer_code']='synthetic_a'
        if change=='different_frame':second['rows'].pop(next(iter(second['rows'])))
        if change=='changed_binding':next(iter(second['rows'].values()))['pair_binding_sha256']='f'*64
        if change=='mixed_domain':second['mode']='HUMAN_SUBMITTED_UNVERIFIED'
        p.compare(first,second)


@pytest.mark.parametrize('diagnostic',sorted(p.DIAGNOSTIC_STRATA))
def test_each_frozen_diagnostic_family_is_counted_separately_from_primary(diagnostic):
    views=[]
    for code in ('SYNTHETIC_A','SYNTHETIC_B'):
        args=list(fixture(code));args[1][code+'-2']['row']['stratum']=diagnostic
        views.append(p.build_view(*args,code,synthetic=True))
    result,_=p.compare(*views)
    assert result['views']['all']['cases']==3
    assert result['views']['primary']['cases']==2
    assert result['views']['diagnostic']['cases']==1
    assert result['views']['diagnostic']['raw']['after_reading']['matched']==1


def test_contingency_kappa_known_example_and_empty_na():
    result=p.table([('yes','yes'),('yes','no'),('no','yes'),('no','no')])
    assert result['cohen_kappa']==0 and result['exact_agreement']==.5
    assert p.table([])['cohen_kappa'] is None
    assert p.table([('uncertain','uncertain')])['exact_agreement']==1
    assert p.table([('uncertain','uncertain')])['cohen_kappa'] is None
