from copy import deepcopy
import json

import pytest

from research.evidence_contract.reviewer_tools import intake, synthetic
from research.evidence_contract.reviewer_tools.strict import loads, canonical, digest, sha_bytes


@pytest.mark.parametrize('raw', [b'{', b'{"x":1,"x":2}', b'{"x":NaN}', b'\xff'])
def test_strict_json_rejects_information_loss(raw):
    with pytest.raises(ValueError): loads(raw)


@pytest.mark.parametrize('phase', ['phase1', 'phase2'])
def test_synthetic_intake_preserves_raw_and_does_not_score(tmp_path, monkeypatch, phase):
    monkeypatch.setattr(intake, 'EC', tmp_path)
    bundle, value = synthetic.fixture(phase)
    seal = dict(snapshot_id=bundle['job'].get('phase1_snapshot'), reviewer_id='SYNTHETIC_A', complete=True)
    raw = ('\ufeff'+json.dumps(value, ensure_ascii=False, indent=3)+'\r\n').encode('utf-8')
    root = tmp_path/'local/intake'
    preview = intake.quarantine(raw, bundle, root, phase1_seal=seal, synthetic=True)
    assert preview['writes'] == 0 and not root.exists()
    result = intake.quarantine(raw, bundle, root, phase1_seal=seal, synthetic=True, dry_run=False)
    folder = root/digest(value)
    assert (folder/'raw.json').read_bytes() == raw
    assert result['raw_sha256'] == sha_bytes(raw) and result['gold_created'] is False
    assert not (folder/'labels.json').exists()
    with pytest.raises(ValueError, match='Already ingested'):
        intake.quarantine(canonical(value), bundle, root, phase1_seal=seal, synthetic=True)
    with pytest.raises(ValueError, match='separate'):
        intake.validate(raw, bundle, phase1_seal=seal)


@pytest.mark.parametrize('mutation', ['extra', 'missing', 'bool_string', 'enum', 'duplicate', 'wrong_slot', 'wrong_reviewer', 'wrong_packet', 'source_extra'])
def test_phase1_rejects_bad_exports(mutation):
    bundle, value = synthetic.fixture(); item = value['items'][0]
    if mutation == 'extra': value['gold'] = True
    if mutation == 'missing': value.pop('exported_at')
    if mutation == 'bool_string': item['touched'] = 'true'
    if mutation == 'enum': item['availability'] = 'definitely'
    if mutation == 'duplicate': value['items'].append(deepcopy(item))
    if mutation == 'wrong_slot': item['slot_id'] = 'SYNTHETIC_OTHER'
    if mutation == 'wrong_reviewer': value['reviewer']['reviewer_id'] = 'SYNTHETIC_B'
    if mutation == 'wrong_packet': value['packet_id'] = 'c'*64
    if mutation == 'source_extra': item['sources'][0]['approved'] = True
    with pytest.raises(ValueError): intake.validate(canonical(value), bundle, synthetic=True)


@pytest.mark.parametrize('mutation', ['no_seal', 'wrong_reviewer', 'wrong_snapshot', 'not_complete', 'duplicate', 'wrong_case', 'enum', 'extra'])
def test_phase2_rejects_order_binding_and_invalid_items(mutation):
    bundle, value = synthetic.fixture('phase2')
    seal = dict(snapshot_id=bundle['job']['phase1_snapshot'], reviewer_id='SYNTHETIC_A', complete=True)
    if mutation == 'no_seal': seal = None
    if mutation == 'wrong_reviewer': seal['reviewer_id'] = 'SYNTHETIC_B'
    if mutation == 'wrong_snapshot': seal['snapshot_id'] = 'd'*64
    if mutation == 'not_complete': seal['complete'] = 'true'
    if mutation == 'duplicate': value['items'] *= 2
    if mutation == 'wrong_case': value['items'][0]['case_id'] = 'SYNTHETIC_OTHER'
    if mutation == 'enum': value['items'][0]['before_reading'] = False
    if mutation == 'extra': value['items'][0]['gold'] = True
    with pytest.raises(ValueError): intake.validate(canonical(value), bundle, phase1_seal=seal, synthetic=True)


@pytest.mark.parametrize('phase', ['phase1', 'phase2'])
def test_issued_archive_hash_and_assigned_reviewer_are_required(tmp_path, phase):
    bundle, _ = synthetic.fixture(phase)
    path = tmp_path/'SYNTHETIC.zip'; expected = synthetic.zip_fixture(path, bundle)
    assert intake.package(path, expected, 'SYNTHETIC_A')['job'] == bundle['job']
    with pytest.raises(ValueError, match='reviewer'): intake.package(path, expected, 'SYNTHETIC_B')
    with pytest.raises(ValueError, match='hash'): intake.package(path, 'f'*64, 'SYNTHETIC_A')


def test_legacy_duplicate_and_public_write_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr(intake, 'EC', tmp_path)
    bundle, value = synthetic.fixture()
    with pytest.raises(ValueError, match='Already ingested'):
        intake.quarantine(canonical(value), bundle, tmp_path/'local/intake', synthetic=True, legacy_digests={digest(value)})
    with pytest.raises(ValueError, match='private'):
        intake.quarantine(canonical(value), bundle, tmp_path/'public', synthetic=True)
