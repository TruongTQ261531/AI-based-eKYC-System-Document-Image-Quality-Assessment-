"""Descriptive phase-1 agreement for genuine reviewer exports; not truth labels."""
from collections import Counter
from itertools import combinations
import argparse
import json
from pathlib import Path
import unicodedata

from .data import read
from .review import PACKET_ROOT,validate_export


def nominal(rows):
    """Nominal alpha with pairable units, and Cohen kappa for two complete columns."""
    pairable=[list(v for v in row if v is not None) for row in rows if sum(v is not None for v in row)>=2]
    counts=Counter();disagreement=0.;pairs=0;matching=0
    for values in pairable:
        c=Counter(values);m=len(values);counts.update(values)
        disagreement+=(m*m-sum(n*n for n in c.values()))/(m-1)
        for a,b in combinations(values,2):pairs+=1;matching+=a==b
    n=sum(counts.values());de=(n*n-sum(v*v for v in counts.values()))/(n*(n-1)) if n>1 else 0
    alpha=1-(disagreement/n)/de if n and de else None
    kappa=None
    if rows and all(len(row)==2 for row in rows):
        common=[row for row in rows if all(v is not None for v in row)]
        if common:
            a=Counter(r[0] for r in common);b=Counter(r[1] for r in common);total=len(common)
            po=sum(x==y for x,y in common)/total
            pe=sum(a[k]*b[k] for k in set(a)|set(b))/(total*total)
            if pe<1:kappa=(po-pe)/(1-pe)
    return dict(units_with_multiple_ratings=len(pairable),pairwise_comparisons=pairs,
                exact_pairwise_agreement=matching/pairs if pairs else None,
                cohen_kappa=kappa,nominal_krippendorff_alpha=alpha,
                alpha_unavailable_reason='no_pairable_units_or_no_category_variation' if alpha is None else None)


def compare(exports,packet,*,allow_unit=False):
    if len(exports)<2:raise ValueError('At least two actual exports are needed; prepared packages are not ratings')
    ids=[v.get('reviewer',{}).get('reviewer_id','').strip().casefold() for v in exports]
    if len(set(ids))!=len(ids):raise ValueError('Two versions from one reviewer are not two reviewers')
    results=[validate_export(v,packet,allow_unit=allow_unit) for v in exports]
    answers=[{i['slot_id']:i for i in r['complete_items']} for r in results]
    slots=[f['slot_id'] for p in packet['pages'] for f in p['fields']]
    metrics={key:nominal([[a[s][key] if s in a else None for a in answers] for s in slots])
             for key in ('availability','readability','semantic_key_confirmed')}
    def literal(value):return ' '.join(unicodedata.normalize('NFC',value).casefold().split())
    transcript_rows=[]
    for slot in slots:
        values=[a.get(slot) for a in answers]
        if all(v and v['readability']=='readable' and v['semantic_key_confirmed']=='yes' and v['observed_transcript'].strip() for v in values):
            transcript_rows.append([literal(v['observed_transcript']) for v in values])
    transcript=nominal(transcript_rows)
    return dict(schema='phase1-agreement/1',scope='descriptive agreement, not accuracy or adjudication',
        declared_reviewer_count=len(ids),distinct_people_independently_verified=False,
        roles=[v['reviewer']['role'] for v in exports],
        declared_output_exposure=[v['reviewer']['output_exposure'] for v in exports],
        planned_field_slots=len(slots),complete_counts=[r['complete_observations'] for r in results],
        categorical=metrics,readable_transcript_exact_agreement=dict(
            common_readable_slots=len(transcript_rows),value=transcript['exact_pairwise_agreement']),
        inter_rater_ci=None,independent_gold_created=False,model_calls=0)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--submissions',nargs='+',type=Path,required=True)
    args=parser.parse_args()
    result=compare([read(p) for p in args.submissions],read(PACKET_ROOT/'packet_manifest.json'))
    print(json.dumps(result,ensure_ascii=True,indent=2))
