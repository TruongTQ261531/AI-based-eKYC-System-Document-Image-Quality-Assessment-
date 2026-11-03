"""Durable main-only experiment; checkpoints and every model call are on disk."""
import ctypes
import os
import subprocess
import sys
import time
import urllib.request
from research.hp_common import *


def state(stage,**items):
    value=dict(pid=os.getpid(),stage=stage,time_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),**items)
    save(CACHE/'workflow.json',value);print('HARD_PAIR_WORKFLOW',stage,flush=True)


def command(label,args,expected=None):
    if expected and expected.exists():return
    folder=CACHE/'logs';folder.mkdir(parents=True,exist_ok=True);path=folder/(label+'_'+str(time.time_ns())+'.log')
    env=os.environ.copy()
    env['PYTORCH_CUDA_ALLOC_CONF']='garbage_collection_threshold:0.6'
    with path.open('w',encoding='utf-8',newline='\n') as stream:
        p=subprocess.Popen([sys.executable,*args],cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,env=env)
        state(label,child_pid=p.pid,log=path.relative_to(ROOT).as_posix())
        code=p.wait()
    if code:raise RuntimeError(label+' exited '+str(code)+'; '+path.relative_to(ROOT).as_posix())


def restore_source_web():
    import socket
    with socket.socket() as probe:occupied=probe.connect_ex(('127.0.0.1',8003))==0
    if occupied:
        try:
            import json
            with urllib.request.urlopen('http://127.0.0.1:8003/api/health',timeout=4) as r:health=json.load(r)
            if health.get('app_id')=='source_visibility_v3':return
        except Exception:pass
        save(CACHE/'web_restore_issue.json',dict(reason='Port8003 occupied by another service; no process stopped'))
        return
    path=CACHE/'restored_source_web.log';path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('a',encoding='utf-8') as stream:
        proc=subprocess.Popen([sys.executable,'-m','research.vlm_setup','run','--','-m','uvicorn','research.v3_web:app',
            '--host','127.0.0.1','--port','8003','--no-access-log'],cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW)
    save(CACHE/'restored_source_web.json',dict(wrapper_pid=proc.pid,url='http://127.0.0.1:8003/',new_model_promoted=False))


def main():
    import msvcrt
    CACHE.mkdir(parents=True,exist_ok=True)
    with (CACHE/'workflow.lock').open('a+b') as lock:
        if lock.tell()==0:lock.write(b'0');lock.flush()
        lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000001)
        try:
            if read(OUT/'preflight.json')['signature']!=signature():raise ValueError('Prepared method changed')
            if read(OUT/'prepare_publication.json')['signature']!=signature():raise ValueError('Pretraining code was not published')
            runtime=read(OUT/'runtime_amendment.json');published=read(OUT/'runtime_publication.json')
            if runtime['signature']!=signature() or runtime['status']!='passed' or published['runtime_amendment_sha256']!=sha(OUT/'runtime_amendment.json'):
                raise ValueError('Runtime policy must be verified and published before continuing')
            gpu=['-m','research.vlm_setup','run','--','-m','research.hp_study']
            for seed in (42,31415):
                command('train_hard_'+str(seed),gpu+['train','--seed',str(seed)],OUT/f'train_hard_{seed}.json')
            for key in KEYS:
                command('development_'+key,gpu+['evaluate','--role','development','--model',key],OUT/f'development_{key}.json')
            analysis=read(OUT/'analysis_publication.json')
            if analysis['signature']!=signature() or analysis['analysis_plan_sha256']!=sha(OUT/'analysis_plan.json'):
                raise ValueError('Coverage sensitivity must be registered before test')
            command('test_seal',gpu+['seal'],OUT/'test_lock.json')
            command('publish_test_seal',['-m','research.hp_publish','seal'],OUT/'test_publication.json')
            for key in KEYS:
                command('test_'+key,gpu+['evaluate','--role','test','--model',key],OUT/f'test_{key}.json')
            command('fresh_repeats',gpu+['fresh'],OUT/'fresh_repeats.json')
            command('feature_replay',['-m','research.vlm_setup','run','--','-m','research.hp_audit','features'],OUT/'feature_audit.json')
            command('numeric_audit',['-m','research.vlm_setup','run','--','-m','research.hp_audit','audit'],OUT/'audit.json')
            command('report',['-m','research.hp_report'],ROOT/'research/HARD_PAIR_RESULTS_VI.md')
            command('publish_final',['-m','research.hp_publish','final'])
            state('complete',audit_passed=True,new_training_runs=2,physical_camera_validated=False)
        except Exception as exc:
            state('failed',error_type=type(exc).__name__,detail=str(exc));raise
        finally:
            ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)
            restore_source_web()


if __name__=='__main__':main()
