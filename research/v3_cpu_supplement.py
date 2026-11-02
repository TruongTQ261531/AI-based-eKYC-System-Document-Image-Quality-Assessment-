"""Exploratory label-prefix sensitivity; primary CPU code is immutable."""
import argparse
import hashlib
import json
import re
import time
import unicodedata
from research.v3_common import *
from research.v2_cpu import ALIASES,extract
from research.v3_cpu import fallback
from research.v3_metrics import scoring,summary
from ekyc.document_fields import fold

MODES=('search','bilingual')
READERS=('rapid_v4','rapid_latin_v5')


def normalize(predictions,mode):
    if mode not in MODES:raise ValueError('Unknown supplemental head')
    result=[]
    for original in predictions:
        text=' '.join(unicodedata.normalize('NFC',original['text']).split());plain=fold(text)
        if re.fullmatch(r'[A-Z0-9<]{44}',re.sub(r'\s+','',text.upper())):
            result.append(dict(original));continue
        hits=[(k,m) for k,p in ALIASES.items() for m in re.finditer(p,plain)]
        if hits:
            key,m=max(hits,key=lambda km:(km[1].end()-km[1].start(),-km[1].start(),km[0]))
            if mode=='bilingual':
                _,m=max((km for km in hits if km[0]==key),key=lambda km:(km[1].end(),km[1].end()-km[1].start()))
            tail=text[m.end():]
            if mode=='bilingual' and tail.lstrip().startswith(('/','(')) and not re.search(r'\d',tail):
                text=text[m.start():m.end()]
            else:text=text[m.start():]
        result.append(dict(original,text=text))
    return result


def predict(predictions,mode,mrz):
    fields=extract(normalize(predictions,mode))
    return fallback(fields,predictions,True)[0] if mrz else fields


def supplement_signature():
    return stable_hash(dict(primary=signature(),code=sha(ROOT/'research/v3_cpu_supplement.py'),
        protocol=sha(ROOT/'research/V3_CPU_LABEL_SUPPLEMENT.md')))


def run(role):
    sig=supplement_signature()
    if role=='test' and read(OUT/'cpu_label_supplement_choice.json')['signature']!=sig:raise ValueError('Supplemental development lock differs')
    records={}
    for reader in READERS:
        for mode in MODES:
            for mrz in (False,True):
                name=reader+'/'+mode+('/mrz_checks' if mrz else '/body');rows=[]
                for sample in load(role):
                    token=hashlib.sha256(sample['uid'].encode()).hexdigest()
                    raw=read(CACHE/'cpu_raw'/role/reader/(token+'.json'))
                    if raw['input_sha256']!=sample['input_sha256']:raise ValueError('Supplemental OCR input differs')
                    start=time.perf_counter();fields=predict(raw['predictions'],mode,mrz);elapsed=time.perf_counter()-start
                    text=json.dumps(fields,ensure_ascii=False);metrics,_=scoring(sample,text)
                    row=dict(uid=sample['uid'],physical_id=sample['physical_id'],source=sample['source'],capture=sample['capture'],
                        model=name,signature=sig,input_sha256=sample['input_sha256'],**metrics,
                        wall_seconds=raw['wall_seconds']+elapsed,parsing_only_seconds=elapsed,
                        latency_is_sum_of_component_timers=True,prediction_sha256=hashlib.sha256(text.encode()).hexdigest(),_private_text=text)
                    save(CACHE/'cpu_label_supplement'/role/reader/mode/str(int(mrz))/(token+'.json'),row)
                    rows.append({k:v for k,v in row.items() if not k.startswith('_private')})
                records[name]=dict(rows=rows,summary=summary(rows));print('LABEL_SUPPLEMENT',role,name,flush=True)
    save(OUT/f'cpu_label_supplement_{role}.json',dict(signature=sig,post_hoc=True,original_test_already_observed=True,
        new_neural_inference_calls=0,models=records))


def seal():
    data=read(OUT/'cpu_label_supplement_development.json')
    if data['signature']!=supplement_signature():raise ValueError('Supplement changed')
    best=max(data['models'],key=lambda k:(data['models'][k]['summary']['f1'],-data['models'][k]['summary']['unsupported_nonempty']))
    save(OUT/'cpu_label_supplement_choice.json',dict(signature=supplement_signature(),selected=best,
        selection_role='development',post_hoc_not_independent_confirmation=True,original_test_summaries_previously_seen=True,
        primary_locks_and_deployment_unchanged=True))


def audit():
    count=0;sig=supplement_signature()
    for role in ('development','test'):
        samples={r['uid']:r for r in load(role)};data=read(OUT/f'cpu_label_supplement_{role}.json')
        if data['signature']!=sig:raise ValueError('Supplement result differs')
        for name,value in data['models'].items():
            reader,mode,policy=name.split('/');mrz=policy=='mrz_checks'
            if len(value['rows'])!=len(samples) or {r['uid'] for r in value['rows']}!=set(samples):raise ValueError('Supplement coverage differs')
            for row in value['rows']:
                sample=samples[row['uid']];token=hashlib.sha256(row['uid'].encode()).hexdigest()
                raw=read(CACHE/'cpu_raw'/role/reader/(token+'.json'));text=json.dumps(predict(raw['predictions'],mode,mrz),ensure_ascii=False)
                metrics,_=scoring(sample,text)
                if any(row[k]!=v for k,v in metrics.items()) or hashlib.sha256(text.encode()).hexdigest()!=row['prediction_sha256']:raise ValueError('Supplement replay differs')
                count+=1
            if summary(value['rows'])!=value['summary']:raise ValueError('Supplement summary differs')
    if count!=1728:raise ValueError('Supplement replay count differs')
    save(OUT/'cpu_label_supplement_audit.json',dict(status='passed',signature=sig,derived_rows_replayed=count,
        new_neural_calls=0,original_primary_results_unchanged=True,post_hoc=True))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['development','test','seal','audit']);action=p.parse_args().action
    if action in ('development','test'):run(action)
    else:globals()[action]()
