"""Shared YuNet detection and SFace alignment; never substitute a guessed face crop."""
import cv2
import numpy as np
from .io import StageError


class FaceEngine:
    def __init__(self, model_dir):
        detector = model_dir / 'face_detection_yunet_2023mar.onnx'
        recognizer = model_dir / 'face_recognition_sface_2021dec.onnx'
        for path in (detector, recognizer):
            if not path.is_file():
                raise StageError(f'Missing model {path}; run python -m ekyc.download_models')
        self.detector = cv2.FaceDetectorYN.create(str(detector), '', (320, 320), 0.85, 0.3, 5000)
        self.document_detector = cv2.FaceDetectorYN.create(str(detector), '', (320, 320), 0.70, 0.3, 5000)
        self.recognizer = cv2.FaceRecognizerSF.create(str(recognizer), '')

    def extract_document(self, image):
        from .document_portrait import DocumentPortrait
        return DocumentPortrait(self.document_detector, self._encode).extract(image)

    def _encode(self, image, face):
        aligned = self.recognizer.alignCrop(image, face)
        feature = self.recognizer.feature(aligned).astype(np.float32)
        norm = float(np.linalg.norm(feature))
        if not np.isfinite(norm) or norm <= 1e-8:
            raise StageError('Invalid face embedding')
        return aligned, feature/norm

    def detect(self, image):
        scale = min(1.0, 1280/max(image.shape[:2]))
        small = cv2.resize(image, None, fx=scale, fy=scale)
        self.detector.setInputSize((small.shape[1], small.shape[0]))
        _, faces = self.detector.detect(small)
        if faces is None or len(faces) != 1:
            raise StageError(f'Exactly one face required, detected {0 if faces is None else len(faces)}')
        face = faces[0].copy()
        face[:14] /= scale
        return face

    def extract(self, image):
        face = self.detect(image)
        aligned, feature = self._encode(image, face)
        return aligned, feature, dict(box=face[:4].tolist(), confidence=float(face[14]))
