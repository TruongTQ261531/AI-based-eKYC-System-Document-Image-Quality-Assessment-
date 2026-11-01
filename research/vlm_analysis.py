"""Predeclared secondary format-tolerant scoring; never modifies predictions."""
import hashlib
import json
import re

from research.vlm_setup import ROOT,OUT,CACHE,save,sha
from research.vlm_data import load
from research.vlm_runtime import signature,score,aggregate


def tolerant(text):
    fenced=False
    match=re.fullmatch(r'\s*```(?:json)?\s*\n?(.*?)\n?```\s*',text,re.S|re.I)
    if match:text=match.group(1);fenced=True
    def unique(pairs):
        result={}
        for k,v in pairs:
            if k in result:raise ValueError('Duplicate key')
            result[k]=v
        return result
    try:
        value=json.loads(text,object_pairs_hook=unique)
        if not isinstance(value,dict):raise ValueError('Not an object')
    except (ValueError,TypeError):return {},dict(syntax_object_success=False,fenced=fenced,null_or_empty=0,bad_type=0)
    result={};null=bad=0
    for k,v in value.items():
        if v is None or isinstance(v,str) and not v.strip():null+=1
        elif isinstance(v,(str,int,float)) and not isinstance(v,bool):result[k]=str(v)
        else:bad+=1
    return result,dict(syntax_object_success=True,fenced=fenced,null_or_empty=null,bad_type=bad)


def main():
    sig=signature();lock=json.loads((OUT/'test_lock.json').read_text(encoding='utf-8'))
    if lock['signature']!=sig:raise ValueError('Source changed after lock')
    samples={r['uid']:r for r in load()};results=[]
    for role in ('development','test'):
        for model in ('original','seed_42','seed_31415'):
            source=json.loads((OUT/f'{role}_{model}_1.json').read_text(encoding='utf-8'));rows=[]
            if source['signature']!=sig:raise ValueError('Evaluation source changed')
            for row in source['rows']:
                private=json.loads((CACHE/'predictions'/f'{role}_{model}_1'/(hashlib.sha256(row['uid'].encode()).hexdigest()+'.json')).read_text(encoding='utf-8'))
                fields,metadata=tolerant(private['_private_text']);sample=samples[row['uid']]
                rows.append(dict(uid=row['uid'],**score(sample['target'],fields,metadata['syntax_object_success']),**metadata,
                    masked_field_outputs=sum(f.get('occluded',False) and f['key'] in fields for f in sample['fields'])))
            results.append(dict(role=role,model=model,strict_summary=source['summary'],tolerant_summary=aggregate(rows),
                syntax_success=sum(r['syntax_object_success'] for r in rows),fenced_outputs=sum(r['fenced'] for r in rows),
                null_or_empty_values=sum(r['null_or_empty'] for r in rows),bad_types=sum(r['bad_type'] for r in rows),rows=rows))
    save(OUT/'format_analysis.json',dict(signature=sig,analysis_sha256=sha(__file__),
        addendum_sha256=sha(ROOT/'research/VLM_EVALUATION_ADDENDUM.md'),primary_metrics_unchanged=True,results=results))


if __name__=='__main__':main()
