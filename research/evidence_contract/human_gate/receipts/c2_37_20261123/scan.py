"""Check this milestone's index diff before commit, or a specific committed tree on replay."""
import argparse
import hashlib
import subprocess
from pathlib import Path

from research.evidence_contract.human_gate.closure import SOURCE
from research.evidence_contract.human_gate.prepare import private_run
from research.evidence_contract.human_gate.prepare37 import BASELINE, MASTER
from research.evidence_contract.reviewer_tools.strict import need
from research.evidence_contract.task55.data import ROOT, read, save_new

HERE = Path(__file__).resolve().parent
EC = 'research/evidence_contract/'
PUBLIC = HERE.relative_to(ROOT).as_posix() + '/'
RECEIPT = PUBLIC + 'release_scan.json'
ALLOWED = {EC + s for s in (
    'human_gate/package.py', 'human_gate/prepare.py', 'human_gate/prepare37.py', 'human_gate/verify37.py',
    'tests/test_c2_37_verify.py', 'C2_37_ANALYSIS_PROTOCOL_VI.md', 'C2_37_D10_VI.md',
    'P6_CLAIM_TO_EVIDENCE_MATRIX.md', 'MASTER_EXECUTION_STATUS.md', 'NEXT_ACTIONS.md',
    'EASE2027_ROADMAP_VI.md', 'C2_37_FIRST_CONTINUATION_VI.md')}
ALLOWED.update(PUBLIC + s for s in ('aggregate.json','verification.json','validation.json','REPLAY.md','scan.py'))


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def scan(commit=None):
    revisions = [BASELINE, commit] if commit else ['--cached', BASELINE]
    paths = set(git('diff','--name-only',*revisions).decode().splitlines())
    need(paths == ALLOWED or paths == ALLOWED | {RECEIPT}, 'Unexpected public paths')
    if commit:
        need(RECEIPT in paths, 'Missing committed scan receipt')
    need(not git('diff','--name-only','--diff-filter=DRT',*revisions), 'Deleted or replaced public artifact')
    ledger = read(SOURCE/'qualification/evidence.json')
    private = set(ledger['images']) | set(ledger['physical_instances']) | {r['candidate_id'] for r in ledger['candidates']}
    private.update(i['crop'] for r in ledger['candidates'] for i in r['inspection'] if 'crop' in i)
    for family in read(private_run(MASTER)/'artifact_rights.json'):
        if family['artifact'] in {'original_frames','derived_frames','region_crops'}:
            private.update(family['members'])
    private.update(('data:image/'+'png;base64,', 'data:image/'+'jpeg;base64,', '-----BEGIN '+'PRIVATE KEY'))
    manifest = {}
    for name in sorted(paths):
        diff = git('diff','--unified=0',*revisions,'--',name).decode()
        added = '\n'.join(s[1:] for s in diff.splitlines() if s.startswith('+') and not s.startswith('+++'))
        need(all(term not in added for term in private), 'Private binding or payload in public diff')
        if name != RECEIPT:
            blob = git('show', (commit or '')+':'+name)
            manifest[name] = hashlib.sha256(blob).hexdigest()
    return dict(status='RELEASE_SCAN_VERIFIED', baseline=BASELINE, public_files_including_receipt=len(ALLOWED)+1,
                private_matches=0, public_blob_sha256_excluding_self=manifest)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--commit')
    revision = parser.parse_args().commit
    result = scan(revision)
    path = ROOT/RECEIPT
    if path.exists():
        need(read(path) == result, 'Release scan receipt mismatch')
    else:
        need(revision is None, 'Missing original receipt')
        save_new(path, result)
    print(result['status'])
