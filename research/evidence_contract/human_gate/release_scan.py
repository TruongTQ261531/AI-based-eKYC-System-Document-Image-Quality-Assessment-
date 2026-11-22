"""Inspect the actual Git diff against the handoff baseline before release."""
import argparse
from pathlib import Path
import subprocess

from .closure import BASE, SOURCE
from .prepare import private_run
from ..reviewer_tools.strict import digest, need
from ..task55.data import EC, ROOT, read, save_new


def git(*args):
    return subprocess.check_output(['git',*args],cwd=ROOT).decode('utf8')


def scan(dest):
    files=git('diff','--name-only',BASE).splitlines()
    need(files and not git('ls-files','--others','--exclude-standard').strip(),'Review all new files before scanning')
    baseline=read(SOURCE/'qualification/evidence.json')
    forbidden=set(baseline['images'])|{r['candidate_id'] for r in baseline['candidates']}|set(baseline['physical_instances'])
    forbidden.update(i['crop'] for r in baseline['candidates'] for i in r['inspection'] if 'crop' in i)
    allowed_existing={'PROJECT_HANDOFF_20261120_VI.md'}|{'research/evidence_contract/'+name for name in
        ('NEXT_ACTIONS.md','MASTER_EXECUTION_STATUS.md','B_OWNER_DECISIONS_20261117.md')}
    public_gate='research/evidence_contract/human_gate/'
    allowed_new={'research/evidence_contract/'+s for s in ('C2_45_HUMAN_EVIDENCE_GATE_VI.md','C2_45_D10_RIGHTS_VI.md',
                 'C2_45_ADJUDICATION_READINESS_VI.md','tests/test_c2_human_gate.py')}
    manifest={}
    for rel in files:
        path=Path(rel)
        need((rel in allowed_existing or rel in allowed_new or rel.startswith(public_gate)) and
             path.suffix in {'.md','.py','.json'} and 'local' not in path.parts,'Unexpected public path')
        if rel==public_gate+'receipts/'+dest.name+'/release_scan.json':
            continue
        diff=git('diff','--no-color','--no-ext-diff','--unified=0',BASE,'--',rel)
        added='\n'.join(s[1:] for s in diff.splitlines() if s.startswith('+') and not s.startswith('+++'))
        need(not any(s in added for s in forbidden),'Private image or candidate binding in public diff')
        need(('BEGIN '+'PRIVATE KEY') not in added and ('data:image/'+'png;base64,') not in added,'Raw content in release')
        manifest[rel]=digest(added)
    need(subprocess.run(['git','check-ignore','-q',str(dest.relative_to(ROOT))],cwd=ROOT).returncode==0,'Private directory not ignored')
    return dict(status='RELEASE_SCAN_VERIFIED',baseline=BASE,diff_paths_excluding_own_receipt=len(manifest),
                added_text_manifest_sha256=digest(manifest),private_identifier_or_image_path_matches=0,
                private_files_staged=0)


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('run')
    dest=private_run(p.parse_args().run)
    result=scan(dest)
    path=dest/'release_scan.json'
    if path.exists():
        need(result==read(path),'Release diff changed')
    else:
        save_new(path,result)
    public=Path(__file__).parent/'receipts'/dest.name/'release_scan.json'
    if public.exists():
        need(result==read(public),'Published release receipt differs')
    print(result['status'])
