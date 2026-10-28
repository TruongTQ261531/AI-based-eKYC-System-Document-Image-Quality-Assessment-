import io
import tarfile

import cv2
import numpy as np
import pytest
from PIL import Image

from ekyc.io import StageError
from research.external_midv2020 import displayed_geometry, header
from research.neural_baseline import decode_heatmap


def test_exif_annotation_frame_matches_opencv_decoding(tmp_path):
    path = tmp_path/'rotated.jpg'
    image = Image.new('RGB', (40, 80)); exif = image.getexif(); exif[274] = 6
    image.save(path, exif=exif)
    geometry = displayed_geometry(path)
    decoded = cv2.imdecode(np.fromfile(str(path), np.uint8), cv2.IMREAD_COLOR)
    assert geometry['raw_dimensions'] == [40, 80]
    assert geometry['exif_orientation'] == 6
    assert (geometry['height'], geometry['width']) == decoded.shape[:2] == (40, 80)


def test_corrupted_author_archive_header_is_not_accepted():
    info = tarfile.TarInfo('images/card/05.jpg'); info.size = 5
    raw = info.tobuf(format=tarfile.USTAR_FORMAT)
    assert header(raw) == ('images/card/05.jpg', 5)
    damaged = bytearray(raw); damaged[0] ^= 1
    with pytest.raises(ValueError, match='checksum'):
        header(bytes(damaged))


def test_neural_model_cannot_fabricate_missing_corner_from_empty_heatmap():
    with pytest.raises(StageError, match='Missing neural corner'):
        decode_heatmap(np.zeros((1, 4, 128, 128), np.float32), 400, 600)
