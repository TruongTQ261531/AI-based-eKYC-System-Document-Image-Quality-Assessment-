"""Secondary crop-induced OCR harm measurement with oracle field localization."""
import argparse
import csv
import hashlib
import json
import re
import time
import unicodedata
from pathlib import Path

import cv2
import numpy as np
import torch

from research.benchmark import SEEDS,METHODS,calibrate,region_for,save,digest
from research.support_regions import area,intersection,frame_polygon


def normalized(text):
    return ' '.join(unicodedata.normalize('NFC',str(text)).upper().split())


def edit_distance(first,second):
    row=list(range(len(second)+1))
    for i,a in enumerate(first,1):
        nxt=[i]
        for j,b in enumerate(second,1):nxt.append(min(nxt[-1]+1,row[j]+1,row[j-1]+(a!=b)))
        row=nxt
    return row[-1]


def eligible_text(value):
    if not 4<=len(value)<=64 or not any(c.isalnum() for c in value):return False
    return all(not c.isalpha() or 'LATIN' in unicodedata.name(c,'') for c in value)


def select_cases(samples):
    ids=np.array(sorted({s['physical_id'] for s in samples}))
    shuffled=np.random.default_rng(SEEDS[0]).permutation(ids);test=set(map(int,shuffled[20:]))
    candidates={}
    for sample in samples:
        if sample['physical_id'] not in test:continue
        frame=frame_polygon(sample['width'],sample['height'])
        for field in sample['fields']:
            quad=np.asarray(field['quad'],np.float32)
            if not eligible_text(field['text']) or area(quad)<1:continue
            if area(intersection(quad,frame))/area(quad)<.995:continue
            sides=np.linalg.norm(np.roll(quad,-1,axis=0)-quad,axis=1)
            if sides.min()<5:continue
            key=(sample['physical_id'],sample['source'])
            rank=hashlib.sha256(f"secondary-ocr-20261028/{sample['uid']}/{field['key']}".encode()).hexdigest()
            candidates.setdefault(key,[]).append((rank,sample,field))
    return [min(rows,key=lambda r:r[0])[1:] for _,rows in sorted(candidates.items())]


def field_patch(image,field,region):
    quad=np.asarray(field['quad'],np.float32)
    h,w=image.shape[:2]
    x1,y1=np.maximum(np.floor(quad.min(axis=0)).astype(int)-2,[0,0])
    x2,y2=np.minimum(np.ceil(quad.max(axis=0)).astype(int)+3,[w,h])
    crop=image[y1:y2,x1:x2].copy()
    if region is not None:
        mask=np.zeros(crop.shape[:2],np.uint8)
        cv2.fillConvexPoly(mask,np.rint(np.asarray(region)-[x1,y1]).astype(np.int32),255)
        crop[mask==0]=0
    top,bottom=np.linalg.norm(quad[1]-quad[0]),np.linalg.norm(quad[2]-quad[3])
    left,right=np.linalg.norm(quad[3]-quad[0]),np.linalg.norm(quad[2]-quad[1])
    width=int(np.clip(48*max(top,bottom)/max(left,right,1),32,640))
    target=np.float32([[0,0],[width-1,0],[width-1,47],[0,47]])
    matrix=cv2.getPerspectiveTransform(quad-np.float32([x1,y1]),target)
    return cv2.warpPerspective(crop,matrix,(width,48))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--data-root',type=Path,required=True)
    parser.add_argument('--models-root',type=Path,required=True)
    parser.add_argument('--cache',type=Path,default=Path('research/cache/predictions.jsonl'))
    parser.add_argument('--output',type=Path,default=Path('research/results/ocr_diagnostic'))
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    torch.set_num_threads(2);cv2.setNumThreads(1)
    samples=json.loads(Path('research/data/primary_samples.json').read_text(encoding='utf-8'))
    predictions={r['uid']:r for r in map(json.loads,args.cache.read_text(encoding='utf-8').splitlines())}
    if len(predictions)!=3500:raise ValueError('Complete primary inference cache required')
    shuffled=np.random.default_rng(SEEDS[0]).permutation(sorted({s['physical_id'] for s in samples}))
    quantiles=calibrate(samples,predictions,set(map(int,shuffled[:20])),.1)
    cases=select_cases(samples)
    import easyocr
    from ekyc.scanocr import VietnameseRecognizer
    english=easyocr.Reader(['en'],gpu=False,model_storage_directory=str(args.models_root/'easyocr'),download_enabled=False,verbose=False)
    vietnamese=VietnameseRecognizer(args.models_root/'scanocr')
    def read_english(patch):
        result=english.recognize(patch,horizontal_list=[[0,patch.shape[1],0,patch.shape[0]]],free_list=[],detail=1,paragraph=False)
        return ' '.join(row[1] for row in result),float(np.mean([row[2] for row in result])) if result else 0.
    readers={'easyocr_en':read_english,'vietocr':vietnamese.predict}
    records=[];started=time.monotonic()
    for index,(sample,field) in enumerate(cases,1):
        image=cv2.imdecode(np.fromfile(str(args.data_root/sample['relative_path']),np.uint8),cv2.IMREAD_COLOR)
        pred=predictions[sample['uid']]['prediction'];truth=normalized(field['text'])
        # Identical raster patches reuse the readout, not a different model result.
        memo={}
        for method in ('unmasked_oracle_field',)+METHODS:
            region=None if method=='unmasked_oracle_field' else region_for(sample,pred,method,quantiles)[0]
            patch=field_patch(image,field,region);patch_hash=hashlib.sha256(patch.tobytes()).hexdigest()
            for engine,reader in readers.items():
                key=(engine,patch_hash)
                if key not in memo:memo[key]=reader(patch)
                text,confidence=memo[key];recognized=normalized(text);distance=edit_distance(truth,recognized)
                records.append(dict(uid=sample['uid'],physical_id=sample['physical_id'],source=sample['source'],
                    field_key=field['key'],method=method,engine=engine,truth_length=len(truth),
                    prediction_length=len(recognized),edit_distance=distance,cer=distance/len(truth),
                    exact=distance==0,confidence=confidence if np.isfinite(confidence) else 0.))
        print(f'OCR field {index}/{len(cases)}, elapsed {time.monotonic()-started:.1f}s',flush=True)
    summaries=[]
    for engine in readers:
        for method in ('unmasked_oracle_field',)+METHODS:
            rows=[r for r in records if r['engine']==engine and r['method']==method]
            summaries.append(dict(engine=engine,method=method,n=len(rows),macro_cer=float(np.mean([r['cer'] for r in rows])),
                exact_match=float(np.mean([r['exact'] for r in rows])),
                micro_cer=sum(r['edit_distance'] for r in rows)/sum(r['truth_length'] for r in rows)))
    save(args.output/'summary.json',summaries);save(args.output/'per_field.json',records)
    save(args.output/'run.json',dict(protocol_sha256=digest('research/SECONDARY_OCR_PROTOCOL.md'),
        code_sha256=digest(__file__),prediction_cache_sha256=digest(args.cache),field_cases=len(cases),
        physical_documents=len({s['physical_id'] for s,_ in cases}),method_engine_rows=len(records),
        elapsed_seconds=round(time.monotonic()-started,2),field_selection='fixed hash among fully visible Latin GT fields',
        scope='oracle-controlled crop-induced OCR harm; NOT end-to-end card OCR accuracy',
        saved_personal_text_or_images=False))
    print(json.dumps(summaries),flush=True)


if __name__=='__main__':main()
