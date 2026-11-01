"""Frozen RapidOCR readers plus an explicit printed-label layout baseline.

No author boxes, expected field set, document type or reference values enter
extraction. Alias rules are registered before the sealed test.
"""
import argparse
import hashlib
import re
import time
import cv2
import numpy as np
from PIL import Image
from scipy.optimize import linear_sum_assignment
from research.v2_common import *
from research.v2_inputs import Views
from research.v2_runtime import scoring,summary
from ekyc.document_fields import fold,PATTERNS

ALIASES={k:v for k,v in PATTERNS.items() if k in KEYS}
ALIASES.update(first_name=r'\b(?:given\s*names?|first\s*names?|forenames?|name)\b',
    last_name=r'\b(?:surnames?|last\s*names?)\b',
    full_name=r'\b(?:ho(?:\s+va)?\s+ten|full\s*name|name\s+and\s+surname)\b',
    personal_number=r'\b(?:personal\s*(?:number|no|code)|identity\s*(?:number|code))\b',
    birth_place=r'\b(?:place\s+of\s+birth|birth\s*place)\b',
    authority=r'\b(?:issuing\s+authority|authority)\b',
    id_number=r'\b(?:so\s+giay\s+to|document\s*(?:number|no)|passport\s*(?:number|no)|id\s*(?:number|no)|number)\b')

def label(text):
    text=' '.join(text.split());plain=fold(text);hits=[]
    for k,p in ALIASES.items():
        m=re.match(p,plain)
        if m:hits.append((m.end(),k))
    if not hits:return None
    end,key=max(hits);tail=text[end:].strip(' :/.-()')
    # A bilingual continuation that is itself a label is not a value.
    if tail and any(re.fullmatch(p,fold(tail)) for p in ALIASES.values()):tail=''
    return key,tail

def extract(predictions):
    nodes=[];values=[];result={}
    for p in predictions:
        q=np.asarray(p['box'],float);box=[*q.min(axis=0),*q.max(axis=0)];found=label(p['text'])
        if found:
            key,tail=found
            if tail:result.setdefault(key,tail)
            else:nodes.append((key,box))
        elif p['text'].strip():values.append((p['text'].strip(),box))
    if nodes and values:
        costs=np.full((len(nodes),len(values)+len(nodes)),6.)
        for i,(_,b0) in enumerate(nodes):
            x,y,c,d=b0;h=max(5.,d-y)
            for j,(_,b1) in enumerate(values):
                a,b,e,f=b1;dy=abs((b+f-y-d)/2);vh=max(5.,f-b)
                right=(a-c>=-.2*h and dy<=.65*max(h,vh));down=(-.1*h<=b-d<=3.5*h and -h<=a-x<=3*h)
                cr=max(0.,a-c)/h+2*dy/h if right else 1e6
                cd=2+max(0.,b-d)/h+abs(a-x)/(2*h) if down else 1e6
                costs[i,j]=min(cr,cd)
        a,b=linear_sum_assignment(costs)
        for i,j in zip(a,b):
            if j<len(values) and costs[i,j]<6:result.setdefault(nodes[i][0],values[j][0])
    return result

def run(role):
    sig=signature()
    if role=='test':
        lock=read(OUT/'test_lock.json');publication=read(OUT/'lock_publication.json')
        if lock['signature']!=sig or publication['lock_sha256']!=sha(OUT/'test_lock.json'):raise ValueError('Test lock not published')
    from research.recovery_runtime import RecoveryEngine
    engine=RecoveryEngine();views=Views();profile=read(OUT/'input_choice.json')['profile'];outputs=[]
    for i,r in enumerate(load(role),1):
        for reader in ('rapid_v4','rapid_latin_v5'):
            path=CACHE/'cpu'/role/reader/(hashlib.sha256(r['uid'].encode()).hexdigest()+'.json')
            if path.exists():
                record=read(path)
                if record['signature']!=sig:raise ValueError('CPU source changed')
            else:
                start=time.perf_counter()
                with Image.open(ROOT/r['path']) as im:image,meta=views.prepare(im,profile)
                output=engine.ocr(cv2.cvtColor(np.asarray(image),cv2.COLOR_RGB2BGR),reader)
                fields=extract(output['predictions']);text=__import__('json').dumps(fields,ensure_ascii=False)
                metrics,_=scoring(r,text)
                record=dict(signature=sig,uid=r['uid'],physical_id=r['physical_id'],source=r['source'],device=r['device'],
                    layout=r['layout'],held_layout=r.get('held_layout',False),capture=r['capture'],model=reader,
                    input_sha256=r['input_sha256'],**metrics,hit_token_limit=False,wall_seconds=time.perf_counter()-start,
                    prediction_sha256=hashlib.sha256(text.encode()).hexdigest(),_private_text=text,**meta)
                save(path,record)
            outputs.append({k:v for k,v in record.items() if not k.startswith('_private')})
        if i%4==0:print('V2_CPU',role,i,flush=True)
    save(OUT/f'{role}_cpu.json',dict(signature=sig,execution_provider='CPUExecutionProvider',profile=profile,
        parser='v2_cpu explicit global aliases + geometric assignment, no training/GT values',
        gpu_cpu_latency_not_controlled_hardware_comparison=True,rows=outputs,
        summaries={k:summary([r for r in outputs if r['model']==k]) for k in ('rapid_v4','rapid_latin_v5')}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('role',choices=['development','test']);run(p.parse_args().role)
