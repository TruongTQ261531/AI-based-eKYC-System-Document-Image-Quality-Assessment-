"""Software regressions and real localhost reads, with exact working-tree hashes."""
import datetime
import re
import subprocess
import sys
import urllib.request
import xml.etree.ElementTree as ET
from research.labels_common import *

def sources():
    names=set(subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode('utf-8').split('\0'))
    names.update(p.relative_to(ROOT).as_posix() for p in (ROOT/'research').glob('labels_*.py'))
    names.update(p.relative_to(ROOT).as_posix() for p in (ROOT/'web').glob('labels_review.*'))
    suffixes={'.py','.js','.cjs','.mjs','.html','.css','.ps1','.bat','.toml','.ini'}
    return [dict(path=n,sha256=sha(ROOT/n)) for n in sorted(names) if n and (Path(n).suffix in suffixes or Path(n).name.startswith('requirements')) and (ROOT/n).is_file()]

def run(name,args,extra=None):
    env=os.environ.copy();env.update(PYTHONIOENCODING='utf-8');env.update(extra or {})
    path=CACHE/(name+'.log')
    if path.exists():path.rename(CACHE/(name+'.'+str(time.time_ns())+'.previous.log'))
    with path.open('w',encoding='utf-8') as stream:
        result=subprocess.run(args,cwd=ROOT,env=env,stdout=stream,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
    if result.returncode:raise RuntimeError('Software check failed; retained '+path.relative_to(ROOT).as_posix())
    return path.read_text(encoding='utf-8')

def xml_counts(path):
    node=ET.parse(path).getroot().find('testsuite');value={k:int(node.attrib[k]) for k in ('tests','errors','failures','skipped')}
    if value['errors'] or value['failures']:raise ValueError('JUnit failures')
    return value

def node_counts(text):
    value={k:int(re.search(r'\b'+k+r'\s+(\d+)',text)[1]) for k in ('tests','pass','fail','cancelled','skipped')}
    if value['tests']!=value['pass'] or value['fail'] or value['cancelled'] or value['skipped']:raise ValueError('Incomplete frontend checks')
    return value

def verify():
    freeze_previous();sig=signature()
    if read(OUT/'audit.json')['status']!='passed':raise ValueError('Scientific audit required')
    before=sources();py=[sys.executable,'-u','-X','utf8']
    main=run('software_main',py+['-m','pytest','tests','research/tests','-q','--junitxml='+str(CACHE/'software_main.xml')])
    optional=run('software_optional',py+['-m','research.vlm_setup','run','--','-m','pytest','research/tests/test_vlm_training_runtime.py','-q','--junitxml='+str(CACHE/'software_optional.xml')])
    node=run('frontend_main',['node','--test','tests/camera_frontend.test.cjs','research/tests/vlm_frontend.test.cjs',
        'research/tests/v3_review.test.cjs','research/tests/v2_frontend.test.cjs','research/tests/recovery_frontend.test.cjs'])
    variant=run('frontend_source',['node','--test','research/tests/v2_frontend.test.cjs'],dict(OCR_TEST_WEB='v3'))
    labels=run('labels_frontend',['node','--test','research/tests/labels_frontend.test.cjs'])
    run('labels_javascript_syntax',['node','--check','web/labels_review.js'])
    passed=int(re.search(r'(\d+) passed',main)[1]);skipped=int(re.search(r'(\d+) skipped',main)[1]);subtests=int(re.search(r'(\d+) subtests passed',main)[1])
    warning=re.search(r'(\d+) warnings?',main);warnings=int(warning[1]) if warning else 0
    a=xml_counts(CACHE/'software_main.xml');b=xml_counts(CACHE/'software_optional.xml')
    if a['tests']!=passed+skipped+subtests or b['tests']!=skipped or b['skipped']:raise ValueError('Skipped checks not covered by overlay')
    n=node_counts(node);v=node_counts(variant);l=node_counts(labels);opener=urllib.request.build_opener(urllib.request.ProxyHandler({}));services={}
    def get(url):
        with opener.open(url,timeout=10) as response:return json.load(response)
    for port in (8000,8003,8005):
        for attempt in range(60):
            try:services[port]=get(f'http://127.0.0.1:{port}/api/health');break
            except Exception:
                if attempt==59:raise
                time.sleep(1)
        save(CACHE/f'health_{port}.json',services[port])
    if services[8000].get('status')!='ready' or services[8000].get('api_version')!='3.2.0':raise ValueError('Mentor service not ready')
    if services[8003].get('app_id')!='source_visibility_v3' or not services[8003].get('ready') or services[8003].get('model')!='partial_42':raise ValueError('Research model not restored')
    if services[8005].get('app_id')!='ocr_labels_v1' or services[8005].get('corpus_images')!=21050 or services[8005].get('evaluation_images')!=304:raise ValueError('Annotation service data incomplete')
    ids=get('http://127.0.0.1:8005/api/blind/tasks')['ids']
    if len(ids)!=48 or len(set(ids))!=48:raise ValueError('Review panel incomplete')
    for key in ids:
        response=get('http://127.0.0.1:8005/api/blind/'+key)
        if response['answers_included'] or any(set(f)-{'field_id','raw_key','semantic_key','polygon'} for f in response['fields']):
            raise ValueError('Blinded route exposes answers or predictions')
    if sources()!=before:raise ValueError('Source changed during software checks')
    evidence=['software_main.log','software_main.xml','software_optional.log','software_optional.xml','frontend_main.log',
              'frontend_source.log','labels_frontend.log','labels_javascript_syntax.log','health_8000.json','health_8003.json','health_8005.json']
    save(OUT/'software_verification.json',dict(status='passed',signature=sig,verified_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        main_passed=passed,main_skipped_optional=skipped,optional_overlay_passed=b['tests'],
        unique_python_checks=passed+b['tests'],subtests_passed=subtests,frontend_checks=n['pass']+v['pass']+l['pass'],annotation_frontend_checks=l['pass'],warnings=warnings,
        annotation_javascript_syntax=True,real_blind_API_tasks_checked=48,human_review_state=services[8005]['review'],
        services_ready=[8000,8003,8005],research_model='partial_42',new_model_promoted=False,
        sources_unchanged_during_checks=True,tested_working_tree_sources=before,source_snapshot_sha256=digest(before),
        tested_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip(),
        evidence=[dict(path=(CACHE/p).relative_to(ROOT).as_posix(),sha256=sha(CACHE/p)) for p in evidence]))
    print('LABEL_SOFTWARE_VERIFIED',passed+b['tests'],subtests,n['pass']+v['pass']+l['pass'],flush=True)

if __name__=='__main__':verify()
