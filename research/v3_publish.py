"""Remote-verifiable joint seals and allowlisted, privacy-preserving artifacts."""
import argparse
import hashlib
import subprocess
from research.v3_common import *
from research.v2_publish import git,BRANCH,publish as publish_r2

def publish(stage):
    preserve_v1()
    if stage=='lock':
        if (R2OUT/'test_original.json').exists() or (OUT/'test_source_42.json').exists():raise ValueError('Test prediction exists before joint publication')
        if read(OUT/'test_lock.json')['signature']!=signature():raise ValueError('Source lock/code changed')
        publish_r2('lock')
    else:publish_r2('final')
    if git('branch','--show-current').decode().strip()!=BRANCH:raise ValueError('Wrong research branch')
    paths=list((ROOT/'research').glob('v3_*.py'))+list((ROOT/'research').glob('V3*.md'))+list((ROOT/'research/tests').glob('test_v3*.py'))
    paths+=list(OUT.glob('*.json'))+list((OUT/'figures').glob('*.png'))+list((OUT/'figures').glob('*.svg'))
    paths+=[R2OUT/'lock_publication.json',ROOT/'start-source-v3.ps1']
    if (ROOT/'research/v3_web').exists():paths+=list((ROOT/'research/v3_web').glob('*'))
    for path in OUT.glob('*.json'):
        value=path.read_text(encoding='utf-8')
        if any('"'+k+'"' in value for k in ('target','body_target','source_refs','accepted_values','_private_text','_private_fields')):
            raise ValueError('Private labels/text detected in public source artifact: '+path.name)
    names=[p.relative_to(ROOT).as_posix() for p in paths if p.is_file()]
    git('add','--',*names)
    if set(git('diff','--cached','--name-only').decode().splitlines())-set(names):raise ValueError('Unrelated staged files detected')
    diff=subprocess.run(['git','diff','--cached','--quiet'],cwd=ROOT)
    if diff.returncode==1:git('commit','-m','Source-aware '+('models and reference-policy lock before joint test' if stage=='lock' else 'complete matched-pixel study and transparent audit'))
    elif diff.returncode:raise ValueError('Staged diff check failed')
    git('push','origin',BRANCH);commit=git('rev-parse','HEAD').decode().strip()
    if git('ls-remote','origin','refs/heads/'+BRANCH).decode().split()[0]!=commit:raise ValueError('Remote tip mismatch')
    if stage=='lock':
        for folder in (OUT,R2OUT):
            blob=git('show',commit+':'+(folder/'test_lock.json').relative_to(ROOT).as_posix())
            if hashlib.sha256(blob).hexdigest()!=sha(folder/'test_lock.json'):raise ValueError('Remote seal bytes differ')
        save(OUT/'lock_publication.json',dict(commit=commit,remote_commit=commit,signature=signature(),
             lock_sha256=sha(OUT/'test_lock.json'),R2_lock_sha256=sha(R2OUT/'test_lock.json'),test_scoring_started=False,
             both_seals_verified_before_any_test_inference=True))
    print('JOINT_PUBLISHED',stage,commit,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['lock','final']);publish(p.parse_args().stage)
