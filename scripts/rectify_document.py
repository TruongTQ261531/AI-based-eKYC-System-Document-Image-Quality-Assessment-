"""Run Module 2 alone on a local image; no Module 1/OCR gate.

Example: python scripts/rectify_document.py --image path/to/photo.jpg --output outputs/rectification
Optional --corners points.json contains [[x,y], ...] in ORIGINAL pixel coordinates.
Artifacts contain the input document: use a local output directory you control.
"""
import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ekyc.io import StageError, read_image, write_image, write_json
from ekyc.module2_homography import Homography


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True, help='New output directory; never overwrite an earlier run')
    parser.add_argument('--corners', type=Path)
    parser.add_argument('--aspect-ratio', type=float, help='Known width/height after geometric corner ordering; omit if unknown')
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Output directory already exists; choose a new directory')
    cv2.setNumThreads(1)
    image = read_image(args.image)
    corners = json.loads(args.corners.read_text(encoding='utf-8-sig')) if args.corners else None
    args.output.mkdir(parents=True)
    try:
        card, geometry = Homography().run(image, corners, aspect_ratio=args.aspect_ratio)
    except StageError as error:
        write_json(args.output/'result.json', dict(status='retake_or_review', reason=str(error)))
        print(str(error))
        return 2
    overlay = image.copy()
    cv2.polylines(overlay, [np.rint(geometry['corners']).astype(np.int32)], True, (0, 200, 0), 3)
    write_image(args.output/'rectified.png', card)
    write_image(args.output/'overlay.jpg', overlay)
    write_json(args.output/'result.json', dict(status='rectified_requires_content_check', geometry=geometry))
    print(f"Saved {args.output/'rectified.png'} ({geometry['width']} x {geometry['height']})")
    print('Check the overlay and crop: a returned rectangle does not prove complete/readable document content.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
