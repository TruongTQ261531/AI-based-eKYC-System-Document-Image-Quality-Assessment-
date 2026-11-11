"""Targeted unit/regression verification and byte preservation audit; no model calls."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

from .pilot import EC, ROOT, read, code_hashes
from ..runner import sha_file, write_once

OUT=EC/'execution/task5_pilot'


def tests(label):
    base=EC/'local'/('task5_'+label)
    log=OUT/(label+'.log');xml=OUT/(label+'.xml')
    if base.exists() or log.exists() or xml.exists():
        raise FileExistsError('Verification artifacts exist; do not overwrite')
    paths=list(EC.glob('*.py'))+list((EC/'tests').glob('*.py'))+list((EC/'task5').glob('*.py'))
    hashes={p.relative_to(ROOT).as_posix():sha_file(p) for p in paths}
    command=[sys.executable,'-B','-m','pytest','research/evidence_contract/tests','research/tests/test_v3_sources.py',
        'research/tests/test_hp_masks.py','research/tests/test_labels_schema.py','-q','-p','no:cacheprovider',
        '--basetemp='+str(base),'--junitxml='+str(xml)]
    stamp=datetime.now(timezone.utc).isoformat();start=time.perf_counter()
    with log.open('xb') as stream:
        process=subprocess.run(command,cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,check=False)
    after={p.relative_to(ROOT).as_posix():sha_file(p) for p in paths}
    suites=ET.parse(xml).getroot().findall('testsuite') if xml.exists() else []
    result=dict(command=command,started_utc=stamp,elapsed_seconds=time.perf_counter()-start,exit_code=process.returncode,
        code_sha256=hashes,code_unchanged_during_tests=hashes==after,stdout_sha256=sha_file(log),
        junit_sha256=sha_file(xml) if xml.exists() else None,
        junit_cases_including_subtests=sum(int(s.get('tests',0)) for s in suites),
        failures=sum(int(s.get('failures',0)) for s in suites),errors=sum(int(s.get('errors',0)) for s in suites),
        skipped=sum(int(s.get('skipped',0)) for s in suites),actual_model_invocations=0,
        control_output_injections=True,confirmatory_inputs=0)
    write_once(OUT/(label+'.execution.json'),result)
    print(json.dumps({k:result[k] for k in ('exit_code','junit_cases_including_subtests','failures','errors','skipped','code_unchanged_during_tests')}))
    if process.returncode or hashes!=after:raise SystemExit(1)


def audit(label):
    before=read(OUT/'preservation_before.json')
    changed=[]
    for row in before['files']:
        path=ROOT/row['path']
        if not path.is_file() or path.stat().st_size!=row['bytes'] or sha_file(path)!=row['sha256']:
            changed.append(row['path'])
    def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,text=True,encoding='utf-8').strip()
    result=dict(timestamp_utc=datetime.now(timezone.utc).isoformat(),head=git('rev-parse','HEAD'),branch=git('branch','--show-current'),
        refs=git('show-ref'),status=git('status','--porcelain=v1'),tracked_diff=git('diff','--stat'),staged_diff=git('diff','--cached','--stat'),
        checked_files=len(before['files']),checked_bytes=sum(r['bytes'] for r in before['files']),changed_preexisting_paths=changed,
        code_sha256=code_hashes(),scope=before['scope'])
    result['head_and_refs_unchanged']=result['head']==before['head'] and result['refs']==before['refs']
    write_once(OUT/(label+'.json'),result)
    print(json.dumps(dict(files=result['checked_files'],changed=len(changed),head_and_refs_unchanged=result['head_and_refs_unchanged'])))
    if changed or not result['head_and_refs_unchanged'] or result['tracked_diff'] or result['staged_diff']:raise SystemExit(1)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('tests','audit'))
    parser.add_argument('--label',required=True)
    args=parser.parse_args()
    if not args.label or not all(c.isalnum() or c in '_-' for c in args.label):raise ValueError('Expected a new label')
    tests(args.label) if args.action=='tests' else audit(args.label)


if __name__=='__main__':main()
