"""Counterexamples with explicit injected provenance and matched reference access."""
from dataclasses import replace

from research.evidence_contract.master.reference_stress import (
    pair_for, reference_for, control_case, measured_translation,
)


def case(scenario, mode):
    pair, audit = pair_for(scenario, 42)
    reference, context, probes = reference_for(pair, audit, scenario)
    return control_case(scenario, 42, mode, pair, reference, context, probes)


def test_union_change_signal_can_false_alarm_on_a_valid_backup():
    row = case('C2_backup', 'correct_correct')
    assert row['expected']['pointwise'] is False
    assert row['methods']['A_change_union']['pointwise']['alarm']
    assert not row['methods']['A_bound_dual']['pointwise']['alarm']
    assert row['methods']['B3_bound']['pointwise'] == row['methods']['A_bound_dual']['pointwise']


def test_poisoned_shared_graph_reference_fools_a_and_b3_together():
    row = case('C2_reference_poison', 'correct_correct')
    assert row['expected']['pointwise'] is False
    assert row['methods']['A_frozen']['pointwise']['alarm']
    assert row['methods']['B3']['pointwise']['alarm']
    assert row['methods']['A_bound_dual']['pointwise']['verdict'] == 'PASS'
    assert row['methods']['B3_bound']['pointwise']['verdict'] == 'PASS'
    assert row['output_origin'] == 'oracle_unit_injected' and not row['real_model_error']


def test_preexisting_error_visibility_does_not_become_regression_evidence():
    row = case('C3_keep', 'wrong_wrong')
    assert row['expected'] == dict(pointwise=True, relation=None, format=False)
    assert not row['methods']['A_frozen']['pointwise']['alarm']
    assert row['methods']['A_bound_dual']['pointwise']['alarm']
    assert row['methods']['A_bound_dual']['relation']['verdict'] == 'INCONCLUSIVE'


def test_full_fixture_inventory_finds_sources_omitted_from_the_test_graph():
    row = case('C1_limited', 'correct_correct')
    sources = row['reference']['after']['sources']
    assert {s['source_id'] for s in sources} == {'body/a', 'duplicate/a', 'mrz/a'}
    assert any(s['state'] == 'SUPPORTED' for s in sources)
    assert row['expected']['pointwise'] is None
    assert row['methods']['A_frozen']['pointwise']['alarm']
    assert row['methods']['A_bound_dual']['pointwise']['verdict'] == 'INCONCLUSIVE'


def test_translation_offset_is_measured_without_trusting_the_declared_homography():
    pair, audit = pair_for('C4_translate', 42)
    observed = measured_translation(pair.original, pair.followup)
    tampered = replace(pair, mutation=replace(pair.mutation, homography=((1., 0., 99.), (0., 1., 99.), (0., 0., 1.))))
    _, _, probes = reference_for(tampered, audit, 'C4_translate')
    assert tuple(probes['measured_offset']) == observed
    assert observed != (99, 99)


def test_collateral_context_loss_is_not_a_readability_certificate():
    row = case('C3_lost_context', 'correct_correct')
    assert row['reference']['after']['sources'][0]['state'] == 'UNKNOWN'
    assert row['expected']['pointwise'] is None
    assert row['methods']['A_bound_dual']['pointwise']['verdict'] == 'INVALID_TEST'
    assert not row['human_readability_verified']
