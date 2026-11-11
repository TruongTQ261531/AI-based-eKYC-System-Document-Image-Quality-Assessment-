"""Check recovery against the byte inventories, with no writes to old artifacts."""
from pathlib import Path
import json
import subprocess

from .data import EC, OUT, ROOT, read, save_new, sha
from .ifv_sampling import RECOVERY, SAMPLE
from .review import PACKET_ROOT


def git(root, *args):
    return subprocess.check_output(['git', '--no-optional-locks', *args], cwd=root, encoding='utf-8').strip()


def verify():
    earlier = read(OUT / 'preservation_before.json')
    start = read(RECOVERY / 'resume_snapshot.json')
    draft = read(RECOVERY / 'draft_checkpoint.json')['files']
    hashes = {}

    def check(items, *, exclude=()):
        checked = 0
        for row in items:
            name = row['path']
            if name in exclude:
                continue
            path = ROOT / name
            if path.stat().st_size != row['bytes']:
                raise ValueError('Unexpected byte count: ' + name)
            if name not in hashes:
                hashes[name] = sha(path)
            if hashes[name] != row['sha256']:
                raise ValueError('Changed historical file: ' + name)
            checked += 1
        return checked

    immutable = check(earlier['files'])
    unmodified = check(start['files'], exclude={row['source'] for row in draft})
    old_by_path = {row['path']: row['sha256'] for row in start['files']}
    for row in draft:
        if sha(ROOT / row['backup']) != old_by_path[row['source']] or row['sha256'] != old_by_path[row['source']]:
            raise ValueError('Interrupted draft backup mismatch')
        if sha(ROOT / row['source']) == row['sha256']:
            raise ValueError('Unexpected unchanged draft in edit list')

    audit = read(OUT / 'audit_run_01.json')
    for path, expected in audit['log_hashes'].items():
        if sha(Path(path)) != expected:
            raise ValueError('Changed historical event log')
    if any((EC / 'local' / name).exists() for name in ('task55_human_submissions', 'task55_output_review')):
        raise ValueError('This closeout is only for the pre-review recovery state')
    gate_artifacts = ('TEST_LOCK.json', 'TEST_MANIFEST.json', 'IFV_RESULTS.md')
    if any((EC / name).exists() for name in gate_artifacts):
        raise ValueError('Unexpected post-gate artifact')

    receipt = read(OUT / 'review_packet_preparation.json')
    for relative, expected in receipt['file_hashes'].items():
        if sha(PACKET_ROOT / relative) != expected:
            raise ValueError('Changed review packet asset')
    sampling = read(RECOVERY / 'ifv_sampling_summary.json')
    if sha(SAMPLE) != sampling['sample_file_sha256']:
        raise ValueError('Changed review sampling frame')
    for path in (PACKET_ROOT / 'index.html', SAMPLE):
        if not git(ROOT, 'check-ignore', path.relative_to(ROOT).as_posix()):
            raise ValueError('Private data is not covered by gitignore')

    status = git(ROOT, 'status', '--short')
    head = git(ROOT, 'rev-parse', 'HEAD')
    refs = git(ROOT, 'show-ref')
    if head != start['head'] or refs != start['refs'].strip():
        raise ValueError('Git refs changed')
    tracked = git(ROOT, 'diff', '--name-only')
    staged = git(ROOT, 'diff', '--cached', '--name-only')
    mentor = ROOT.parent / 'mentor-ekyc-v3.2.0'
    if tracked or staged or git(mentor, 'status', '--short'):
        raise ValueError('Unexpected tracked or mentor edits')

    log_names = ('ifv_prepare', 'ifv_sample', 'python_ifv_tests_02', 'node_review_tests',
                 'node_review_syntax', 'node_stage2_ui_test', 'controls_run_02')
    logs = {name: RECOVERY / (name + '.log') for name in log_names}
    for name, path in logs.items():
        if not path.read_text(encoding='utf-8-sig').strip().endswith('Exit: 0'):
            raise ValueError('Missing successful execution evidence: ' + name)
    failed_control = RECOVERY / 'controls_run_01.log'
    if not failed_control.read_text(encoding='utf-8-sig').strip().endswith('Exit: 1'):
        raise ValueError('Missing retained failed run')

    result = dict(status='VERIFIED_DEVELOPMENT_RECOVERY', head=head, git_status=status.splitlines(),
                  refs_unchanged=True, tracked_diff=tracked, staged_diff=staged, mentor_status='clean',
                  earlier_snapshot_byte_matches=immutable, resume_snapshot_entries=len(start['files']),
                  resume_snapshot_byte_matches=unmodified, archived_and_completed_drafts=len(draft),
                  original_inference_log_hashes_matching=len(audit['log_hashes']),
                  historical_model_assets_checked_at_recovery=len(read(EC / 'RECOVERY_EVIDENCE.json')['checkpoints']['verified_assets']),
                  actual_new_model_inference_calls=0, actual_human_observations=0, confirmatory_opened=False,
                  no_gate_artifacts_present=True, successful_log_sha256={name: sha(path) for name, path in logs.items()},
                  retained_failed_control_log_sha256=sha(failed_control),
                  browser_smoke=read(RECOVERY / 'browser_smoke_01.json')['status'],
                  review_packet_id=receipt['packet_id'], review_assets_verified=len(receipt['file_hashes']),
                  sampling_id=sampling['sample_id'])
    save_new(RECOVERY / 'final_verification.json', result)
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    verify()
