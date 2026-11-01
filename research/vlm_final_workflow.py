"""Resumable post-publication tests; no training or test-based model selection."""
import json
import os
import subprocess
import sys
import time
from research.vlm_setup import ROOT,CACHE,OUT,save,sha


def main():
    import msvcrt
    with (CACHE/'final_workflow.lock').open('a+b') as mutex:
        if mutex.tell()==0:mutex.write(b'0');mutex.flush()
        mutex.seek(0);msvcrt.locking(mutex.fileno(),msvcrt.LK_NBLCK,1)
        publication=json.loads((OUT/'pretest_publication.json').read_text(encoding='utf-8'))
        for name,digest in publication['locks'].items():
            path=OUT/name
            if sha(path)!=digest:raise ValueError('Published test lock changed')
            original=subprocess.check_output(['git','show',publication['lock_commit']+':'+path.relative_to(ROOT).as_posix()],cwd=ROOT)
            if original!=path.read_bytes():raise ValueError('Test lock was not in declared publication commit')
        tasks=[]
        for model in ('original','seed_42','seed_31415'):
            for repeat in (1,2,3):
                tasks.append((f'test_{model}_{repeat}',True,['research.vlm_train','evaluate','--role','test','--model',model,'--repeat',str(repeat)],OUT/f'test_{model}_{repeat}.json'))
        for repeat in (1,2,3):
            tasks.append((f'test_control_{repeat}',True,['research.vlm_control','evaluate','--role','test','--repeat',str(repeat)],OUT/f'control/test_seed_42_{repeat}.json'))
        tasks.extend([
            ('test_cpu',False,['research.vlm_baseline','test'],OUT/'test_ocr.json'),
            ('fresh_online',True,['research.vlm_online'],OUT/'fresh_online.json'),
            ('secondary_format',False,['research.vlm_analysis'],None),
            ('audit',False,['research.vlm_final_report','audit'],None),
            ('report',False,['research.vlm_final_report','report'],None),
            ('adapter_export',False,['research.vlm_package'],None)])
        logdir=CACHE/'logs';logdir.mkdir(parents=True,exist_ok=True)
        for stage,overlay,args,result in tasks:
            if result and result.exists():
                print('ALREADY_COMPLETED',stage,flush=True);continue
            path=logdir/f'final_{stage}_{time.time_ns()}.txt'
            state=dict(stage=stage,pid=os.getpid(),time_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),log=path.relative_to(ROOT).as_posix())
            save(CACHE/'final_workflow.json',state)
            command=[sys.executable,'-m',*args]
            if overlay:command=[sys.executable,'-m','research.vlm_setup','run','--','-m',*args]
            with path.open('w',encoding='utf-8') as log:
                process=subprocess.Popen(command,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace')
                for line in process.stdout:log.write(line);log.flush();print(line.rstrip(),flush=True)
                status=process.wait()
                if status:
                    save(CACHE/'final_workflow.json',dict(**state,status='failed',exit_code=status))
                    raise SystemExit(status)
        save(CACHE/'final_workflow.json',dict(stage='completed',test_based_reselection=False,all_declared_stages_completed=True))
        print('ALL_FINETUNE_STAGES_COMPLETED',flush=True)


if __name__=='__main__':main()
