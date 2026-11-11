"""Bounded development controls reusing TASK 3/5 fixtures. No actual reader is loaded."""
from dataclasses import replace
import json
from unittest.mock import patch

import numpy as np

from .. import contracts, generator
from ..fixtures import backup_fixture
from ..task5 import baselines, planning
from ..tests.test_runner_oracle import output
from .data import digest, save_new, sha
from .ifv_sampling import RECOVERY


def ink_region(pair, component):
    """Fixture ink probe via NumPy slices. Does not call project/raster/validate_pair."""
    q = np.asarray(component.geometry)
    x0, y0 = np.floor(q.min(axis=0)).astype(int)
    x1, y1 = np.ceil(q.max(axis=0)).astype(int)
    original = pair.original[y0:y1, x0:x1]
    after = pair.followup[y0:y1, x0:x1]
    ink = np.all(original < 70, axis=2)
    if not np.any(ink):
        raise AssertionError('Empty independent probe on authored fixture')
    return dict(ink_pixels=int(ink.sum()), filled=bool(np.all(after[ink] == pair.mutation.fill)),
                region_unchanged=bool(np.array_equal(original, after)))


def check_case(name, pair, before, after, expected, probes, expected_verdicts, *, kind='output_control'):
    first = output(before, pair.original)
    second = output(after, pair.followup)
    checks = baselines.run_checks(pair.graph, pair.validation, first, second)
    observed = {key: baselines.unpack(value)['verdict'] for key, value in checks.items()}
    if any(observed[key] != wanted for key, wanted in expected_verdicts.items()):
        raise AssertionError((name, expected_verdicts, observed))
    return dict(control_id=name, kind=kind, oracle_truth_basis='developer-authored expectation and fixture pixels',
                expected_behavior=expected, expected_verdicts=expected_verdicts, observed=observed,
                probes=probes, contract=pair.mutation.contract_id, transform=pair.mutation.to_dict(),
                before_pixel_sha256=first.input_pixel_sha256, after_pixel_sha256=second.input_pixel_sha256,
                graph_sha256=pair.graph.sha256, before_injected_sha256=digest(before),
                after_injected_sha256=digest(after), output_origin='oracle_unit_injected',
                verified_real_model_fault=False)


def evaluate_controls():
    image, graph, a, b = backup_fixture()
    source = {s.kind: s.components[0] for s in graph.field(a).realizations}
    truth = {f.key: f.reference_value for f in graph.fields}
    wrong_b = {**truth, b: 'WRONG_FIXTURE_VALUE'}
    removed = generator.plan(graph, 'all_sources_mask', target_key=a)
    both = dict(A='CANDIDATE_VIOLATION', B3='CANDIDATE_VIOLATION')
    passes = dict(A='PASS', B3='PASS')
    cases = []

    mrz_only = replace(removed, kind='single_source_mask', contract_id='C2',
                       hidden_source_ids=('body/a', 'duplicate/a'),
                       mask_geometry=tuple(q for q in removed.mask_geometry if max(p[1] for p in q) < 300),
                       expected_source_state=((a, 'SUPPORTED'),))
    pair = generator.generate(image, graph, mrz_only)
    probes = {kind: ink_region(pair, comp) for kind, comp in source.items()}
    assert probes['body']['filled'] and probes['duplicated_body']['filled'] and probes['mrz']['region_unchanged']
    cases.append(check_case('C2_correct_mrz_only', pair, truth, truth,
                            'NO_FAULT: retained MRZ supports the correct value', probes,
                            dict(**passes, B2='CANDIDATE_VIOLATION', A_no_alternative='CANDIDATE_VIOLATION')))

    pair = generator.generate(image, graph, removed)
    probes = {kind: ink_region(pair, comp) for kind, comp in source.items()}
    assert all(p['filled'] for p in probes.values())
    cases.append(check_case('C1_assert_after_total_erasure', pair, truth, truth,
                            'FAULT_ACTIVATED: known unsupported assertion within the fixture', probes, both))
    cases.append(check_case('C1_clean_refusal', pair, truth, {b: truth[b]},
                            'NO_FAULT: target absent and correctly left blank', probes, passes))

    mutation = generator.plan(graph, 'pair_a_mask', target_key=a, retained_key=b)
    pair = generator.generate(image, graph, mutation)
    probes = {c.role: ink_region(pair, c) for c in graph.field(b).realizations[0].components}
    assert all(p['region_unchanged'] for p in probes.values())
    cases.append(check_case('C3_neighbor_regresses', pair, truth, wrong_b,
                            'FAULT_ACTIVATED: B correct before, corrupted after while its source/context are retained',
                            probes, dict(**both, A_no_NI='INCONCLUSIVE')))
    cases.append(check_case('C3_neighbor_wrong_already', pair, wrong_b, wrong_b,
                            'Existing pointwise error; new pair regression is unestablished', probes,
                            dict(A='INCONCLUSIVE', B3='CANDIDATE_VIOLATION')))

    # Mutate the common decision dependency in memory on a known bad control.
    # A and B3 can agree and be jointly wrong. No task code or cache is changed.
    first, second = output(truth, pair.original), output(wrong_b, pair.followup)
    with patch.object(contracts, 'assessment', return_value='correct'):
        a_decision = baselines.unpack(baselines.proposed(graph, pair.validation, first, second))['verdict']
        b3_decision = baselines.unpack(baselines.visible_reference(graph, pair.validation, first, second))['verdict']
    assert a_decision == b3_decision == 'PASS'
    mutated = dict(cases[-2], control_id='C3_shared_matcher_forced_correct',
                   kind='in_memory_oracle_dependency_mutation', stage='testing_oracle',
                   expected_behavior='FAULT_ACTIVATED: shared matcher masks a known wrong injected value',
                   observed=dict(A=a_decision, B3=b3_decision),
                   mutant_expected_verdicts=passes, mutation='replace contracts.assessment with constant correct',
                   mutation_status='FAULT_ACTIVATED')
    cases.append(mutated)

    mutation = generator.plan(graph, 'geometry_translate', target_key=b)
    pair = generator.generate(image, graph, mutation)
    dx, dy = int(mutation.homography[0][2]), int(mutation.homography[1][2])
    h, w = image.shape[:2]
    exact = np.array_equal(pair.followup[dy:dy + h, dx:dx + w], image)
    assert exact
    probes = dict(full_inverse_translation_byte_match=bool(exact), dx=dx, dy=dy)
    cases.append(check_case('C4_translation_unchanged', pair, truth, truth,
                            'NO_FAULT: exact translation and correct output', probes, passes))
    cases.append(check_case('C4_translation_value_corruption', pair, truth, wrong_b,
                            'FAULT_ACTIVATED: exact translation but injected field corruption', probes, both))

    for name, pair in planning.diagnostics():
        values = {field.key: field.reference_value for field in pair.graph.fields}
        validity = 'INVALID_TEST' if name in ('shared_context_loss', 'incomplete_target_erasure') else 'INCONCLUSIVE'
        expected = dict(A=validity, B3=validity, B3_V3_gate=validity)
        probes = {}
        if name == 'incomplete_target_erasure':
            probes = {kind: ink_region(pair, comp) for kind, comp in source.items()}
            assert sum(p['filled'] for p in probes.values()) == 1 and sum(p['region_unchanged'] for p in probes.values()) == 2
            expected['A_no_validator'] = 'CANDIDATE_VIOLATION'
        elif name == 'shared_context_loss':
            retained = pair.graph.field(pair.mutation.retained_key)
            probes = {c.role: ink_region(pair, c) for c in retained.realizations[0].components}
            assert probes['value']['region_unchanged'] and probes['semantic_context']['filled']
        elif name == 'limited_source_universe':
            probes = {kind: ink_region(pair, comp) for kind, comp in source.items()}
            assert probes['body']['filled'] and probes['mrz']['region_unchanged'] and probes['duplicated_body']['region_unchanged']
            # TASK4 intentionally elevates a declared-only assertion to a
            # triage candidate. The independent verdict remains inconclusive
            # under incomplete coverage. The first failed expectation is logged.
            expected['A'] = 'CANDIDATE_VIOLATION'
        cases.append(check_case(name, pair, values, values, validity + ': authored diagnostic',
                                probes, expected, kind='mutation_validity_control'))
        if name == 'limited_source_universe':
            cases[-1].update(independent_contract_eligibility='INCONCLUSIVE',
                             oracle_candidate_on_unknown=True,
                             intended_review='Backup ink remains outside declared scope. Candidate is not verified absence.')
    return cases


def run():
    cases = evaluate_controls()
    result = dict(controls=len(cases), matched_expected=True, method='TASK 3/5 fixtures plus bounded checks',
                  actual_reader_calls=0, real_model_errors_added=0, human_labels_created=0,
                  code_sha256=sha(__file__), cases=cases)
    save_new(RECOVERY / 'controlled_results.json', result)
    print(json.dumps({k: v for k, v in result.items() if k != 'cases'}), flush=True)


if __name__ == '__main__':
    run()
