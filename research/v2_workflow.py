"""Durable supervisor: preparation stops at a publishable seal; test is separate."""
import argparse
import os
import subprocess
import sys
import time
from research.v2_common import *

def state(stage,**kw):
    value=dict(pid=os.getpid(),stage=stage,time_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),**kw)
    save(CACHE/'workflow.json',value);print(value,flush=True)

def command(label,args,expected=None):
    if expected and expected.exists():
        state('already_complete',item=label);return
    path=CACHE/'logs'/(label+'_'+str(time.time_ns())+'.txt');path.parent.mkdir(parents=True,exist_ok=True)
    state(label,log=path.relative_to(ROOT).as_posix());start=time.perf_counter()
    with path.open('w',encoding='utf-8',newline='\n') as log:
        proc=subprocess.Popen([sys.executable,*args],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
        state(label,child_pid=proc.pid,log=path.relative_to(ROOT).as_posix())
        code=proc.wait()
    record=dict(stage=label,exit_code=code,wall_seconds=time.perf_counter()-start,log=path.relative_to(ROOT).as_posix())
    with (CACHE/'workflow_events.jsonl').open('a',encoding='utf-8') as f:f.write(__import__('json').dumps(record)+'\n')
    if code:state('failed',failure=record);raise SystemExit(code)

def main():
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['prepare','test']);a=p.parse_args()
    import msvcrt
    CACHE.mkdir(parents=True,exist_ok=True)
    with (CACHE/'workflow.lock').open('a+b') as lock:
        if lock.tell()==0:lock.write(b'0');lock.flush()
        lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        prefix=['-m','research.vlm_setup','run','--','-m','research.v2_study']
        if a.stage=='prepare':
            for profile in ('raw2','raw4'):
                command('probe_'+profile,prefix+['probe','--profile',profile],OUT/f'probe_{profile}.json')
            for profile in ('raw2','raw4','rect2','rect4'):
                command('inputs_'+profile,prefix+['inputs','--profile',profile],OUT/f'input_panel_{profile}.json')
            command('choose_inputs',prefix+['choose'],OUT/'input_choice.json')
            for seed0 in CONFIG['seeds']:
                for variant in ('control','partial'):
                    command(f'train_{variant}_{seed0}',prefix+['train','--variant',variant,'--seed',str(seed0)],OUT/f'train_{variant}_{seed0}.json')
            for key in ('original','v1','control_42','partial_42','control_31415','partial_31415'):
                command('development_'+key,prefix+['evaluate','--role','development','--model',key],OUT/f'development_{key}.json')
            command('development_cpu',['-m','research.v2_cpu','development'],OUT/'development_cpu.json')
            command('seal',prefix+['seal'],OUT/'test_lock.json')
            state('ready_to_publish_test_lock',test_scoring_started=False)
        else:
            if not (OUT/'lock_publication.json').exists():raise ValueError('Publish and verify the pre-test seal first')
            for key in ('original','v1','control_42','partial_42','control_31415','partial_31415'):
                command('test_'+key,prefix+['evaluate','--role','test','--model',key],OUT/f'test_{key}.json')
            command('test_cpu',['-m','research.v2_cpu','test'],OUT/'test_cpu.json')
            state('test_complete_audit_pending')

if __name__=='__main__':main()
