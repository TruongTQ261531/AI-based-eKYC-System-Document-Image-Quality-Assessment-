"""Post-hoc descriptive reference-policy transitions; never selects a model."""
from collections import Counter
import hashlib
from research.v3_common import *
from research.v3_metrics import scoring as source_score,summary as source_summary,canonical
from research.v2_runtime import scoring as body_score,summary as body_summary
from research.v2_metrics import canonical as body_canonical
from research.v3_fusion import MODELS,BASES

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
        cache=R2CACHE if model in BASES else CACHE;old_rows=[];new_rows=[];transitions=Counter()
        for uid,row in source.items():
            private=read(cache/'predictions'/f'test_{model}'/(hashlib.sha256(uid.encode()).hexdigest()+'.json'));raw=private['_private_text']
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
        result[model]=dict(body_contract_f1=a['f1'],source_contract_f1=b['f1'],max_precision_f1=b['max_precision_f1'],
            body_outside_contract=a['unsupported_nonempty'],source_outside_contract=b['unsupported_nonempty'],
            formerly_outside_now_correct=transitions['outside_contract -> correct'],
            newly_supported_but_omitted=transitions['not_requested -> omitted'],transitions=dict(transitions))
    data=dict(signature=signature(),post_hoc_descriptive=True,used_for_model_selection=False,new_model_inference_calls=0,
        source_test_reference_fields=sum(len(r['target']) for r in source.values()),
        body_test_reference_fields=sum(len(r['target']) for r in body.values()),
        added_reference_origins=dict(additions),changed_reference_cases_by_capture=dict(reference_changes),models=result,
        diagnostics_code_sha256=sha(ROOT/'research/v3_diagnostics.py'))
    save(OUT/'reference_policy_diagnostics.json',data)
    return data

if __name__=='__main__':run()
