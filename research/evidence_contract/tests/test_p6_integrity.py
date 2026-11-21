from collections import Counter
import json

import pytest
from research.evidence_contract.execution.master_01.p6_integrity_20261121 import audit, characterize, verify

PAIR=dict(pixel_equal=True,training_included=True,trained_sha='adapter-A',evaluated_sha='adapter-A',exact_evaluated=True)


def test_same_pixels_need_both_checkpoint_and_actual_eval():
    assert audit.classify(**PAIR)==audit.STATES[0]
    assert audit.classify(**(PAIR|dict(exact_evaluated=False)))==audit.STATES[3]
    assert audit.classify(**(PAIR|dict(evaluated_sha='adapter-B',reuse=True)))==audit.STATES[1]
    assert audit.classify(**(PAIR|dict(training_included=False)))==audit.STATES[2]


@pytest.mark.parametrize('missing',[dict(training_included=None),dict(trained_sha=None),dict(evaluated_sha=None),
                                    dict(provenance_consistent=False),dict(upstream_unknown=True)])
def test_missing_or_contradictory_checkpoint_provenance(missing):
    assert audit.classify(**(PAIR|missing))=='UNKNOWN_LINEAGE'


def test_same_physical_or_parent_does_not_imply_equal_pixels():
    ev=dict(decoded_pixel='pixels-original',file='parent-bytes',physical_id='document')
    member=dict(path='another_crop.png',file='crop-bytes',pixel='different-pixels',records=[dict(physical_id='document')],
                bound_parent_files=['parent-bytes'],dhash=1)
    signals=audit.links(member,ev)
    assert signals==dict(exact_pixel=False,same_file=False,same_physical_id=True,evaluation_file_declared_parent=True)
    near=member|dict(dhash=1,records=[dict(physical_id='same-template-other-document')],bound_parent_files=[])
    assert not any(audit.links(near,ev).values())
    assert audit.classify(**(PAIR|dict(pixel_equal=False)))=='UNKNOWN_LINEAGE'


def test_complete_training_sequence_preserves_repeated_inputs():
    rows=['a','b','b','c']
    seq=audit.sequence(rows,42,8)
    assert seq==audit.sequence(rows,42,8)
    assert Counter(seq)=={'a':2,'b':4,'c':2}
    assert seq[:4]!=seq[4:]


def test_missing_log_manifest_and_contradictory_binding(tmp_path,monkeypatch):
    monkeypatch.setattr(audit,'ROOT',tmp_path)
    log=tmp_path/'train.json'
    assert audit.checkpoint_gap(log)=='missing_training_log'
    cp=tmp_path/'ckpt'
    cp.mkdir()
    log.write_text(json.dumps(dict(selected_checkpoint='ckpt',signature='training',selected_adapter_sha256='expected')))
    assert audit.checkpoint_gap(log)=='missing_checkpoint_manifest'
    (cp/'complete.json').write_text(json.dumps(dict(signature='different-run',sha256={'adapter_model.safetensors':'expected'})))
    assert audit.checkpoint_gap(log)=='missing_checkpoint_bytes'
    (cp/'adapter_model.safetensors').write_bytes(b'mocked weights')
    assert audit.checkpoint_gap(log)=='checkpoint_provenance_mismatch'


def test_frozen_d4_strata_and_missing_actual_truth():
    folder=audit.EXEC/'d4_development_20261117'
    data=characterize.summarize(audit.read(folder/'controls_01/control_results.json'),
                                audit.read(folder/'historical_01/summary.json'),
                                audit.read(folder/'controls_01/summary.json')['counterexamples'])
    verify.verify_d4(data)
    assert data['missed_true_faults'] is None and data['real_fault_sensitivity'] is None
    assert any(s['value_kind']=='malformed_value_kind' and s['shared_gate']=='reference_rejected' for s in data['strata'])
    assert any(s['after_literal']=='literal_value_mismatch' for s in data['strata'])
    data['strata'][0]['pointwise_checked_reason']='not_in_frozen_results'
    with pytest.raises(ValueError):
        verify.verify_d4(data)


@pytest.mark.parametrize('payload',[{'uid':'raw'},{'ok':['D:/private/photo.jpg']},{'field':'secret-doc'},{'raw_text':'x'}])
def test_no_private_publication(payload):
    with pytest.raises(ValueError):
        verify.release_check(payload,{'secret-doc'})


def test_generator_cannot_write_private_members_to_public_path(tmp_path,monkeypatch):
    monkeypatch.setattr(audit,'LOCAL',tmp_path/'authorized')
    with pytest.raises(ValueError,match='private local'):
        audit.main(tmp_path/'public')
    assert not (tmp_path/'public').exists()
