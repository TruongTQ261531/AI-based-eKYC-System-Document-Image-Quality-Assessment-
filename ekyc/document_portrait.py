"""Locate a printed portrait in the current rectified card, without template lookup."""
import cv2
import numpy as np

from .io import StageError


class PortraitError(StageError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def overlap(a, b):
    left = np.maximum(a[:2], b[:2])
    right = np.minimum(a[:2] + a[2:4], b[:2] + b[2:4])
    intersection = float(np.prod(np.maximum(0, right - left)))
    return intersection / max(1., a[2]*a[3] + b[2]*b[3] - intersection)


class DocumentPortrait:
    def __init__(self, detector, encode):
        self.detector = detector
        self.encode = encode

    def detect(self, card, target, enhance=False):
        scale = target / max(card.shape[:2])
        view = cv2.resize(card, None, fx=scale, fy=scale)
        if enhance:
            lab = cv2.cvtColor(view, cv2.COLOR_BGR2LAB)
            lab[:, :, 0] = cv2.createCLAHE(2., (8, 8)).apply(lab[:, :, 0])
            view = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        self.detector.setInputSize((view.shape[1], view.shape[0]))
        _, detected = self.detector.detect(view)
        result = []
        for item in ([] if detected is None else detected):
            face = item.copy()
            face[:14] /= scale
            x, y, w, h = face[:4]
            # Reject impossible boxes/landmarks, not unfamiliar document layouts.
            points = face[4:14].reshape(5, 2)
            if (not np.isfinite(face).all() or w < 24 or h < 28 or
                    x < -w*.1 or y < -h*.1 or x+w > card.shape[1]+w*.1 or
                    y+h > card.shape[0]+h*.1 or not .45 < w/h < 1.6):
                continue
            if (np.any(points < [x-w*.1, y-h*.1]) or
                    np.any(points > [x+w*1.1, y+h*1.1])):
                continue
            eye_distance = np.linalg.norm(points[0]-points[1])
            if not .15*w < eye_distance < .85*w:
                continue
            if abs(points[0, 1]-points[1, 1]) > .45*eye_distance:
                continue
            if np.mean(points[:2, 1]) >= np.mean(points[3:, 1]):
                continue
            result.append(face)
        return result

    def extract(self, image):
        ambiguous = False
        orientations = []
        for turns in range(4):
            card = np.ascontiguousarray(np.rot90(image, turns))
            initial = self.detect(card, 1280, False)
            orientations.append((max((float(f[14]) for f in initial), default=0.), turns, card, initial))
        # YuNet sometimes fires on an upside-down face. Compare orientations before
        # choosing one, so OCR isn't rotated using the first weak detection.
        for _, turns, card, initial in sorted(orientations, key=lambda v: v[0], reverse=True):
            # A face must be reproduced in two distinct detection views.
            groups = []
            for view_id, (target, enhanced) in enumerate(((1280, False), (800, False), (1600, True))):
                for face in (initial if view_id == 0 else self.detect(card, target, enhanced)):
                    group = next((g for g in groups if overlap(g['face'], face) >= .5), None)
                    if group is None:
                        groups.append(dict(face=face, views={view_id}))
                    else:
                        group['views'].add(view_id)
                        if face[14] > group['face'][14]:
                            group['face'] = face
                # Inspect all scales before selection so a second portrait isn't hidden.
            candidates = sorted((g for g in groups if len(g['views']) >= 2),
                                key=lambda g: g['face'][2]*g['face'][3], reverse=True)
            if not candidates:
                continue
            main = candidates[0]
            crop, embedding = self.encode(card, main['face'])
            duplicates = 0
            for other in candidates[1:]:
                # Printed duplicate/ghost portraits may coexist; another identity is ambiguous.
                _, second = self.encode(card, other['face'])
                if float(np.dot(embedding.ravel(), second.ravel())) < .363:
                    ambiguous = True
                    break
                duplicates += 1
            else:
                return card, crop, embedding, dict(
                    box=main['face'][:4].tolist(), confidence=float(main['face'][14]),
                    rotation_ccw_degrees=turns*90, coordinate_space='oriented_rectified_card',
                    supporting_views=len(main['views']), duplicate_portraits=duplicates,
                    method='yunet_multiview_sface', status='available')
            # A genuinely ambiguous view must not be bypassed by rotating until one disappears.
            if ambiguous:
                raise PortraitError('id_face_ambiguous')
        raise PortraitError('id_face_unavailable')
