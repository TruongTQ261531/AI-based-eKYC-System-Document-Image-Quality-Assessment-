"""Durable sequential GPU work, resumable checkpoints, and research-web restore."""
import ctypes
import os
import socket
import subprocess
import sys
import time
import urllib.request
from research.fc_common import *
from research.fc_io import save_retry as save


def state(stage,**extra):
    save(CACHE/'workflow.json',dict(pid=os.getpid(),stage=stage,time_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),**extra))
    print('FAIR_CONTROLS_WORKFLOW',stage,flush=True)


def command(stage,args,expected=None):
    if expected and expected.exists():return
    folder=CACHE/'logs';folder.mkdir(parents=True,exist_ok=True);path=folder/(stage+'_'+str(time.time_ns())+'.log')
    env=os.environ.copy();env['PYTORCH_CUDA_ALLOC_CONF']='garbage_collection_threshold:0.6'
    with path.open('w',encoding='utf-8',newline='\n') as stream:
        p=subprocess.Popen([sys.executable,*args],cwd=ROOT,env=env,stdout=stream,stderr=subprocess.STDOUT,
                           creationflags=subprocess.CREATE_NO_WINDOW)
        state(stage,child_pid=p.pid,log=path.relative_to(ROOT).as_posix());code=p.wait()
    if code:raise RuntimeError(stage+' exited '+str(code)+'; '+path.relative_to(ROOT).as_posix())


def port_used():
    with socket.socket() as s:return s.connect_ex(('127.0.0.1',8003))==0


def health():
    import json
    with urllib.request.build_opener(urllib.request.ProxyHandler({})).open('http://127.0.0.1:8003/api/health',timeout=5) as r:
        return json.load(r)


def pause_source_web():
    if not port_used():return
    try:
        import psutil
    except ModuleNotFoundError:
        from research.vlm_setup import CACHE as runtime_cache
        sys.path.insert(0,str(runtime_cache/'site'))
        try:import psutil
        finally:sys.path.pop(0)
    if health().get('app_id')!='source_visibility_v3':raise ValueError('Port8003 belongs to another service')
    owners={c.pid for c in psutil.net_connections(kind='tcp') if c.status=='LISTEN' and c.laddr.port==8003}
    if len(owners)!=1 or None in owners:raise ValueError('Cannot identify the research server owner')
    proc=psutil.Process(owners.pop());args=proc.cmdline()
    if 'uvicorn' not in args or 'research.v3_web:app' not in args or '8003' not in args:
        raise ValueError('Unexpected process; no process stopped')
    save(CACHE/f'service_pause_{time.time_ns()}.json',dict(pid=proc.pid,args=args,reason='Release only own SourceV3 research server'))
    proc.terminate();proc.wait(timeout=15)


def restore_source_web():
    if port_used():
        try:
            if health().get('app_id')=='source_visibility_v3':return
        except Exception:pass
        save(CACHE/'web_restore_issue.json',dict(reason='Port8003 occupied; no other process stopped'));return
    path=CACHE/'restored_source_web.log'
    with path.open('a',encoding='utf-8') as stream:
        p=subprocess.Popen([sys.executable,'-m','research.vlm_setup','run','--','-m','uvicorn','research.v3_web:app',
            '--host','127.0.0.1','--port','8003','--no-access-log'],cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW)
    save(CACHE/'restored_source_web.json',dict(wrapper_pid=p.pid,url='http://127.0.0.1:8003/',model='partial_42',new_model_promoted=False))


def main():
    import msvcrt
    CACHE.mkdir(parents=True,exist_ok=True)
    with (CACHE/'workflow.lock').open('a+b') as lock:
        if lock.tell()==0:lock.write(b'0');lock.flush()
        lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000001)
        try:
            if read(OUT/'preflight.json')['signature']!=signature():raise ValueError('Preflight contract changed')
            command('publish_prepare',['-m','research.fc_publish','prepare'],OUT/'prepare_publication.json')
            if read(OUT/'prepare_publication.json')['signature']!=signature():raise ValueError('Preparation not published')
            pause_source_web()
            gpu=['-m','research.vlm_setup','run','--','-m','research.fc_runner']
            for seed in SEEDS:
                for arm in NEW_ARMS:
                    command(f'train_{arm}_{seed}',gpu+['train','--arm',arm,'--seed',str(seed)],OUT/f'train_{arm}_{seed}.json')
            command('training_inventory',['-m','research.vlm_setup','run','--','-m','research.fc_audit','inventory'],OUT/'training_state_inventory.json')
            for key in KEYS:
                command('development_'+key,gpu+['evaluate','--role','development','--model',key],OUT/f'development_{key}.json')
            command('test_seal',gpu+['seal'],OUT/'test_lock.json')
            command('publish_test_seal',['-m','research.fc_publish','seal'],OUT/'test_publication.json')
            for key in KEYS:
                command('test_'+key,gpu+['evaluate','--role','test','--model',key],OUT/f'test_{key}.json')
            for key in KEYS:
                command('fresh_'+key,gpu+['fresh','--model',key],OUT/f'fresh_{key}.json')
            command('feature_audit',['-m','research.vlm_setup','run','--','-m','research.fc_audit','features'],OUT/'feature_audit.json')
            command('numeric_audit',['-m','research.vlm_setup','run','--','-m','research.fc_audit','audit'],OUT/'audit.json')
            restore_source_web()
            command('software_verification',['-m','research.fc_verify'],OUT/'software_verification.json')
            command('report',['-m','research.fc_report'],ROOT/'research/FAIR_CONTROLS_RESULTS_VI.md')
            command('publish_final',['-m','research.fc_publish','final'])
            state('complete',audit_passed=True,software_checks_passed=True,new_training_runs=4,reused_training_runs=4,model_promoted=False)
        except Exception as exc:
            state('failed',error_type=type(exc).__name__,detail=str(exc));raise
        finally:
            ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)
            restore_source_web()


if __name__=='__main__':main()
