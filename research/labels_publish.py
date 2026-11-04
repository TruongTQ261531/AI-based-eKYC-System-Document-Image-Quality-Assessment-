"""Publish annotation evidence before new predictions, and audited outcomes afterwards."""
import argparse
import subprocess
from research.labels_common import *
from research.labels_audit import data_scope

def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,stderr=subprocess.STDOUT).decode('utf-8').strip()

def no_private_values(value):
    if isinstance(value,dict):
        forbidden={'reference_text','observed_transcript','source_refs','accepted_values','target','_private_text','_private_boxes','glyphs','mask_regions'}
        if set(value)&forbidden:raise ValueError('Private annotation/prediction in public evidence')
        if 'fields' in value and isinstance(value['fields'],(dict,list)):raise ValueError('Private field payload in public evidence')
        for child in value.values():no_private_values(child)
    elif isinstance(value,list):
        for child in value:no_private_values(child)

def publish(stage):
    freeze_previous()
    if git('branch','--show-current')!='main':raise ValueError('Use existing main')
    sig=signature()
    if stage=='prepare':
        if any((CACHE/'predictions').glob('*/*.json')):raise ValueError('Cannot register after new predictions')
        audit=read(OUT/'data_audit.json')
        if audit['status']!='passed' or audit['data_scope']!=data_scope():raise ValueError('Passed matching data audit required')
        if read(OUT/'preflight_software.json')['status']!='passed':raise ValueError('New contract tests required')
        save(OUT/'test_lock.json',dict(signature=sig,data_audit_sha256=sha(OUT/'data_audit.json'),
            models_sha256=sha(OUT/'models.json'),evaluation_sha256=sha(DATA/'evaluation.json'),
            scheduled_main_calls=912,scheduled_fresh_calls=24,training_runs=0,model_selection=False,
            source='Provider/renderer annotations; no OCR pseudo-labels or independent-human claim'))
    elif stage=='review_setup':
        if read(OUT/'prepare_publication.json')['signature']!=sig:raise ValueError('Main experiment changed during human supplement')
        if read(OUT/'single_review_verification.json')['status']!='passed':raise ValueError('Single-review contract checks required')
    else:
        for name in ('audit.json','software_verification.json'):
            if read(OUT/name)['status']!='passed' or read(OUT/name)['signature']!=sig:raise ValueError('Matching audited verification required')
        if read(OUT/'report_provenance.json')['report_sha256']!=sha(ROOT/'research/OCR_LABELS_RESULTS_VI.md'):raise ValueError('Report differs')
    paths=list((ROOT/'research').glob('labels_*.py'))+list((ROOT/'research').glob('OCR_LABELS*.md'))
    paths+=list((ROOT/'research/tests').glob('test_labels*.py'))+list((ROOT/'web').glob('labels_review.*'))
    paths+=[ROOT/'start-ocr-labels.ps1']+list(OUT.glob('*.json'))+list(OUT.glob('font_layout*.png'))+list(OUT.glob('font_layout*.svg'))
    for path in OUT.glob('*.json'):no_private_values(read(path))
    names=[p.relative_to(ROOT).as_posix() for p in paths if p.is_file()]
    git('add','--',*names)
    if set(git('diff','--cached','--name-only').splitlines())-set(names):raise ValueError('Unrelated staged files')
    code=subprocess.run(['git','diff','--cached','--quiet'],cwd=ROOT).returncode
    if code==1:git('commit','-m','OCR field annotation '+stage+' protocol and transparent evidence')
    elif code:raise ValueError('Git staged check failed')
    git('push','origin','main');tip=git('rev-parse','HEAD')
    if git('ls-remote','origin','refs/heads/main').split()[0]!=tip:raise ValueError('Remote main differs')
    if stage=='prepare':
        lock=subprocess.check_output(['git','show',tip+':research/results/ocr_labels_v1/test_lock.json'],cwd=ROOT)
        if hashlib.sha256(lock).hexdigest()!=sha(OUT/'test_lock.json'):raise ValueError('Published lock differs')
        save(OUT/'prepare_publication.json',dict(signature=sig,commit=tip,remote_commit=tip,
            lock_sha256=sha(OUT/'test_lock.json'),new_predictions_started=False))
    print('LABEL_PUBLISHED',stage,tip,flush=True)
    return tip

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['prepare','review_setup','final']);publish(p.parse_args().stage)
