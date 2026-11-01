"""Publish only V2 code and numeric evidence, with a remotely verified test seal."""
import argparse
import hashlib
import subprocess
from research.v2_common import *

BRANCH='research/vlm-v2-evidence'

def git(*args):
    r=subprocess.run(['git',*args],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    if r.returncode:raise RuntimeError(r.stderr.decode('utf-8',errors='replace'))
    return r.stdout

def publish(stage):
    preserve_v1()
    if git('branch','--show-current').decode().strip()!=BRANCH:raise ValueError('Refuse to publish a different branch')
    if stage=='lock':
        lock=read(OUT/'test_lock.json')
        if lock['signature']!=signature():raise ValueError('V2 source changed before publication')
        if any(OUT.glob('test_original.json')):raise ValueError('Test already scored before publication')
    paths=list((ROOT/'research').glob('v2_*.py'))+list((ROOT/'research').glob('V2*.md'))
    paths+=list((ROOT/'research/v2_web').glob('*'))+[ROOT/'research/v2_web/.gitattributes']
    paths+=list((ROOT/'research/tests').glob('test_v2*.py'))+list((ROOT/'research/tests').glob('v2*.cjs'))
    paths+=[ROOT/'start-vlm-v2.ps1']
    paths+=list(OUT.glob('*.json'))
    paths+=list((OUT/'figures').glob('*.png'))+list((OUT/'figures').glob('*.svg'))
    # This allowlist cannot reach research/data, cache, other branches or V1.
    for path in list(OUT.glob('*.json')):
        text=path.read_text(encoding='utf-8')
        if any('"'+bad+'"' in text for bad in ('_private_text','_private_fields','target','accepted_values')):
            raise ValueError('Private label/prediction text in public artifact: '+path.name)
    paths=[str(p.relative_to(ROOT)).replace('\\','/') for p in paths if p.is_file()]
    git('add','--',*paths)
    staged=git('diff','--cached','--name-only').decode().splitlines()
    if set(staged)-set(paths):raise ValueError('Non-V2 staged files detected; do not commit unrelated work')
    diff=subprocess.run(['git','diff','--cached','--quiet'],cwd=ROOT)
    if diff.returncode==1:git('commit','-m','V2 '+('seal models and source before unseen test' if stage=='lock' else 'publish complete repeated benchmark and audit'))
    elif diff.returncode:raise ValueError('Could not inspect staged changes')
    git('push','origin',BRANCH)
    commit=git('rev-parse','HEAD').decode().strip();remote=git('ls-remote','origin','refs/heads/'+BRANCH).decode().split()[0]
    if commit!=remote:raise ValueError('Remote tip differs from local commit')
    if stage=='lock':
        blob=git('show',commit+':'+(OUT/'test_lock.json').relative_to(ROOT).as_posix())
        if hashlib.sha256(blob).hexdigest()!=sha(OUT/'test_lock.json'):raise ValueError('Remote lock bytes differ')
        save(OUT/'lock_publication.json',dict(commit=commit,remote_commit=remote,lock_sha256=sha(OUT/'test_lock.json'),
            signature=signature(),test_scoring_started=False,source='git remote verified before any V2 test inference'))
    print('V2_PUBLISHED',stage,commit,flush=True)
    return commit

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['lock','final']);publish(p.parse_args().stage)
