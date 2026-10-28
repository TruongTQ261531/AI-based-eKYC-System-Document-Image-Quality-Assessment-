import json
from pathlib import Path


class StageError(RuntimeError):
    """Expected input/model failure; must never result in an approval."""


def read_image(path):
    import cv2
    import numpy as np
    image = cv2.imdecode(np.fromfile(str(path), dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None or image.size == 0:
        raise StageError(f'Cannot decode image: {path}')
    return image


def write_image(path, image):
    import cv2
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    ok, encoded = cv2.imencode(path.suffix, image)
    if not ok:
        raise StageError(f'Cannot encode image: {path}')
    encoded.tofile(str(path))


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
    temp.replace(path)
