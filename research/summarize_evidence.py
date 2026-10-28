"""Generate tables, exploratory paired intervals and scientific figures."""
import gzip
import hashlib
import importlib.metadata
import json
import platform
import statistics
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from research.benchmark import save, digest

BASE = Path('research/results')


def load_rows(path):
    with gzip.open(path, 'rt', encoding='utf-8') as stream:
        return [json.loads(line) for line in stream]


def enrich(row):
    harm = row['field_retention'] is None or row['field_retention'] < .98
    return dict(row, harm=harm, harmful_auto=harm and row['auto_accept'],
                correct_field_auto=not harm and row['auto_accept'],
                accepted_utility=row['auto_accept'] and row['utility_success'])


def paired_interval(rows, method, reference, metric, rng):
    grouped = {}
    for row in rows:
        if row['method'] in (method, reference):
            grouped.setdefault((row['method'], row['physical_id']), []).append(row[metric])
    ids = sorted({group for name, group in grouped if name == method})
    delta = np.array([np.mean(grouped[(method, group)])-np.mean(grouped[(reference, group)]) for group in ids])
    boot = delta[rng.integers(0, len(delta), (2000, len(delta)))].mean(axis=1)
    return dict(method=method, reference=reference, metric=metric, physical_ids=len(ids),
                mean_paired_delta=float(delta.mean()), ci95=np.quantile(boot, [.025, .975]).tolist())


def main():
    output = BASE/'evidence'; output.mkdir(exist_ok=True)
    primary = json.loads((BASE/'feasibility_v1/summary.json').read_text())
    means = []
    for method in dict.fromkeys(row['method'] for row in primary):
        subset = [r for r in primary if r['method'] == method and r['source'] == 'all']
        result = dict(method=method)
        for metric in ('mean_iou', 'field_retention_98', 'median_area_ratio', 'utility_success', 'auto_accept'):
            values = [row[metric] for row in subset]
            result[metric] = dict(mean=statistics.mean(values), split_sd=statistics.stdev(values))
        means.append(result)
    save(output/'primary_all_seed_means.json', means)
    repeat = []
    for name in ('data_audit.json', 'splits.json', 'summary.json', 'summary.csv', 'paired_bootstrap.json', 'per_image.jsonl.gz'):
        original = BASE/'feasibility_v1'/name; repeated = BASE/'repeat'/name
        repeat.append(dict(file=name, identical=original.read_bytes() == repeated.read_bytes(), sha256=digest(original)))
    save(output/'analysis_repeat.json', dict(inference_repeated=False, new_inference_passes=0, files=repeat,
        metadata_note='Legacy repeat/run.json inference_passes=1 describes the cached experiment, not new inference.'))
    all_baseline_rows = [enrich(r) for r in load_rows(BASE/'feasibility_v1/per_image.jsonl.gz') if r['method'] in ('single', 'adaptive_uncalibrated')]
    raw = [r for r in all_baseline_rows if r['seed'] == 13]
    v2 = load_rows(BASE/'risk_policy_v2/per_image.jsonl.gz')
    rows = raw + [r for r in v2 if r['seed'] == 13]
    rng = np.random.default_rng(2026102802)
    intervals = []
    for method in dict.fromkeys(r['method'] for r in v2):
        for reference in ('single', 'adaptive_uncalibrated'):
            for metric in ('harmful_auto', 'auto_accept', 'correct_field_auto', 'accepted_utility'):
                intervals.append(paired_interval(rows, method, reference, metric, rng))
    save(output/'risk_policy_paired_bootstrap.json', intervals)
    ocr = json.loads((BASE/'ocr_diagnostic/per_field.json').read_text())
    ocr_intervals = []
    for engine in ('easyocr_en', 'vietocr'):
        for row in ocr:
            row['macro_cer'] = row['cer']
        subset = [r for r in ocr if r['engine'] == engine]
        for method in dict.fromkeys(r['method'] for r in subset if r['method'] != 'unmasked_oracle_field'):
            ocr_intervals.append(dict(engine=engine, **paired_interval(subset, method, 'unmasked_oracle_field', 'macro_cer', rng)))
    save(output/'ocr_paired_bootstrap.json', ocr_intervals)
    v2_summary = json.loads((BASE/'risk_policy_v2/summary.json').read_text())
    v2_means = []
    for method in dict.fromkeys(r['method'] for r in v2_summary):
        subset = [r for r in v2_summary if r['method'] == method and r['stratum'] == 'all']
        def describe(metric):
            values = [r[metric] for r in subset if r[metric] is not None]
            return dict(mean=statistics.mean(values) if values else None,
                        split_sd=statistics.stdev(values) if len(values)>1 else None,
                        defined_splits=len(values))
        v2_means.append(dict(method=method, **{metric: describe(metric)
                        for metric in ('harmful_auto', 'auto_accept', 'correct_field_auto', 'accepted_utility', 'conditional_harm')}))
    save(output/'risk_policy_all_seed_means.json', v2_means)
    versions = {}
    for name in ('numpy', 'opencv-python', 'opencv-python-headless', 'torch', 'easyocr', 'vietocr', 'matplotlib', 'pytest'):
        try: versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError: pass
    save(output/'environment.json', dict(python=platform.python_version(), platform=platform.platform(),
        processor=platform.processor(), packages=versions, device='CPU', new_dependencies_installed=False))
    plt.rcParams.update({'font.size': 10, 'figure.dpi': 160})
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), constrained_layout=True)
    labels = [r['method'].replace('calibrated_', 'CP_').replace('uncalibrated', 'raw') for r in means]
    x = np.arange(len(means))
    axes[0].barh(x, [100*r['field_retention_98']['mean'] for r in means], color='#087f8c')
    axes[0].set(yticks=x, yticklabels=labels, xlabel='Frames retaining >=98% of every visible text field (%)', xlim=(0, 105))
    axes[0].invert_yaxis()
    axes[1].barh(x, [r['median_area_ratio']['mean'] for r in means], color='#cf7620')
    axes[1].set(yticks=x, yticklabels=[], xlabel='Mean across splits of median crop / visible-card area', xlim=(0, 4.7))
    axes[1].invert_yaxis(); axes[1].axvline(1, color='gray', linestyle=':')
    fig.suptitle('Containment alone rewards large crops: all five fixed splits')
    for suffix in ('png', 'pdf'): fig.savefig(output/f'primary_tradeoff.{suffix}')
    plt.close(fig)
    baseline_means = []
    from research.risk_policy import aggregate
    for method in ('single', 'adaptive_uncalibrated'):
        stats = [aggregate([r for r in all_baseline_rows if r['method'] == method and r['seed'] == seed])
                 for seed in (13, 29, 47, 71, 97)]
        baseline_means.append(dict(method=method, **{key: dict(mean=statistics.mean(r[key] for r in stats),
            split_sd=statistics.stdev(r[key] for r in stats)) for key in
            ('auto_accept', 'harmful_auto', 'conditional_harm', 'correct_field_auto', 'accepted_utility')}))
    save(output/'baseline_policy_means.json', baseline_means)
    plotted = baseline_means + v2_means
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5), constrained_layout=True)
    y = np.arange(len(plotted))
    for ax, metric, color, title in zip(axes, ('auto_accept', 'harmful_auto'), ('#087f8c', '#cf7620'),
            ('Automatic-processing coverage (%)', 'Harmful automatic decisions / all frames (%)')):
        ax.barh(y, [100*r[metric]['mean'] for r in plotted], color=color,
                xerr=[100*(r[metric]['split_sd'] or 0) for r in plotted], capsize=2)
        ax.set(yticks=y, yticklabels=[r['method'] for r in plotted] if ax is axes[0] else [], xlabel=title)
        ax.invert_yaxis()
    axes[1].axvline(10, linestyle='--', color='#bd5324')
    fig.suptitle('Bounded-area review policies: mean +/- SD across five overlapping splits\n10% line is a marginal expected-risk target, not conditional accuracy')
    for suffix in ('png', 'pdf'): fig.savefig(output/f'risk_policy_tradeoff.{suffix}')
    plt.close(fig)
    print(json.dumps(v2_means, indent=2))


if __name__ == '__main__': main()
