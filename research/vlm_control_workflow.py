"""Queue the declared control after primary dev, stop before any test scoring."""
import json
import os
import subprocess
import sys
import time

from research.vlm_setup import ROOT,CACHE,save


def main():
    import msvcrt
    with (CACHE/'control_workflow.lock').open('a+b') as mutex:
        if mutex.tell()==0:mutex.write(b'0');mutex.flush()
        mutex.seek(0);msvcrt.locking(mutex.fileno(),msvcrt.LK_NBLCK,1)
        while True:
            state=json.loads((CACHE/'workflow.json').read_text(encoding='utf-8'))
            if state['stage']=='ready_for_test_lock_publication':break
            if state['stage']=='failed':raise RuntimeError('Primary workflow failed; control not started')
            save(CACHE/'control_workflow.json',dict(stage='waiting_primary_development',pid=os.getpid()))
            time.sleep(30)
        logdir=CACHE/'logs';logdir.mkdir(parents=True,exist_ok=True)
        for stage,args in [('train',['train']),('development',['evaluate','--role','development']),('seal',['seal'])]:
            path=logdir/f'control_{stage}_{time.time_ns()}.txt'
            save(CACHE/'control_workflow.json',dict(stage=stage,pid=os.getpid(),log=path.relative_to(ROOT).as_posix()))
            with path.open('w',encoding='utf-8') as log:
                process=subprocess.Popen([sys.executable,'-m','research.vlm_setup','run','--','-m','research.vlm_control',*args],
                    cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace')
                for line in process.stdout:log.write(line);log.flush();print(line.rstrip(),flush=True)
                if process.wait():
                    save(CACHE/'control_workflow.json',dict(stage='failed',failed_stage=stage,log=path.relative_to(ROOT).as_posix()))
                    raise SystemExit(1)
        save(CACHE/'control_workflow.json',dict(stage='ready_for_test_lock_publication',test_scoring_started=False))
        print('CONTROL_READY_FOR_PRETEST_PUBLICATION',flush=True)


if __name__=='__main__':main()
