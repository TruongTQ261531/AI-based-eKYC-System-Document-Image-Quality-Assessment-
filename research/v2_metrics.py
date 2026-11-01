"""KV scoring accepts verbatim printed dates; no invented century for short years."""
import re
import unicodedata
from datetime import date

def normalized(value):return ' '.join(unicodedata.normalize('NFC',str(value)).upper().split())

def canonical(key,value):
    text=normalized(value)
    if key in ('dob','expiry_date','issue_date'):
        m=re.fullmatch(r'(\d{1,2})[ ./-]+(\d{1,2})[ ./-]+(\d{4})[ .]*',text)
        iso=re.fullmatch(r'(\d{4})-(\d{2})-(\d{2})',text)
        try:
            if m:
                d,mo,y=map(int,m.groups());return date(y,mo,d).isoformat()
            if iso:return date(*map(int,iso.groups())).isoformat()
        except ValueError:pass
        # Transcription, not authenticity validation. An unparsed/short-year
        # printed string can still be transcribed literally and correctly.
    if key=='gender':
        return {'M':'NAM','MALE':'NAM','NAM':'NAM','F':'NỮ','FEMALE':'NỮ','NỮ':'NỮ','NU':'NỮ'}.get(text,text)
    return text

def score(target,prediction,valid,accepted_values=None):
    alternatives=accepted_values or {k:[v] for k,v in target.items()}
    correct=sum(k in prediction and any(canonical(k,v)==canonical(k,prediction[k]) for v in alternatives[k]) for k in target)
    return dict(correct=correct,reference=len(target),predicted=len(prediction),valid_json=bool(valid),
        literal_correct=sum(k in prediction and any(normalized(v)==normalized(prediction[k]) for v in alternatives[k]) for k in target),
        extra_keys=sum(k not in target for k in prediction),missing_keys=sum(k not in prediction for k in target),
        exact_document=bool(valid and len(prediction)==len(target) and correct==len(target)))
