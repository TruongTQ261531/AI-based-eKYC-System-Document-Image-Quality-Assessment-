"""Small known-text OCR diagnostic; synthetic evidence, not a camera benchmark."""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ekyc.io import StageError, write_image, write_json
from ekyc.module2_homography import Homography

TEXT = ['DOCUMENT SAMPLE', 'FULL NAME: SAMPLE PERSON', 'ID NUMBER: 123456789', 'DATE OF BIRTH: 01/02/1990']


def normalize(text):
    return ' '.join(re.sub(r'[^A-Z0-9 ]', '', text.upper()).split())


def edit_distance(a, b):
    row = list(range(len(b)+1))
    for i, x in enumerate(a, 1):
        new = [i]
        for j, y in enumerate(b, 1):
            new.append(min(new[-1]+1, row[j]+1, row[j-1]+(x != y)))
        row = new
    return row[-1]


def capture(dark=False, perspective=True):
    card = np.full((440, 780, 3), 230, np.uint8)
    for index, line in enumerate(TEXT):
        cv2.putText(card, line, (35, 80+85*index), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (25, 25, 25), 2, cv2.LINE_AA)
    src = np.float32([[0,0],[779,0],[779,439],[0,439]])
    dst = np.float32([[170,110],[830,190],[930,640],[70,550]]) if perspective else src+np.float32([100,100])
    matrix = cv2.getPerspectiveTransform(src, dst)
    frame = cv2.warpPerspective(card, matrix, (1040,760), borderValue=(45,45,45))
    if dark:
        frame = (frame.astype(np.float32)*.30).astype(np.uint8)
    return frame


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, default=ROOT/'outputs/module2_review/baseline_module2_homography.py')
    parser.add_argument('--output', type=Path, default=ROOT/'outputs/module2_review/ocr_probe')
    args = parser.parse_args()
    cv2.setNumThreads(1)
    import torch
    torch.set_num_threads(2)
    from ekyc.module3_ocr import OCRExtraction
    print('Loading existing English OCR assets; downloads disabled', flush=True)
    reader = OCRExtraction(ROOT/'models').reader
    spec = importlib.util.spec_from_file_location('ekyc._ocr_baseline', args.baseline)
    baseline = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(baseline)
    detectors = {'baseline': baseline.Homography(), 'current': Homography()}
    expected = normalize(' '.join(TEXT))
    expected_tokens = Counter(expected.split())
    cache, records = {}, []
    for scenario, dark, perspective in [('front',False,False),('perspective',False,True),('dark_perspective',True,True)]:
        image = capture(dark, perspective)
        images = {'raw':image}
        for name, detector in detectors.items():
            try:
                images[name] = detector.run(image)[0]
            except StageError:
                images[name] = None
        for name, pixels in images.items():
            record = {'scenario':scenario, 'method':name}
            if pixels is None:
                record.update(status='localization_rejected', recognized='', token_recall=0., character_error_rate=1.)
            else:
                fingerprint = hashlib.sha256(pixels.tobytes()+str(pixels.shape).encode()).hexdigest()
                if fingerprint not in cache:
                    lines = reader.readtext(pixels, detail=1, paragraph=False)
                    lines.sort(key=lambda line: (min(p[1] for p in line[0]), min(p[0] for p in line[0])))
                    cache[fingerprint] = ' '.join(line[1] for line in lines)
                raw_text = cache[fingerprint]
                recognized = normalize(raw_text)
                hits = sum((Counter(recognized.split()) & expected_tokens).values())
                record.update(status='read', recognized=raw_text,
                              token_recall=hits/sum(expected_tokens.values()),
                              character_error_rate=edit_distance(expected, recognized)/len(expected))
                write_image(args.output/f'{scenario}_{name}.png',pixels)
            records.append(record)
            print(scenario, name, 'token recall', round(record['token_recall'],3), 'CER', round(record['character_error_rate'],3),flush=True)
    result = dict(limitation='Three synthetic printed-text scenes only; not real document OCR accuracy. OCR confidence is not used as correctness.',
                  expected=expected, records=records,
                  current_sha256=hashlib.sha256((ROOT/'ekyc/module2_homography.py').read_bytes()).hexdigest(),
                  baseline_sha256=hashlib.sha256(args.baseline.read_bytes()).hexdigest())
    write_json(args.output/'report.json',result)
    table=['# Synthetic OCR diagnostic', '', result['limitation'], '',
           '| Scene | Method | Expected-token recall | Character error rate |', '|---|---|---:|---:|']
    for r in records:
        table.append(f"| {r['scenario']} | {r['method']} | {r['token_recall']:.3f} | {r['character_error_rate']:.3f} |")
    (args.output/'report.md').write_text('\n'.join(table)+'\n', encoding='utf-8')


if __name__ == '__main__':
    main()
