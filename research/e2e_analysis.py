"""Report all policies/readers/repeats, clustered uncertainty and review curves."""
import csv
import gzip
import json
import statistics
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from research.benchmark import digest,save
from research.e2e_eval import aggregate
from research.e2e_pipeline import POLICIES

ROOT=Path('research/results/e2e_ocr_v2')


def scalar(row,metric):
    if metric=='total_wall':return row['timing']['total_wall']
    fields=row['score']['fields']
    if not fields:return None
    if metric=='field_exact':return float(np.mean([f['exact'] for f in fields]))
    if metric=='macro_cer':return float(np.mean([f['cer'] for f in fields]))
    raise KeyError(metric)


def paired_bootstrap(rows,policy,reader,metric,test_ids,rng,reference='raw_fullframe',stratum=None):
    grouped=defaultdict(list)
    for row in rows:
        if row['repeat']!=1 or row['source']=='midv2020' or row['physical_id'] not in test_ids or row['engine']!=reader:continue
        if stratum is not None and row['selection_stratum']!=stratum:continue
        if row['policy'] not in (policy,reference):continue
        value=scalar(row,metric)
        if value is not None:grouped[(row['policy'],row['physical_id'])].append(value)
    ids=[g for g in sorted(test_ids) if (policy,g) in grouped and (reference,g) in grouped]
    if not ids:raise ValueError('No paired physical IDs for bootstrap')
    delta=np.array([np.mean(grouped[(policy,g)])-np.mean(grouped[(reference,g)]) for g in ids])
    bootstrap=delta[rng.integers(0,len(delta),(2000,len(delta)))].mean(axis=1)
    return dict(policy=policy,reference=reference,engine=reader,metric=metric,physical_ids=len(ids),stratum=stratum,
        mean_paired_delta=float(delta.mean()),ci95=np.quantile(bootstrap,[.025,.975]).tolist(),
        weighting=('Equal physical-ID means of per-image latencies' if metric=='total_wall' else
                   'Equal physical-ID means of per-image field means; differs from pooled-field tables'),
        interpretation='Exploratory paired ID-level interval; no multiplicity correction')


def main():
    with gzip.open(ROOT/'per_image.jsonl.gz','rt',encoding='utf-8') as stream:rows=[json.loads(line) for line in stream]
    summary=json.loads((ROOT/'summary.json').read_text())
    with (ROOT/'summary.csv').open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(summary[0]));writer.writeheader();writer.writerows(summary)
    # Compare exactly the same panel in all three passes; do not average full
    # pass161 with the two smaller32-image passes.
    manifest=json.loads((ROOT/'manifest.json').read_text())
    panel=set(manifest['replication_uids']);matched_summary=[]
    for repeat in (1,2,3):
        for policy in POLICIES:
            for reader in ('easyocr_en','vietocr'):
                selected=[r for r in rows if r['uid'] in panel and r['repeat']==repeat and r['policy']==policy and r['engine']==reader]
                for stratum in ('primary','three_corners','four_corner_control','external'):
                    subset=[r for r in selected if r['source']!='midv2020'] if stratum=='primary' else [r for r in selected if r['selection_stratum']==stratum]
                    matched_summary.append(dict(repeat=repeat,policy=policy,engine=reader,stratum=stratum,**aggregate(subset)))
    save(ROOT/'matched_repeat_summary.json',matched_summary)
    means=[]
    for stratum in ('primary','three_corners','four_corner_control','external'):
        for reader in ('easyocr_en','vietocr'):
            for policy in POLICIES:
                subset=[r for r in matched_summary if r['stratum']==stratum and r['engine']==reader and r['policy']==policy]
                result=dict(stratum=stratum,engine=reader,policy=policy)
                for metric in ('field_exact','micro_cer','macro_cer','routed_fraction','geometry_review_fraction','no_text_fraction',
                               'digit_field_exact','conditional_field_exact','mean_wall_seconds','p95_wall_seconds','mean_cpu_seconds'):
                    values=[r[metric] for r in subset if r[metric] is not None]
                    result[metric]=dict(mean=statistics.mean(values) if values else None,
                        repeat_sd=statistics.stdev(values) if len(values)>1 else None)
                means.append(result)
    save(ROOT/'matched_repeat_means.json',means)
    splits=json.loads(Path('research/results/feasibility_v1/splits.json').read_text());split_results=[]
    for split in splits:
        for reader in ('easyocr_en','vietocr'):
            for policy in POLICIES:
                selected=[r for r in rows if r['repeat']==1 and r['source']!='midv2020' and r['engine']==reader and
                          r['policy']==policy and r['physical_id'] in split['test_ids']]
                split_results.append(dict(seed=split['seed'],engine=reader,policy=policy,**aggregate(selected)))
    save(ROOT/'five_id_split_descriptive.json',split_results)
    rng=np.random.default_rng(20261030);intervals=[]
    for reader in ('easyocr_en','vietocr'):
        for policy in POLICIES[1:]:
            for metric in ('field_exact','macro_cer','total_wall'):
                intervals.append(paired_bootstrap(rows,policy,reader,metric,set(splits[0]['test_ids']),rng))
    save(ROOT/'paired_bootstrap.json',intervals)
    # Mechanism controls: a gain over strict rejection alone cannot identify a
    # benefit from support masking/cropping. Pre-outcome supplementary plan.
    rng=np.random.default_rng(20261031);mechanism=[]
    for reader in ('easyocr_en','vietocr'):
        for policy,reference in (('three_support','three_fullframe'),
                                 ('three_support_bbox','three_fullframe'),
                                 ('three_parallelogram05','three_fullframe'),
                                 ('three_support','three_support_bbox'),
                                 ('three_support','three_parallelogram05')):
            for metric in ('field_exact','macro_cer','total_wall'):
                mechanism.append(paired_bootstrap(rows,policy,reader,metric,set(splits[0]['test_ids']),rng,
                                                  reference=reference,stratum='three_corners'))
    save(ROOT/'mechanism_bootstrap.json',mechanism)
    curves=[]
    for reader in ('easyocr_en','vietocr'):
        for policy in POLICIES:
            for stratum in ('primary','three_corners','external'):
                selected=[r for r in rows if r['repeat']==1 and r['engine']==reader and r['policy']==policy and
                    (r['source']!='midv2020' if stratum=='primary' else r['selection_stratum']==stratum)]
                total=sum(r['score']['eligible_fields'] for r in selected)
                for threshold in (0.,.25,.5,.75,.9,.95):
                    accepted=[r for r in selected if r['routed'] and r['score']['any_text'] and r['score']['median_confidence']>=threshold]
                    fields=[f for r in accepted for f in r['score']['fields']]
                    curves.append(dict(engine=reader,policy=policy,stratum=stratum,confidence_threshold=threshold,
                        retained_images=len(accepted),all_images=len(selected),review_proxy_fraction=1-len(accepted)/len(selected),
                        conditional_field_exact=float(np.mean([f['exact'] for f in fields])) if fields else None,
                        correct_field_yield=sum(f['exact'] for f in fields)/total if total else None,
                        production_threshold_selected=False))
    save(ROOT/'confidence_review_curves.json',curves)
    failures=[]
    for reader in ('easyocr_en','vietocr'):
        for policy in POLICIES:
            selected=[r for r in rows if r['repeat']==1 and r['engine']==reader and r['policy']==policy]
            fields=[f for r in selected for f in r['score']['fields']]
            failures.append(dict(engine=reader,policy=policy,geometry_review_images=sum(not r['routed'] for r in selected),
                routed_no_text_images=sum(r['routed'] and not r['score']['any_text'] for r in selected),
                missed_target_fields=sum(not f['detected'] for f in fields),
                detected_wrong_fields=sum(f['detected'] and not f['exact'] for f in fields),
                truncated_regions=sum(r['truncated_regions'] for r in selected),
                gt_corner_visibility={str(k):sum(r['score']['gt_visible_corners']==k for r in selected) for k in range(5)}))
    save(ROOT/'failure_breakdown.json',failures)
    corner_rows=[r for r in rows if r['repeat']==1 and r['engine']=='easyocr_en' and
                 r['policy']=='raw_fullframe' and r['selection_stratum']=='three_corners']
    save(ROOT/'corner_visibility.json',dict(neural_three_corner_images=len(corner_rows),
        ground_truth_visible_corner_counts={str(k):sum(r['score']['gt_visible_corners']==k for r in corner_rows) for k in range(5)},
        interpretation='Neural observed-corner count is a prediction, not GT physical corner visibility'))
    full=[r for r in summary if r['repeat']==1]
    fig,axes=plt.subplots(1,2,figsize=(12,5),constrained_layout=True)
    for ax,reader in zip(axes,('easyocr_en','vietocr')):
        selected=[r for r in full if r['engine']==reader and r['stratum']=='three_corners']
        x=np.arange(len(selected));ax.bar(x,[100*r['field_exact'] for r in selected],color='#087f8c')
        labels={'raw_fullframe':'raw full frame','neural_strict':'strict reject',
                'three_fullframe':'3-corner full frame','three_support':'support mask',
                'three_support_bbox':'support bbox','three_parallelogram05':'parallelogram +5%'}
        ax.set(xticks=x,xticklabels=[labels[r['policy']] for r in selected],
               ylabel='Exact transcription of evaluable fields (%)',title=reader)
        ax.tick_params(axis='x',rotation=35)
    fig.suptitle('Prediction-only end-to-end OCR on the 91 three-corner cases\nSpatial transcription evaluation; not semantic field labeling')
    for suffix in ('png','pdf'):fig.savefig(ROOT/f'field_accuracy.{suffix}')
    plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(12,5),constrained_layout=True)
    for ax,reader in zip(axes,('easyocr_en','vietocr')):
        selected=[r for r in full if r['engine']==reader and r['stratum']=='primary']
        for result in selected:
            ax.scatter(result['mean_wall_seconds'],100*result['field_exact'],s=40)
        ax.set(xlabel='Mean measured CPU-pipeline wall time (seconds/image)',ylabel='Exact field transcription (%)',title=reader)
        for index,result in enumerate(selected):
            offset=(-22,13) if result['policy']=='three_support' else (10,-15) if result['policy']=='three_support_bbox' else (4,4)
            ax.annotate(str(index+1),(result['mean_wall_seconds'],100*result['field_exact']),xytext=offset,
                        textcoords='offset points',arrowprops={'arrowstyle':'-','linewidth':.5} if index in (3,4) else None)
        ax.margins(x=.12,y=.1)
        ax.text(.02,.98,'\n'.join(f'{i+1}: {r["policy"]}' for i,r in enumerate(selected)),transform=ax.transAxes,va='top',fontsize=8)
    fig.suptitle('Full first pass: 141 primary images; support and bbox nearly coincide')
    for suffix in ('png','pdf'):fig.savefig(ROOT/f'accuracy_latency.{suffix}')
    plt.close(fig)
    save(ROOT/'analysis_provenance.json',dict(code_sha256=digest(__file__),input_rows_sha256=digest(ROOT/'per_image.jsonl.gz'),
         bootstrap_resamples=2000,bootstrap_unit='physical_document',bootstrap_test_seed=13,
         supplementary_plan_sha256=digest('research/E2E_ANALYSIS_PLAN.md'),
         repeats_are_independent_samples=False,semantic_kie_evaluated=False))
    print('ANALYSIS_COMPLETE',len(rows),'rows')


if __name__=='__main__':main()
