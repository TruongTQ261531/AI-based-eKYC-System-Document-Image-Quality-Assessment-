"""Pointwise D4 planning analysis on a fixed, externally validated primary frame."""
import argparse
from collections import Counter, defaultdict
import json
from math import ceil
import random

from .reporting_v2 import summarize

ARMS = ('checked_v2', 'mrz_metadata_asserted')
STATES = {'FAULT', 'NO_FAULT', 'UNKNOWN', 'INVALID_TEST'}
COVERAGE_FLOOR = 0.80
SENSITIVITY_FLOOR = 0.80
FAR_MARGIN = 0.05
REPLICATES = 10000
SEED = 20261121


def rates(counts):
    n, decided, faults, detected, nonfaults, excess_alarms = counts
    return (decided / n if n else None, detected / faults if faults else None,
            excess_alarms / nonfaults if nonfaults else None)


def missing_truth_bounds(total, denominator, contributions):
    """Extrema when any subset of unresolved cases can enter the denominator."""
    endpoints = []
    for reverse in (False, True):
        s, n = total, denominator
        if n:
            endpoints.append(s / n)
        for value in sorted(contributions, reverse=reverse):
            count = contributions[value]
            s += count * value
            n += count
            endpoints.append(s / n)
    return dict(minimum=min(endpoints) if endpoints else None, maximum=max(endpoints) if endpoints else None,
                can_be_undefined=denominator == 0)


def analyze(rows):
    clusters = defaultdict(lambda: [0] * 6)
    arm_counts = {arm: Counter() for arm in ARMS}
    missing_alarm, missing_delta = Counter(), Counter()
    seen = set()
    for row in rows:
        key = row['case_id']
        cluster = row['physical_id']
        if not all(isinstance(i, str) and i.strip() for i in (key, cluster)) or key in seen:
            raise ValueError('Expected distinct case IDs and known physical IDs')
        seen.add(key)
        truth = row['truth']
        checked, asserted = (row[a] for a in ARMS)
        if (truth is not None and type(truth) is not bool) or not {checked, asserted} <= STATES:
            raise ValueError('Invalid truth or pointwise state')
        for arm in ARMS:
            arm_counts[arm][truth, row[arm]] += 1
        if truth is None:
            missing_alarm[int(checked == 'FAULT')] += 1
            missing_delta[int(asserted == 'FAULT') - int(checked == 'FAULT')] += 1
        observation = (1, checked in {'FAULT', 'NO_FAULT'}, truth is True,
                       truth is True and checked == 'FAULT', truth is False,
                       (int(asserted == 'FAULT') - int(checked == 'FAULT')) if truth is False else 0)
        for index, count in enumerate(observation):
            clusters[cluster][index] += count

    vectors = [clusters[key] for key in sorted(clusters)]
    total = [sum(values) for values in zip(*vectors)] if vectors else [0] * 6
    names = ('checked_coverage', 'checked_all_fault_sensitivity', 'asserted_minus_checked_far')
    point = rates(total)
    fields = ('cases','checked_decisions','known_faults','checked_fault_alarms','known_nonfaults','net_nonfault_alarms')
    result = dict(counts=dict(zip(fields, total)), physical_ids=len(vectors), missing_truth=total[0]-total[2]-total[4],
                  estimates=dict(zip(names, point)), lower95=None, status='INSUFFICIENT_INFORMATION')
    result['by_arm'] = {arm: summarize([dict(truth=truth, state=state, count=count, reason='unspecified')
                                        for (truth, state), count in cells.items()])
                        for arm, cells in arm_counts.items()}
    result['missing_truth_bounds'] = dict(
        checked_sensitivity=missing_truth_bounds(total[3], total[2], missing_alarm),
        paired_far_difference=missing_truth_bounds(total[5], total[4], missing_delta))
    # The minimum is a reporting guard. Achieved precision still depends on the data.
    if min(sum(v[i] > 0 for v in vectors) for i in (2, 4)) < 30:
        return result
    rng = random.Random(SEED)
    draws = [[], [], []]
    undefined = [0, 0, 0]
    for _ in range(REPLICATES):
        sample = rng.choices(vectors, k=len(vectors))
        for i, value in enumerate(rates(list(map(sum, zip(*sample))))):
            if value is None:
                undefined[i] += 1
            else:
                draws[i].append(value)
    result['undefined_replicates'] = dict(zip(names, undefined))
    if any(undefined) or any(min(values) == max(values) for values in draws):
        return result
    lower = [sorted(values)[ceil(.05 * REPLICATES) - 1] for values in draws]
    result['lower95'] = dict(zip(names, lower))
    passed = lower[0] >= COVERAGE_FLOOR and lower[1] >= SENSITIVITY_FLOOR and lower[2] > FAR_MARGIN
    result['status'] = 'DESIGN_CRITERIA_MET' if passed else 'DESIGN_CRITERIA_UNMET'
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('frame', type=argparse.FileType(encoding='utf-8'))
    print(json.dumps(analyze(json.load(parser.parse_args().frame)), indent=2, allow_nan=False))
