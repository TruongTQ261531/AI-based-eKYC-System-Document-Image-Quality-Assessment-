"""Post-hoc descriptive reference-policy transitions; never selects a model."""
from collections import Counter
import hashlib
import numpy as np
from research.v3_common import *
from research.v3_metrics import scoring as source_score,summary as source_summary,canonical
from research.v2_runtime import scoring as body_score,summary as body_summary
from research.v2_metrics import canonical as body_canonical
from research.v3_fusion import MODELS,BASES


def contract_interactions():
    """Exploratory paired difference of reported training gains, same outputs."""
    records={kind:{key:read(folder/f'test_{key}.json') for key in
        ('control_42','partial_42','control_31415','partial_31415')}
        for kind,folder in [('body',R2OUT),('source',OUT)]}
    first=records['source']['partial_42']['rows'];ids=sorted({r['physical_id'] for r in first})
    origins={r['physical_id']:r['source'] for r in first};rng=np.random.default_rng(20261103)
    draws=np.concatenate([rng.choice([i for i,p in enumerate(ids) if origins[p]==s],(10000,24),replace=True)
        for s in ('authored','midv2020')],axis=1)
    distributions={}
    for kind,models in records.items():
        distributions[kind]={}
        for key,value in models.items():
            if {r['physical_id'] for r in value['rows']}!=set(ids):raise ValueError('Interaction ID coverage differs')
            a=np.array([[sum(r[f] for r in value['rows'] if r['physical_id']==pid)
                for f in ('correct','reference','predicted')] for pid in ids])[draws].sum(axis=1)
            distributions[kind][key]=2*a[:,0]/np.maximum(a[:,1]+a[:,2],1)
    rows=[]
    for seed in (42,31415):
        part='partial_'+str(seed);control='control_'+str(seed);gains={}
        for kind in records:
            gains[kind]=records[kind][part]['summary']['f1']-records[kind][control]['summary']['f1']
        sample=(distributions['source'][part]-distributions['source'][control])-(distributions['body'][part]-distributions['body'][control])
        rows.append(dict(seed=seed,body_contract_gain=gains['body'],source_contract_gain=gains['source'],
            gain_change=gains['source']-gains['body'],ci95_low=float(np.percentile(sample,2.5)),ci95_high=float(np.percentile(sample,97.5))))
    return dict(post_hoc_exploratory=True,used_for_model_selection=False,new_generation_calls=0,
        seed=20261103,resamples=10000,independent_document_instances=48,source_stratified=True,
        intervals_are_not_multiplicity_adjusted=True,definition='(partial-control F1 under source) minus (partial-control F1 under body)',rows=rows)

def run():
    if read(OUT/'audit.json')['status']!='passed':raise ValueError('Audited test outputs required')
    source={r['uid']:r for r in load('test')};body={r['uid']:r for r in read(R2DATA/'samples.json') if r['role']=='test'}
    additions=Counter();reference_changes=Counter()
    for uid,row in source.items():
        previous=body[uid]
        for key in set(row['target'])-set(previous['target']):
            kinds={('MRZ' if ref['source'].startswith('mrz_') else 'body') for ref in row['source_refs'][key]}
            additions['+'.join(sorted(kinds))]+=1
        reference_changes[row['capture']]+=row['target']!=previous['target']
    result={}
    for model in MODELS:
        cache=R2CACHE if model in BASES else CACHE;old_rows=[];new_rows=[];transitions=Counter();limit_hits=0;generated=[]
        for uid,row in source.items():
            private=read(cache/'predictions'/f'test_{model}'/(hashlib.sha256(uid.encode()).hexdigest()+'.json'));raw=private['_private_text']
            limit_hits+=bool(private['hit_token_limit']);generated.append(private['generated_tokens'])
            old,fields=body_score(body[uid],raw);old['hit_token_limit']=private['hit_token_limit']
            new,_=source_score(row,raw);old_rows.append(old);new_rows.append(new)
            for key in set(body[uid]['target'])|set(row['target'])|set(fields):
                def status(refs,match):
                    if key not in refs:return 'outside_contract' if key in fields else 'not_requested'
                    if key not in fields:return 'omitted'
                    return 'correct' if match else 'wrong_value'
                old_hit=key in fields and any(body_canonical(key,fields[key])==body_canonical(key,v) for v in body[uid]['accepted_values'].get(key,[]))
                new_hit=key in fields and any(canonical(key,fields[key])==canonical(key,ref['value'],ref['kind']) for ref in row['source_refs'].get(key,[]))
                transitions[status(body[uid]['target'],old_hit)+' -> '+status(row['target'],new_hit)]+=1
        a=body_summary(old_rows);b=source_summary(new_rows)
        if b!=read(OUT/f'test_{model}.json')['summary']:raise ValueError('Descriptive source replay differs from audited table')
        new_count=sum(additions.values());new_correct=transitions['outside_contract -> correct']
        new_wrong=transitions['outside_contract -> wrong_value'];new_missing=transitions['not_requested -> omitted']
        if new_correct+new_wrong+new_missing!=new_count:raise ValueError('New-reference decomposition differs')
        result[model]=dict(body_contract_f1=a['f1'],source_contract_f1=b['f1'],max_precision_f1=b['max_precision_f1'],
            test_generations=len(new_rows),generation_token_limit=CONFIG['generation_max_new_tokens'],token_limit_hits=limit_hits,
            median_generated_tokens=__import__('statistics').median(generated),
            newly_supported_reference_fields=new_count,newly_supported_wrong_values=new_wrong,
            newly_supported_recall=new_correct/max(1,new_count),
            body_outside_contract=a['unsupported_nonempty'],source_outside_contract=b['unsupported_nonempty'],
            formerly_outside_now_correct=transitions['outside_contract -> correct'],
            newly_supported_but_omitted=transitions['not_requested -> omitted'],transitions=dict(transitions))
    interactions=contract_interactions();save(OUT/'reference_policy_interactions.json',interactions)
    data=dict(signature=signature(),post_hoc_descriptive=True,used_for_model_selection=False,new_model_inference_calls=0,
        training_gain_contract_interactions=interactions,
        source_test_reference_fields=sum(len(r['target']) for r in source.values()),
        body_test_reference_fields=sum(len(r['target']) for r in body.values()),
        added_reference_origins=dict(additions),changed_reference_cases_by_capture=dict(reference_changes),models=result,
        new_reference_subset_analysis_post_hoc=True,new_reference_fields_are_not_independent_identities=True,
        diagnostics_code_sha256=sha(ROOT/'research/v3_diagnostics.py'))
    save(OUT/'reference_policy_diagnostics.json',data)
    return data

if __name__=='__main__':run()
