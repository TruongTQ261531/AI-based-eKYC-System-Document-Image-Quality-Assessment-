"""Main-only publication with a remote-verified lock before training or test."""
import argparse
import hashlib
import subprocess
from research.fc_common import *
from research.fc_io import save_retry as save


def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,stderr=subprocess.STDOUT).decode().strip()


def publish(stage):
    preserve();sig=signature()
    if git('branch','--show-current')!='main':raise ValueError('Publish on main only')
    if stage=='prepare':
        if any((CACHE/'training').glob('*/step_*/complete.json')):raise ValueError('Pretraining publication is too late')
        if read(OUT/'preflight.json')['status']!='passed' or read(OUT/'preflight.json')['signature']!=sig:
            raise ValueError('Matching preflight required')
    elif stage=='seal':
        if any((CACHE/'predictions').glob('test_*/*.json')):raise ValueError('Cannot seal after test generation')
        if read(OUT/'test_lock.json')['signature']!=sig:raise ValueError('Test contract differs')
    elif stage=='recovery':
        if read(OUT/'io_recovery.json')['signature']!=sig:raise ValueError('Recovery contract differs')
        if any((CACHE/'predictions').glob('test_*/*.json')):raise ValueError('This recovery record must precede new test generation')
    else:
        if read(OUT/'audit.json')['status']!='passed':raise ValueError('Passed audit required')
        if read(OUT/'report_provenance.json')['report_sha256']!=sha(ROOT/'research/FAIR_CONTROLS_RESULTS_VI.md'):
            raise ValueError('Report provenance differs')
    paths=list((ROOT/'research').glob('fc_*.py'))+list((ROOT/'research').glob('FAIR_CONTROLS*.md'))
    paths+=list((ROOT/'research/tests').glob('test_fc*.py'))+list(OUT.glob('*.json'))
    for path in OUT.glob('*.json'):
        value=path.read_text(encoding='utf-8')
        if any('"'+k+'"' in value for k in ('target','source_refs','body_target','accepted_values','_private_text','fields','mask_regions')):
            raise ValueError('Private labels or OCR text in public file '+path.name)
    names=[p.relative_to(ROOT).as_posix() for p in paths if p.is_file()]
    git('add','--',*names)
    if set(git('diff','--cached','--name-only').splitlines())-set(names):raise ValueError('Unrelated staged files')
    code=subprocess.run(['git','diff','--cached','--quiet'],cwd=ROOT).returncode
    if code==1:git('commit','-m','Matched-control '+stage+' protocol and auditable evidence')
    elif code:raise ValueError('Staged check failed')
    git('push','origin','main');tip=git('rev-parse','HEAD')
    if git('ls-remote','origin','refs/heads/main').split()[0]!=tip:raise ValueError('Remote main differs')
    if stage in ('prepare','seal'):
        file=ROOT/'research/FAIR_CONTROLS_PROTOCOL.md' if stage=='prepare' else OUT/'test_lock.json'
        blob=subprocess.check_output(['git','show',tip+':'+file.relative_to(ROOT).as_posix()],cwd=ROOT)
        if hashlib.sha256(blob).hexdigest()!=sha(file):raise ValueError('Remote protocol/lock bytes differ')
        record=dict(signature=sig,commit=tip,remote_commit=tip,
                    protocol_sha256=sha(ROOT/'research/FAIR_CONTROLS_PROTOCOL.md'))
        if stage=='prepare':record.update(training_started=False,train_sha256=sha(DATA/'train.json'))
        else:record.update(test_generation_started=False,lock_sha256=sha(OUT/'test_lock.json'))
        save(OUT/('prepare_publication.json' if stage=='prepare' else 'test_publication.json'),record)
    if stage=='recovery':save(OUT/'io_publication.json',dict(signature=sig,commit=tip,remote_commit=tip,
        recovery_sha256=sha(OUT/'io_recovery.json'),before_new_test_generation=True))
    print('FC_PUBLISHED',stage,tip,flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['prepare','seal','recovery','final']);publish(p.parse_args().stage)
