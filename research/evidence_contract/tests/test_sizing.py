import pytest

from research.evidence_contract.oracle_reliability import sizing as s


def test_wilson_matches_nist_one_sided_example_and_empty_is_na():
    # Two-sided alpha=.10 has the same lower endpoint as one-sided 95%.
    assert s.wilson(.13,200,.10)['low']==pytest.approx(.09577,abs=.00001)
    assert s.wilson(.5,0)['width'] is None
    assert s.wilson(0,10)['low']==0
    assert s.wilson(1,10)['high']==1


def test_cluster_size_does_not_count_as_independent_ids():
    assert s.design_effect(1,.8)==1
    assert s.effective_n(20,6,1)==20
    assert s.effective_n(20,6,.5)<s.effective_n(20,6,.2)<s.effective_n(20,6,0)
    assert s.effective_n(20,6,.5,.7)<s.effective_n(20,6,.5,.9)


def test_precision_plan_is_monotone_and_minimal():
    base=s.required_ids(.5,6,.2,.9,.2)
    assert s.required_ids(.5,6,.5,.9,.2)>base
    assert s.required_ids(.5,6,.2,.7,.2)>base
    assert s.wilson(.5,s.effective_n(base,6,.2,.9))['width']<=.2
    assert s.wilson(.5,s.effective_n(base-1,6,.2,.9))['width']>.2
    assert s.required_ids(.5,6,.2,0,.2) is None


def test_paired_normal_algebra_null_symmetry_missingness():
    assert s.paired_normal_power(100,.1,.1)==pytest.approx(.05)
    assert s.paired_normal_power(100,.08,.03)==pytest.approx(s.paired_normal_power(100,.03,.08))
    assert s.paired_normal_power(0,.08,.03) is None
    assert s.paired_required_ids(6,.2,.02,.08,.03,.8)>s.paired_required_ids(6,.2,.1,.08,.03,.8)
    assert s.paired_required_ids(6,.2,.1,.08,.08,.8) is None


@pytest.mark.parametrize('p',[-.1,1.1,True,float('nan'),float('inf')])
def test_invalid_probability_rejected(p):
    with pytest.raises(ValueError):s.probability(p)
