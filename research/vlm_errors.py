"""Numerical error taxonomy from saved outputs; never publish field values."""
import hashlib
import json
from collections import Counter
from research.vlm_setup import CACHE,OUT,save,sha
from research.vlm_data import load
from research.vlm_runtime import parsed,semantic_value,signature
from research.vlm_analysis import tolerant


def classify(sample,fields,valid):
    target=sample['target'];printed={f['key']:f for f in sample['fields']}
    counts=Counter(format_failure=int(not valid),visible_reference_fields=len(target),
        opaque_mask_opportunities=sum(f.get('occluded',False) for f in sample['fields']))
    for key,value in target.items():
        if key not in fields:counts['omitted_visible']+=1
        elif semantic_value(key,value)!=semantic_value(key,fields[key]):counts['wrong_visible_value']+=1
        else:counts['correct_visible_value']+=1
    for key in fields:
        if key in target:continue
        if key not in printed:counts['output_unprinted_field']+=1
        elif printed[key].get('occluded',False):counts['output_opaque_masked_field']+=1
        else:counts['output_clipped_label_or_value']+=1
    return dict(counts)


def main():
    samples={r['uid']:r for r in load('test')};out=[]
    variants=[(m,m,OUT,CACHE) for m in ('original','seed_42','seed_31415')]
    variants.append(('control_seed_42','seed_42',OUT/'control',CACHE/'control'))
    for label,key,public,private_root in variants:
        source=json.loads((public/f'test_{key}_1.json').read_text(encoding='utf-8'))
        for parser in ('strict','format_tolerant'):
            rows=[];totals=Counter()
            for row in source['rows']:
                private=json.loads((private_root/'predictions'/f'test_{key}_1'/(hashlib.sha256(row['uid'].encode()).hexdigest()+'.json')).read_text(encoding='utf-8'))
                if parser=='strict':fields,valid=parsed(private['_private_text'])
                else:
                    fields,metadata=tolerant(private['_private_text']);valid=metadata['syntax_object_success']
                counts=classify(samples[row['uid']],fields,valid);totals.update(counts)
                rows.append(dict(uid=row['uid'],**counts))
            out.append(dict(model=label,parser=parser,totals=dict(totals),rows=rows))
    cpu=json.loads((OUT/'test_ocr.json').read_text(encoding='utf-8'))
    for model in cpu['summaries']:
        rows=[];totals=Counter()
        for row in (r for r in cpu['rows'] if r['model']==model):
            path=CACHE/'cpu_baseline'/signature()/'test'/(hashlib.sha256(row['uid'].encode()).hexdigest()+'.json')
            private=json.loads(path.read_text(encoding='utf-8'))
            fields=next(r['_private_fields'] for r in private['rows'] if r['model']==model)
            counts=classify(samples[row['uid']],fields,True);totals.update(counts)
            rows.append(dict(uid=row['uid'],**counts))
        out.append(dict(model=model,parser='python_dict',totals=dict(totals),rows=rows))
    save(OUT/'error_taxonomy.json',dict(signature=signature(),code_sha256=sha(__file__),results=out,
        cpu_taxonomy_added_after_baseline_scores=True,primary_scoring_and_model_choice_unchanged=True,
        geometry_proxy_only=True,clipped_output_not_automatically_factual_hallucination=True,
        zero_mask_outputs_is_not_a_calibrated_safety_claim=True))


if __name__=='__main__':main()
