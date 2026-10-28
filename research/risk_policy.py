"""Exploratory document-balanced risk control with bounded-area review."""
import argparse
import csv
import gzip
import hashlib
import json
import math
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

from research.benchmark import SEEDS, metrics, save, digest, scale_sets
from research.support_regions import expand_region, area

GRID = (0., .25, .5, .75, 1., 1.5, 2., 3., 4., 6., 8., 12., 16., 32., math.inf)
RULES = ('erm_cap', 'crc_cap', 'crc_uncapped', 'frame_crc_cap')


def choose_index(losses, alpha=.1, correction=True):
    """Rows are exchangeable units, columns a fixed ordered policy family."""
    losses = np.asarray(losses, float)
    if losses.ndim != 2 or not len(losses) or not np.isfinite(losses).all():
        raise ValueError('Nonempty finite loss matrix required')
    if not 0 < alpha < 1 or (losses < 0).any() or (losses > 1).any():
        raise ValueError('Bounded losses and alpha in (0,1) required')
    if (np.diff(losses, axis=1) > 1e-12).any():
        raise ValueError('Loss family is not monotone')
    risk = (losses.sum(axis=0) + 1) / (len(losses) + 1) if correction else losses.mean(axis=0)
    eligible = np.flatnonzero(risk <= alpha)
    # Always-review endpoint is safe even if finite-sample correction cannot
    # certify it with fewer than 9 calibration units at alpha=.1.
    index = int(eligible[0]) if len(eligible) else losses.shape[1] - 1
    return index, float(risk[index]), bool(len(eligible))


def row_for(sample, pred, scale_name, amount):
    constant, adaptive = scale_sets(pred)
    scales = np.asarray(constant if scale_name == 'constant' else adaptive)
    family_pred = dict(pred, scales=scales.tolist())
    # Reuse the frozen v1 metrics/region construction, changing only lambda.
    row = metrics(sample, family_pred, 'calibrated_adaptive', {'adaptive': amount})
    if math.isinf(amount):
        row['auto_accept'] = False
    row['harm'] = row['field_retention'] is None or row['field_retention'] < .98
    row['harmful_auto'] = row['auto_accept'] and row['harm']
    row['correct_field_auto'] = row['auto_accept'] and not row['harm']
    row['accepted_utility'] = row['auto_accept'] and row['utility_success']
    return row


def evaluate_sample(args):
    sample, pred = args
    return {family: [row_for(sample, pred, family, value) for value in GRID]
            for family in ('constant', 'adaptive')}


def aggregate(rows):
    by_id = {}
    for row in rows:
        by_id.setdefault(row['physical_id'], []).append(row)
    keys = ('harmful_auto', 'auto_accept', 'correct_field_auto', 'accepted_utility', 'harm')
    result = {key: float(np.mean([np.mean([r[key] for r in group]) for group in by_id.values()])) for key in keys}
    accepted = [row for row in rows if row['auto_accept']]
    visible = [row for row in rows if row['visible']]
    result.update(n=len(rows), physical_ids=len(by_id),
        conditional_harm=float(np.mean([r['harm'] for r in accepted])) if accepted else None,
        mean_iou=float(np.mean([r['iou'] for r in visible])),
        median_area_ratio=float(np.median([r['area_ratio'] for r in visible])),
        invisible_auto=sum(r['auto_accept'] for r in rows if not r['visible']))
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=Path('research/results/risk_policy_v2'))
    parser.add_argument('--workers', type=int, default=3)
    args = parser.parse_args(); args.output.mkdir(parents=True, exist_ok=True)
    samples = json.loads(Path('research/data/primary_samples.json').read_text(encoding='utf-8'))
    predictions = {r['uid']: r for r in map(json.loads, Path('research/cache/predictions.jsonl').read_text().splitlines())}
    splits = json.loads(Path('research/results/feasibility_v1/splits.json').read_text())
    started = time.monotonic()
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        grids = list(pool.map(evaluate_sample, [(s, predictions[s['uid']]['prediction']) for s in samples], chunksize=10))
    print(f'Computed {len(samples)} frames x 2 scale families x {len(GRID)} policies', flush=True)
    for family in ('constant', 'adaptive'):
        for grid in grids:
            for key in ('harm', 'harmful_auto', 'auto_accept'):
                if (np.diff([int(r[key]) for r in grid[family]]) > 0).any():
                    raise ValueError(f'Non-monotone {family}/{key} on {grid[family][0]["uid"]}')
    all_rows, summaries, choices = [], [], []
    for split in splits:
        cal_indices = [i for i, s in enumerate(samples) if s['physical_id'] in split['calibration_ids']]
        test_indices = [i for i, s in enumerate(samples) if s['physical_id'] in split['test_ids']]
        for family in ('constant', 'adaptive'):
            for rule in RULES:
                target = 'harm' if rule == 'crc_uncapped' else 'harmful_auto'
                matrix = np.asarray([[r[target] for r in grids[i][family]] for i in cal_indices], float)
                grouped = np.asarray([matrix[[j for j, i in enumerate(cal_indices) if samples[i]['physical_id'] == group]].mean(axis=0)
                                      for group in split['calibration_ids']])
                index, corrected, certified = choose_index(matrix if rule == 'frame_crc_cap' else grouped,
                                                            correction=rule != 'erm_cap')
                method = family + '_' + rule
                choices.append(dict(seed=split['seed'], method=method, parameter=GRID[index] if np.isfinite(GRID[index]) else 'infinity',
                    calibration_group_loss=float(grouped[:, index].mean()), criterion=corrected,
                    finite_grid_criterion_met=certified, calibration_ids=split['calibration_ids'], test_ids=split['test_ids']))
                rows = [dict(grids[i][family][index], method=method, seed=split['seed']) for i in test_indices]
                all_rows.extend(rows)
                for source in ('all', 'midv500', 'midv2019'):
                    subset = rows if source == 'all' else [r for r in rows if r['source'] == source]
                    summaries.append(dict(seed=split['seed'], method=method, stratum=source, **aggregate(subset)))
                for quality in ('Clean', 'Blur', 'Cropped', 'Dark', 'Distorted'):
                    summaries.append(dict(seed=split['seed'], method=method, stratum=quality,
                        **aggregate([r for r in rows if r['quality_label'] == quality])))
        print(f'Evaluated v2 seed {split["seed"]}', flush=True)
    save(args.output/'choices.json', choices); save(args.output/'summary.json', summaries)
    with (args.output/'summary.csv').open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(summaries[0])); writer.writeheader(); writer.writerows(summaries)
    with (args.output/'per_image.jsonl.gz').open('wb') as target, gzip.GzipFile(fileobj=target, mode='wb', mtime=0, filename='') as compressed:
        for row in all_rows: compressed.write((json.dumps(row, allow_nan=False)+'\n').encode())
    save(args.output/'run.json', dict(protocol_sha256=digest('research/RISK_POLICY_PROTOCOL.md'),
        code_sha256=digest(__file__), primary_predictions_sha256=digest('research/cache/predictions.jsonl'),
        grids_evaluated=len(samples)*2*len(GRID), distinct_images=len(samples), seeds=list(SEEDS),
        new_model_inference_passes=0, training_runs=0, monotonicity_violations=0,
        elapsed_seconds=round(time.monotonic()-started, 2), exploratory_after_v1=True))
    print('V2_COMPLETE', flush=True)


if __name__ == '__main__': main()
