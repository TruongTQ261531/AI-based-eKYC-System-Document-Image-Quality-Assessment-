"""Module 4: MediaPipe motion evidence. This is NOT a certified anti-spoof detector."""
import math
import cv2
import numpy as np
from .io import StageError


class MotionEvidence:
    def __init__(self):
        self.eye_state = 'unknown'
        self.closed_at = None
        self.blinks = 0
        self.yaws = []

    def update(self, blink, yaw, timestamp_ms):
        if blink < 0.25:
            if self.eye_state == 'closed' and 50 <= timestamp_ms-self.closed_at <= 1200:
                self.blinks += 1
            self.eye_state = 'open'
        elif blink > 0.60 and self.eye_state == 'open':
            self.eye_state = 'closed'
            self.closed_at = timestamp_ms
        self.yaws.append(float(yaw))

    def result(self):
        # Demand both directions, not a single static tilted face.
        left = any(yaw < -0.12 for yaw in self.yaws)
        right = any(yaw > 0.12 for yaw in self.yaws)
        return dict(blinks=self.blinks, turned_left=left, turned_right=right,
                    passed=self.blinks >= 1 and left and right)


class LivenessDetection:
    def __init__(self, settings):
        self.settings = settings

    def run(self, video_path, face_engine):
        import mediapipe as mp
        model = self.settings.models_dir/'face_landmarker.task'
        if not model.exists():
            raise StageError('Missing face_landmarker.task; run python -m ekyc.download_models')
        options = mp.tasks.vision.FaceLandmarkerOptions(
            base_options=mp.tasks.BaseOptions(model_asset_path=str(model)),
            running_mode=mp.tasks.vision.RunningMode.VIDEO, num_faces=2,
            output_face_blendshapes=True,
            min_face_detection_confidence=0.6, min_face_presence_confidence=0.6)
        capture = cv2.VideoCapture(str(video_path))
        if not capture.isOpened():
            raise StageError('Cannot decode selfie video')
        fps = capture.get(cv2.CAP_PROP_FPS)
        if not math.isfinite(fps) or fps <= 0 or fps > 240:
            capture.release()
            raise StageError('Invalid video frame rate')
        stride = max(1, round(fps/self.settings.sample_fps))
        evidence = MotionEvidence()
        embeddings, crops, timestamps = [], [], []
        valid = sampled = decoded = 0
        multiple_faces = False
        last_identity_ms = -1000
        try:
            with mp.tasks.vision.FaceLandmarker.create_from_options(options) as landmarker:
                while True:
                    ok, frame = capture.read()
                    if not ok:
                        break
                    index = decoded
                    decoded += 1
                    if decoded/fps > self.settings.max_video_seconds:
                        raise StageError(f'Video exceeds {self.settings.max_video_seconds:g} seconds')
                    if index % stride:
                        continue
                    sampled += 1
                    timestamp = int(index*1000/fps)
                    small = cv2.resize(frame, None, fx=min(1,640/frame.shape[1]), fy=min(1,640/frame.shape[1]))
                    rgb = np.ascontiguousarray(cv2.cvtColor(small, cv2.COLOR_BGR2RGB))
                    result = landmarker.detect_for_video(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb), timestamp)
                    if len(result.face_landmarks) != 1:
                        multiple_faces |= len(result.face_landmarks) > 1
                        evidence.eye_state = 'unknown'
                        continue
                    valid += 1
                    points = result.face_landmarks[0]
                    shapes = {category.category_name: category.score for category in result.face_blendshapes[0]}
                    blink = min(shapes.get('eyeBlinkLeft', 0), shapes.get('eyeBlinkRight', 0))
                    # Nose displacement relative to the two cheeks, normalized by face width.
                    mid = (points[234].x + points[454].x)/2
                    yaw = (points[1].x-mid)/max(abs(points[454].x-points[234].x), 1e-6)
                    evidence.update(blink, yaw, timestamp)
                    if timestamp-last_identity_ms >= 500:
                        try:
                            crop, embedding, _ = face_engine.extract(frame)
                            embeddings.append(embedding)
                            crops.append(crop)
                            timestamps.append(timestamp)
                            last_identity_ms = timestamp
                        except StageError:
                            pass
        finally:
            capture.release()
        duration = decoded/fps
        if duration < self.settings.min_video_seconds:
            raise StageError('Selfie video must be at least two seconds')
        motion = evidence.result()
        coverage = valid/max(sampled, 1)
        continuous_identity = False
        if len(embeddings) >= 3:
            vectors = np.concatenate(embeddings, axis=0)
            pairwise = vectors@vectors.T
            continuous_identity = bool(float(pairwise.min()) >= self.settings.match_threshold)
        passed = motion['passed'] and coverage >= 0.85 and not multiple_faces and continuous_identity
        report = dict(passed=bool(passed), method='mediapipe_blink_and_head_turn_heuristic',
            **{k:v for k,v in motion.items() if k != 'passed'},
            duration_seconds=duration, sampled_frames=sampled, valid_face_frames=valid,
            face_coverage=coverage, multiple_faces=multiple_faces, identity_consistent=continuous_identity,
            identity_samples=len(embeddings), identity_timestamps_ms=timestamps,
            requires_review=True, limitation='Motion evidence alone cannot rule out replay or deepfake attacks.')
        return report, embeddings, crops
