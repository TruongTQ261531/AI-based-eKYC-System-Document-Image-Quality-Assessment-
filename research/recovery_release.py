"""Capture actual final test logs and validate the frozen inference source."""
import hashlib
import json
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

from research.benchmark import save,digest
from research.recovery_study import OUT


def main():
    commands=[('python',[sys.executable,'-m','pytest','tests','research/tests','--ignore=tests/test_manifest.py','-q','--junitxml='+str(OUT/'tests.xml')]),
              ('frontend',['node','--test','tests/camera_frontend.test.cjs','research/tests/recovery_frontend.test.cjs'])]
    outcomes=[]
    for name,command in commands:
        started=time.perf_counter();result=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                    encoding='utf-8',errors='replace')
        path=OUT/(name+'_tests.txt');path.write_text(result.stdout,encoding='utf-8',newline='\n')
        outcomes.append(dict(name=name,command=command,return_code=result.returncode,elapsed_seconds=time.perf_counter()-started,log_sha256=digest(path)))
        print(name,'TEST_EXIT',result.returncode,flush=True)
        if result.returncode:raise RuntimeError('Test failed; inspect '+str(path))
        if name=='frontend':outcomes[-1]['tests']=int(re.search(r'\btests (\d+)',result.stdout)[1])
    xml=ET.parse(OUT/'tests.xml').getroot()
    n=sum(int(s.attrib['tests']) for s in xml.iter('testsuite'))
    failed=sum(int(s.attrib['failures'])+int(s.attrib['errors']) for s in xml.iter('testsuite'))
    if failed:raise ValueError('JUnit reported failures')
    manifest=json.loads((OUT/'manifest.json').read_text())
    from pathlib import Path
    for name,value in manifest['code_sha256'].items():
        if digest(Path('research')/name)!=value:raise ValueError('Frozen inference code changed')
    changed=subprocess.check_output(['git','diff','mentor/ekyc-v3.2.0','--name-only','--','ekyc','web','tests','start.ps1','open-ekyc.ps1'],text=True).splitlines()
    if changed:raise ValueError('Mentor runtime diff must remain empty')
    save(OUT/'validation.json',dict(code_sha256=digest(__file__),time_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
        python_tests=n,frontend_tests=outcomes[1]['tests'],failed=failed,commands=outcomes,mentor_changed_paths=changed,
        excluded_tests='tests/test_manifest.py requires original raw manifest; study inputs hash-audited separately',
        physical_camera_motion_tested=False,frontend_camera_tests='Mocked DOM/media plus actual browser specimen flow',
        core_source_hashes_match=True))
    print('RELEASE_VALIDATION_PASS',n,'Python',outcomes[1]['tests'],'frontend',flush=True)


if __name__=='__main__':main()
