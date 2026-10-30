"""All held-out outcomes, clustered uncertainty, schema and truncation audits."""
import csv
import gzip
import json
from collections import defaultdict

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from research.benchmark import save,digest
from research.e2e_eval import aggregate
from research.recovery_data import load_samples
from research.recovery_runtime import POLICIES,READERS
from research.recovery_selection import quality
from research.recovery_study import OUT,CACHE,METHODS,path_for
from research.recovery_semantic_eval import score_semantics
from research.recovery_visible_eval import score_visible


def paired_interval(rows,method,reader,source,metric='exact'):
    by=defaultdict(list)
    for row in rows:
        if row['repeat']!=1 or row['role']!='test' or row['source']!=source or row['engine']!=reader or row['policy'] not in (method,'completion'):continue
        value=quality(row) if metric=='exact' else row['timing']['total_wall']
        if value is not None:by[(row['policy'],row['physical_id'])].append(value)
    ids=sorted({identity for policy,identity in by if (method,identity) in by and ('completion',identity) in by})
    delta=np.array([np.mean(by[(method,g)])-np.mean(by[('completion',g)]) for g in ids])
    rng=np.random.default_rng(20261030);boot=delta[rng.integers(0,len(ids),(2000,len(ids)))].mean(axis=1)
    return dict(method=method,reader=reader,source=source,metric=metric,physical_ids=len(ids),
        mean_delta=float(delta.mean()),ci95=np.quantile(boot,[.025,.975]).tolist(),
        weighting='Equal physical-document means of per-image values',exploratory_no_multiplicity_correction=True)


def main():
    if not (OUT/'audit.json').exists():raise RuntimeError('Evaluate after locking selectors before analysis')
    with gzip.open(OUT/'per_image.jsonl.gz','rt') as stream:rows=[json.loads(line) for line in stream]
    summary=json.loads((OUT/'summary.json').read_text());models=json.loads((OUT/'selector_models.json').read_text())
    samples=load_samples();lookup={s['uid']:s for s in samples}
    # Alphabet compatibility is a diagnostic only; keep the complete locked
    # target set regardless of unsupported characters.
    from research.recovery_runtime import RecoveryEngine
    from research.e2e_eval import target_fields
    from research.ocr_diagnostic import normalized
    baseline=RecoveryEngine();alphabet=[]
    for reader in READERS:
        characters=baseline.readers[reader].text_rec.postprocess_op.character
        supported=set(normalized(''.join(c for c in characters if c!='blank')))|{' '}
        for source in ('authored_specimen','midv2020_derived'):
            selected=[s for s in samples if s['role']=='test' and s['source']==source]
            targets=[f for s in selected for f in target_fields(s)[0]]
            alphabet.append(dict(reader=reader,source=source,fields=len(targets),
                fully_supported_fields=sum(all(c in supported for c in normalized(f['text'])) for f in targets),
                target_set_redefined=False))
    save(OUT/'alphabet_coverage.json',alphabet)
    del baseline
    for reader in READERS:
        used=set(models['selectors'][reader]['training_ids']);test={s['physical_id'] for s in samples if s['role']=='test'}
        if used&test:raise ValueError('Test identity in model fitting provenance')
    intervals=[paired_interval(rows,method,reader,source,metric) for source in ('authored_specimen','midv2020_derived')
               for reader in READERS for method in POLICIES+METHODS if method!='completion' for metric in ('exact','wall')]
    save(OUT/'paired_bootstrap.json',intervals)
    with (OUT/'summary.csv').open('w',encoding='utf-8',newline='') as stream:
        keys=list(dict.fromkeys(key for r in summary for key in r));writer=csv.DictWriter(stream,fieldnames=keys)
        writer.writeheader();writer.writerows(summary)
    slices=[]
    for reader in READERS:
        for method in POLICIES+METHODS:
            selected=[r for r in rows if r['repeat']==1 and r['role']=='test' and r['engine']==reader and r['policy']==method]
            for key in ('capture','unseen_layout','observed_corners'):
                for value in sorted({str(r[key]) for r in selected}):
                    subset=[r for r in selected if str(r[key])==value]
                    slices.append(dict(reader=reader,method=method,slice_key=key,slice_value=value,**aggregate(subset)))
    save(OUT/'test_slices.json',slices)
    canonical=[];visible=[];truncation=[];curves=[]
    private={}
    for s in samples:
        if s['source']!='authored_specimen':continue
        record=json.loads(path_for(1,s['uid']).read_text(encoding='utf-8'))
        private[s['uid']]={(r['engine'],r['policy']):r for r in record['rows']}
    for row in rows:
        if row['repeat']!=1 or row['source']!='authored_specimen':continue
        policy=row.get('chosen_policy',row['policy']);sample=lookup[row['uid']]
        predicted=private[row['uid']][(row['engine'],policy)]['_private_semantic']
        visible.append(dict(uid=row['uid'],reader=row['engine'],method=row['policy'],role=row['role'],
            **score_visible(sample,private[row['uid']][(row['engine'],policy)]['_private_predictions'])))
        judged=score_semantics(sample,predicted)
        correct_by_key={f['field_key']:f['exact'] for f in row['score']['fields']}
        judged['transcription_correct_semantic_wrong']=sum(correct_by_key.get(f['field_key'],False) and not f['exact'] for f in judged['fields'])
        canonical.append(dict(uid=row['uid'],reader=row['engine'],method=row['policy'],role=row['role'],**judged))
    save(OUT/'canonical_semantics.json',canonical)
    save(OUT/'visible_transcription.json',visible)
    schema=[]
    for role in ('development','calibration','test'):
        for reader in READERS:
            for method in POLICIES+METHODS:
                selected=[r for r in canonical if r['role']==role and r['reader']==reader and r['method']==method]
                n=sum(r['eligible_fields'] for r in selected)
                schema.append(dict(role=role,reader=reader,method=method,fields=n,
                    canonical_exact=sum(r['canonical_exact'] for r in selected)/max(n,1),
                    literal_exact=sum(r['literal_exact'] for r in selected)/max(n,1),
                    transcription_correct_semantic_wrong=sum(r['transcription_correct_semantic_wrong'] for r in selected)))
    save(OUT/'canonical_semantic_summary.json',schema)
    visible_summary=[]
    for reader in READERS:
        for method in POLICIES+METHODS:
            selected=[r for r in visible if r['role']=='test' and r['reader']==reader and r['method']==method]
            for scope in ('all_visible_references','partially_captured_fields'):
                fields=[f for r in selected for f in r['fields'] if scope=='all_visible_references' or f['partial']]
                n=len(fields);chars=sum(f['reference_length'] for f in fields)
                visible_summary.append(dict(reader=reader,method=method,scope=scope,fields=n,
                    exact=sum(f['exact'] for f in fields)/max(n,1),micro_cer=sum(f['edit_distance'] for f in fields)/max(chars,1)))
    save(OUT/'visible_transcription_summary.json',visible_summary)
    for source in ('authored_specimen','midv2020_derived'):
        for reader in READERS:
            for method in POLICIES+METHODS:
                selected=[r for r in rows if r['repeat']==1 and r['role']=='test' and r['source']==source and r['engine']==reader and r['policy']==method]
                partial=[r for r in selected if any(f['geometric_visibility']<.995 for f in lookup[r['uid']]['fields'])]
                accepted=[r for r in selected if not r.get('review_recommended',not r['routed'])]
                retained_partial=[r for r in partial if r in accepted]
                truncation.append(dict(source=source,reader=reader,method=method,images=len(selected),
                    retained=len(accepted),geometrically_partial=len(partial),retained_partial=len(retained_partial),
                    retained_partial_fraction=len(retained_partial)/max(len(accepted),1),
                    truncation_review_recall=1-len(retained_partial)/len(partial) if partial else None,
                    interpretation='Geometric diagnostic, not legal document validity or human legibility'))
                if method not in METHODS:continue
                total=sum(r['score']['eligible_fields'] for r in selected)
                for threshold in (0.,.25,.5,.75,.9,.95):
                    kept=[r for r in selected if r['routed'] and r['features'][6]>=threshold];fields=[f for r in kept for f in r['score']['fields']]
                    curves.append(dict(source=source,reader=reader,method=method,threshold=threshold,retention=len(kept)/len(selected),
                        conditional_exact=float(np.mean([f['exact'] for f in fields])) if fields else None,
                        correct_field_yield=sum(f['exact'] for f in fields)/max(total,1),test_threshold_selected=False))
    save(OUT/'truncation_diagnostics.json',truncation);save(OUT/'review_curves.json',curves)
    primary=[r for r in summary if r['role']=='test' and r['reader']=='rapid_latin_v5']
    names=['raw','completion','bbox','max_confidence',models['selectors']['rapid_latin_v5']['primary_method']]
    titles={'raw':'Raw','completion':'Completion +5%','bbox':'Support bbox','max_confidence':'Max confidence',names[-1]:'Locked cascade'}
    fig,axes=plt.subplots(1,2,figsize=(12,4.8),constrained_layout=True)
    for ax,source in zip(axes,('authored_specimen','midv2020_derived')):
        chosen=[next(r for r in primary if r['source']==source and r['method']==name) for name in names]
        ax.bar(np.arange(len(names)),[100*r['field_exact'] for r in chosen],color=['#a1b2ba']*4+['#0a7076'])
        ax.set(xticks=np.arange(len(names)),xticklabels=[titles[n] for n in names],ylabel='Pooled visible-field exact (%)',title=source,ylim=(0,100))
        ax.tick_params(axis='x',rotation=25)
    fig.suptitle('Held-out identities / Latin PP-OCRv5; primary cascade selected on development')
    for ext in ('png','pdf'):fig.savefig(OUT/('test_accuracy.'+ext))
    plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(12,4.8),constrained_layout=True)
    for ax,source in zip(axes,('authored_specimen','midv2020_derived')):
        chosen=[next(r for r in primary if r['source']==source and r['method']==name) for name in names]
        ax.bar(np.arange(len(names)),[r['mean_wall_seconds'] for r in chosen],color=['#a1b2ba']*4+['#0a7076'])
        ax.set(xticks=np.arange(len(names)),xticklabels=[titles[n] for n in names],ylabel='Measured / reconstructed trace wall (s/image)',title=source)
        ax.tick_params(axis='x',rotation=25)
    fig.suptitle('Exhaustive candidates: selector costs reconstructed; fresh online times reported separately')
    for ext in ('png','pdf'):fig.savefig(OUT/('trace_cost.'+ext))
    plt.close(fig)
    save(OUT/'analysis_provenance.json',dict(code_sha256=digest(__file__),rows_sha256=digest(OUT/'per_image.jsonl.gz'),
        canonical_evaluator_sha256=digest('research/recovery_semantic_eval.py'),
        visible_evaluator_sha256=digest('research/recovery_visible_eval.py'),
        addendum_sha256=digest('research/RECOVERY_EVALUATION_ADDENDUM.md'),bootstrap_resamples=2000,
        trained_test_id_overlap=0,multiple_comparison_correction=False))
    print('RECOVERY_ANALYSIS_COMPLETE',len(rows),'rows',flush=True)


if __name__=='__main__':main()
