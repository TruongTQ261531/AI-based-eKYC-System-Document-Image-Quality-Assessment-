"""Existing frozen CPU OCR+KIE comparators on the NEW corpus only."""
import argparse
import hashlib
import json
import time

import cv2

from research.vlm_data import load
from research.vlm_runtime import signature,score,aggregate
from research.vlm_setup import ROOT,CACHE,OUT,save,sha
from research.layout_kie import LayoutKIEEngine,extract


def run(role):
    sig=signature()
    if role=='test':
        lock=json.loads((OUT/'test_lock.json').read_text(encoding='utf-8'))
        if lock['signature']!=sig: raise ValueError('Pre-test lock missing or changed')
    locked=json.loads((ROOT/'research/results/recovery_v4/selector_models.json').read_text(encoding='utf-8'))
    engine=LayoutKIEEngine();rows=[]
    for i,sample in enumerate(load(role),1):
        path=CACHE/'cpu_baseline'/role/(hashlib.sha256(sample['uid'].encode()).hexdigest()+'.json')
        if path.exists():
            record=json.loads(path.read_text(encoding='utf-8'))
            if record['signature']!=sig: raise ValueError('Baseline checkpoint changed')
        else:
            if sha(ROOT/sample['path'])!=sample['input_sha256']: raise ValueError('Input changed')
            image=cv2.imread(str(ROOT/sample['path']));started=time.perf_counter()
            raw=engine.ocr(image,'rapid_latin_v5');fields,_,_=extract(raw['predictions'])
            wall=time.perf_counter()-started
            native=engine.online(image,locked)
            record=dict(signature=sig,uid=sample['uid'],physical_id=sample['physical_id'],capture=sample['capture'],rows=[])
            for name,prediction,elapsed in [('ocr_raw_layout',fields,wall),('ocr_existing_web',native['fields'],native['actual_wall_seconds'])]:
                record['rows'].append(dict(uid=sample['uid'],physical_id=sample['physical_id'],capture=sample['capture'],model=name,
                    wall_seconds=elapsed,**score(sample['target'],prediction,True),
                    masked_field_outputs=sum(f.get('occluded',False) and f['key'] in prediction for f in sample['fields']),
                    _private_fields=prediction))
            save(path,record)
        rows.extend({k:v for k,v in r.items() if not k.startswith('_private')} for r in record['rows'])
        if i%8==0: print('CPU_BASELINE',role,i,flush=True)
    save(OUT/f'{role}_ocr.json',dict(signature=sig,execution_provider='CPUExecutionProvider',
        rows=rows,summaries={name:aggregate([r for r in rows if r['model']==name]) for name in ('ocr_raw_layout','ocr_existing_web')},
        mixed_cpu_gpu_latencies_are_deployment_settings_not_controlled_backend_comparison=True))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('role',choices=['development','test']);run(p.parse_args().role)
