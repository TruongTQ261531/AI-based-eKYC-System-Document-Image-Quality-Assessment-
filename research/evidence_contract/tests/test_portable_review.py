"""Standalone reviewer package integrity and blinding controls; no human labels."""
from pathlib import Path
from unittest.mock import Mock
import zipfile

import pytest

from research.evidence_contract.task55 import portable_review as portable
from research.evidence_contract.task55.data import read,sha,save_new,digest


def test_phase1_package_contains_images_but_no_answers_or_model_outputs(tmp_path,monkeypatch):
    monkeypatch.setattr(portable,'EC',tmp_path)
    result=portable.phase1('R02',root=tmp_path/'local/export')
    folder=tmp_path/'local/export/reviewer_R02_phase1'
    manifest=read(folder/'MANIFEST.json')
    assert all(sha(folder/name)==h for name,h in manifest['files'].items())
    assert len(list((folder/'images').glob('*.png')))==31
    job=read(folder/'REVIEW_JOB.json')
    assert job['field_slots']==86 and job['model_outputs_included'] is False
    html=(folder/'index.html').read_text(encoding='utf-8')
    assert 'BLIND_REVIEW_PROFILE' in html and 'R02' in html
    assert all(s not in html for s in ('observed_transcript','before_output','author_reference','BLIND_REVIEW_RESUME'))
    assert result['actual_new_reviewers']==0 and not result['independence_verified']
    with zipfile.ZipFile(folder.with_suffix('.zip')) as archive:
        assert len(archive.namelist())==result['files']
        assert all(n.startswith(folder.name+'/') and '..' not in Path(n).parts for n in archive.namelist())
    with pytest.raises(FileExistsError):portable.phase1('R02',root=tmp_path/'local/export')


def test_phase2_never_opens_outputs_before_phase1_seal(tmp_path,monkeypatch):
    blocked=Mock(side_effect=ValueError('not sealed'))
    reader=Mock()
    monkeypatch.setattr(portable.ifv,'sealed_phase1',blocked)
    monkeypatch.setattr(portable.ifv,'open_stage2',reader)
    with pytest.raises(ValueError,match='not sealed'):portable.phase2('unit')
    reader.assert_not_called()


def test_phase2_view_uses_own_evidence_and_hides_author_hint(tmp_path,monkeypatch):
    monkeypatch.setattr(portable,'EC',tmp_path)
    original=tmp_path/'task55_blind_review_v1/images';original.mkdir(parents=True)
    image=original/'unit.png';image.write_bytes(b'unit-only-image-bytes')
    monkeypatch.setattr(portable,'PACKET_ROOT',original.parent)
    canonical=tmp_path/'task55_output_review/unit-reviewer';canonical.mkdir(parents=True)
    (canonical/'index.html').write_text('unit',encoding='utf-8')
    save_new(canonical/'publication.json',{'unit_injected':True})
    observation=dict(observed_transcript='OWN_UNIT_EVIDENCE',sources=[],image_sha256=sha(image))
    case=dict(case_id='UNIT',before_image='../../task55_blind_review_v1/images/unit.png',
              after_image='../../task55_blind_review_v1/images/unit.png',
              before_evidence=observation,after_evidence=observation,
              author_reference='PRIVATE_AUTHOR_HINT',before_output={'value':'UNIT'},after_output={'value':'UNIT'})
    save_new(canonical/'packet.json',dict(packet_id='canonical-unit',phase1_snapshot='unit',cases=[case]))
    monkeypatch.setattr(portable.ifv,'sealed_phase1',lambda snapshot:(None,None,{'reviewer_id':'R02'}))
    monkeypatch.setattr(portable.ifv,'open_stage2',lambda snapshot:canonical/'index.html')
    result=portable.phase2('unit',root=tmp_path/'local/export')
    folder=tmp_path/'local/export/reviewer_R02_phase2'
    page=folder/'reviews/unit-reviewer/index.html'
    text=page.read_text(encoding='utf-8')
    assert 'OWN_UNIT_EVIDENCE' in text
    assert 'PRIVATE_AUTHOR_HINT' not in text and 'author_reference' not in text
    assert 'canonical-unit' in text
    assert sha((page.parent/case['before_image']).resolve())==sha(image)
    assert result['images']==1 and result['actual_new_reviewers']==0


def test_only_pseudonyms_are_accepted():
    with pytest.raises(ValueError):portable.reviewer_code('Real Person')
