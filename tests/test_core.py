import json
from pathlib import Path
import numpy as np
import pytest
from ekyc.config import Settings
from ekyc.dataset import split_for
from ekyc.io import StageError
from ekyc.module2_homography import Homography, order_corners
from ekyc.module3_ocr import parse_lines
from ekyc.module4_liveness import MotionEvidence
from ekyc.module5_matching import FaceMatching
from ekyc.pipeline import EKYCPipeline


def test_cross_dataset_split():
    assert all(split_for(f'doc_{n:02d}') == split_for(f'{n:02d}_id') for n in range(1,51))
    assert {split_for(f'doc_{n:02d}') for n in range(1,51)} == {'train','val','test'}


def test_homography_geometry():
    image = np.zeros((200,300,3),dtype=np.uint8)
    corners = [[280,180],[20,20],[20,180],[280,20]]
    card, result = Homography().run(image,corners)
    assert card.shape == (160,260,3)
    assert result['requires_review'] is False
    assert np.allclose(order_corners(corners)[0], [20,20])
    with pytest.raises(StageError):
        Homography().run(image, [[-1,0],[280,0],[280,180],[0,180]])
    with pytest.raises(StageError):
        Homography().run(image)


def test_parser_does_not_guess_dob_from_expiry():
    parsed = parse_lines([{'text':'EXPIRY 02/03/2030'}, {'text':'FULL NAME: JOHN SMITH'},
                          {'text':'ID NUMBER: 123456789'}, {'text':'DATE OF BIRTH: 01/02/1990'}])
    assert parsed['dob'] == '01/02/1990'
    assert parsed['full_name'] == 'JOHN SMITH'
    assert parsed['id_number'] == '123456789'
    assert parse_lines([{'text':'EXPIRY 02/03/2030'}])['dob'] is None
    assert parse_lines([{'text':'PERSONALAUSWEIS REPUBLIK OSTERREICH'}])['id_number'] is None


def test_liveness_static_and_incomplete_blink_fail():
    motion = MotionEvidence()
    for t in range(0,3000,100):
        motion.update(.1,0,t)
    assert not motion.result()['passed']
    motion.update(.9,-.2,3000)
    assert motion.result()['blinks'] == 0
    motion.update(.1,.2,3200)
    assert motion.result()['passed']


def test_matching_rejects_mixed_identities():
    matching = FaceMatching()
    assert matching.run(np.array([1,0]), [np.array([1,0])]*3)['passed']
    assert not matching.run(np.array([1,0]), [np.array([1,0]),np.array([1,0]),np.array([0,1])])['passed']
    with pytest.raises(StageError):
        matching.run(np.array([1,0]), [np.array([0,0])]*3)


def test_quality_rejection_stops_pipeline(tmp_path, monkeypatch):
    import ekyc.pipeline as module
    monkeypatch.setattr(module, 'read_image', lambda path: np.zeros((100,100,3),dtype=np.uint8))
    pipeline = EKYCPipeline(Settings(output_dir=tmp_path))
    class Reject:
        def run(self,image): return {'passed':False,'label':'Blur'}
    pipeline._quality = Reject()
    result = pipeline.run(Path('unused'))
    assert result['decision']=='rejected'
    assert set(result['stages']) == {'module1_quality'}
    assert json.loads((tmp_path/result['run_id']/'result.json').read_text())['decision']=='rejected'


def test_decode_failure_persisted(tmp_path):
    pipeline = EKYCPipeline(Settings(output_dir=tmp_path))
    result = pipeline.run(tmp_path/'missing.jpg')
    assert result['decision']=='error'
    assert result['failed_stage']=='module1_quality'
    assert (tmp_path/result['run_id']/'result.json').exists()


@pytest.mark.parametrize('live_pass,expected_stages,decision', [(False,4,'rejected'), (True,5,'review_required')])
def test_full_orchestration_gates(tmp_path, monkeypatch, live_pass, expected_stages, decision):
    import ekyc.pipeline as module
    from ekyc.module4_liveness import LivenessDetection
    from ekyc.module2_homography import Homography
    image=np.zeros((100,100,3),dtype=np.uint8)
    feature=np.array([[1.,0.]])
    monkeypatch.setattr(module,'read_image',lambda _:image)
    monkeypatch.setattr(Homography,'run',lambda *a:(image,{'requires_review':False}))
    monkeypatch.setattr(LivenessDetection,'run',lambda *a:({'passed':live_pass},[feature]*3,[image]*3))
    pipeline=EKYCPipeline(Settings(output_dir=tmp_path))
    class Quality:
        def run(self,*a): return {'passed':True}
    class OCR:
        def run(self,*a): return {'raw_lines':[]},image,feature
    pipeline._quality,pipeline._ocr,pipeline._faces=Quality(),OCR(),object()
    result=pipeline.run(Path('card'),Path('video'))
    assert len(result['stages'])==expected_stages
    assert result['decision']==decision
