"""Evidence-relative KV scoring with explicit, unguessed date precision."""
import re
from research.v2_metrics import canonical as body_canonical,normalized
from research.v2_runtime import aggregate
from research.vlm_analysis import tolerant
from research.vlm_runtime import parsed

MONTHS={k:i+1 for i,k in enumerate(('JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC'))}

def date_value(text,kind='prediction'):
    text=normalized(text)
    if kind=='date_yymmdd' or re.fullmatch(r'\d{6}',text):
        if re.fullmatch(r'\d{6}',text):
            y,m,d=int(text[:2]),int(text[2:4]),int(text[4:])
            if 1<=m<=12 and 1<=d<=31:return ('year2',y,m,d)
    m=re.fullmatch(r'(\d{1,2})[ ./-]+(\d{1,2})[ ./-]+(\d{2})[ .]*',text)
    if m:
        d,mo,y=map(int,m.groups())
        if 1<=mo<=12 and 1<=d<=31:return ('year2',y,mo,d)
    m=re.fullmatch(r'(\d{1,2})[ ./-]*([A-Z]{3})[ ./-]*(\d{2})',text)
    if m and m[2] in MONTHS:return ('year2',int(m[3]),MONTHS[m[2]],int(m[1]))
    m=re.fullmatch(r'(\d{1,2})[ ./-]*([A-Z]{3})[ ./-]*(\d{4})',text)
    if m and m[2] in MONTHS:return ('year4',int(m[3]),MONTHS[m[2]],int(m[1]))
    iso=body_canonical('dob',text)
    if re.fullmatch(r'\d{4}-\d{2}-\d{2}',iso):
        y,m,d=map(int,iso.split('-'));return ('year4',y,m,d)
    return None

def canonical(key,value,kind='prediction'):
    if key in ('dob','expiry_date','issue_date'):
        date=date_value(value,kind)
        if date is not None:return date
    return body_canonical(key,value)

def reference_precision(ref):
    value=date_value(ref['value'],ref['kind'])
    return 4 if value and value[0]=='year4' else 2 if value else 0

def score(sample,fields,valid):
    refs=sample['source_refs'];target=sample['target'];correct=literal=max_precision=overreach=0
    for key in target:
        if key not in fields:continue
        candidates=refs[key];pred=canonical(key,fields[key])
        hit=any(pred==canonical(key,r['value'],r['kind']) for r in candidates)
        correct+=hit;literal+=any(normalized(fields[key])==normalized(r['value']) for r in candidates)
        best=max(reference_precision(r) for r in candidates) if key in ('dob','expiry_date','issue_date') else 0
        max_precision+=hit and (not best or any(pred==canonical(key,r['value'],r['kind']) and reference_precision(r)==best for r in candidates))
        if best==2 and isinstance(pred,tuple) and pred[0]=='year4':overreach+=1
    return dict(correct=correct,reference=len(target),predicted=len(fields),valid_json=bool(valid),literal_correct=literal,
        extra_keys=sum(k not in target for k in fields),missing_keys=sum(k not in fields for k in target),
        unsupported_nonempty=sum(k not in target for k in fields),visible_omissions=sum(k not in fields for k in target),
        wrong_visible_values=sum(k in fields for k in target)-correct,exact_document=bool(valid and len(fields)==len(target) and correct==len(target)),
        max_precision_correct=int(max_precision),date_century_overreach=overreach,
        masked_field_outputs=sum(k in fields and k not in target for k in sample.get('masked_keys',[])),
        empty_reference=not target,correct_empty_abstention=not target and not fields and bool(valid))

def scoring(sample,text):
    fields,meta=tolerant(text);result=score(sample,fields,meta['syntax_object_success']);strict,valid=parsed(text)
    result['strict']=score(sample,strict,valid)
    return dict(result,**meta),fields

def summary(rows):
    result=aggregate(rows)
    result.update({k:sum(r[k] for r in rows) for k in ('unsupported_nonempty','wrong_visible_values','visible_omissions',
        'empty_reference','correct_empty_abstention','max_precision_correct','date_century_overreach')})
    result['max_precision_f1']=2*result['max_precision_correct']/max(1,result['reference']+result['predicted'])
    result['retake_proxy_rate']=sum(r['predicted']==0 or not r['valid_json'] for r in rows)/max(len(rows),1)
    return result
