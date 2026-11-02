"""Image-only body-label and conventional TD3 OCR fallback comparators."""
import argparse
import hashlib
import json
import re
import time
import cv2
import numpy as np
from PIL import Image
from research.v3_common import *
from research.v3_sources import parse_td3
from research.v3_metrics import scoring,summary
from research.v2_inputs import Views
from research.v2_cpu import extract
from ekyc.document_fields import text_rows

def mrz_candidates(predictions):
    lines=text_rows(predictions)+[p['text'] for p in predictions]
    lines=list(dict.fromkeys(re.sub(r'\s+','',s.upper()) for s in lines))
    candidates=[]
    for first in lines:
        if len(first)!=44 or not first.startswith('P'):continue
        for second in lines:
            if first==second:continue
            parsed=parse_td3(first,second)
            if parsed:candidates.append(parsed)
    return max(candidates,key=lambda p:sum(p['checks'].values())) if candidates else None

def fallback(body,predictions,strict=False):
    fields=dict(body);parsed=mrz_candidates(predictions)
    if parsed is None:return fields,dict(mrz_pair_found=False,added=0)
    pair_valid=all(parsed['checks'][k] for k in ('id_number','dob','expiry_date','composite'))
    added=0
    for span in parsed['spans']:
        if strict and not (span['checksum_valid'] if span['checksum_valid'] is not None else pair_valid):continue
        if span['key'] not in fields:fields[span['key']]=span['value'];added+=1
    return fields,dict(mrz_pair_found=True,added=added,numeric_checks=parsed['checks'],
        names_gender_nationality_not_individually_checksum_protected=True,authenticity_verified=False)

def run(role):
    sig=signature();profile=read(R2OUT/'input_choice.json')['profile']
    if role=='test':
        seal0=read(OUT/'test_lock.json');pub=read(OUT/'lock_publication.json')
        if seal0['signature']!=sig or pub['lock_sha256']!=sha(OUT/'test_lock.json'):raise ValueError('Source seal not published')
    from research.recovery_runtime import RecoveryEngine
    engine=RecoveryEngine();views=Views();rows=[]
    for i,r in enumerate(load(role),1):
        for reader in ('rapid_v4','rapid_latin_v5'):
            key=hashlib.sha256(r['uid'].encode()).hexdigest();path=CACHE/'cpu_raw'/role/reader/(key+'.json')
            if path.exists():
                raw=read(path)
                if raw['input_sha256']!=r['input_sha256'] or raw['profile']!=profile:raise ValueError('OCR pixel/profile changed')
            else:
                start=time.perf_counter()
                with Image.open(ROOT/r['path']) as image:view,meta=views.prepare(image,profile)
                result=engine.ocr(cv2.cvtColor(np.asarray(view),cv2.COLOR_RGB2BGR),reader)
                raw=dict(input_sha256=r['input_sha256'],predictions=result['predictions'],
                         wall_seconds=time.perf_counter()-start,**meta)
                save(path,raw)
            body=extract(raw['predictions'])
            for policy in ('body','mrz_format','mrz_checks'):
                start=time.perf_counter();fields,info=(body,dict(mrz_pair_found=False,added=0)) if policy=='body' else fallback(body,raw['predictions'],policy=='mrz_checks')
                text=json.dumps(fields,ensure_ascii=False);metrics,_=scoring(r,text);name=reader+'/'+policy
                record=dict(signature=sig,uid=r['uid'],physical_id=r['physical_id'],input_sha256=r['input_sha256'],
                    source=r['source'],device=r['device'],layout=r['layout'],held_layout=r.get('held_layout',False),capture=r['capture'],model=name,
                    **metrics,**info,prediction_sha256=hashlib.sha256(text.encode()).hexdigest(),
                    wall_seconds=raw['wall_seconds']+time.perf_counter()-start,_private_text=text)
                save(CACHE/'cpu'/role/reader/policy/(key+'.json'),record)
                rows.append({k:v for k,v in record.items() if not k.startswith('_private')})
        if i%4==0:print('SOURCE_CPU',role,i,flush=True)
    names=sorted({r['model'] for r in rows})
    save(OUT/f'{role}_cpu.json',dict(signature=sig,profile=profile,execution_provider='CPUExecutionProvider',
        OCR_inference_shared_across_three_postprocessors=True,checksum_is_not_authenticity=True,
        summaries={k:summary([r for r in rows if r['model']==k]) for k in names},rows=rows))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('role',choices=['development','test']);run(p.parse_args().role)
