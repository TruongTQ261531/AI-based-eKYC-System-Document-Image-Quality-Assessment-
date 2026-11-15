"""Reference trust/binding and semantic endpoint controls; no human labels."""
from copy import deepcopy
from dataclasses import replace
import json

import numpy as np
import pytest

from research.evidence_contract.master import reference_policy as policy
from research.evidence_contract.source_graph import pixel_sha256
from research.evidence_contract.tests.test_runner_oracle import output


def fixture(*, before_value='DEMO12345', after_value='WRONG', after_state='SUPPORTED', complete=True):
    first = np.zeros((3, 3, 3), dtype=np.uint8)
    second = np.full((3, 3, 3), 255, dtype=np.uint8)
    before = output({'id_number': before_value}, first)
    after = output({'id_number': after_value}, second)
    context = policy.PairContext('C3', 'id_number', pixel_sha256(first), pixel_sha256(second), 'a' * 64, 'VALID', 'mask')
    source = dict(source_id='unit', semantic_key='id_number', kind='body', state='SUPPORTED', value='DEMO12345',
                  conditions=dict(semantic_link=True, integrity=True))
    payload = dict(schema=policy.SCHEMA, policy=policy.POLICY, scope='constructed_control', field_key='id_number',
                   value_kind='identifier', provenance='Unit control only; no person or external approval',
                   mutation_sha256=context.mutation_sha256,
                   before=dict(pixel_sha256=context.before_pixel_sha256, inventory_complete=True, sources=[deepcopy(source)]),
                   after=dict(pixel_sha256=context.after_pixel_sha256, inventory_complete=complete,
                              sources=[dict(source, state=after_state)]))
    return payload, context, before, after


def evaluate(payload, context, before, after, **kwargs):
    return policy.evaluate(policy.seal_reference(payload), context, before, after, **kwargs)


def test_existing_error_is_visible_in_field_lane_without_claiming_a_new_regression():
    values = fixture(before_value='WRONG', after_value='WRONG')
    result = evaluate(*values)
    assert result['pointwise']['alarm']
    assert result['relation']['verdict'] == 'INCONCLUSIVE'
    assert not result['human_readability_verified'] and not result['software_fault_confirmed']


def test_correct_original_and_corrupt_followup_are_a_conditional_failure_only():
    result = evaluate(*fixture())
    assert result['pointwise']['alarm'] and result['relation']['alarm']
    assert result['relation']['verdict'] == 'CANDIDATE_VIOLATION'
    assert result['format']['verdict'] == 'PASS'


def test_constructed_reference_cannot_be_used_on_real_origin_even_if_approved():
    payload, context, before, after = fixture()
    reference = policy.seal_reference(payload)
    result = policy.evaluate(reference, context, replace(before, output_origin='actual_model'),
                             replace(after, output_origin='actual_model'), approved_external_ids={reference['reference_id']})
    assert not result['reference_accepted'] and not result['pointwise']['alarm']


def test_external_reference_requires_its_exact_approved_id_not_a_boolean_or_a_previous_version():
    payload, context, before, after = fixture()
    payload['scope'] = 'external_reference'
    reference = policy.seal_reference(payload)
    assert not policy.evaluate(reference, context, before, after)['reference_accepted']
    assert policy.evaluate(reference, context, before, after, approved_external_ids={reference['reference_id']})['reference_accepted']
    payload['after']['sources'][0]['value'] = 'AMENDED'
    amendment = policy.seal_reference(payload)
    assert not policy.evaluate(amendment, context, before, after, approved_external_ids={reference['reference_id']})['reference_accepted']


@pytest.mark.parametrize('mismatch', ['content', 'key', 'mutation', 'image', 'semantic_key', 'duplicate_source', 'boolean_string'])
def test_corrupt_or_misbound_reference_never_emits_a_semantic_alarm(mismatch):
    payload, context, before, after = fixture()
    if mismatch == 'key': payload['field_key'] = 'school'
    if mismatch == 'mutation': payload['mutation_sha256'] = 'b' * 64
    if mismatch == 'image': payload['after']['pixel_sha256'] = 'b' * 64
    if mismatch == 'semantic_key': payload['after']['sources'][0]['semantic_key'] = 'school'
    if mismatch == 'duplicate_source': payload['after']['sources'] *= 2
    if mismatch == 'boolean_string': payload['after']['sources'][0]['conditions']['semantic_link'] = 'true'
    reference = policy.seal_reference(payload)
    if mismatch == 'content': reference['after']['sources'][0]['value'] = 'TAMPERED'
    result = policy.evaluate(reference, context, before, after)
    assert not result['reference_accepted']
    assert result['pointwise']['verdict'] == 'INCONCLUSIVE'


@pytest.mark.parametrize('complete,semantic,integrity', [(False, True, True), (True, False, True), (True, True, False)])
def test_empty_output_does_not_establish_absence_without_scope_and_semantic_erasure_proof(complete, semantic, integrity):
    payload, context, before, after = fixture(after_state='REMOVED', after_value='', complete=complete)
    payload['after']['sources'][0]['conditions'] = dict(semantic_link=semantic, integrity=integrity)
    result = evaluate(payload, replace(context, contract='C1'), before, after)
    assert result['pointwise']['verdict'] == 'INCONCLUSIVE' and not result['pointwise']['alarm']


def test_complete_verified_removal_is_checked_for_nonempty_assertion():
    payload, context, before, after = fixture(after_state='REMOVED', after_value='DEMO12345')
    result = evaluate(payload, replace(context, contract='C1'), before, after)
    assert result['pointwise']['assessment'] == 'unsupported_assertion'
    assert result['pointwise']['alarm'] and result['relation']['alarm']


def test_conflicting_supported_sources_are_not_resolved_by_majority_or_first_value():
    payload, context, before, after = fixture(after_value='DEMO12345')
    another = dict(payload['after']['sources'][0], source_id='alternative', value='CONFLICT')
    payload['after']['sources'].append(another)
    result = evaluate(payload, context, before, after)
    assert result['pointwise']['reason'] == 'conflicting_supported_references'
    assert not result['pointwise']['alarm']


@pytest.mark.parametrize('missing', ['semantic_link', 'integrity', 'format_valid', 'field_checksum', 'composite_checksum'])
def test_mrz_reference_needs_all_conditions_required_by_this_conservative_policy(missing):
    payload, context, before, after = fixture(after_value='DEMO12345')
    source = payload['after']['sources'][0]
    source['kind'] = 'mrz'
    source['conditions'] = {name: True for name in policy.CONDITIONS}
    del source['conditions'][missing]
    result = evaluate(payload, replace(context, contract='C2'), before, after)
    assert result['pointwise']['verdict'] == 'INCONCLUSIVE'


def test_reader_or_image_mismatch_is_invalid_before_reference_scoring():
    payload, context, before, after = fixture()
    result = evaluate(payload, context, before, replace(after, input_pixel_sha256='b' * 64))
    assert result['pointwise']['verdict'] == 'INVALID_TEST'
    assert not result['reference_accepted']


@pytest.mark.parametrize('validity', ['INVALID_TEST', 'INCONCLUSIVE'])
def test_common_mutation_gate_is_not_bypassed_by_an_approved_reference(validity):
    payload, context, before, after = fixture()
    result = evaluate(payload, replace(context, validity=validity), before, after)
    assert result['pointwise']['verdict'] == validity and not result['pointwise']['alarm']


def test_malformed_structure_has_a_separate_alarm_and_unknown_field_judgment():
    payload, context, before, after = fixture()
    bad = output({}, np.full((3, 3, 3), 255, dtype=np.uint8), usable_text='{"id_number":')
    result = evaluate(payload, context, before, bad)
    assert result['format']['alarm']
    assert result['pointwise']['verdict'] == 'INCONCLUSIVE'
    assert result['relation']['verdict'] == 'INCONCLUSIVE'


def test_typed_values_preserve_o_zero_accents_case_sensitive_identifiers_and_date_precision():
    assert policy.canonical_value('DEMO123', 'identifier') != policy.canonical_value('DEM0123', 'identifier')
    assert policy.canonical_value('demo123', 'identifier') != policy.canonical_value('DEMO123', 'identifier')
    assert policy.canonical_value(' ĐẶNG   VĂN ', 'text') == policy.canonical_value('đặng văn', 'text')
    assert policy.canonical_value('Đặng', 'text') != policy.canonical_value('Dang', 'text')
    assert policy.canonical_value('2024-02-29', 'date_full') == policy.canonical_value('29/02/2024', 'date_full')
    assert policy.canonical_value('2023-02-29', 'date_full') is None
    assert policy.canonical_value('990101', 'date_yymmdd') != policy.canonical_value('1999-01-01', 'date_full')
    assert policy.canonical_value('990101', 'date_full') is None


def test_reference_loader_rejects_duplicate_keys_and_seal_requires_an_explicit_new_version(tmp_path):
    path = tmp_path / 'reference.json'
    path.write_text('{"scope":"constructed_control","scope":"external_reference"}', encoding='utf-8')
    with pytest.raises(ValueError, match='Duplicate'): policy.load_reference(path)
    payload, *_ = fixture()
    sealed = policy.seal_reference(payload)
    with pytest.raises(ValueError, match='already sealed'): policy.seal_reference(sealed)
