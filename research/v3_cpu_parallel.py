"""Overlap independent CPU baselines with GPU test, only after both seals publish."""
import os
import subprocess
import sys
import time
from research.v3_common import *

def state(stage,**kw):
    save(CACHE/'cpu_parallel_state.json',dict(stage=stage,pid=os.getpid(),time_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),**kw))
    print('CPU_PARALLEL',stage,flush=True)

def main():
    import msvcrt
    CACHE.mkdir(parents=True,exist_ok=True)
    with (CACHE/'cpu_parallel.lock').open('a+b') as lock:
        if lock.tell()==0:lock.write(b'0');lock.flush()
        lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        state('waiting_for_both_published_test_seals')
        try:
            while not (OUT/'lock_publication.json').exists():
                if read(CACHE/'workflow.json').get('stage')=='failed':raise ValueError('Main supervisor failed before joint publication')
                time.sleep(10)
            pub=read(OUT/'lock_publication.json')
            if pub['signature']!=signature() or pub['lock_sha256']!=sha(OUT/'test_lock.json') or pub['R2_lock_sha256']!=sha(R2OUT/'test_lock.json'):raise ValueError('Both published seals required')
            for module,folder in [('research.v2_cpu',R2OUT),('research.v3_cpu',OUT)]:
                if (folder/'test_cpu.json').exists():continue
                log=CACHE/'logs'/('parallel_'+module.rsplit('.',1)[1]+'_'+str(time.time_ns())+'.txt');log.parent.mkdir(parents=True,exist_ok=True)
                with log.open('w',encoding='utf-8') as stream:
                    p=subprocess.Popen([sys.executable,'-m',module,'test'],cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT)
                    state(module,child_pid=p.pid,log=log.relative_to(ROOT).as_posix());code=p.wait()
                if code:raise RuntimeError(module+' exited '+str(code))
            state('complete')
        except Exception as exc:state('failed',detail=str(exc));raise

if __name__=='__main__':main()
