"""Per-frame face geometry and quality from existing MediaPipe weights.

Pose/iris measurements are approximate observations, not a presentation-attack
classifier or a calibrated gaze tracker. No camera images are retained here.
"""
import cv2
import numpy as np

from .io import StageError


def rotation_angles(matrix):
    rotation = np.asarray(matrix, dtype=np.float64)[:3, :3]
    if rotation.shape != (3, 3) or not np.isfinite(rotation).all():
        raise StageError('Invalid face rotation')
    # Remove any estimated scale before extracting Euler angles.
    u, _, vt = np.linalg.svd(rotation)
    rotation = u @ vt
    if np.linalg.det(rotation) < 0:
        raise StageError('Invalid reflected face rotation')
    pitch, yaw, roll = cv2.RQDecomp3x3(rotation)[0]
    return dict(pitch=float(pitch), yaw=float(yaw), roll=float(roll))


def iris_ratio(points, left, right, iris):
    axis = points[right] - points[left]
    width = float(np.linalg.norm(axis))
    if width < 12:
        return None
    ratio = float(np.dot(points[iris]-points[left], axis) / (width*width))
    return ratio if .05 <= ratio <= .95 else None


class FaceObservation:
    def __init__(self, model_dir):
        import mediapipe as mp
        model = model_dir/'face_landmarker.task'
        if not model.is_file():
            raise StageError('Missing face_landmarker.task')
        self.mp = mp
        self.landmarker = mp.tasks.vision.FaceLandmarker.create_from_options(
            mp.tasks.vision.FaceLandmarkerOptions(
                base_options=mp.tasks.BaseOptions(model_asset_path=str(model)),
                running_mode=mp.tasks.vision.RunningMode.IMAGE,
                num_faces=2, min_face_detection_confidence=.6,
                min_face_presence_confidence=.6,
                output_face_blendshapes=True,
                output_facial_transformation_matrixes=True))

    def close(self):
        self.landmarker.close()

    def observe(self, image):
        scale = min(1., 960/max(image.shape[:2]))
        view = cv2.resize(image, None, fx=scale, fy=scale)
        rgb = np.ascontiguousarray(cv2.cvtColor(view, cv2.COLOR_BGR2RGB))
        result = self.landmarker.detect(self.mp.Image(image_format=self.mp.ImageFormat.SRGB, data=rgb))
        count = len(result.face_landmarks)
        if count != 1:
            return dict(face_count=count, quality_ok=False,
                        problems=['multiple_faces' if count > 1 else 'face_missing'], overlay=[])
        points = np.array([[p.x*view.shape[1], p.y*view.shape[0]] for p in result.face_landmarks[0]])
        if len(points) < 478 or not np.isfinite(points).all() or not result.facial_transformation_matrixes:
            raise StageError('Incomplete face geometry')
        h, w = view.shape[:2]
        x1, y1 = points[:468].min(axis=0)
        x2, y2 = points[:468].max(axis=0)
        fw, fh = x2-x1, y2-y1
        problems = []
        if fw < max(100, w*.18) or fh < h*.28:
            problems.append('face_too_small')
        if fw > w*.85 or fh > h*.94:
            problems.append('face_too_close')
        if x1 < w*.015 or x2 > w*.985 or y1 < h*.015 or y2 > h*.985:
            problems.append('face_outside')
        if abs((x1+x2)/(2*w)-.5) > .22 or abs((y1+y2)/(2*h)-.5) > .22:
            problems.append('face_off_center')
        roi = view[max(0,int(y1)):min(h,int(y2)+1), max(0,int(x1)):min(w,int(x2)+1)]
        if not roi.size:
            raise StageError('Invalid face area')
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, None, fx=min(1.,256/max(gray.shape)), fy=min(1.,256/max(gray.shape)))
        brightness, contrast = float(gray.mean()), float(gray.std())
        sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        if brightness < 40: problems.append('face_dark')
        if brightness > 230: problems.append('face_bright')
        if sharpness < 25 or contrast < 10: problems.append('face_blur')
        angles = rotation_angles(result.facial_transformation_matrixes[0])
        if abs(angles['roll']) > 22: problems.append('face_tilted')
        if abs(angles['yaw']) > 48 or abs(angles['pitch']) > 42:
            problems.append('face_extreme_pose')
        shapes = {c.category_name: float(c.score) for c in result.face_blendshapes[0]}
        ratios = [iris_ratio(points,33,133,468), iris_ratio(points,362,263,473)]
        gaze = float(np.mean(ratios)) if all(r is not None for r in ratios) and abs(ratios[0]-ratios[1]) < .3 else None
        indices = (10,152,234,454,1,33,133,362,263,61,291,468,473)
        return dict(face_count=1, quality_ok=not problems, problems=problems, pose=angles,
                    blink_left=shapes.get('eyeBlinkLeft',0.), blink_right=shapes.get('eyeBlinkRight',0.),
                    gaze_horizontal=gaze,
                    smile=(shapes.get('mouthSmileLeft',0.)+shapes.get('mouthSmileRight',0.))/2,
                    metrics=dict(brightness=brightness,sharpness=sharpness,contrast=contrast,
                                 face_width_px=float(fw),face_width_fraction=float(fw/w)),
                    overlay=[[float(points[i,0]/w),float(points[i,1]/h)] for i in indices])
