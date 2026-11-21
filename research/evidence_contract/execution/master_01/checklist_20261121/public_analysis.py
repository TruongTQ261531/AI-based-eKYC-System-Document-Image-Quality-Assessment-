"""Recompute the checklist's public descriptive results without private images or reviews."""
from collections import Counter
import json
from pathlib import Path

from research.evidence_contract.oracle_reliability.verify_d4 import verify
from research.evidence_contract.reviewer_tools.strict import need
from research.evidence_contract.task55.data import read, sha

HERE = Path(__file__).resolve().parent
MASTER = HERE.parent


def analyze():
    d4 = MASTER / 'd4_development_20261117'
    controls = d4 / 'controls_01'
    p2 = MASTER / 'p2_20261120'
    baseline = read(HERE / 'baseline_replay.json')
    for name, expected in baseline['protected_sha256'].items():
        need(sha(MASTER.parents[3] / name) == expected, f'Baseline input changed: {name}')
    need(verify(controls) == baseline['d4'], 'D4 replay receipt')
    selected = [r for r in read(controls / 'control_results.json') if r['family'] == 'literal_mrz_intervention']
    arm_counts = {}
    for arm in ('checked_v2', 'mrz_metadata_asserted'):
        decisions = Counter(r['panels']['1']['arms'][arm]['pointwise']['state'] for r in selected)
        arm_counts[arm] = dict(sorted(decisions.items()))
    review = read(MASTER / 'reviewer_intake_20261120_r03_phase2/r02_r03_agreement.json')
    agreement = {}
    for endpoint, view in review['views']['primary']['derived'].items():
        cells = view['contingencies']
        matched = sum(c['count'] for c in cells if c['first'] == c['second'])
        total = sum(c['count'] for c in cells)
        need((matched, total) == (view['matched'], view['compared']), 'Reviewer contingency mismatch')
        agreement[endpoint] = [matched, total]
    audit = read(p2 / 'aggregate.json')
    receipt = read(p2 / 'verification.json')
    need(sha(p2 / 'aggregate.json') == receipt['aggregate_sha256'], 'P2 aggregate changed')
    c2 = audit['c2']
    need(all(sum(v.values()) == c2['candidate_count'] for v in c2['condition_counts'].values()), 'C2 counts')
    checked = dict(d4=baseline['d4'], tier1_intervention_pointwise=arm_counts, historical=baseline['historical']['state_counts'],
                   pixel_groups=receipt['cross_role_exact_pixel_patterns'], c2_conditions=c2['condition_counts'],
                   c2_eligible=c2['eligible'], c2_denominator=c2['candidate_count'], reviewer_agreement=agreement)
    return checked


if __name__ == '__main__':
    print(json.dumps(analyze(), sort_keys=True, indent=2))
