"""Rerun the historical checklist on a checkout with the project's private inputs."""
import argparse
from collections import defaultdict
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

from research.evidence_contract.oracle_reliability import d4_historical, d4_run, verify_d4, verify_p2
from research.evidence_contract.reviewer_tools.strict import digest, need
from research.evidence_contract.task55.data import EC, ROOT, read, save_new, sha

BASE = 'dd2e109bf1e2f7b8190dbd1efa0d527865b1207f'
MASTER = EC / 'execution/master_01'
D4 = MASTER / 'd4_development_20261117'
P2 = MASTER / 'p2_20261120'
TIMERS = {'input_normalization_ns_shared', 'evaluation_ns', 'mrz_work_ns', 'pair_total_ns',
          'shared_authority_ns', 'runtime_ns', 'process_cpu_ns'}


def without_timers(value):
    if isinstance(value, list):
        return [without_timers(item) for item in value]
    if isinstance(value, dict):
        return {k: without_timers(v) for k, v in value.items() if k not in TIMERS}
    return value


def manifest():
    previous = read(P2 / 'baseline.json')['protected_files']
    for name, expected in previous.items():
        need(sha(ROOT / name) == expected, f'Protected input changed: {name}')
    bound = set(ROOT / name for name in previous)
    bound.update(p for p in P2.iterdir() if p.is_file())
    bound.update((EC / 'oracle_reliability' / name) for name in (
        'p2_audit.py', 'pixel_lineage_audit.py', 'c2_evidence_audit.py', 'verify_p2.py'))
    return {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(bound)}


def replay(private_run, output):
    need(output.resolve().is_relative_to((EC / 'local').resolve()), 'Choose a private output')
    output.mkdir(parents=True, exist_ok=False)
    files = manifest()
    published = Path(__file__).with_name('baseline_replay.json')
    if published.exists():
        need(files == read(published)['protected_sha256'], 'Checklist baseline differs')
    else:
        for ref in ('HEAD', 'origin/main'):
            actual = subprocess.check_output(['git','rev-parse',ref], cwd=ROOT, text=True).strip()
            need(actual == BASE, f'Initial baseline must match fetched main: {ref}')
    prior = D4 / 'controls_01'
    with TemporaryDirectory(dir=EC / 'execution') as scratch:
        controls = Path(scratch) / 'controls'
        d4_run.run(controls)
        result = verify_d4.verify(controls)
        need(result == verify_d4.verify(prior), 'Control arithmetic changed')
        for name in read(prior / 'manifest.json')['files']:
            if name.endswith('.json'):
                need(without_timers(read(controls / name)) == without_timers(read(prior / name)),
                     f'Control replay mismatch: {name}')
            else:
                need((controls / name).read_text(encoding='utf8') == (prior / name).read_text(encoding='utf8'),
                     f'Control table mismatch: {name}')
        need(read(controls / 'manifest.json')['sources'] == read(prior / 'manifest.json')['sources'],
             'D4 sources changed')
        historical = d4_historical.run(Path(scratch) / 'historical', output / 'historical')
        old = read(D4 / 'historical_01/summary.json')
        old_rows = read(EC / 'local/master_01/d4_development_20261117/historical_01/rows.json')
        fresh_rows = read(output / 'historical/rows.json')
        need(digest(old_rows) == old['private_rows_sha256'], 'Historical row binding changed')
        need(without_timers(old_rows) == without_timers(fresh_rows), 'Historical row decisions changed')
        for item in (historical, old):
            del item['private_rows_sha256']  # Private rows include fresh per-arm timers.
        need(historical == old, 'Historical state counts or scope changed')

    need(verify_p2.verify(private_run, P2) == read(P2 / 'verification.json'), 'P1/P2 verification changed')
    lineage = read(private_run / 'pixel_private.json')
    group_index = {}
    for field in ('file', 'pixel'):
        by_hash = defaultdict(list)
        for i, row in enumerate(lineage['rows']):
            if field in row:
                by_hash[row[field]].append(i)
        group_index[field] = {h: indices for h, indices in by_hash.items() if len(indices) > 1}
    group_index['near'] = lineage['candidate_components']
    group_index['lineage_sha256'] = sha(private_run / 'pixel_private.json')
    expected = read(P2 / 'aggregate.json')['pixel']
    for field, key in [('file', 'file_duplicate_groups'), ('pixel', 'pixel_duplicate_groups'),
                       ('near', 'near_candidate_components')]:
        need(len(group_index[field]) == expected[key], f'Duplicate group count: {field}')
    save_new(output / 'duplicate_groups.json', group_index)

    args = [sys.executable, '-X', 'utf8', '-B', '-m', 'pytest', '-q', '-p', 'no:cacheprovider',
            'research/evidence_contract/tests', '--basetemp', str(output / 'pytest')]
    with (output / 'regression.log').open('xb') as log:
        subprocess.run(args, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, check=True)
    need(manifest() == files, 'Frozen evidence changed during replay')
    receipt = dict(baseline_commit=BASE, checkout_at_replay=subprocess.check_output(
        ['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip(),
        branch_at_replay=subprocess.check_output(['git','branch','--show-current'], cwd=ROOT, text=True).strip(),
        fetched_main=subprocess.check_output(['git','rev-parse','origin/main'], cwd=ROOT, text=True).strip(),
        checklist_code_sha256={p.name: sha(p) for p in (Path(__file__), Path(__file__).with_name('public_analysis.py'),
            EC / 'oracle_reliability/protocol_v3.py', EC / 'tests/test_protocol_v3.py')},
        protected_sha256=files, d4=result, historical=historical,
        excluded_timer_fields=sorted(TIMERS), matched_private_historical_rows=len(old_rows),
        comparison='All constructed payloads excluding listed timers; historical public summary except timing-dependent row digest',
        p2_verification_sha256=sha(P2 / 'verification.json'),
        private_group_index_sha256=sha(output / 'duplicate_groups.json'),
        regression=(output / 'regression.log').read_text(encoding='utf8').strip().splitlines()[-1],
        regression_log_sha256=sha(output / 'regression.log'), model_calls=0, training_runs=0)
    save_new(output / 'baseline_replay.json', receipt)
    print(receipt['regression'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('private_run', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    replay(args.private_run, args.output)
