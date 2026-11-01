"""Final file/provenance and privacy checks without rerunning frozen studies."""
import json
import re
import subprocess
import time
import xml.etree.ElementTree as ET
from research.vlm_setup import ROOT,OUT,CACHE,sha,save
from research.vlm_runtime import signature


def main():
    v4=ROOT/'research/results/recovery_v4'
    index=json.loads((v4/'artifact_index.json').read_text(encoding='utf-8'))
    for row in index['files']:
        if sha(ROOT/row['path'])!=row['sha256']:raise ValueError('Frozen V4 artifact changed: '+row['path'])
    manifest=json.loads((v4/'manifest.json').read_text(encoding='utf-8'))
    for group in ('code_sha256','shared_code_sha256'):
        for name,digest in manifest[group].items():
            if sha(ROOT/'research'/name)!=digest:raise ValueError('Frozen V4 source changed: '+name)
    changed=subprocess.check_output(['git','diff','4110f22b94699d30950cd1c0b23532ee9ccaaa59','--name-only','--',
        'ekyc','web','tests','start.ps1','open-ekyc.ps1'],cwd=ROOT,text=True).splitlines()
    if changed:raise ValueError('Mentor runtime changed')
    forbidden={'_private_text','_private_fields','target','targets','full_name','id_number','dob','address','fields','text'}
    hits=[]
    def scan(value,path):
        if isinstance(value,dict):
            for key,item in value.items():
                if key in forbidden or key.startswith('_private'):hits.append((path,key))
                scan(item,path)
        elif isinstance(value,list):
            for item in value:scan(item,path)
    json_paths=list(OUT.rglob('*.json'))
    for path in json_paths:scan(json.loads(path.read_text(encoding='utf-8')),path.relative_to(ROOT).as_posix())
    if hits:raise ValueError('Private fields in public results: '+repr(hits))
    xml=ET.parse(OUT/'final_python_tests.xml').getroot()
    suites=list(xml.iter('testsuite'))
    failures=sum(int(s.attrib.get('failures',0))+int(s.attrib.get('errors',0)) for s in suites)
    if failures:raise ValueError('Final Python tests failed')
    import torch
    if torch.__version__!='2.14.1+cpu':raise ValueError('Original OCR PyTorch environment changed')
    ignored=subprocess.run(['git','check-ignore',str(CACHE/'model/model.safetensors')],cwd=ROOT,stdout=subprocess.PIPE,text=True)
    if ignored.returncode:raise ValueError('Model cache must be ignored by Git')
    frontend=(OUT/'frontend_tests.txt').read_text(encoding='utf-8')
    frontend_count=int(re.search(r'\btests (\d+)',frontend)[1])
    if int(re.search(r'\bfail (\d+)',frontend)[1]):raise ValueError('Final frontend tests failed')
    evidence=dict(status='passed',signature=signature(),time_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
        frozen_v4_artifacts_verified=len(index['files']),frozen_v4_source_files_verified=sum(len(manifest[k]) for k in ('code_sha256','shared_code_sha256')),
        mentor_changed_paths=changed,public_json_files_scanned=len(json_paths),private_key_hits=0,
        python_tests=sum(int(s.attrib['tests']) for s in suites),python_failures=failures,
        frontend_tests=frontend_count,frontend_log_sha256=sha(OUT/'frontend_tests.txt'),
        original_torch=torch.__version__,original_cuda_available=torch.cuda.is_available(),new_venv=False,
        optional_runtime_isolated=True,model_cache_git_ignored=True,physical_camera_tested=False,
        actual_browser_validation_sha256=sha(OUT/'browser_validation.json'),
        retained_issue_stages=[e['stage'] for e in json.loads((OUT/'execution_notes.json').read_text(encoding='utf-8'))['events']],
        execution_notes_sha256=sha(OUT/'execution_notes.json'),
        all_browser_demo_documents_exact=json.loads((OUT/'browser_validation.json').read_text(encoding='utf-8'))['all_demo_documents_exact'],
        no_core_b_or_liveness_claim=True)
    save(OUT/'release_validation.json',evidence)
    paths=set(OUT.rglob('*'))
    for pattern in ('vlm*.py','VLM*.md','start-vlm*.ps1'):paths.update((ROOT/'research').glob(pattern))
    paths.update((ROOT/'research/vlm_web').rglob('*'))
    paths.update((ROOT/'research/tests').glob('*vlm*'))
    paths.add(ROOT/'.gitattributes')
    paths={p for p in paths if p.is_file() and p!=OUT/'artifact_index.json'}
    save(OUT/'artifact_index.json',dict(signature=signature(),files=[dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(paths)],
        excludes='private cache/data and this self-referential index',weights_committed=False))
    print('RELEASE_VALIDATED',len(paths),'files',evidence['python_tests'],'Python tests',flush=True)


if __name__=='__main__':main()
