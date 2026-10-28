"""Local RGB presentation-attack classification, separate from face matching.

MiniFASNetV2 / V1SE (Silent-Face-Anti-Spoofing, ONNX by yakhyo).
Input: unaligned BGR context crops, float32 0..255. Class 1 is bona fide.
These are model scores, not calibrated probabilities or PAD certification.
"""
import hashlib

import cv2
import numpy as np

from .io import StageError
from .scanocr import cpu_session

METHOD = 'minifasnet_v2_v1se_rgb_v1'
MODELS = (
    ('MiniFASNetV2.onnx', 2.7, 'b32929adc2d9c34b9486f8c4c7bc97c1b69bc0ea9befefc380e4faae4e463907'),
    ('MiniFASNetV1SE.onnx', 4., 'ebab7f90c7833fbccd46d3a555410e78d969db5438e169b6524be444862b3676'),
)


def context_crop(image, box, scale):
    """Upstream boundary-shift crop preserves surrounding screen/print context."""
    h, w = image.shape[:2]
    x, y, bw, bh = np.asarray(box, dtype=float)
    if not np.isfinite([x,y,bw,bh]).all() or min(bw,bh) < 16 or bw>w or bh>h:
        raise StageError('Invalid PAD face box')
    scale = min(scale, (w-1)/bw, (h-1)/bh)
    nw, nh = bw*scale, bh*scale
    left = min(max(x+bw/2-nw/2, 0), w-1-nw)
    top = min(max(y+bh/2-nh/2, 0), h-1-nh)
    crop = image[int(top):int(top+nh)+1, int(left):int(left+nw)+1]
    if not crop.size:
        raise StageError('Empty PAD crop')
    resized = cv2.resize(crop, (80,80))
    return np.ascontiguousarray(resized.transpose(2,0,1)[None], dtype=np.float32)


def classify_logits(outputs):
    probabilities = []
    if len(outputs) != 2:
        raise StageError('Both PAD models are required')
    for logits in outputs:
        values = np.asarray(logits, dtype=np.float64).reshape(-1)
        if values.shape != (3,) or not np.isfinite(values).all():
            raise StageError('Invalid PAD prediction')
        exp = np.exp(values-values.max())
        probabilities.append(float((exp/exp.sum())[1]))
    # Require agreement for live. Strong spoof evidence in either model stops
    # the challenge immediately; disagreement never becomes a live result.
    decision = ('live' if min(probabilities) >= .80 else
                'spoof' if min(probabilities) <= .20 else 'uncertain')
    return dict(decision=decision, method=METHOD, live_scores=probabilities)


class PresentationAttackDetection:
    def __init__(self, models_dir):
        self.models = []
        for filename, scale, digest in MODELS:
            path = models_dir/'pad'/filename
            with path.open('rb') as source:
                if hashlib.file_digest(source, 'sha256').hexdigest() != digest:
                    raise StageError('PAD model checksum mismatch')
            session = cpu_session(path)
            shape = session.get_inputs()[0].shape
            if len(shape)!=4 or shape[1:] != [3,80,80] or shape[0] not in (1,'batch_size'):
                raise StageError('Invalid PAD input contract')
            self.models.append((session, scale))

    def check(self, image, faces):
        try:
            face = faces.detect(image)
        except StageError:
            return dict(decision='uncertain', method=METHOD)
        outputs = [session.run(None, {session.get_inputs()[0].name: context_crop(image,face[:4],scale)})[0]
                   for session, scale in self.models]
        return classify_logits(outputs)
