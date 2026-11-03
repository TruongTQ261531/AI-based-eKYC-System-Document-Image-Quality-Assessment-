"""Allowlisted main publication; test is blocked until the remote seal is verified."""
import argparse
import subprocess
from research.hp_common import *


def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,stderr=subprocess.STDOUT).decode().strip()


def publish(stage):
    preserve();sig=signature()
    if git('branch','--show-current')!='main':raise ValueError('Publication requires main')
    if stage=='prepare':
        if any((CACHE/'training').glob('hard_*/step_*/complete.json')):raise ValueError('Pretraining publication must precede training')
        if read(OUT/'preflight.json')['status']!='passed' or read(OUT/'preflight.json')['signature']!=sig:raise ValueError('Matching preflight required')
    if stage=='seal':
        if any((CACHE/'predictions').glob('test_*/*.json')):raise ValueError('Cannot register test after inference')
        if read(OUT/'test_lock.json')['signature']!=sig:raise ValueError('Test contract differs')
    paths=list((ROOT/'research').glob('hp_*.py'))+list((ROOT/'research').glob('HARD_PAIR*.md'))
    paths+=list((ROOT/'research/tests').glob('test_hp*.py'))+list(OUT.glob('*.json'))
    names=[p.relative_to(ROOT).as_posix() for p in paths if p.is_file()]
    for path in OUT.glob('*.json'):
        value=path.read_text(encoding='utf-8')
        if any('"'+k+'"' in value for k in ('target','source_refs','body_target','accepted_values','_private_text','fields','mask_regions')):
            raise ValueError('Private OCR labels in public artifact '+path.name)
    git('add','--',*names)
    staged=set(git('diff','--cached','--name-only').splitlines())
    if staged-set(names):raise ValueError('Unrelated staged files detected')
    result=subprocess.run(['git','diff','--cached','--quiet'],cwd=ROOT)
    if result.returncode==1:git('commit','-m','Paired-mask '+stage+' evidence and controlled experiment')
    elif result.returncode:raise ValueError('Staged diff check failed')
    git('push','origin','main');tip=git('rev-parse','HEAD')
    if git('ls-remote','origin','refs/heads/main').split()[0]!=tip:raise ValueError('Remote tip mismatch')
    if stage=='prepare':
        blob=subprocess.check_output(['git','show',tip+':research/HARD_PAIR_PROTOCOL.md'],cwd=ROOT)
        if __import__('hashlib').sha256(blob).hexdigest()!=sha(ROOT/'research/HARD_PAIR_PROTOCOL.md'):raise ValueError('Remote protocol bytes differ')
        save(OUT/'prepare_publication.json',dict(signature=sig,commit=tip,remote_commit=tip,training_started=False,
            protocol_sha256=sha(ROOT/'research/HARD_PAIR_PROTOCOL.md'),samples_sha256=sha(DATA/'samples.json')))
    if stage=='seal':
        rel=(OUT/'test_lock.json').relative_to(ROOT).as_posix()
        blob=subprocess.check_output(['git','show',tip+':'+rel],cwd=ROOT)
        if __import__('hashlib').sha256(blob).hexdigest()!=sha(OUT/'test_lock.json'):raise ValueError('Remote test seal bytes differ')
        save(OUT/'test_publication.json',dict(signature=sig,commit=tip,remote_commit=tip,lock_sha256=sha(OUT/'test_lock.json'),
            test_inference_started=False))
    print('HP_PUBLISHED',stage,tip,flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['prepare','seal','final']);publish(p.parse_args().stage)
