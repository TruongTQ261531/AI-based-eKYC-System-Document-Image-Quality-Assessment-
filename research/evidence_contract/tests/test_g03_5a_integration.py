"""Offline G03.5A controls; no local panel, production identities, reference or model needed."""
import pytest

from research.evidence_contract.adjudication import synthetic_dry_run as signing
from research.evidence_contract.human_gate import integration37 as local
from research.evidence_contract.human_gate import integration37_fixture as fixture
from research.evidence_contract.human_gate.review import QUESTIONS
from research.evidence_contract.oracle_reliability import controls
from research.evidence_contract.oracle_reliability.semantic_registry import proposal
from research.evidence_contract.reviewer_tools.strict import canonical, digest, sha_bytes


def issued():
    full = {side: dict(file=digest(side), pixel=digest([side])) for side in ('before', 'after')}
    item = dict(schema='g03.5a-synthetic-item/1', candidate_id=digest('SYNTH_CASE'),
                physical_id='SYNTH_PANEL/SYNTH_TEMPLATE/SYNTH_ID', field='id_number', native_key='id_number',
                primary_source='region_0', backup_source='mrz_line0+mrz_line1', proposed_mapping=proposal('id_number'),
                source_precision=dict(body='LITERAL_IDENTIFIER', mrz='TD3_LITERAL_IDENTIFIER'), full=full,
                allowed_evidence_sha256=[r['file'] for r in full.values()],
                evidence_by_side={s: [r['file']] for s, r in full.items()})
    regions = [dict(region_attributes=dict(field_name=k, value=v)) for k, v in (
        ('id_number', 'SYNTH_PERSONAL'), ('mrz_line0', controls.LINE1), ('mrz_line1', controls.LINE2))]
    return item, regions


def test_source_slot_and_locked_date():
    item, regions = issued()
    assert local.bind_case(item, regions).compatibility == 'UNSUPPORTED_SOURCE_SLOT'
    regions[0]['region_attributes'] = dict(field_name='birth_date', value='12.08.1974')
    item.update(field='dob', native_key='birth_date', proposed_mapping=proposal('birth_date'),
                source_precision=dict(body='DAY_MONTH_FOUR_DIGIT_YEAR', mrz='YYMMDD_CENTURY_UNSPECIFIED'))
    row = local.bind_case(item, regions)
    assert (row.field, row.body_precision, row.mrz_precision, row.compatibility) == (
        'dob', 'DAY_MONTH_FOUR_DIGIT_YEAR', 'YYMMDD_CENTURY_UNSPECIFIED', 'UNSUPPORTED_PRECISION')


@pytest.mark.parametrize('change', ['field', 'native', 'body_precision', 'mrz_precision', 'primary', 'backup'])
def test_rejects_swapped_members_of_locked_case(change):
    item, regions = issued()
    if change == 'field': item['field'] = 'dob'
    if change == 'native': item['native_key'] = 'number'
    if change == 'body_precision': item['source_precision']['body'] = 'DAY_MONTH_FOUR_DIGIT_YEAR'
    if change == 'mrz_precision': item['source_precision']['mrz'] = 'YYMMDD_CENTURY_UNSPECIFIED'
    if change == 'primary': item['primary_source'] = 'region_1'
    if change == 'backup': item['backup_source'] = 'mrz_line1+mrz_line0'
    with pytest.raises(ValueError):
        local.bind_case(item, regions)


@pytest.mark.parametrize('change', ['order', 'field', 'frame', 'missing', 'duplicate'])
def test_queue_seal_detects_edits(tmp_path, change):
    item, _ = issued()
    other = dict(item, candidate_id=digest('SYNTH_OTHER'))
    queue = [item, other]
    pin = sha_bytes(canonical(queue))
    if change == 'order': queue.reverse()
    if change == 'field': other['field'] = 'expiry_date'
    if change == 'frame': other['full']['after'] = other['full']['before']
    if change == 'missing': queue.pop()
    if change == 'duplicate': queue[1] = item
    path = tmp_path/'queue.json'
    path.write_bytes(canonical(queue))
    with pytest.raises(ValueError, match='Sealed'):
        local.sealed_json(path, pin)


def test_manifest_role_and_actual_bytes(tmp_path):
    item, _ = issued()
    folder = tmp_path/'R02'/'assets'
    folder.mkdir(parents=True)
    files = {}
    for side in ('before', 'after'):
        # Issued fixture uses digest(side), the hash of these canonical string bytes.
        (folder/side).write_bytes(canonical(side))
        files['assets/'+side] = digest(side)
    manifest = dict(files, **{'index.html': digest('offline form')})
    (tmp_path/'R02_manifest.json').write_bytes(canonical(manifest))
    local.verify_manifest(tmp_path, 'R02', digest(manifest), [item])
    with pytest.raises(ValueError, match='manifest'):
        local.verify_manifest(tmp_path, 'R02', digest('different role'), [item])
    (folder/'after').write_bytes(canonical('before'))
    with pytest.raises(ValueError, match='byte hash'):
        local.verify_manifest(tmp_path, 'R02', digest(manifest), [item])


@pytest.mark.parametrize(('index', 'state', 'reason'), [
    (0, 'UNSUPPORTED_PRECISION', 'D4_INCOMPATIBLE'), (0, 'UNSUPPORTED_SOURCE_SLOT', 'D4_INCOMPATIBLE'),
    (0, 'UNKNOWN', 'D4_INCOMPATIBLE'), (1, 'PENDING', 'RIGHTS_MISSING'), (1, 'DENIED', 'RIGHTS_MISSING'),
    (2, 'MISSING', 'REFERENCE_MISSING'), (3, 'NO_VERIFIED_PAIR', 'PAIRED_OUTPUT_MISSING')])
def test_each_input_blocker_is_independent(index, state, reason):
    args = ['STRUCTURALLY_COMPATIBLE', 'PERMITTED', 'APPROVED', 'VERIFIED_PAIR']
    assert local.input_blockers(*args) == ()  # Logical input check grants no execution authority.
    args[index] = state
    assert local.input_blockers(*args) == (reason,)


@pytest.fixture
def intake_args():
    item, _ = issued()
    private, keys = signing.test_keys()
    roster = dict(R02='SYNTHETIC_A', R03='SYNTHETIC_B')
    manifests = {r: digest(['SYNTH_MANIFEST', r]) for r in roster}
    submissions = []
    for role, actor in roster.items():
        form = dict(schema='c2-source-review/1', role='reviewer', assessor=role, candidate_id=item['candidate_id'],
                    item_sha256=digest(item), exposure='UNCERTAIN', semantic_judgment='UNKNOWN',
                    precision_judgment='UNKNOWN', observations=dict.fromkeys(QUESTIONS, 'UNKNOWN'),
                    rationale='Synthetic fixture.', basis_sha256=item['allowed_evidence_sha256'])
        signed = signing.sign(dict(schema='g03.5a-fixture-observation/1', mode='SYNTHETIC', authority_id=actor,
                                   authority_role='reviewer', timestamp='2026-11-28T00:00:00Z', assessor=role,
                                   item_sha256=digest(item), manifest_sha256=manifests[role],
                                   observation_sha256=digest(form)), private)
        submissions.append((role, canonical(form), signed))
    return dict(item=item, manifest_digests=manifests, roster=roster, keys=keys, submissions=submissions,
                sharing='PERMITTED', retention='PERMITTED'), private


def test_signed_observations_and_empty_checkpoint_are_not_reference(intake_args):
    args, _ = intake_args
    result = fixture.intake(**args, journal_checkpoint='0'*64)
    assert len(result['verified_observations']) == 2
    assert result['journal_status'] == 'CHECKPOINT_VERIFIED' and result['approved_reference'] is False
    assert fixture.intake(**args)['journal_status'] == 'CHECKPOINT_PENDING'


@pytest.mark.parametrize('change', ['missing_sharing', 'missing_retention', 'other_assessor', 'same_key',
                                   'other_manifest', 'duplicate', 'altered_form', 'wrong_signature',
                                   'wrong_mode', 'changed_precision', 'real_domain', 'wrong_checkpoint',
                                   'unknown_registry_candidate', 'uncheckpointed_journal'])
def test_intake_fails_closed(intake_args, change):
    args, private = intake_args
    role, raw, envelope = args['submissions'][0]
    if change == 'missing_sharing': args['sharing'] = 'PENDING'
    if change == 'missing_retention': args['retention'] = 'PENDING'
    if change == 'other_assessor': args['roster']['R02'], args['roster']['R03'] = reversed(args['roster'].values())
    if change == 'same_key': args['keys']['SYNTHETIC_B'] = args['keys']['SYNTHETIC_A']
    if change == 'other_manifest': args['manifest_digests']['R02'] = digest('other')
    if change == 'duplicate': args['submissions'].append(args['submissions'][0])
    if change == 'altered_form': args['submissions'][0] = (role, raw.replace(b'UNCERTAIN', b'PREVIOUSLY_SEEN'), envelope)
    if change == 'wrong_signature': envelope['signature_hex'] = '00'
    if change == 'wrong_mode':
        args['submissions'][0] = (role, raw, signing.sign(dict(envelope['payload'], mode='PRODUCTION'), private))
    if change == 'changed_precision': args['item']['source_precision']['body'] = 'date_yymmdd'
    if change == 'real_domain': args['item']['schema'] = 'c2-issued-item/1'
    if change == 'wrong_checkpoint': args['journal_checkpoint'] = digest('rollback')
    if change in ('unknown_registry_candidate', 'uncheckpointed_journal'):
        e = dict(schema='reference-decision/1', mode='SYNTHETIC', registry_version=fixture.registry.VERSION,
                 authority_role='reviewer', authority_id='SYNTHETIC_A', timestamp='2026-11-28T00:00:00Z',
                 action='REVIEW_PROPOSED', candidate_id=digest('unregistered'), bindings={},
                 sequence=1, supersedes_id=None, previous_event_sha256='0'*64, basis_sha256=[sha_bytes(raw)])
        args['events'] = [signing.sign(e, private)]
        if change == 'unknown_registry_candidate': args['journal_checkpoint'] = digest(args['events'][0])
    with pytest.raises(ValueError):
        fixture.intake(**args)


@pytest.mark.parametrize('change', ['complete', 'missing_side', 'missing_both', 'swapped', 'changed_pixel',
                                   'checkpoint', 'config', 'runtime', 'preprocessing', 'version', 'output', 'duplicate'])
def test_pair_requires_both_frames_and_same_reader(change):
    item, _ = issued()
    reader = {k: digest(k) for k in ('name', 'version', 'checkpoint', 'config', 'preprocessing', 'runtime')}
    records = [(s, dict(reader=dict(reader), input=dict(item['full'][s]), output_sha256=sha_bytes(s.encode())),
                s.encode()) for s in ('before', 'after')]
    if change == 'complete':
        assert fixture.paired_output(item, reader, records) == 'VERIFIED_PAIR'
        return
    if change in ('missing_side', 'missing_both'):
        assert fixture.paired_output(item, reader, records[:int(change == 'missing_side')]) == 'NO_VERIFIED_PAIR'
        return
    record = records[1][1]
    if change == 'swapped': record['input'] = item['full']['before']
    if change == 'changed_pixel': record['input']['pixel'] = digest('other pixel')
    if change in reader: record['reader'][change] = digest('other reader')
    if change == 'output': record['output_sha256'] = sha_bytes(b'wrong')
    if change == 'duplicate': records.append(records[1])
    with pytest.raises(ValueError):
        fixture.paired_output(item, reader, records)
