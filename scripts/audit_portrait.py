"""Offline detection coverage, not identity accuracy; never part of inference."""
import csv
import time
from collections import Counter

import cv2
import numpy as np

from ekyc.config import ROOT
from ekyc.faces import FaceEngine
from ekyc.io import StageError, read_image, write_json
from ekyc.module2_homography import Homography


def main():
    cv2.setNumThreads(2)
    rows = list(csv.DictReader((ROOT/'data/manifest.csv').open(encoding='utf-8-sig')))
    references = [r for r in rows if r['is_reference']=='1' and r['split'] in ('val','test')]
    engine = FaceEngine(ROOT/'models')
    records = []
    started = time.monotonic()
    def compare(card, category, rotation, row):
        result = dict(category=category, rotation=rotation, document=row['document'], split=row['split'])
        try:
            engine.extract(card)
            result['baseline'] = 'available'
        except StageError:
            result['baseline'] = 'unavailable'
        try:
            _, _, _, info = engine.extract_document(card)
            result['current'] = 'available'
            result['correction_ccw'] = info['rotation_ccw_degrees']
        except StageError as error:
            result['current'] = getattr(error, 'code', 'unavailable')
        records.append(result)
    for row in references:
        image = read_image(ROOT/row['relative_path'])
        for turns in range(4):
            compare(np.ascontiguousarray(np.rot90(image, turns)), 'reference', turns*90, row)
        print(f'references={len(records)}/64', flush=True)
    # One deterministic frame per held-out document for each condition, at most 8 per label.
    for label in ('Clean', 'Blur', 'Dark', 'Distorted', 'Cropped'):
        selected = {}
        for row in rows:
            if row['split'] in ('val','test') and row['label']==label and row['is_reference']!='1':
                selected.setdefault(row['document'], row)
        for row in list(selected.values())[:8]:
            try:
                card, _ = Homography().run(read_image(ROOT/row['relative_path']))
                compare(card, label, 0, row)
            except StageError:
                records.append(dict(category=label, document=row['document'], split=row['split'],
                                    baseline='not_run_geometry_failed', current='not_run_geometry_failed'))
        print(f'frames: {label}', flush=True)
    # Non-face inputs must not become a fabricated portrait.
    rng = np.random.default_rng(42)
    for name, image in [('blank',np.full((500,800,3),180,np.uint8)),
                        ('noise',rng.integers(0,256,(500,800,3),dtype=np.uint8))]:
        compare(image, 'negative', 0, {'document':name,'split':'synthetic'})
    summary = {}
    for category in sorted({r['category'] for r in records}):
        group = [r for r in records if r['category']==category]
        summary[category] = dict(count=len(group), baseline=dict(Counter(r['baseline'] for r in group)),
                                current=dict(Counter(r['current'] for r in group)))
    report = dict(summary=summary, cases=records, elapsed_seconds=round(time.monotonic()-started,1),
        limitation='Detection coverage only. No ground-truth face boxes/identity labels; not biometric accuracy. Reference rotations are correlated views, not independent samples. No actual user camera photo provided.')
    write_json(ROOT/'outputs/portrait_audit.json', report)
    print(summary, flush=True)


if __name__=='__main__': main()
