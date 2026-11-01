"""Continue after the preparation supervisor, without relying on chat availability."""
import os
import subprocess
import sys
import time
from research.v2_common import *

def state(stage,**kw):
    save(CACHE/'completion.json',dict(pid=os.getpid(),stage=stage,time_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),**kw))
    print('V2_COMPLETION',stage,flush=True)

def command(label,args):
    path=CACHE/'logs'/(label+'_'+str(time.time_ns())+'.txt');path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',encoding='utf-8') as log:
        proc=subprocess.Popen([sys.executable,*args],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
        state(label,child_pid=proc.pid,log=path.relative_to(ROOT).as_posix());code=proc.wait()
    if code:raise RuntimeError(label+' exited '+str(code)+'; '+str(path))

def main():
    if (OUT/'source_graph_hold.json').exists():
        raise ValueError('V3 source-aware study registered before test; use research.v3_workflow for the joint sealed comparison')
    import msvcrt,ctypes
    CACHE.mkdir(parents=True,exist_ok=True)
    with (CACHE/'completion.lock').open('a+b') as lock:
        if lock.tell()==0:lock.write(b'0');lock.flush()
        lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        # Temporary sleep prevention, automatically released on process exit.
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000001)
        state('waiting_for_pretest_seal')
        try:
            while not (OUT/'test_lock.json').exists():
                workflow=read(CACHE/'workflow.json') if (CACHE/'workflow.json').exists() else {}
                if workflow.get('stage')=='failed':raise ValueError('Preparation failed; retain logs and fix before continuing')
                time.sleep(10)
            time.sleep(3)
            if not (OUT/'lock_publication.json').exists():command('publish_pretest_lock',['-m','research.v2_publish','lock'])
            command('sealed_test',['-m','research.v2_workflow','test'])
            gpu=['-m','research.vlm_setup','run','--','-m','research.v2_audit']
            if not (OUT/'fresh_repeats.json').exists():command('fresh_repeats',gpu+['fresh'])
            command('numeric_audit',gpu+['audit'])
            command('measured_report',['-m','research.v2_report'])
            command('publish_final_results',['-m','research.v2_publish','final'])
            state('complete_browser_validation_pending',test_scored=True,audit_passed=True)
        except Exception as exc:
            state('failed',error_type=type(exc).__name__,detail=str(exc));raise
        finally:ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)

if __name__=='__main__':main()
