"""Preparatory pointwise ratio inference from ordered, paired independent-unit counts.

Columns: cases, decisions, labelled faults, detections, labelled nonfaults, net alarms.
Rows in each batch must be aggregated at the method's declared independent unit.
"""
from functools import lru_cache
import math

import numpy as np
from scipy.stats import t

from . import protocol_v3 as v3
from .p5_simulation import bootstrap_weights

DEN = [0, 2, 4]
NUM = [1, 3, 5]
THRESHOLDS = np.array([v3.COVERAGE_FLOOR, v3.SENSITIVITY_FLOOR, v3.FAR_MARGIN])


def passes(bounds):
    return np.stack([bounds[:, 0] >= THRESHOLDS[0], bounds[:, 1] >= THRESHOLDS[1],
                     bounds[:, 2] > THRESHOLDS[2]], axis=1)


@lru_cache(maxsize=16)
def critical(groups):
    return t.ppf(.95, groups - 1)


def _percentile(counts):
    batches, ids, _ = counts.shape
    weights = bootstrap_weights(ids)
    # Maximum absolute integer sum is 800, exactly representable in float32.
    sums = (counts.transpose(0, 2, 1).reshape(-1, ids).astype(np.float32) @ weights.T)
    sums = sums.reshape(batches, 6, -1).astype(float)
    with np.errstate(divide='ignore', invalid='ignore'):
        draws = sums[:, NUM] / sums[:, DEN]
    invalid = (sums[:, DEN] == 0).any(axis=(1, 2))
    constant = (draws.max(axis=2) == draws.min(axis=2)).any(axis=1)
    rank = math.ceil(.05 * v3.REPLICATES) - 1
    draws.partition(rank, axis=2)
    return draws[:, :, rank], invalid, constant


def infer(counts, method, monotone=False):
    """Return joint-issued lower bounds and one mutually exclusive status per batch.

    The bounded method conditions on fixed exogenous unit capacities (column zero).
    Its narrower FAR support requires a proved monotone alarm contrast.
    """
    counts = np.asarray(counts)
    if counts.ndim != 3 or counts.shape[1] < 1 or counts.shape[2] != 6:
        raise ValueError('Expected batch by independent unit by six integer counts')
    if method not in ('v3', 'cluster_t', 'bounded'):
        raise ValueError('Unknown method')
    if not np.issubdtype(counts.dtype, np.integer) or np.any(counts > 800) or np.any(counts < -800):
        raise ValueError('Expected integer counts within the 800-case frame')
    counts = counts.astype(np.int64, copy=False)
    d, c, f, h, n, delta = counts.transpose(2, 0, 1)
    if ((d <= 0).any() or (d.sum(axis=1) > 800).any()
            or (method == 'v3' and (counts.shape[1] > 200 or (d > 4).any()))
            or (c < 0).any() or (c > d).any() or (f < 0).any() or (n < 0).any()
            or (f + n > d).any() or (h < 0).any() or (h > np.minimum(f,c)).any()
            or (np.abs(delta) > n).any() or (monotone and (delta < 0).any())):
        raise ValueError('Inconsistent paired counts')
    batch, groups, _ = counts.shape
    lower = np.full((batch, 3), np.nan)
    status = np.full(batch, 'sparse_units', dtype='U24')
    selected = np.flatnonzero(((f > 0).sum(axis=1) >= 30) & ((n > 0).sum(axis=1) >= 30))
    if not len(selected):
        return lower, status
    data = counts[selected]
    status[selected] = 'issued'
    if method == 'v3':
        bounds, invalid, constant = _percentile(data)
        status[selected[constant]] = 'constant_bootstrap'
        status[selected[invalid]] = 'undefined_bootstrap'
    else:
        x, y = data[:, :, NUM].astype(float), data[:, :, DEN].astype(float)
        sx, sy = x.sum(axis=1), y.sum(axis=1)
        support = np.array([0., 0., 0. if monotone else -1.])
        if method == 'bounded':
            # Range of X-rY at the true r, per case: <=1 for Bernoulli
            # or monotone alarms and <=2 for an unrestricted signed contrast.
            penalty = np.sqrt(.5 * np.log(20) * (data[:, :, 0] ** 2).sum(axis=1))
            bounds = (sx - penalty[:, None] * (1-support)) / sy
        else:
            # Invert sum(X-rY) = t * sqrt(G * sample_variance(X-rY)).
            # Positive denominator separation makes the one-sided root unique.
            x -= x.mean(axis=1, keepdims=True)
            y -= y.mean(axis=1, keepdims=True)
            scale = critical(groups) ** 2 * groups / (groups - 1)
            xx = scale * (x*x).sum(axis=1)
            xy = scale * (x*y).sum(axis=1)
            yy = scale * (y*y).sum(axis=1)
            a = sy*sy - yy
            b = sx*sy - xy
            center = sx/sy
            zero_variance = np.max(np.abs(x - center[:, None, :]*y), axis=1) < 1e-10
            disc = b*b - a*(sx*sx - xx)
            with np.errstate(divide='ignore', invalid='ignore'):
                bounds = (b - np.sqrt(np.maximum(disc, 0))) / a
            status[selected[zero_variance.any(axis=1)]] = 'constant_score'
            status[selected[(a <= 0).any(axis=1)]] = 'weak_denominator'
        bounds = np.maximum(support, bounds)
    ready = status[selected] == 'issued'
    lower[selected[ready]] = bounds[ready]
    return lower, status
