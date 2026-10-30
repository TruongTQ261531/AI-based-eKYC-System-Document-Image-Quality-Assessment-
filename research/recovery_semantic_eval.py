"""Canonical schema comparison; source-reviewed before test release."""
from ekyc.document_fields import date_value,fold
from research.e2e_eval import target_fields
from research.ocr_diagnostic import normalized


def canonical(key,value):
    if not isinstance(value,str) or not value.strip():return None
    if key in ('dob','expiry_date','issue_date'):
        parsed=date_value(value)
        return parsed or None
    if key=='gender':
        return {'male':'NAM','m':'NAM','nam':'NAM','female':'NỮ','f':'NỮ','nu':'NỮ'}.get(fold(value))
    return normalized(value)


def score_semantics(sample,predicted):
    targets,_=target_fields(sample);fields=[]
    for target in targets:
        key=target['key'];truth=canonical(key,target['text']);actual=canonical(key,predicted.get(key))
        fields.append(dict(field_key=key,reference_valid=truth is not None,exact=truth is not None and actual==truth,
            literal_exact=normalized(predicted.get(key) or '')==normalized(target['text']),predicted=actual is not None))
    return dict(fields=fields,eligible_fields=len(fields),canonical_exact=sum(f['exact'] for f in fields),
                literal_exact=sum(f['literal_exact'] for f in fields))
