"""Reject changed aggregate counts and attempts to relabel injected evidence."""
from copy import deepcopy
import json

import pytest

from research.evidence_contract.master import reference_stress as stress
from research.evidence_contract.master.reference_stress_verify import verify


@pytest.fixture(scope='module')
def saved():
    pair, audit = stress.pair_for('C2_reference_poison', 42)
    reference, context, probes = stress.reference_for(pair, audit, 'C2_reference_poison')
    cases = [stress.control_case('C2_reference_poison', 42, mode, pair, reference, context, probes)
             for mode in ('correct_correct', 'correct_wrong')]
    methods = list(cases[0]['methods'])
    summary = stress.summarize(cases, methods)
    report = dict(scope='CONSTRUCTED_CONTROL_DEVELOPMENT_ONLY', confirmatory=False, external_reference_approved=False,
                  model_calls=0, training_steps=0, human_labels_created=0, new_external_reviewers=0, natural_model_faults=0,
                  cases_sha256=stress.digest(cases), control_executions=2, unique_injected_comparisons=2, unique_pixel_pairs=1,
                  all_executions=summary, deduplicated=summary, by_scenario={'C2_reference_poison': summary},
                  bound_field_matches_equal_information_baseline=True,
                  format_lane=dict(detected=0, injected=0, false_alarms=0))
    return cases, report


def write(folder, cases, report):
    (folder / 'cases.json').write_text(json.dumps(cases), encoding='utf-8')
    (folder / 'results.json').write_text(json.dumps(report), encoding='utf-8')


def test_saved_control_arithmetic_and_injected_scope_verify(tmp_path, saved):
    write(tmp_path, *saved)
    assert verify(tmp_path)['control_executions'] == 2
    assert verify(tmp_path)['human_gold_created'] is False


def test_changed_confusion_counts_are_rejected(tmp_path, saved):
    for kind in ('wrong_count', 'boolean_count', 'float_count'):
        cases, report = deepcopy(saved)
        counts = report['all_executions']['pointwise']['B3']['confusion']
        if kind == 'wrong_count': counts['FP'] += 1
        elif kind == 'boolean_count': counts['FN'] = False
        else: counts['FN'] = 0.0
        write(tmp_path, cases, report)
        with pytest.raises(ValueError, match='arithmetic'): verify(tmp_path)


def test_rehashed_control_cannot_be_called_a_real_model_error(tmp_path, saved):
    cases, report = deepcopy(saved)
    cases[0]['real_model_error'] = True
    report['cases_sha256'] = stress.digest(cases)
    write(tmp_path, cases, report)
    with pytest.raises(ValueError, match='constructed control'): verify(tmp_path)
