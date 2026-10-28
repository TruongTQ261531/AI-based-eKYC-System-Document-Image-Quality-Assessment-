import numpy as np
import pytest

from ekyc.document_portrait import DocumentPortrait, PortraitError
from ekyc.module3_ocr import OCRExtraction
from ekyc.pipeline import EKYCPipeline
from ekyc.module2_homography import Homography


def face(x=30, confidence=.94):
    return np.array([x, 20, 50, 70, x+12, 40, x+36, 40, x+25, 52,
                     x+15, 70, x+35, 70, confidence], np.float32)


def encoder(image, detection):
    return image[:20, :20], np.array([[1., 0.]])


def test_rotation_and_multiple_views_preserve_original_pixels(monkeypatch):
    image = np.arange(100*200*3, dtype=np.uint8).reshape(100, 200, 3)
    finder = DocumentPortrait(None, encoder)
    monkeypatch.setattr(finder, 'detect', lambda card, *args: [face()] if card.shape[:2] == (200,100) else [])
    oriented, _, _, metadata = finder.extract(image)
    np.testing.assert_array_equal(oriented, np.rot90(image))
    assert metadata['rotation_ccw_degrees'] == 90
    assert metadata['supporting_views'] == 3


def test_one_spurious_detection_is_not_a_portrait(monkeypatch):
    finder = DocumentPortrait(None, encoder)
    monkeypatch.setattr(finder, 'detect', lambda card, target, enhanced: [face()] if target == 1280 else [])
    with pytest.raises(PortraitError, match='id_face_unavailable'):
        finder.extract(np.zeros((100,200,3), np.uint8))


def test_duplicate_printed_portraits_allowed_but_other_identity_blocked(monkeypatch):
    finder = DocumentPortrait(None, encoder)
    monkeypatch.setattr(finder, 'detect', lambda *args: [face(), face(120)])
    image = np.zeros((100,200,3), np.uint8)
    assert finder.extract(image)[3]['duplicate_portraits'] == 1
    finder.encode = lambda im, f: (im, np.array([[1.,0.]]) if f[0]<100 else np.array([[0.,1.]]))
    with pytest.raises(PortraitError, match='id_face_ambiguous'):
        finder.extract(image)


def test_ocr_reads_oriented_card_and_keeps_fields_if_portrait_missing():
    original = np.zeros((100,200,3), np.uint8)
    oriented = np.ones((200,100,3), np.uint8)
    class Reader:
        def read(self, image):
            self.seen = image
            return [dict(box=[[0,0],[60,0],[60,20],[0,20]], text='Example', confidence=.98, field='full_name')]
    class Faces:
        def extract_document(self, image):
            return oriented, image, np.array([[1.,0.]]), {'rotation_ccw_degrees':90}
    ocr = OCRExtraction.__new__(OCRExtraction)
    ocr.reader, ocr.min_confidence = Reader(), .4
    result, _, feature = ocr.run(original, Faces())
    assert ocr.reader.seen is oriented and feature is not None
    assert result['fields']['full_name'] == 'Example'
    class Missing:
        def extract_document(self, image): raise PortraitError('id_face_unavailable')
    result, _, feature = ocr.run(original, Missing())
    assert feature is None and result['fields']['full_name'] == 'Example'
    assert result['face_error'] == 'id_face_unavailable'


def test_missing_portrait_keeps_ocr_review_without_biometric_pass(monkeypatch):
    class Quality:
        def run(self, image): return {'passed':True}
    class OCR:
        def run(self, image, engine):
            return {'fields':{'full_name':'Example'}, 'accepted_line_count':1,
                    'face_error':'id_face_ambiguous'}, None, None
    pipeline = EKYCPipeline()
    pipeline._quality, pipeline._ocr, pipeline._faces = Quality(), OCR(), object()
    monkeypatch.setattr(Homography, 'run', lambda self, image: (image, {'requires_review':True}))
    result, embedding = pipeline.process_document(np.zeros((200,300,3), np.uint8))
    assert embedding is None and result['status'] == 'review'
    assert result['fields']['full_name'] == 'Example'
    assert result['can_match_selfie'] is False
    assert result['issues'][0]['code'] == 'id_face_ambiguous'
