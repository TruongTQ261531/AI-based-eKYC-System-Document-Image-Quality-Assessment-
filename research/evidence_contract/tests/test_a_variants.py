"""Exploratory composition controls; no human truth or predictor is constructed."""
from copy import deepcopy

from research.evidence_contract.master.a_variants import lanes,evaluate_panel


def row():
    def check(verdict):return dict(verdict=verdict,alarm=verdict=='CANDIDATE_VIOLATION')
    return dict(validity='VALID',stratum='primary',checks=dict(A=check('INCONCLUSIVE'),
        B2=check('CANDIDATE_VIOLATION'),B3=check('CANDIDATE_VIOLATION'),A_flat=check('INCONCLUSIVE')))


def test_dual_lane_does_not_relabel_existing_relation_as_regression():
    source=row();saved=deepcopy(source)
    variants=lanes(source)
    assert variants['A_dual']['pointwise']==source['checks']['B3']
    assert variants['A_dual']['relation']==source['checks']['A']
    assert variants['A_change_union']['pointwise']['alarm']
    assert variants['A_change_union']['relation']['verdict']=='INCONCLUSIVE'
    assert source==saved


def test_invalid_common_gate_dominates_output_change_alerts():
    source=row();source['validity']='INVALID_TEST'
    assert lanes(source)['A_change_union']['pointwise']['verdict']=='INVALID_TEST'
    assert not lanes(source)['A_change_union']['pointwise']['alarm']


def test_missing_reference_abstention_is_not_reported_as_a_pass():
    variants=lanes(row())
    for endpoint in ('pointwise','relation'):
        assert variants['A_reference_gate'][endpoint]['verdict']=='INCONCLUSIVE'
        assert not variants['A_reference_gate'][endpoint]['alarm']


def test_composed_field_lane_keeps_known_fault_as_missed_if_abstaining():
    links={'unit':dict(row=row())}
    labels={'unit':dict(pointwise='CONFIRMED_FAULT',relation='INCONCLUSIVE')}
    result=evaluate_panel(links,labels)
    assert result['pointwise']['A_frozen']['confusion']['FN']==1
    assert result['pointwise']['A_dual']['confusion']['TP']==1
    assert result['pointwise']['A_dual']==result['pointwise']['B3']
    assert result['pointwise']['A_reference_gate']['decision_coverage_on_reviewed']['value']==0
    assert result['relation']['A_dual']['labeled_cases']==0
