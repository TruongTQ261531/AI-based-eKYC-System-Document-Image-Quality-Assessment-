"""Paired cluster analysis for development tests and a prospective SAP."""
from collections import defaultdict
import math
from numbers import Integral

import numpy as np


def ratio(numerator, denominator):
    return numerator / denominator if denominator else None


def rate(numerator, denominator):
    return dict(numerator=numerator, denominator=denominator, value=ratio(numerator, denominator))


def positive_integer(value):
    return isinstance(value, Integral) and not isinstance(value, (bool, np.bool_)) and value > 0


def paired_interval(records, *, draws=10000, seed=7297, minimum_clusters=20):
    """Records contain cluster id and A/B numerators and denominators per pair."""
    if not positive_integer(draws) or not positive_integer(minimum_clusters) or minimum_clusters < 2:
        raise ValueError("Positive draws and at least two independent clusters are required")
    groups = defaultdict(lambda: np.zeros(4, dtype=np.int64))
    for cluster, an, ad, bn, bd in records:
        values = (an, ad, bn, bd)
        if (not isinstance(cluster, str) or not cluster
                or any(not isinstance(v, Integral) or isinstance(v, (bool, np.bool_)) for v in values)
                or not 0 <= an <= ad or not 0 <= bn <= bd):
            raise ValueError("Paired ratios require a cluster and coherent counts")
        totals = [int(a) + int(b) for a, b in zip(groups[cluster], values)]
        if max(totals) > np.iinfo(np.int64).max:
            raise ValueError("Cluster totals exceed supported integer range")
        groups[cluster] = np.asarray(totals, dtype=np.int64)
    array = np.array([groups[key] for key in sorted(groups) if groups[key][1] or groups[key][3]], dtype=np.int64).reshape(-1, 4)
    n = len(array)
    sums = [sum(int(value) for value in array[:, col]) for col in range(4)]
    if max(sums) > np.iinfo(np.int64).max:
        raise ValueError("Pooled totals exceed supported integer range")
    an, ad, bn, bd = sums
    ra, rb = rate(an, ad), rate(bn, bd)
    result = dict(A=ra, B=rb, delta=ra["value"] - rb["value"] if ad and bd else None,
                  clusters=n, clusters_A=int(np.count_nonzero(array[:, 1])),
                  clusters_B=int(np.count_nonzero(array[:, 3])), draws=0, seed=seed,
                  ci95=None, lower95_one_sided=None, reason=None)
    if not ad or not bd:
        result["reason"] = "zero_denominator"
    elif min(result["clusters_A"], result["clusters_B"]) < minimum_clusters:
        result["reason"] = "insufficient_independent_clusters"
    else:
        rng = np.random.default_rng(seed)
        # Chunking bounds memory for larger panels without changing the random stream.
        deltas = []
        for begin in range(0, draws, 256):
            idx = rng.integers(n, size=(min(256, draws - begin), n))
            totals = array[idx].sum(axis=1)
            valid = (totals[:, 1] > 0) & (totals[:, 3] > 0)
            a, b, c, d = totals[valid].T
            deltas.extend((a / b - c / d).tolist())
        result["draws"] = len(deltas)
        if len(deltas) < .95 * draws:
            result["reason"] = "unstable_denominator_in_resamples"
        else:
            result["ci95"] = np.percentile(deltas, [2.5, 97.5]).tolist()
            result["lower95_one_sided"] = float(np.percentile(deltas, 5))
    return result


def sign_flip(cluster_deltas, *, direction, draws=10000, seed=8273, minimum_discordant=8):
    """Randomization on matched clusters with common denominators and exchangeability."""
    if direction not in ("greater", "less"):
        raise ValueError("Declare direction before the test")
    if not positive_integer(draws) or not positive_integer(minimum_discordant):
        raise ValueError("Positive draw and discordance counts are required")
    diffs = np.asarray(cluster_deltas, dtype=float)
    if diffs.ndim != 1 or not np.isfinite(diffs).all():
        raise ValueError("Cluster differences must be finite")
    diffs = diffs[diffs != 0]
    if len(diffs) < minimum_discordant:
        return None
    if direction == "less":
        diffs = -diffs
    observed = diffs.sum()
    if len(diffs) <= 16:
        codes = np.arange(1 << len(diffs), dtype=np.uint32)[:, None]
        signs = 1 - 2 * ((codes >> np.arange(len(diffs), dtype=np.uint32)) & 1).astype(np.int8)
        return float(np.mean(signs @ diffs >= observed - 1e-12))
    rng = np.random.default_rng(seed)
    extreme = 0
    for begin in range(0, draws, 256):
        signs = 1 - 2 * rng.integers(2, size=(min(256, draws - begin), len(diffs)), dtype=np.int8)
        extreme += int(np.sum(signs @ diffs >= observed - 1e-12))
    return (extreme + 1) / (draws + 1)


def holm_family(values):
    from research.fc_statistics import holm
    keys = list(values)
    if any(p is not None and (isinstance(p, (bool, np.bool_)) or not math.isfinite(p) or not 0 <= p <= 1)
           for p in values.values()):
        raise ValueError("Expected p in [0, 1] or None")
    adjusted = holm([values[key] if values[key] is not None else 1. for key in keys])
    # Missing prespecified tests keep their multiplicity slot.
    return {key: p if values[key] is not None else None for key, p in zip(keys, adjusted)}
