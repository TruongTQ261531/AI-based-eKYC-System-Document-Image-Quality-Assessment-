"""Store the test logs privately and emit aggregate receipts for this run."""
import argparse
import hashlib
import re
import subprocess
import sys
import time
from pathlib import Path

from research.evidence_contract.task55.data import EC, ROOT, save_new

TARGETED = ['test_c2_evidence_audit.py', 'test_semantic_lineage_c2.py', 'test_pixel_lineage_audit.py',
            'test_reference_policy.py', 'test_reference_workflow.py', 'test_review_agreement.py',
            'test_post_p6_qualification.py']


def main():
    p = argparse.ArgumentParser()
    p.add_argument('run')
    name = p.parse_args().run
    if Path(name).name!=name or name in ('.','..'):
        raise ValueError('Expected private run name')
    dest = EC/'local/post_p6'/name
    for suite,files in [('targeted',TARGETED),('full',[])]:
        tests = Path('research/evidence_contract/tests')
        paths = [str(tests/f) for f in files] or [str(tests)]
        command = [sys.executable,'-X','utf8','-B','-m','pytest','-q','-p','no:cacheprovider',
                   *paths,'--basetemp',str(dest/(suite+'_tmp'))]
        begin = time.monotonic()
        log = dest/(suite+'.log')
        with log.open('xb') as out:
            result = subprocess.run(command,cwd=ROOT,stdout=out,stderr=subprocess.STDOUT)
        raw = log.read_bytes()
        line = next((s for s in reversed(raw.decode('utf8','replace').splitlines())
                     if re.search(r'\d+ (?:passed|failed|skipped|error)',s)), '')
        receipt = dict(suite=suite,tests=files or ['all Evidence Contract tests'],exit_code=result.returncode,
                       summary=line.strip(),seconds=round(time.monotonic()-begin,2),
                       log_sha256=hashlib.sha256(raw).hexdigest())
        save_new(dest/(suite+'.json'),receipt)
        print(receipt['summary'],flush=True)
        result.check_returncode()


if __name__ == '__main__':
    main()
