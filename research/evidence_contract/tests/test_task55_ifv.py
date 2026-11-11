"""Review protocol tests. All observations in this file are isolated unit controls."""
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from research.evidence_contract.task55 import ifv, ifv_sampling, review
from research.evidence_contract.task55.data import OUT, PILOT, digest, read, sha


def bind(value):
    return dict(**value, packet_id=digest(value))


def phase1():
    fields = [{'slot_id': f'F-{key}', 'field_key': key} for key in ('a', 'b')]
    packet = bind(dict(schema='blind-reference-review/1', purpose='blind_review',
                       pages=[dict(image_id='i1', file_sha256='f' * 64, fields=fields)]))
    item = dict(slot_id='F-a', image_id='i1', image_sha256='f' * 64, field_key='a', touched=True,
                availability='visible', readability='readable', semantic_key_confirmed='yes',
                observed_transcript='UNIT_EXAMPLE', notes='', prior_exposure='no',
                sources=[dict(kind='body', location='left', availability='visible', readability='readable',
                              observed_text='UNIT_EXAMPLE')])
    submission = dict(schema='blind-human-review/1', packet_id=packet['packet_id'], packet_purpose='blind_review',
                      mode='unit_injected', export_kind='reviewed_observations',
                      reviewer=dict(reviewer_id='test', role='unknown', output_exposure='none', independence_verified=False),
                      items=[item])
    return packet, submission


def phase2(contract='C3'):
    evidence = dict(availability='visible', readability='readable', semantic_key_confirmed='yes',
                    observed_transcript='UNIT_EXAMPLE', sources=[])
    case = dict(case_id='CASE-unit', contract=contract, field_key='id_number', source_inventory_scope='complete',
                before_evidence=evidence, after_evidence=deepcopy(evidence),
                before_output=dict(value='UNIT_EXAMPLE', structured_output_usable=True),
                after_output=dict(value='WRONG_UNIT', structured_output_usable=True))
    item = dict(case_id=case['case_id'], before_reading='correct', after_reading='wrong_value',
                test_validity='valid', absence_check='not_applicable', reason='unit pair checked',
                first_reveal_at='2026-11-09T09:00:00Z', output_note='unit field wrong')
    return case, item


def test_existing_packet_is_output_free_and_has_real_local_images():
    root = review.PACKET_ROOT
    packet = read(root / 'packet_manifest.json')
    record = read(OUT / 'review_packet_preparation.json')
    ifv.bound_manifest(packet, 'packet_id')
    assert packet['packet_id'] == record['packet_id']
    assert len(packet['pages']) == 31
    assert sum(len(p['fields']) for p in packet['pages']) == 86
    assert set(record['file_hashes']) == {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
    assert all(sha(root / name) == value for name, value in record['file_hashes'].items())
    html = (root / 'index.html').read_text(encoding='utf-8')
    for forbidden in ('author_reference', 'predicted_fields', 'CANDIDATE_VIOLATION', 'B3_visible_reference'):
        assert forbidden not in html


def test_partial_evidence_preserves_incomplete_observation():
    packet, submission = phase1()
    pending = deepcopy(submission['items'][0])
    pending.update(slot_id='F-b', field_key='b', entry_complete=True)
    pending['sources'][0]['availability'] = ''
    submission['items'].append(pending)
    result = review.validate_export(submission, packet, allow_unit=True)
    assert result['complete_observations'] == result['incomplete_observations'] == 1
    assert result['complete_items'][0]['slot_id'] == 'F-a'
    assert result['model_failure_gold_labels_issued'] == 0


def test_no_unit_or_draft_imported_as_human():
    packet, submission = phase1()
    with pytest.raises(ValueError, match='Synthetic'):
        review.validate_export(submission, packet)
    submission['export_kind'] = 'draft'
    with pytest.raises(ValueError, match='Draft'):
        review.validate_export(submission, packet, allow_unit=True)


def test_no_certification_from_self_attestation():
    packet, submission = phase1()
    submission['reviewer']['independence_verified'] = True
    with pytest.raises(ValueError, match='self-attestation'):
        review.validate_export(submission, packet, allow_unit=True)


def test_image_or_packet_tampering_rejected():
    packet, submission = phase1()
    submission['items'][0]['image_sha256'] = 'a' * 64
    with pytest.raises(ValueError, match='Image/field/hash'):
        review.validate_export(submission, packet, allow_unit=True)
    packet['pages'][0]['fields'] = []
    with pytest.raises(ValueError, match='Modified packet'):
        review.validate_export(submission, packet, allow_unit=True)


def test_frozen_sample_includes_alerts_and_no_alerts_with_known_probabilities():
    audit = read(OUT / 'audit_run_01.json')
    frame, strata = ifv_sampling.select(audit['rows'])
    frozen = read(ifv_sampling.SAMPLE)
    assert frame == frozen['frame'] and strata == frozen['strata']
    assert len(frame) == 120 and sum(c['selected'] for c in frame) == 46
    assert all(c['selected'] for c in frame if c['row']['stratum'] == 'primary' and c['row']['checks']['A']['alarm'])
    assert sum(c['selected'] and c['stratum'].startswith('primary/A_no_alert') for c in frame) == 28
    assert sum(len(c['alias_evaluations']) for c in frame) == 132
    assert all(0 < c['inclusion_probability'] <= 1 for c in frame)


def test_no_frozen_human_export_means_no_output_access(tmp_path):
    with patch.object(ifv, 'SUBMISSIONS', tmp_path), patch.object(ifv, 'FrozenPilot') as reader:
        with pytest.raises(ValueError, match='Import a real phase-1 export'):
            ifv.open_stage2('0' * 64)
        reader.assert_not_called()


def test_phase2_build_seals_first_and_keeps_join_outside_packet(tmp_path):
    # Observations and reader outputs are injected doubles in the test scratch
    # directory. Neither the human importer nor the historical cache is used.
    packet = read(review.PACKET_ROOT / 'packet_manifest.json')
    fixture_items = [dict(image_id=p['image_id'], field_key=f['field_key'], provenance='unit_injected')
                     for p in packet['pages'] for f in p['fields']]
    evidence = dict(complete_items=fixture_items, incomplete_observations=0, missing_slots=0)
    reviewer = dict(reviewer_id='unit-fixture', role='unknown', output_exposure='none', independence_verified=False)
    sample = read(ifv_sampling.SAMPLE)
    output = SimpleNamespace(fields={}, json_validity={'usable_for_contracts': True})
    cached = {(c['row']['reader'], c['row'][side]): output for c in sample['frame'] if c['selected']
              for side in ('original_pixel_sha256', 'followup_pixel_sha256')}
    packs = read(PILOT / 'scoring.json')['packs']
    reviewer_hash = digest(['reviewer-id/1', 'unit-fixture'])

    def offline_double():
        assert (tmp_path / 'review' / reviewer_hash / 'evidence_seal.json').is_file()
        return SimpleNamespace(packs=packs, outputs=cached, assert_read_only=lambda: None)

    with patch.object(ifv, 'STAGE2', tmp_path / 'review'), patch.object(ifv, 'JOINS', tmp_path / 'joins'), \
            patch.object(ifv, 'sealed_phase1', return_value=(packet, evidence, reviewer)), \
            patch.object(ifv, 'FrozenPilot', side_effect=offline_double) as reader:
        path = ifv.open_stage2('f' * 64)
        assert len(read(path.parent / 'packet.json')['cases']) == 46
        assert (tmp_path / 'joins' / (reviewer_hash + '.json')).is_file()
        assert not (path.parent / 'analyst_join.json').exists()
        html = path.read_text(encoding='utf-8')
        assert all(word not in html for word in ('B3_visible_reference', 'CANDIDATE_VIOLATION', 'partial_42'))
        assert ifv.open_stage2('f' * 64) == path
        reader.assert_called_once()
        with pytest.raises(ValueError, match='already bound'):
            ifv.open_stage2('e' * 64)


def test_malformed_review_not_treated_as_human():
    case, item = phase2()
    packet = bind(dict(purpose='blind_output_review', phase1_snapshot='a' * 64, cases=[case]))
    value = dict(mode='unit_injected', schema='ifv-output-observations/1', packet_id=packet['packet_id'],
                 phase1_snapshot=packet['phase1_snapshot'], items=[item])
    with pytest.raises(ValueError, match='remain separate'):
        ifv.validate_stage2(value, packet)
    assert ifv.validate_stage2(value, packet, allow_unit=True)['CASE-unit']['pointwise'] == 'CONFIRMED_FAULT'
    item['output_note'] = ''
    with pytest.raises(ValueError, match='observation note'):
        ifv.validate_stage2(value, packet, allow_unit=True)


def test_c1_missing_graph_source_scope_stays_uncertain():
    case, item = phase2('C1')
    case['after_evidence'].update(availability='not_seen', readability='unreadable', observed_transcript='')
    item.update(after_reading='unsupported_verified', absence_check='all_sources_removed')
    assert ifv.labels_for(case, item) == ('CONFIRMED_FAULT', 'CONFIRMED_FAULT')
    case['source_inventory_scope'] = 'limited'
    assert ifv.labels_for(case, item) == ('INCONCLUSIVE', 'INCONCLUSIVE')


def test_c2_requires_actual_mrz_checks_or_readable_duplicate():
    case, item = phase2('C2')
    line1 = 'P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<'
    line2 = 'L898902C36UTO7408122F1204159ZE184226B<<<<<10'
    assert ifv.td3_document_number(line1, line2) == 'L898902C3'
    assert ifv.td3_document_number(line1, line2[:9] + '0' + line2[10:]) is None
    evidence = case['after_evidence']
    evidence.update(observed_transcript='L898902C3', sources=[])
    assert ifv.labels_for(case, item) == ('INCONCLUSIVE', 'INCONCLUSIVE')
    evidence['sources'] = [dict(kind='mrz', availability='visible', readability='readable',
                                mrz_line_1=line1, mrz_line_2=line2)]
    assert ifv.labels_for(case, item) == ('CONFIRMED_FAULT', 'CONFIRMED_FAULT')


@pytest.mark.parametrize('contract', ['C3', 'C4'])
def test_already_wrong_original_does_not_prove_pair_regression(contract):
    case, item = phase2(contract)
    assert ifv.labels_for(case, item) == ('CONFIRMED_FAULT', 'CONFIRMED_FAULT')
    item['before_reading'] = 'wrong_value'
    assert ifv.labels_for(case, item) == ('CONFIRMED_FAULT', 'INCONCLUSIVE')
    item['test_validity'] = 'invalid'
    assert ifv.labels_for(case, item) == ('INVALID_TEST', 'INVALID_TEST')


def test_missing_invalid_unknown_remain_outside_precision_denominator():
    link = lambda alarm: dict(row=dict(checks=dict(A=dict(alarm=alarm))))
    links = {key: link(alarm) for key, alarm in (('tp', True), ('fp', True), ('fn', False), ('tn', False),
                                                ('unknown', True), ('invalid', True), ('unreviewed', False))}
    statuses = dict(tp='CONFIRMED_FAULT', fp='NO_FAULT', fn='CONFIRMED_FAULT', tn='NO_FAULT',
                    unknown='INCONCLUSIVE', invalid='INVALID_TEST')
    labels = {k: dict(relation=v) for k, v in statuses.items()}
    report = ifv.metrics(labels, links, endpoint='relation', method='A')
    assert report['counts'] == dict(TP=1, FP=1, FN=1, TN=1)
    assert report['precision'] == dict(n=1, d=2, value=.5)
    assert report['excluded']['INCONCLUSIVE_alarms'] == report['excluded']['INVALID_TEST_alarms'] == 1
    assert report['excluded']['UNREVIEWED'] == 1 and report['population_recall'] is None
    assert ifv.metrics({}, links, endpoint='relation', method='A')['precision']['value'] is None


def test_output_template_does_not_expose_analyst_labels_or_reader():
    source = (Path(ifv.__file__).parent / 'ifv_stage2.js').read_text(encoding='utf-8')
    assert 'test_validity, absence_check, reason' in source and 'a.reason) reveal()' in source
    assert 'reader_id' not in source and 'CANDIDATE_VIOLATION' not in source
