"""Audit data/weights and select images without OCR outcomes."""
import hashlib
import importlib.metadata
import inspect
import json
from pathlib import Path

import easyocr.config

from research.benchmark import digest
from research.external_midv2020 import metadata
from research.neural_baseline import MODEL_SHA
from research.ocr_diagnostic import normalized,eligible_text

ORIGINAL=Path('D:/laptrinhcuatao/Ekyc/full_dataset_original')
MODELS=Path('D:/laptrinhcuatao/Ekyc/models')


def image_path(sample):
    if sample['source']=='midv2020':return Path('research/data/midv2020')/sample['code']/sample['filename']
    return ORIGINAL/sample['relative_path']


def load_samples():
    primary=[s for s in json.loads(Path('research/data/primary_samples.json').read_text(encoding='utf-8')) if s['uid'].endswith('_15')]
    cached={r['uid']:r for r in map(json.loads,Path('research/cache/docaligner/predictions.jsonl').read_text().splitlines())}
    partial=json.loads(Path('research/cache/docaligner/partial_corners.json').read_text())
    selected=[dict(s,selection_stratum='three_corners',expected_corners=3) for s in primary if s['uid'] in partial and
              sum(p is not None for p in partial[s['uid']]['points'])==3]
    groups={}
    for sample in primary:
        if cached[sample['uid']]['prediction']['detected']:groups.setdefault(sample['physical_id'],[]).append(sample)
    for group in groups.values():
        chosen=min(group,key=lambda s:hashlib.sha256(('e2e-control-20261030/'+s['uid']).encode()).digest())
        selected.append(dict(chosen,selection_stratum='four_corner_control',expected_corners=4))
    if len(selected)!=141 or len(groups)!=50:raise ValueError('Fixed 91+50 primary cases required')
    templates,_=metadata('templates')
    for record in json.loads(Path('research/data/midv2020/selection.json').read_text()):
        uid='midv2020/'+record['code']+'/'+Path(record['filename']).stem
        values={r['region_attributes']['field_name']:r['region_attributes'].get('value')
                for r in templates[record['code']][record['filename']]['regions']}
        fields=[dict(field,text=values[field['key']]) for field in record['fields']]
        expected=4 if cached[uid]['prediction']['detected'] else sum(p is not None for p in partial[uid]['points'])
        selected.append(dict(record,uid=uid,physical_id=record['code']+'/'+Path(record['filename']).stem,
            source='midv2020',quality_label='external_photo',fields=fields,selection_stratum='external',expected_corners=expected))
    if len(selected)!=161:raise ValueError('All 161 selected images required')
    selected.sort(key=lambda s:s['uid'])
    for sample in selected:
        actual=digest(image_path(sample))
        if actual!=cached[sample['uid']]['input_sha256']:raise ValueError('Source image changed since frozen baseline')
        sample['input_sha256']=actual
    return selected


def source_manifest():
    records=[]
    for key in ('craft','english_g2'):
        cfg=easyocr.config.detection_models[key] if key=='craft' else easyocr.config.recognition_models['gen2'][key]
        path=MODELS/'easyocr'/cfg['filename']
        with path.open('rb') as stream:md5=hashlib.file_digest(stream,'md5').hexdigest()
        if md5!=cfg['md5sum']:raise ValueError(f'Official EasyOCR MD5 mismatch {key}')
        records.append(dict(component=key,file=path.name,bytes=path.stat().st_size,sha256=digest(path),
            official_url=cfg['url'],official_md5=md5))
    expected=json.loads(Path('models/identity_model_sources.json').read_text())
    for name in ('base.yml','vgg-transformer.yml','vgg_transformer.pth'):
        path=MODELS/'scanocr'/name;item=next(r for r in expected if r['file']=='scanocr/'+name)
        if digest(path)!=item['sha256']:raise ValueError('VietOCR pinned source mismatch')
        records.append(dict(component='vietocr',file=name,bytes=path.stat().st_size,sha256=item['sha256'],official_url=item['url']))
    path=Path('research/cache/docaligner/fastvit_sa24.onnx')
    if digest(path)!=MODEL_SHA:raise ValueError('DocAligner pinned source mismatch')
    records.append(dict(component='docaligner',file=path.name,bytes=path.stat().st_size,sha256=MODEL_SHA,
        official_url='https://docsaid.org/fr/models/docaligner'))
    packages={name:importlib.metadata.version(name) for name in ('easyocr','vietocr','torch','opencv-python-headless','onnxruntime','numpy','scipy')}
    return dict(weights=records,packages=packages,annotation_manifest_sha256=digest('research/data/sources.json'),
        upstream_training_overlap='Not independently resolved; MIDV exposure possible',
        predictor_receives_ground_truth=False,existing_mentor_runtime_changed=False)
