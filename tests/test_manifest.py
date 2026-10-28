import csv
from collections import Counter
from ekyc.config import ROOT


def test_prepared_dataset_integrity():
    rows=list(csv.DictReader((ROOT/'data/manifest.csv').open(encoding='utf-8-sig')))
    assert len(rows)==21050
    assert len({r['relative_path'] for r in rows})==21050
    assert all((ROOT/r['relative_path']).is_file() for r in rows)
    assert Counter(r['label'] for r in rows)=={'Clean':9050,'Blur':3000,'Cropped':3000,'Dark':3000,'Distorted':3000}
    extras=[r for r in rows if r['origin']=='user_requested_clean']
    assert len(extras)==50 and all(r['label']=='Clean' and r['source']=='midv2019' for r in extras)
    original={r['image_name']:r['label'] for r in csv.DictReader((ROOT/'Multilabel.csv').open())}
    assert all(r['label']==original[r['image_name']] for r in rows if r['origin']=='Multilabel.csv')
    splits={s:{r['document'] for r in rows if r['split']==s} for s in ('train','val','test')}
    assert not (splits['train']&splits['test'] or splits['train']&splits['val'] or splits['val']&splits['test'])
