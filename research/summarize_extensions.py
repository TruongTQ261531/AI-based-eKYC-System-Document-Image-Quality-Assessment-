"""Publish supplementary neural/partial-support summaries without new inference."""
import gzip
import json
import statistics
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from research.benchmark import save
from research.summarize_evidence import paired_interval


def describe(values):
    values=[v for v in values if v is not None]
    return dict(mean=statistics.mean(values) if values else None,
                split_sd=statistics.stdev(values) if len(values)>1 else None,defined_splits=len(values))


def main():
    root=Path('research/results');output=root/'evidence'
    rows=json.loads((root/'neural_baseline/summary.json').read_text())
    neural=[]
    for method in dict.fromkeys(r['method'] for r in rows):
        subset=[r for r in rows if r['source']=='all' and r['method']==method]
        neural.append(dict(method=method,**{k:describe([r[k] for r in subset]) for k in
            ('mean_iou','field_retention_98','utility_success','auto_accept','crop_harm_given_auto')}))
    save(output/'neural_all_seed_means.json',neural)
    rows=json.loads((root/'partial_support_v3/summary.json').read_text())
    partial=[]
    for method in dict.fromkeys(r['method'] for r in rows):
        subset=[r for r in rows if r['stratum']=='all' and r['method']==method]
        partial.append(dict(method=method,**{k:describe([r[k] for r in subset]) for k in
            ('auto_accept','harmful_auto','conditional_harm','accepted_utility','correct_field_auto','mean_iou','median_area_ratio')}))
    save(output/'partial_all_seed_means.json',partial)
    with gzip.open(root/'partial_support_v3/per_image.jsonl.gz','rt') as stream:
        first=[r for r in map(json.loads,stream) if r['seed']==13]
    rng=np.random.default_rng(2026102803);intervals=[]
    for result in partial:
        method=result['method']
        if method=='neural_original':continue
        for metric in ('auto_accept','harmful_auto','accepted_utility','correct_field_auto'):
            intervals.append(paired_interval(first,method,'neural_original',metric,rng))
    save(output/'partial_paired_bootstrap.json',intervals)
    fig,axes=plt.subplots(1,3,figsize=(13,4.5),constrained_layout=True)
    y=np.arange(len(partial))
    for ax,metric,title,color in zip(axes,('auto_accept','accepted_utility','harmful_auto'),
            ('Automatic coverage (%)','Accepted geometric utility (%)','Harmful auto / all frames (%)'),
            ('#087f8c','#42673c','#c97621')):
        ax.barh(y,[100*r[metric]['mean'] for r in partial],color=color,
                xerr=[100*(r[metric]['split_sd'] or 0) for r in partial],capsize=2)
        ax.set(yticks=y,yticklabels=[r['method'] for r in partial] if ax is axes[0] else [],xlabel=title)
        ax.invert_yaxis()
    fig.suptitle('Exactly-three-corner rescue: mean +/- split SD; same 700-image subset\nExploratory: missing corner is not reconstructed by support policies')
    for suffix in ('png','pdf'):fig.savefig(output/f'partial_support_tradeoff.{suffix}')
    plt.close(fig)
    print(json.dumps(dict(neural=neural,partial=partial),indent=2))


if __name__=='__main__':main()
