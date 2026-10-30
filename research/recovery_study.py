"""Locked, resumable prediction/fit/evaluate phases with sealed test scoring."""
import argparse
import contextlib
import gzip
import hashlib
import json
import os
import platform
import time
from collections import defaultdict
from pathlib import Path

import cv2
import numpy as np

from research.benchmark import digest,save
from research.e2e_eval import score,aggregate
from research.e2e_benchmark import hash_json,atomic_json
from research.ocr_diagnostic import normalized
from research.recovery_assets import manifest as assets
from research.recovery_data import load_samples
from research.recovery_runtime import RecoveryEngine,POLICIES,READERS
from research.recovery_selection import fit_selectors,choose,combined_cost

CACHE=Path('research/cache/recovery_v4')
OUT=Path('research/results/recovery_v4')
CODE=('recovery_assets.py','recovery_acquire.py','recovery_data.py','recovery_runtime.py','recovery_upstream.py','recovery_selection.py','recovery_study.py')
METHODS=('fixed_completion','max_confidence','allviews_ridge','allviews_stumps','cascade_ridge','cascade_stumps')


@contextlib.contextmanager
def process_lock(path):
    path=Path(path);path.parent.mkdir(exist_ok=True,parents=True)
    with path.open('a+b') as stream:
        if path.stat().st_size==0:stream.write(b'0');stream.flush()
        stream.seek(0)
        if os.name=='nt':
            import msvcrt
            try:msvcrt.locking(stream.fileno(),msvcrt.LK_NBLCK,1)
            except OSError as e:raise RuntimeError('Another recovery benchmark owns the process lock') from e
        else:
            import fcntl
            try:fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except OSError as e:raise RuntimeError('Another recovery benchmark owns the process lock') from e
        try:yield
        finally:
            stream.seek(0)
            if os.name=='nt':msvcrt.locking(stream.fileno(),msvcrt.LK_UNLCK,1)
            else:fcntl.flock(stream,fcntl.LOCK_UN)


def panel(samples):
    result=[]
    for source in ('authored_specimen','midv2020_derived'):
        for role in ('development','calibration','test'):
            by_id=defaultdict(list)
            for s in samples:
                if s['source']==source and s['role']==role:by_id[s['physical_id']].append(s)
            ids=sorted(by_id,key=lambda x:hashlib.sha256(('panel/'+x).encode()).digest())[:4]
            for identity in ids:
                result.append(min(by_id[identity],key=lambda s:hashlib.sha256(('panel-case/'+s['uid']).encode()).digest()))
    if len(result)!=24:raise ValueError('Expected24 distinct-ID panel')
    return sorted(result,key=lambda s:s['uid'])


def prepared(samples):
    model=assets();model['lcnet_sha256']=digest('research/cache/upstream/lcnet100.onnx')
    source=dict(code_sha256={n:digest('research/'+n) for n in CODE},
        shared_code_sha256={n:digest('research/'+n) for n in ('e2e_pipeline.py','e2e_eval.py','partial_support.py')},
        protocol_sha256=digest('research/RESEARCH_V4_PROTOCOL.md'),assets=model,
        inputs=[{k:s[k] for k in ('uid','physical_id','role','input_sha256')} for s in samples],
        annotations_sha256=hash_json([{k:s[k] for k in ('uid','gt','fields')} for s in samples]),
        sample_counts=[540,24,24],panel_uids=[s['uid'] for s in panel(samples)],policies=list(POLICIES),readers=list(READERS),
        python=platform.python_version(),platform=platform.platform(),threads=2,
        test_scoring_after_model_lock=True,randomized_nonraw_policy_order=True)
    return hash_json(source),source


def path_for(repeat,uid):return CACHE/f'pass{repeat}'/(hashlib.sha256(uid.encode()).hexdigest()[:24]+'.json')


def journal(event,**kwargs):
    CACHE.mkdir(parents=True,exist_ok=True)
    with (CACHE/'events.jsonl').open('a',encoding='utf-8') as stream:
        stream.write(json.dumps(dict(time_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),event=event,**kwargs))+'\n')


def inference():
    samples=load_samples();signature,source=prepared(samples);lock=CACHE/'signature.json'
    if lock.exists() and json.loads(lock.read_text())['signature']!=signature:raise ValueError('Immutable recovery cache is stale')
    save(lock,dict(signature=signature));save(OUT/'manifest.json',dict(signature=signature,**source))
    schedule=[]
    for repeat,group in ((1,samples),(2,panel(samples)),(3,panel(samples))):
        order=np.random.default_rng(202610300+repeat).permutation(len(group))
        for i in order:schedule.append((repeat,group[int(i)]))
    pending=[]
    for repeat,s in schedule:
        p=path_for(repeat,s['uid'])
        if p.exists():
            old=json.loads(p.read_text(encoding='utf-8'))
            if old['signature']!=signature or old['uid']!=s['uid']:raise ValueError('Checkpoint signature or identity mismatch')
        else:pending.append((repeat,s))
    journal('start',signature=signature,pending=len(pending));loading=time.perf_counter();engine=RecoveryEngine()
    load_seconds=time.perf_counter()-loading;warm=time.perf_counter();blank=np.full((200,600,3),255,np.uint8)
    cv2.putText(blank,'SYNTHETIC WARMUP 2026',(10,100),cv2.FONT_HERSHEY_SIMPLEX,1,(0,0,0),2)
    for reader in READERS:engine.ocr(blank,reader)
    for key in ('fastvit','lcnet'):engine.locate(blank,key)
    save(OUT/'initialization.json',dict(loading_wall=load_seconds,warmup_wall=time.perf_counter()-warm,excluded_from_case_latency=True))
    started=time.perf_counter()
    for index,(repeat,sample) in enumerate(pending,1):
        try:
            if digest(sample['path'])!=sample['input_sha256']:raise ValueError('Source image changed')
            image=cv2.imdecode(np.fromfile(sample['path'],np.uint8),cv2.IMREAD_COLOR)
            if image.shape[:2]!=(sample['height'],sample['width']):raise ValueError('Source dimensions changed')
            rng=np.random.default_rng(int(hashlib.sha256((str(repeat)+sample['uid']).encode()).hexdigest()[:12],16))
            order=list(POLICIES);rng.shuffle(order)
            rows,calls=engine.views(image,policy_order=order)
            for row in rows:
                row['prediction_sha256']=hash_json([dict(text=normalized(p['text']),box=np.round(p['box'],5).tolist()) for p in row['_private_predictions']])
                # Test annotations are deliberately not scored in this phase.
                if sample['role']!='test':row['score']=score(sample,row['_private_predictions'],row['routed'])
            record=dict(signature=signature,repeat=repeat,uid=sample['uid'],physical_id=sample['physical_id'],
                source=sample['source'],role=sample['role'],input_sha256=sample['input_sha256'],rows=rows,**calls)
            atomic_json(path_for(repeat,sample['uid']),record);journal('case_complete',repeat=repeat,uid=sample['uid'])
        except Exception as error:
            journal('failure',repeat=repeat,uid=sample['uid'],error_type=type(error).__name__);raise
        print(f'RECOVERY {index}/{len(pending)} pass{repeat} complete={588-len(pending)+index}/588 wall={time.perf_counter()-started:.1f}s',flush=True)
    save(OUT/'execution.json',dict(signature=signature,fresh_cases=len(pending),expected_cases=588,
        elapsed_seconds=time.perf_counter()-started,no_cases_dropped=True,exit_status='complete'))
    journal('inference_complete',signature=signature)


def records(samples):
    return [json.loads(path_for(1,s['uid']).read_text(encoding='utf-8')) for s in samples]


def fit():
    samples=load_samples();signature,_=prepared(samples)
    # Only dev/cal checkpoint files enter fitting; no test file is even opened.
    allowed=records([s for s in samples if s['role']!='test'])
    if any(r['signature']!=signature for r in allowed):raise ValueError('Fitting checkpoint signature mismatch')
    fitted={reader:fit_selectors(allowed,reader) for reader in READERS};thresholds={}
    for reader in READERS:
        thresholds[reader]={}
        for method in METHODS:
            conf=[]
            for record in allowed:
                if record['role']!='calibration':continue
                rows={r['policy']:r for r in record['rows'] if r['engine']==reader}
                chosen,_=choose(rows,method,fitted[reader]['models']);conf.append(rows[chosen]['features'][6])
            thresholds[reader][method]=float(np.quantile(conf,.2))
    result=dict(signature=signature,selectors=fitted,review_thresholds=thresholds,
        calibration_target_retention=.8,test_checkpoint_files_opened=False,test_accuracy_inspected=False,
        training_roles=['development'],calibration_roles=['calibration'])
    save(OUT/'selector_models.json',result);save(OUT/'selector_lock.json',dict(signature=signature,model_sha256=digest(OUT/'selector_models.json')))
    print('SELECTORS_LOCKED',[(r,fitted[r]['primary_method']) for r in READERS],flush=True)


def semantic_score(sample,predicted):
    from research.e2e_eval import target_fields
    targets,_=target_fields(sample)
    return dict(eligible_fields=len(targets),exact=sum(normalized(predicted.get(f['key']) or '')==normalized(f['text']) for f in targets),
        predicted_keys=len(predicted),unmatched_keys=sum(k not in {f['key'] for f in sample['fields']} for k in predicted))


def evaluate():
    samples=load_samples();signature,_=prepared(samples);model=json.loads((OUT/'selector_models.json').read_text())
    lock=json.loads((OUT/'selector_lock.json').read_text())
    if model['signature']!=signature or lock['model_sha256']!=digest(OUT/'selector_models.json'):raise ValueError('Selector lock changed')
    public=[];checkpoint_hashes=[];recomputed=0;failures=0
    for repeat,group in ((1,samples),(2,panel(samples)),(3,panel(samples))):
        for sample in group:
            path=path_for(repeat,sample['uid']);record=json.loads(path.read_text(encoding='utf-8'))
            if record['signature']!=signature or record['input_sha256']!=sample['input_sha256']:raise ValueError('Checkpoint mismatch')
            rows=[]
            for old in record['rows']:
                row=dict(old);measured=score(sample,row['_private_predictions'],row['routed']);recomputed+=1
                if 'score' in row and row['score']!=measured:raise ValueError('Saved development/calibration score differs')
                row['score']=measured;row.update({k:sample[k] for k in ('uid','physical_id','source','role','layout','unseen_layout','capture')})
                row['repeat']=repeat;row['timing']=dict(total_wall=row['total_wall'],total_cpu=row['total_cpu'])
                if sample['source']=='authored_specimen':row['semantic_score']=semantic_score(sample,row['_private_semantic'])
                rows.append(row)
                public.append({k:v for k,v in row.items() if not k.startswith('_private')})
            for reader in READERS:
                by_policy={r['policy']:r for r in rows if r['engine']==reader}
                for method in METHODS:
                    chosen,cost=choose(by_policy,method,model['selectors'][reader]['models']);base=by_policy[chosen]
                    routed=base['routed'] and base['features'][6]>=model['review_thresholds'][reader][method]
                    row={k:v for k,v in base.items() if not k.startswith('_private')}
                    row.update(policy=method,chosen_policy=chosen,review_recommended=not routed,
                        estimated_trace_wall=cost,latency_is_trace_estimate=True,
                        primary_selected_on_development=method==model['selectors'][reader]['primary_method'])
                    # The text remains available for human review; selective
                    # acceptance is a separate operational decision, not OCR erasure.
                    requested=(POLICIES if method=='max_confidence' or method.startswith('allviews_') else
                               ('completion',chosen) if chosen!='completion' else ('completion',))
                    cpu_cost=combined_cost(by_policy,requested,kind='cpu') if len(requested)>1 else base['total_cpu']
                    row['timing']=dict(total_wall=cost,total_cpu=cpu_cost)
                    row['selector_cpu_not_remeasured']=True
                    public.append(row)
            checkpoint_hashes.append(dict(repeat=repeat,uid=sample['uid'],sha256=digest(path)))
    with (OUT/'per_image.jsonl.gz').open('wb') as target,gzip.GzipFile(fileobj=target,mode='wb',filename='',mtime=0) as stream:
        for row in public:stream.write((json.dumps(row,allow_nan=False)+'\n').encode())
    summary=[]
    for role in ('development','calibration','test'):
        for source in ('authored_specimen','midv2020_derived'):
            for reader in READERS:
                for method in POLICIES+METHODS:
                    chosen=[r for r in public if r['repeat']==1 and r['role']==role and r['source']==source and r['engine']==reader and r['policy']==method]
                    result=dict(role=role,source=source,reader=reader,method=method,**aggregate(chosen))
                    if method in METHODS:
                        accepted=[r for r in chosen if not r['review_recommended']];ff=[f for r in accepted for f in r['score']['fields']]
                        total=sum(r['score']['eligible_fields'] for r in chosen)
                        result.update(retention=len(accepted)/len(chosen),conditional_exact=float(np.mean([f['exact'] for f in ff])) if ff else None,
                            correct_field_yield=sum(f['exact'] for f in ff)/max(total,1))
                    else:result['retention']=result['routed_fraction']
                    if source=='authored_specimen':
                        n=sum(r['semantic_score']['eligible_fields'] for r in chosen)
                        result['semantic_field_exact']=sum(r['semantic_score']['exact'] for r in chosen)/max(n,1)
                    summary.append(result)
    save(OUT/'summary.json',summary)
    repeat_groups=[]
    for sample in panel(samples):
        for reader in READERS:
            for method in POLICIES:
                selected=[r for r in public if r['uid']==sample['uid'] and r['engine']==reader and r['policy']==method]
                repeat_groups.append(dict(uid=sample['uid'],reader=reader,method=method,
                    predictions_match=len({r['prediction_sha256'] for r in selected})==1,
                    scores_match=len({hash_json(r['score']['fields']) for r in selected})==1,
                    wall_mean=float(np.mean([r['total_wall'] for r in selected])),wall_sd=float(np.std([r['total_wall'] for r in selected],ddof=1))))
    save(OUT/'repeat_audit.json',dict(groups=repeat_groups,prediction_mismatches=sum(not r['predictions_match'] for r in repeat_groups),
        score_mismatches=sum(not r['scores_match'] for r in repeat_groups),fresh_cases=48))
    save(OUT/'audit.json',dict(signature=signature,private_checkpoints=len(checkpoint_hashes),public_rows=len(public),
        rescored_native_rows=recomputed,score_mismatches=0,test_scoring_after_lock=True,selector_model_sha256=lock['model_sha256'],
        checkpoint_hashes=checkpoint_hashes,test_labels_used_for_training=False,latency_warning='Selector rows use reconstructed execution costs; online repeated traces measured separately'))
    journal('evaluation_complete',rows=len(public));print('RECOVERY_EVALUATED',len(public),'rows',flush=True)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=('infer','fit','evaluate'));args=parser.parse_args()
    CACHE.mkdir(exist_ok=True,parents=True);OUT.mkdir(exist_ok=True,parents=True)
    with process_lock(CACHE/'process.lock'):
        {'infer':inference,'fit':fit,'evaluate':evaluate}[args.phase]()


if __name__=='__main__':main()
