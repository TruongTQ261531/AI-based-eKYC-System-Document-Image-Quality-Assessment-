from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import pytest

from research.evidence_contract.oracle_reliability import policy,reference_registry
from research.evidence_contract.oracle_reliability.d4_controls import cases,inputs
from research.evidence_contract.oracle_reliability.mrz_ablation_v1 import compare_pair,adapter_proof


@pytest.mark.parametrize('tier',(1,2))
@pytest.mark.parametrize('case',cases(),ids=lambda c:c['name'])
def test_predeclared_d4_controls_and_frozen_regression(case,tier):
    args=inputs(case);before=deepcopy(args)
    result=compare_pair(*args,minimum_grade=tier)
    assert result['arms']['checked_v2']==policy.evaluate(*args,minimum_grade=tier)
    assert args==before
    for arm,expected in case['expected_by_tier'][str(tier)].items():
        assert [result['arms'][arm][e]['state'] for e in policy.ENDPOINTS]==expected
    assert result['cost']['arms']['mrz_metadata_asserted']['literal_td3_calls']==0
    assert result['approved_reference_count']==0 and result['scientific_go'] is False


def test_only_declared_resolver_call_changes_and_no_global_patch():
    proof=adapter_proof()
    assert proof['changed_resolver_call_sites']==1 and proof['other_resolver_ast_identical']
    original=(policy.resolve,policy.td3_value,policy.evaluate)
    args=inputs(next(c for c in cases() if c['name']=='TD3_bad_checksum'))
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(lambda _:compare_pair(*args),range(4)))
    assert original==(policy.resolve,policy.td3_value,policy.evaluate)
    assert all(r['arms']==results[0]['arms'] for r in results)


def test_production_empty_registry_cannot_be_bypassed_by_metadata():
    c=next(c for c in cases() if c['name']=='reference_unapproved')
    result=compare_pair(*inputs(c),production=True,candidates=[{'approved':True}],events=[])
    assert not reference_registry.approved_ids()
    assert all(r['pointwise']['state']=='UNKNOWN' for r in result['arms'].values())
    with pytest.raises(ValueError):compare_pair(*inputs(c),candidates=[{'approved':True}])


def test_full_date_precision_remains_common_guard():
    c=next(c for c in cases() if c['name']=='TD3_wrong_precision')
    result=compare_pair(*inputs(c))
    assert all(r['pointwise']['state']=='UNKNOWN' for r in result['arms'].values())
