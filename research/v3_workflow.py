"""Durable joint supervisor; never opens test until both prospective studies seal."""
import ctypes
import os
import subprocess
import sys
import time
from research.v3_common import *

def state(stage,**kw):
    save(CACHE/'workflow.json',dict(pid=os.getpid(),stage=stage,time_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),**kw))
    print('SOURCE_STUDY',stage,flush=True)

def command(label,args,expected=None):
    if expected and expected.exists():return
    path=CACHE/'logs'/(label+'_'+str(time.time_ns())+'.txt');path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',encoding='utf-8') as log:
        p=subprocess.Popen([sys.executable,*args],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
        state(label,child_pid=p.pid,log=path.relative_to(ROOT).as_posix());code=p.wait()
    if code:raise RuntimeError(label+' exited '+str(code)+'; '+str(path))

def main():
    import msvcrt
    CACHE.mkdir(parents=True,exist_ok=True)
    with (CACHE/'workflow.lock').open('a+b') as lock:
        if lock.tell()==0:lock.write(b'0');lock.flush()
        lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000001)
        state('waiting_for_r2_development_and_v3_implementation')
        try:
            while not ((R2OUT/'test_lock.json').exists() and (OUT/'implementation_ready.json').exists()):
                status=read(R2CACHE/'workflow.json')
                if status.get('stage')=='failed':raise ValueError('R2 preparation failed; preserve logs and investigate')
                time.sleep(10)
            time.sleep(3)
            ready=read(OUT/'implementation_ready.json')
            if ready['signature']!=signature():raise ValueError('Implementation differs from the published pretraining contract')
            gpu=['-m','research.vlm_setup','run','--','-m','research.v3_study']
            for seed0 in CONFIG['seeds']:
                command('source_train_'+str(seed0),gpu+['train','--seed',str(seed0)],OUT/f'train_source_{seed0}.json')
            for key in ('source_42','source_31415'):
                command('source_development_'+key,gpu+['evaluate','--role','development','--model',key],OUT/f'development_{key}.json')
            command('source_development_rescore',gpu+['rescore','--role','development'],OUT/'development_comparison.json')
            command('source_development_cpu',['-m','research.v3_cpu','development'],OUT/'development_cpu.json')
            command('hybrid_development',['-m','research.v3_fusion','development'],OUT/'development_fusion.json')
            command('source_seal',gpu+['seal'],OUT/'test_lock.json')
            command('hybrid_seal',['-m','research.v3_fusion','seal'],OUT/'fusion_lock.json')
            command('joint_lock_publication',['-m','research.v3_publish','lock'],OUT/'lock_publication.json')
            command('r2_registered_test',['-m','research.v2_workflow','test'])
            for key in ('source_42','source_31415'):
                command('source_test_'+key,gpu+['evaluate','--role','test','--model',key],OUT/f'test_{key}.json')
            command('source_test_rescore',gpu+['rescore','--role','test'],OUT/'test_comparison.json')
            command('source_test_cpu',['-m','research.v3_cpu','test'],OUT/'test_cpu.json')
            command('hybrid_test',['-m','research.v3_fusion','test'],OUT/'test_fusion.json')
            audit=['-m','research.vlm_setup','run','--','-m','research.v2_audit']
            command('r2_fresh',audit+['fresh'],R2OUT/'fresh_repeats.json')
            command('r2_audit',audit+['audit'],R2OUT/'audit.json')
            command('r2_report',['-m','research.v2_report'],ROOT/'research/V2_RESULTS_VI.md')
            command('source_fresh',gpu+['fresh'],OUT/'fresh_repeats.json')
            command('source_audit',['-m','research.vlm_setup','run','--','-m','research.v3_audit'],OUT/'audit.json')
            command('hybrid_fresh',['-m','research.vlm_setup','run','--','-m','research.v3_fusion','fresh'],OUT/'fusion_fresh.json')
            command('hybrid_audit',['-m','research.v3_fusion','audit'],OUT/'fusion_audit.json')
            command('source_report',['-m','research.v3_report'],ROOT/'research/V3_RESULTS_VI.md')
            command('joint_publication',['-m','research.v3_publish','final'])
            state('complete_browser_validation_pending')
        except Exception as exc:
            state('failed',error_type=type(exc).__name__,detail=str(exc));raise
        finally:ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)

if __name__=='__main__':main()
