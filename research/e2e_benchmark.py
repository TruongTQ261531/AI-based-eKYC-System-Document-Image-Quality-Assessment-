"""Resumable three-pass OCR benchmark. Text remains in private local checkpoints."""
import gzip
import hashlib
import importlib
import inspect
import json
import os
import time
import traceback
from pathlib import Path

import cv2
import numpy as np

from ekyc.io import StageError
from research.benchmark import digest,save
from research.e2e_data import MODELS,load_samples,image_path,source_manifest,replication_panel
from research.e2e_eval import score,aggregate,target_fields
from research.e2e_pipeline import Engine,POLICIES,tick,elapsed,policy_image,to_source,raster_hash
from research.ocr_diagnostic import normalized

OUT=Path('research/results/e2e_ocr_v2')
CACHE=Path('research/cache/e2e_ocr_v2')
ENGINES=('easyocr_en','vietocr')


def hash_json(value):return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,allow_nan=False).encode()).hexdigest()


def atomic_json(path,value):
    path.parent.mkdir(parents=True,exist_ok=True);temp=path.with_suffix('.tmp')
    temp.write_text(json.dumps(value,ensure_ascii=False,allow_nan=False),encoding='utf-8')
    os.replace(temp,path)


def checkpoint_path(repeat,uid):return CACHE/f'pass{repeat}'/(hashlib.sha256(uid.encode()).hexdigest()[:20]+'.json')


def event(value):
    CACHE.mkdir(parents=True,exist_ok=True)
    with (CACHE/'events.jsonl').open('a',encoding='utf-8') as stream:
        stream.write(json.dumps(dict(time_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),**value))+'\n')


def prepared_signature(samples):
    code={name:digest('research/'+name) for name in ('e2e_data.py','e2e_eval.py','e2e_pipeline.py','e2e_benchmark.py')}
    installed={}
    for name in ('easyocr.easyocr','easyocr.utils','easyocr.detection','vietocr.tool.translate','ekyc.scanocr'):
        module=importlib.import_module(name);installed[name]=digest(inspect.getsourcefile(module))
    provenance=source_manifest()
    manifest=dict(protocol_sha256=digest('research/E2E_OCR_PROTOCOL.md'),code_sha256=code,installed_sources_sha256=installed,
        model_sources=provenance,image_uids=[s['uid'] for s in samples],
        input_hashes={s['uid']:s['input_sha256'] for s in samples},
        evaluation_annotations_sha256=hash_json([{k:s[k] for k in ('uid','gt','fields')} for s in samples]),
        repeats=3,pass_image_counts=[161,32,32],replication_uids=[s['uid'] for s in replication_panel(samples)],
        order_seeds=[202610301,202610302,202610303],policies=list(POLICIES),engines=list(ENGINES),
        scope='Predicted-box OCR with spatial field transcription evaluation; not semantic KIE',
        fresh_ocr_across_passes=True,within_image_identical_raster_reuse=True)
    return hash_json(manifest),manifest


def process_image(engine,sample,repeat,signature):
    started=tick();raw=np.fromfile(str(image_path(sample)),np.uint8);image=cv2.imdecode(raw,cv2.IMREAD_COLOR)
    decode=elapsed(started)
    if image is None or image.shape[:2]!=(sample['height'],sample['width']):raise ValueError('Decoded source dimensions changed')
    if hashlib.sha256(raw).hexdigest()!=sample['input_sha256']:raise ValueError('Source image bytes changed')
    location,local_time=engine.locate(image)
    count=4 if location['quad'] is not None else sum(p is not None for p in location['points'])
    if count!=sample['expected_corners']:raise ValueError('Fresh corner pattern differs from locked eligibility')
    memo={};rows=[]
    for policy in POLICIES:
        started=tick();routed=True;reason=None;transform=None;mode='review';rhash=None
        try:policy_pixels,transform,mode=policy_image(image,location,policy)
        except StageError as error:routed=False;reason=str(error)
        transform_time=elapsed(started);reused=False
        if routed:
            rhash=raster_hash(policy_pixels);reused=rhash in memo
            if not reused:memo[rhash]=engine.ocr(policy_pixels)
            ocr=memo[rhash]
        else:ocr=dict(predictions={k:[] for k in ENGINES},detection=dict(wall=0.,cpu=0.),
                      recognition={k:dict(wall=0.,cpu=0.) for k in ENGINES},truncated_regions=0)
        for reader in ENGINES:
            started=tick()
            predictions=to_source(ocr['predictions'][reader],transform) if routed else []
            mapping_time=elapsed(started)
            used_local=local_time if policy!='raw_fullframe' else dict(wall=0.,cpu=0.)
            stages=dict(decode=decode,localize=used_local,transform=transform_time,detect=ocr['detection'],
                        recognize=ocr['recognition'][reader],map_boxes=mapping_time)
            timing={f'{stage}_{kind}':value[kind] for stage,value in stages.items() for kind in ('wall','cpu')}
            timing['total_wall']=sum(t['wall'] for t in stages.values());timing['total_cpu']=sum(t['cpu'] for t in stages.values())
            evaluated=score(sample,predictions,routed)
            canonical=[dict(box=[[round(float(x),6) for x in point] for point in p['box']],text=normalized(p['text'])) for p in predictions]
            rows.append(dict(repeat=repeat,uid=sample['uid'],physical_id=sample['physical_id'],source=sample['source'],
                selection_stratum=sample['selection_stratum'],quality_label=sample['quality_label'],observed_corners=count,
                policy=policy,engine=reader,routed=routed,review_reason=reason,transform_mode=mode,
                raster_sha256=rhash,ocr_reused_within_image=reused,truncated_regions=ocr['truncated_regions'],
                score=evaluated,timing=timing,prediction_sha256=hash_json(canonical),
                output_raster_dimensions=list(policy_pixels.shape[1::-1]) if routed else None,
                _private_predictions=predictions))
    return dict(signature=signature,repeat=repeat,uid=sample['uid'],input_sha256=sample['input_sha256'],
                unique_ocr_executions=len(memo),localizer_calls=1,rows=rows)


def publish(samples,signature,manifest):
    rows=[];executions=0
    for repeat in (1,2,3):
        for sample in samples if repeat==1 else replication_panel(samples):
            case=json.loads(checkpoint_path(repeat,sample['uid']).read_text(encoding='utf-8'))
            if case['signature']!=signature:raise ValueError('Checkpoint signature mismatch')
            executions+=case['unique_ocr_executions']
            rows.extend({k:v for k,v in row.items() if not k.startswith('_private')} for row in case['rows'])
    summaries=[]
    for repeat in (1,2,3):
        for policy in POLICIES:
            for reader in ENGINES:
                selected=[r for r in rows if r['repeat']==repeat and r['policy']==policy and r['engine']==reader]
                for stratum in ('primary','three_corners','four_corner_control','external'):
                    subset=[r for r in selected if r['source']!='midv2020'] if stratum=='primary' else [r for r in selected if r['selection_stratum']==stratum]
                    summaries.append(dict(repeat=repeat,policy=policy,engine=reader,stratum=stratum,**aggregate(subset)))
    save(OUT/'summary.json',summaries)
    with (OUT/'per_image.jsonl.gz').open('wb') as target,gzip.GzipFile(fileobj=target,mode='wb',mtime=0,filename='') as stream:
        for row in rows:stream.write((json.dumps(row,allow_nan=False)+'\n').encode())
    sample_audit=[]
    for sample in samples:
        targets,excluded=target_fields(sample)
        sample_audit.append(dict(uid=sample['uid'],physical_id=sample['physical_id'],source=sample['source'],
            selection_stratum=sample['selection_stratum'],input_sha256=sample['input_sha256'],
            expected_corners=sample['expected_corners'],eligible_fields=len(targets),excluded_fields=excluded))
    save(OUT/'sample_audit.json',sample_audit);save(OUT/'manifest.json',dict(signature=signature,**manifest))
    comparisons=[]
    for sample in replication_panel(samples):
        for policy in POLICIES:
            for reader in ENGINES:
                matched=[r for r in rows if r['uid']==sample['uid'] and r['policy']==policy and r['engine']==reader]
                comparisons.append(dict(uid=sample['uid'],policy=policy,engine=reader,
                    predictions_identical=len({r['prediction_sha256'] for r in matched})==1,
                    field_scores_identical=len({hash_json(r['score']['fields']) for r in matched})==1))
    save(OUT/'repeat_audit.json',dict(compared_image_policy_engine=len(comparisons),
        prediction_mismatches=sum(not r['predictions_identical'] for r in comparisons),
        field_score_mismatches=sum(not r['field_scores_identical'] for r in comparisons),
        unique_ocr_executions=executions,unique_localizer_calls=len(samples)+64,
        replication_panel_images=32,full_sample_passes=1,additional_panel_passes=2,
        no_cross_pass_ocr_cache=True,rows=comparisons))
    print('PUBLISHED',len(rows),'image-policy-engine rows',flush=True)


def main():
    OUT.mkdir(parents=True,exist_ok=True);CACHE.mkdir(parents=True,exist_ok=True)
    samples=load_samples();signature,manifest=prepared_signature(samples)
    lock=CACHE/'signature.json'
    if lock.exists() and json.loads(lock.read_text())['signature']!=signature:raise ValueError('Stale experiment cache; use another version')
    save(lock,dict(signature=signature));save(OUT/'manifest.json',dict(signature=signature,**manifest))
    pending=[]
    for repeat in (1,2,3):
        scheduled=samples if repeat==1 else replication_panel(samples)
        order=np.random.default_rng(202610300+repeat).permutation(len(scheduled))
        for index in order:
            sample=scheduled[int(index)];path=checkpoint_path(repeat,sample['uid'])
            if path.exists():
                case=json.loads(path.read_text(encoding='utf-8'))
                if case['signature']!=signature or case['uid']!=sample['uid']:raise ValueError('Invalid completed checkpoint')
            else:pending.append((repeat,sample))
    event(dict(event='start',signature=signature,pending_images=len(pending)))
    if pending:
        engine=Engine(MODELS)
        save(OUT/'initialization.json',dict(model_loading=engine.loading,synthetic_warmup=engine.warmup,
             vietocr_batch_parity=engine.parity,excluded_from_inference_latency=True))
        started=time.perf_counter()
        for index,(repeat,sample) in enumerate(pending,1):
            try:
                case=process_image(engine,sample,repeat,signature)
                atomic_json(checkpoint_path(repeat,sample['uid']),case)
                event(dict(event='complete',repeat=repeat,uid=sample['uid'],unique_ocr_executions=case['unique_ocr_executions']))
            except Exception as error:
                event(dict(event='failure',repeat=repeat,uid=sample['uid'],error_type=type(error).__name__,message=str(error)))
                raise
            print(f'E2E pass{repeat} image {index}/{len(pending)} {sample["uid"]} unique_ocr={case["unique_ocr_executions"]} wall={time.perf_counter()-started:.1f}s',flush=True)
        save(OUT/'execution.json',dict(signature=signature,fresh_images_this_invocation=len(pending),
            elapsed_seconds=time.perf_counter()-started,complete_image_checkpoints=len(samples)+64,
            startup_excluded=True,unexpected_cases_dropped=0))
    publish(samples,signature,manifest)
    event(dict(event='complete_experiment',signature=signature))


if __name__=='__main__':main()
