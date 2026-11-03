"""Run software regressions, preserve logs, and confirm restored local services."""
import datetime
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from research.fc_common import *
from research.fc_io import save_retry as save


def run(name,args,extra_env=None):
    env=os.environ.copy();env.update(PYTHONIOENCODING='utf-8')
    if extra_env:env.update(extra_env)
    save(CACHE/'verification_progress.json',dict(stage=name,time_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
    path=CACHE/(name+'.log')
    if path.exists():path.rename(CACHE/(name+'_'+str(time.time_ns())+'.previous.log'))
    with path.open('w',encoding='utf-8',newline='\n') as stream:
        result=subprocess.run(args,cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,env=env,
                              creationflags=subprocess.CREATE_NO_WINDOW)
    if result.returncode:raise RuntimeError(name+' failed; retained '+path.relative_to(ROOT).as_posix())
    return path.read_text(encoding='utf-8')


def junit(name):
    value=ET.parse(CACHE/name).getroot().find('testsuite')
    result={k:int(value.attrib[k]) for k in ('tests','errors','failures','skipped')}
    if result['failures'] or result['errors']:raise ValueError('JUnit failure: '+name)
    return result


def node_counts(text):
    value={k:int(re.search(r'\b'+k+r'\s+(\d+)',text)[1]) for k in ('tests','pass','fail','cancelled','skipped')}
    if value['fail'] or value['cancelled'] or value['skipped'] or value['tests']!=value['pass']:
        raise ValueError('Incomplete frontend regression')
    return value


def source_snapshot():
    names=set(subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode('utf-8').split('\0'))
    names.update(p.relative_to(ROOT).as_posix() for p in (ROOT/'research').glob('fc_*.py'))
    suffixes={'.py','.js','.cjs','.mjs','.html','.css','.ps1','.bat','.toml','.ini'}
    paths=[ROOT/n for n in sorted(names) if n and
           (Path(n).suffix in suffixes or Path(n).name.startswith('requirements'))]
    return [dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p)) for p in paths if p.is_file()]


def verify():
    preserve();audit=read(OUT/'audit.json')
    if audit['status']!='passed' or audit['signature']!=signature():raise ValueError('Study audit required')
    tested_sources=source_snapshot()
    py=[sys.executable,'-u','-X','utf8']
    main=run('software_main',py+['-m','pytest','tests','research/tests','-q',
        '--junitxml='+str(CACHE/'software_main.xml')])
    optional=run('software_optional',py+['-m','research.vlm_setup','run','--','-m','pytest',
        'research/tests/test_vlm_training_runtime.py','-q','--junitxml='+str(CACHE/'software_optional.xml')])
    node=run('frontend_primary',['node','--test','tests/camera_frontend.test.cjs',
        'research/tests/vlm_frontend.test.cjs','research/tests/v3_review.test.cjs',
        'research/tests/v2_frontend.test.cjs','research/tests/recovery_frontend.test.cjs'])
    variant=run('frontend_source',['node','--test','research/tests/v2_frontend.test.cjs'],dict(OCR_TEST_WEB='v3'))
    match=re.search(r'(\d+) passed, (\d+) skipped, (\d+) warnings?, (\d+) subtests passed',main)
    if not match:raise ValueError('Main pytest summary not recognized')
    passed,skipped,warnings,subtests=map(int,match.groups());jmain=junit('software_main.xml');joptional=junit('software_optional.xml')
    if jmain['tests']!=passed+skipped+subtests or jmain['skipped']!=skipped:
        raise ValueError('Main summary/JUnit mismatch')
    if joptional['tests']!=skipped or joptional['skipped'] or not re.search(r'\b'+str(skipped)+r' passed\b',optional):
        raise ValueError('Optional overlay did not exercise all skipped tests')
    n,v=node_counts(node),node_counts(variant)
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}));services={}
    for port in (8000,8003):
        error=None
        for _ in range(6):
            try:
                with opener.open(f'http://127.0.0.1:{port}/api/health',timeout=5) as response:
                    if response.status!=200:raise ValueError('Non200 health')
                    raw=response.read()
                services[port]=json.loads(raw);(CACHE/f'health_{port}.json').write_bytes(raw);break
            except Exception as exc:error=exc;time.sleep(1)
        if port not in services:raise RuntimeError('Local service not ready '+str(port)) from error
    if services[8000].get('status')!='ready' or services[8000].get('api_version')!='3.2.0':
        raise ValueError('Mentor service differs')
    if services[8003].get('app_id')!='source_visibility_v3' or not services[8003].get('ready') or services[8003].get('model')!='partial_42':
        raise ValueError('Research service was not restored to the old model')
    files=['software_main.log','software_main.xml','software_optional.log','software_optional.xml',
           'frontend_primary.log','frontend_source.log','health_8000.json','health_8003.json']
    if source_snapshot()!=tested_sources:raise ValueError('Source changed during software verification')
    save(OUT/'software_verification.json',dict(status='passed',signature=signature(),
        verified_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        main_passed=passed,main_skipped_optional=skipped,optional_overlay_passed=joptional['tests'],
        combined_unique_python_checks=passed+joptional['tests'],subtests_passed=subtests,
        warning_count=warnings,frontend_primary=n,frontend_source=v,frontend_total=n['pass']+v['pass'],
        mentor_ready=True,mentor_version=services[8000]['api_version'],research_ready=True,research_model=services[8003]['model'],
        research_health_progress_scope='Existing V3, not FC experiment',new_model_promoted=False,
        independent_camera_validation=False,new_dependencies_installed=False,
        tested_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip(),
        tested_working_tree_sources=tested_sources,sources_unchanged_during_checks=True,
        tested_source_snapshot_sha256=hashlib.sha256(json.dumps(tested_sources,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
        verifier_sha256=sha(ROOT/'research/fc_verify.py'),study_audit_sha256=sha(OUT/'audit.json'),
        evidence=[dict(path=(CACHE/name).relative_to(ROOT).as_posix(),sha256=sha(CACHE/name)) for name in files]))
    print('FC_SOFTWARE_VERIFIED',passed+joptional['tests'],subtests,n['pass']+v['pass'],flush=True)


if __name__=='__main__':verify()
