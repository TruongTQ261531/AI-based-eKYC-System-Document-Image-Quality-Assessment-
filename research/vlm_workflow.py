"""Supervise preparation -> GPU smoke -> two seeds -> development -> test seal.

Runs independently of chat output, records every subprocess exit and stops
before test scoring so the pre-test choice can be committed/pushed first.
"""
import json
import os
import subprocess
import sys
import time

from research.vlm_setup import ROOT,CACHE,OUT,save,PACKAGES


def readiness():
    manifest=json.loads((OUT/'assets.json').read_text(encoding='utf-8'))
    expected={r['package']:r for r in manifest['packages']}
    ready=[]
    for name in PACKAGES:
        marker=CACHE/'site'/(name.replace('-','_')+'.extracted.json')
        if marker.exists() and json.loads(marker.read_text())['sha256']==expected[name]['sha256']: ready.append(name)
    return (CACHE/'model/model.safetensors').exists(),ready


def state(stage,**items):
    value=dict(pid=os.getpid(),stage=stage,time_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),**items)
    save(CACHE/'workflow.json',value)
    print(json.dumps(value),flush=True)


def command(label,args):
    logs=CACHE/'logs';logs.mkdir(parents=True,exist_ok=True)
    path=logs/(label+'_'+str(time.time_ns())+'.txt')
    state(label,log=path.relative_to(ROOT).as_posix())
    start=time.perf_counter()
    with path.open('w',encoding='utf-8',newline='\n') as log:
        process=subprocess.Popen([sys.executable,*args],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                                 text=True,encoding='utf-8',errors='replace')
        for line in process.stdout:
            log.write(line);log.flush();print(line.rstrip(),flush=True)
        code=process.wait()
    result=dict(stage=label,exit_code=code,wall_seconds=time.perf_counter()-start,log=path.relative_to(ROOT).as_posix())
    with (CACHE/'workflow_events.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(result)+'\n')
    if code: state('failed',failure=result);raise SystemExit(code)


def main():
    import msvcrt
    CACHE.mkdir(parents=True,exist_ok=True)
    with (CACHE/'workflow.lock').open('a+b') as owner:
        if owner.tell()==0:owner.write(b'0');owner.flush()
        owner.seek(0);msvcrt.locking(owner.fileno(),msvcrt.LK_NBLCK,1)
        while True:
            model,packages=readiness()
            if model and len(packages)==len(PACKAGES):break
            state('waiting_preparation',model_ready=model,packages_ready=len(packages),packages_total=len(PACKAGES))
            time.sleep(30)
        prefix=['-m','research.vlm_setup','run','--','-m','research.vlm_train']
        command('gpu_smoke',prefix+['smoke'])
        for seed in [42,31415]:command(f'train_seed_{seed}',prefix+['train','--seed',str(seed)])
        for model in ['original','seed_42','seed_31415']:
            command('development_'+model,prefix+['evaluate','--role','development','--model',model])
        command('development_cpu_baseline',['-m','research.vlm_baseline','development'])
        command('create_test_lock',prefix+['seal'])
        state('ready_for_test_lock_publication',test_scoring_started=False,
              instruction='Commit/push test_lock.json with final source/config BEFORE evaluating test.')


if __name__=='__main__':main()
