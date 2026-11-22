"""Run the gate regressions and keep raw logs under the private run."""
import argparse
from pathlib import Path
import platform
import re
import subprocess
import sys
import time

from .prepare import private_run
from ..task55.data import ROOT, save_new, sha

TARGETS=('test_c2_human_gate','test_post_p6_qualification','test_reference_workflow','test_semantic_lineage_c2',
         'test_c2_evidence_audit','test_review_agreement','test_pixel_lineage_audit')


def run(dest):
    for suite,selected in [('targeted',TARGETS),('full',())]:
        base=Path('research/evidence_contract/tests')
        paths=[base/(p+'.py') for p in selected] or [base]
        cmd=[sys.executable,'-X','utf8','-B','-m','pytest','-q','-p','no:cacheprovider',
             *map(str,paths),'--basetemp',str(dest/(suite+'_tmp'))]
        start=time.monotonic()
        log=dest/(suite+'.log')
        with log.open('xb') as stream:
            result=subprocess.run(cmd,cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT)
        summary=next((s for s in reversed(log.read_text(encoding='utf8',errors='replace').splitlines())
                      if re.search(r'\d+ (passed|failed|error)',s)), '')
        save_new(dest/(suite+'_tests.json'),dict(suite=suite,exit_code=result.returncode,tests=list(selected) or ['all'],
            summary=summary.strip(),log_sha256=sha(log),python=platform.python_version(),
            seconds=round(time.monotonic()-start,2)))
        print(summary,flush=True)
        result.check_returncode()


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('run')
    run(private_run(p.parse_args().run))
