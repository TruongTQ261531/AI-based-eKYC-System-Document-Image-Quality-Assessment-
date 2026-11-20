"""Independent stdlib D4 file, frame and paired arithmetic verifier."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

from .verify import need
from .verify_reporting_v2 import verify as arithmetic


ARMS = ('checked_v2', 'mrz_metadata_asserted')
ENDPOINTS = ('pointwise', 'relation', 'structure')
ARTIFACTS = {
    'expected_controls.json', 'control_results.json', 'aggregate_cells.json',
    'accounting.json', 'divergences.json', 'guard_matrix.json', 'summary.json',
    'expected_vs_actual.md',
}


def digest(value):
    canonical = json.dumps(value, ensure_ascii=False, sort_keys=True,
                           separators=(',', ':'), allow_nan=False)
    return hashlib.sha256(canonical.encode()).hexdigest()


def verify(folder):
    folder = Path(folder)

    def read(name):
        return json.loads((folder / name).read_bytes())

    manifest = read('manifest.json')
    need(set(manifest['files']) == ARTIFACTS, 'Incomplete or unexpected D4 artifact inventory')
    for name, expected_hash in manifest['files'].items():
        need(hashlib.sha256((folder / name).read_bytes()).hexdigest() == expected_hash, name)

    rows = read('control_results.json')
    spec = read('expected_controls.json')
    summary = read('summary.json')
    need(digest(spec) == manifest['source_spec_sha256'], 'Control specification hash')
    expected = {c['name']: c for c in spec}
    need(len(rows) == len(spec) == len(expected) == summary['controls'], 'Control count')
    need({r['name'] for r in rows} == expected.keys(), 'Control names')

    divergences = read('divergences.json')
    published_differences = {(d['name'], d['tier']): d for d in divergences}
    need(len(published_differences) == len(divergences), 'Duplicate published divergence')
    observed = set()
    projected = Counter()
    costs = {arm: Counter() for arm in ARMS}
    for row in rows:
        name = row['name']
        case = expected[name]
        need(row['truth'] == case['truth'] and row['expected'] == case['expected_by_tier']
             and row['family'] == case['family'], f'Control specification mismatch for {name}')
        need(row['physical_ids'] == 0 and set(row['panels']) == {'1', '2'}, f'Control frame for {name}')
        for tier, panel in row['panels'].items():
            pair = (name, int(tier))
            fingerprint = digest(dict(row['shared_input'], tier=int(tier)))
            need(panel['shared_input_sha256'] == fingerprint, f'Input fingerprint for {pair}')
            need(panel['minimum_grade'] == int(tier) and panel['approved_reference_count'] == 0,
                 f'Tier or reference count for {pair}')
            need(not panel['independent_gold'] and not panel['scientific_go'], f'Evidence scope for {pair}')
            need(panel['cost']['model_calls'] == panel['cost']['training_runs'] == 0, f'Model cost for {pair}')
            need(set(panel['arms']) == set(ARMS), f'Methods for {pair}')
            for arm, value in panel['arms'].items():
                states = [value[e]['state'] for e in ENDPOINTS]
                need(states == row['expected'][tier][arm], f'Endpoint states for {pair} {arm}')
                for index, endpoint in enumerate(ENDPOINTS):
                    decision = value[endpoint]
                    need(decision['alarm'] == (decision['state'] in ('FAULT', 'STRUCTURAL_ERROR')),
                         f'Alarm for {pair} {arm} {endpoint}')
                    cell = ('constructed_D4_tier' + tier, row['family'], row['shared_input']['context']['contract'],
                            'symbolic_not_physical', arm, endpoint, row['truth'][index], decision['state'], decision['reason'])
                    projected[cell] += 1
                costs[arm].update(panel['cost']['arms'][arm])

            checked, asserted = (panel['arms'][arm] for arm in ARMS)
            endpoints = [e for e in ENDPOINTS if checked[e] != asserted[e]]
            if endpoints:
                need(row['family'] == 'literal_mrz_intervention', f'Unexpected divergence for {pair}')
                need(name not in summary['valid_MRZ_parity_cases'], f'Valid MRZ parity for {pair}')
                observed.add(pair)
                published = published_differences.get(pair)
                need(published is not None, f'Missing divergence for {pair}')
                need(published['shared_input_sha256'] == fingerprint and published['endpoints'] == endpoints
                     and published['checked_reasons'] == {e: checked[e]['reason'] for e in endpoints}
                     and published['asserted_reasons'] == {e: asserted[e]['reason'] for e in endpoints},
                     f'Divergence details for {pair}')

    need(observed == published_differences.keys(), 'Divergence inventory')
    need(len(observed) == summary['divergence_tier_pairs']
         and len({name for name, tier in observed}) == summary['divergence_unique_controls'], 'Divergence counts')
    names = ('dataset', 'partition', 'contract', 'cluster', 'method', 'endpoint', 'truth', 'state', 'reason')
    published = Counter()
    for cell in read('aggregate_cells.json'):
        published[tuple(cell[k] for k in names)] += cell['count']
    need(projected == published, 'Aggregate cells')
    need({a: dict(c) for a, c in costs.items()} == summary['costs'], 'Arm costs')
    need(costs['mrz_metadata_asserted']['literal_td3_calls'] == 0, 'Asserted arm literal calls')
    need(summary['paired_evaluations'] == 2 * len(rows) and summary['arm_evaluations'] == 4 * len(rows),
         'Evaluation counts')
    need(summary['model_calls'] == summary['training_runs'] == summary['reference_approvals_created'] == 0,
         'Development scope')
    need(summary['scientific_gate'] == 'NO_GO_SUPERIORITY' and not summary['prospective_started'], 'Scientific gate')
    totals = arithmetic(folder / 'aggregate_cells.json', folder / 'accounting.json')
    return dict(status='PASS', controls=len(rows), paired_tier_evaluations=2 * len(rows),
                divergence_tier_pairs=len(observed), arithmetic=totals,
                shared_input_fingerprints_checked=2 * len(rows), physical_ids=0,
                scope='Independent accounting/binding, not empirical truth or efficacy')


if __name__ == '__main__':
    print(json.dumps(verify(sys.argv[1]), indent=2))
