"""Synthetic operating characteristics of frozen protocol v3. No image or reader access."""
import argparse
from dataclasses import asdict, dataclass, replace
from functools import lru_cache
import hashlib
import json
import math
from pathlib import Path
import random

import numpy as np

from . import protocol_v3 as v3

NAMES = ('decision_coverage', 'all_fault_sensitivity', 'paired_far_difference')
FLOORS = (v3.COVERAGE_FLOOR, v3.SENSITIVITY_FLOOR, v3.FAR_MARGIN)


@dataclass(frozen=True)
class Assumptions:
    ids: int
    cases: int
    prevalence: float
    truth_availability: float
    icc: float
    abstention: float
    sensitivity: float
    discordance: float
    miss_truth_multiplier: float

    def targets(self, effect):
        sensitive = self.sensitivity
        q = self.truth_availability
        observed_fault_rate = sensitive + (1-sensitive)*self.miss_truth_multiplier
        return (1-self.abstention, sensitive / observed_fault_rate if q and self.prevalence and observed_fault_rate else None,
                effect if q and self.prevalence < 1 else None)


def sample_ids(rng, a, effect, repetitions):
    """One draw per synthetic case, with a shared full-case draw on copy-mode IDs."""
    for p in (a.prevalence, a.truth_availability, a.icc, a.abstention, a.sensitivity,
              a.discordance, a.miss_truth_multiplier):
        if not 0 <= p <= 1:
            raise ValueError('Probabilities must be in [0,1]')
    if not 1 <= a.ids <= 200 or not 1 <= a.cases <= 4 or abs(effect) > a.discordance:
        raise ValueError('Invalid frame or discordance smaller than the absolute effect')
    # Nonfaults: asserted-only (+1), checked-only (-1), both, neither.
    plus = (a.discordance + effect)/2
    both = .03
    checked_far = (a.discordance-effect)/2 + both
    alarm_rate = a.prevalence*a.sensitivity + (1-a.prevalence)*checked_far
    if a.discordance + both > 1 or 1-a.abstention < alarm_rate:
        raise ValueError('Impossible joint distribution of alarms and decisions')
    decide_if_silent = 1-a.abstention/(1-alarm_rate) if alarm_rate < 1 else 1.
    shape = (repetitions, a.ids, a.cases)
    fault = rng.random(shape) < a.prevalence
    u = rng.random(shape)
    checked = np.where(fault, u < a.sensitivity, (u >= plus) & (u < a.discordance+both))
    delta = np.where(u < plus, 1, np.where(u < a.discordance, -1, 0))
    decided = checked | (rng.random(shape) < decide_if_silent)
    availability = np.where(fault & ~checked, a.truth_availability*a.miss_truth_multiplier, a.truth_availability)
    known = rng.random(shape) < availability
    # Keep all outcomes, pairing and missingness together. Mixture gives ICC rho
    # for every nonconstant single-case statistic under equal case marginals.
    shared = rng.random((repetitions, a.ids)) < a.icc
    fields = (decided, known & fault, known & fault & checked, known & ~fault, (known & ~fault)*delta)
    return np.stack([np.where(shared, x[:,:,0]*a.cases, x.sum(axis=2)) for x in fields], axis=2)


@lru_cache(maxsize=3)
def bootstrap_weights(ids):
    # Match random.Random.choices with equal weights in v3, including its fixed seed.
    rng = random.Random(v3.SEED)
    values = np.empty((v3.REPLICATES, ids), dtype=np.float32)
    for i in range(v3.REPLICATES):
        values[i] = np.bincount(rng.choices(range(ids), k=ids), minlength=ids)
    return values


def bootstrap(vectors, cases):
    """Return diagnostics per cohort after the 30-ID guard; use identical resamples for both arms."""
    count, ids, _ = vectors.shape
    w = bootstrap_weights(ids)
    # Float32 multiply-adds are exact for these integer counts (absolute sums <=800).
    sums = (vectors.transpose(0,2,1).reshape(-1,ids).astype(np.float32) @ w.T).reshape(count,5,-1)
    sums = sums.astype(np.float64)
    with np.errstate(invalid='ignore', divide='ignore'):
        rates = np.stack((sums[:,0]/(ids*cases), sums[:,2]/sums[:,1], sums[:,4]/sums[:,3]), axis=1)
    bad = (sums[:,1] == 0) | (sums[:,3] == 0)
    constant = rates.min(axis=2) == rates.max(axis=2)
    kth = math.ceil(.05 * v3.REPLICATES)-1
    rates.partition(kth, axis=2)
    return rates[:,:,kth], constant, bad.sum(axis=1)


def wilson(k, n):
    if not n:
        return dict(k=int(k), n=0, rate=None, lo=None, hi=None)
    p = k/n
    z = 1.959963984540054
    scale = 1+z*z/n
    center = (p+z*z/(2*n))/scale
    width = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n))/scale
    return dict(k=int(k), n=int(n), rate=float(p), lo=0. if k==0 else max(0.,center-width),
                hi=1. if k==n else min(1.,center+width))


def operating_point(a, effect, trials, seed, label):
    rng = np.random.default_rng(seed)
    target = a.targets(effect)
    joint = short = bad_trials = bad_draws = constant_trials = issued = relax_pass = 0
    degenerate = np.zeros(3, dtype=np.int64)
    covered = np.zeros(3, dtype=np.int64)
    all_cover = 0
    for start in range(0, trials, 32):
        vec = sample_ids(rng, a, effect, min(32,trials-start))
        enough = ((vec[:,:,1] > 0).sum(axis=1) >= 30) & ((vec[:,:,3] > 0).sum(axis=1) >= 30)
        short += int((~enough).sum())
        if not enough.any():
            continue
        lower, const, invalid = bootstrap(vec[enough], a.cases)
        bad_draws += int(invalid.sum())
        bad_trials += int((invalid > 0).sum())
        valid = invalid == 0
        degenerate += (const & valid[:,None]).sum(axis=0)
        constant_trials += int((valid & const.any(axis=1)).sum())
        issued_mask = valid & ~const.any(axis=1)
        issued += int(issued_mask.sum())
        ok = (lower[:,0] >= FLOORS[0]) & (lower[:,1] >= FLOORS[1]) & (lower[:,2] > FLOORS[2])
        joint += int((ok & issued_mask).sum())
        relax_pass += int((ok & valid & ~const[:,1:].any(axis=1)).sum())
        hits = lower[issued_mask] <= np.asarray(target,dtype=float) + 1e-14
        covered += hits.sum(axis=0)
        all_cover += int(hits.all(axis=1).sum())
    return dict(label=label, assumptions=asdict(a), effect=effect, target=target, trials=trials,
                joint_pass=wilson(joint,trials), insufficient=wilson(trials-issued,trials),
                issued=issued, short_clusters=short, invalid_bootstrap_cohorts=bad_trials,
                invalid_bootstrap_draws=bad_draws, bootstrap_draws=(trials-short)*v3.REPLICATES,
                degenerate_any=constant_trials, degenerate_by_metric=dict(zip(NAMES,map(int,degenerate))),
                coverage_if_issued={k:wilson(int(c),issued) for k,c in zip(NAMES,covered)},
                simultaneous_coverage_if_issued=wilson(all_cover,issued),
                pass_if_only_coverage_degeneracy_waived=wilson(relax_pass,trials),
                additional_passes_if_waived=wilson(relax_pass-joint,trials))


def profile_grid(a, design):
    # Boundary of FAR is a true null (strict >). For inclusive floors use a true
    # null immediately below .80. Invert observed sensitivity under selective missingness.
    boundary = .7999
    mult = a.miss_truth_multiplier
    latent = boundary*mult/(1-boundary+boundary*mult)
    stress_effect = min(.15, a.discordance)
    yield 'null_far', a, v3.FAR_MARGIN
    yield 'null_coverage', replace(a, abstention=1-boundary), stress_effect
    yield 'null_sensitivity', replace(a, sensitivity=latent), stress_effect
    for e in design['effects']:
        if e <= a.discordance:
            yield 'effect_grid', a, e


def power_verdict(p, threshold):
    if p['lo'] >= threshold:
        return 'FEASIBLE'
    if p['hi'] < threshold:
        return 'INFEASIBLE'
    return 'INSUFFICIENT_EVIDENCE'


def summarize(points, design):
    threshold = design['criteria']['target_joint_power']
    alpha = design['criteria']['nominal_type_I']
    nominal = design['criteria']['nominal_lower_bound_coverage']
    grid = [p for p in points if p['label']=='effect_grid']
    primary = next(p for p in grid if p['effect']==design['reference_effect'])
    power = power_verdict(primary['joint_pass'],threshold)
    size = [p['joint_pass'] for p in points if p['label'].startswith('null_')]
    coverage = list(primary['coverage_if_issued'].values())
    ruled_out = any(p['lo'] > alpha for p in size) or any(p['hi'] is not None and p['hi'] < nominal for p in coverage)
    confirmed = all(p['hi'] <= alpha for p in size) and all(p['lo'] is not None and p['lo'] >= nominal for p in coverage)
    verdict = 'INFEASIBLE' if power=='INFEASIBLE' or ruled_out else (
        'FEASIBLE' if power=='FEASIBLE' and confirmed else 'INSUFFICIENT_EVIDENCE')
    return dict(power_verdict=power, statistical_verdict=verdict,
                mde_grid_estimate=next((p['effect'] for p in grid if p['joint_pass']['rate']>=threshold),None),
                mde_grid_mc_supported=next((p['effect'] for p in grid if p['joint_pass']['lo']>=threshold),None),
                largest_effect_examined=grid[-1]['effect'])


def simulate(design):
    if design['bootstrap_replicates'] != v3.REPLICATES or design['trials'] < 1:
        raise ValueError('Expected v3 bootstrap count and positive trial count')
    results = {}
    for name, overrides in design['profiles'].items():
        a = Assumptions(**(design['defaults'] | overrides))
        seed = [design['seed'], int.from_bytes(hashlib.sha256(name.encode()).digest()[:4],'big')]
        points = [operating_point(assumptions, effect, design['trials'], seed, label)
                  for label, assumptions, effect in profile_grid(a, design)]
        results[name] = dict(points=points, **summarize(points, design))
        print(name, results[name]['statistical_verdict'], flush=True)
    return results


if __name__ == '__main__':
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('design', type=Path)
    cli.add_argument('output', type=Path)
    args = cli.parse_args()
    if args.output.exists():
        cli.error('Choose a fresh output file')
    design = json.loads(args.design.read_bytes())
    results = simulate(design)
    with args.output.open('x',encoding='utf8',newline='\n') as f:
        json.dump(dict(design_sha256=hashlib.sha256(args.design.read_bytes()).hexdigest(),
                       profiles=results),f,indent=2,allow_nan=False)
        f.write('\n')
