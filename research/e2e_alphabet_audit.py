"""Explain model alphabet limits; never replace the locked primary target set."""
import collections
import gzip
import json
from pathlib import Path

import easyocr.config
import yaml

from research.benchmark import save,digest
from research.e2e_data import load_samples,MODELS
from research.e2e_eval import target_fields
from research.ocr_diagnostic import normalized

ROOT=Path('research/results/e2e_ocr_v2')


def main():
    english=easyocr.config.recognition_models['gen2']['english_g2']['characters']
    config=yaml.safe_load((MODELS/'scanocr/base.yml').read_text(encoding='utf-8'))
    alphabets={'easyocr_en':set(normalized(english))|{' '},'vietocr':set(normalized(config['vocab']))|{' '}}
    supported={};coverage=[];samples=load_samples()
    for reader,alphabet in alphabets.items():
        missing=collections.Counter();n=0;ok=0
        for sample in samples:
            targets,_=target_fields(sample)
            for field in targets:
                truth=normalized(field['text']);valid=all(c in alphabet for c in truth)
                supported[(reader,sample['uid'],field['key'])]=valid;n+=1;ok+=valid
                missing.update(c for c in truth if c not in alphabet)
        coverage.append(dict(engine=reader,eligible_fields=n,alphabet_supported_fields=ok,
            unsupported_codepoints={f'U+{ord(c):04X}':count for c,count in sorted(missing.items())},
            interpretation='Necessary alphabet compatibility only; not a recognition-accuracy bound'))
    save(ROOT/'alphabet_coverage.json',coverage)
    with gzip.open(ROOT/'per_image.jsonl.gz','rt',encoding='utf-8') as stream:
        rows=[json.loads(line) for line in stream if json.loads(line)['repeat']==1]
    diagnostic=[]
    for reader in alphabets:
        for policy in dict.fromkeys(r['policy'] for r in rows):
            selected=[(r,f) for r in rows if r['engine']==reader and r['policy']==policy for f in r['score']['fields']]
            for subset in ('all_locked_fields','alphabet_supported','alphabet_unsupported'):
                chosen=[f for r,f in selected if subset=='all_locked_fields' or
                    supported[(reader,r['uid'],f['field_key'])]==(subset=='alphabet_supported')]
                diagnostic.append(dict(engine=reader,policy=policy,subset=subset,fields=len(chosen),
                    field_exact=sum(f['exact'] for f in chosen)/len(chosen) if chosen else None,
                    micro_cer=sum(f['edit_distance'] for f in chosen)/sum(f['truth_length'] for f in chosen) if chosen else None,
                    secondary_diagnostic_not_primary_redefinition=True))
    save(ROOT/'alphabet_diagnostic_scores.json',diagnostic)
    save(ROOT/'alphabet_audit_provenance.json',dict(code_sha256=digest(__file__),primary_target_set_changed=False,
        source_text_published=False,semantic_kie_evaluated=False))
    print('ALPHABET_AUDIT_COMPLETE',coverage)


if __name__=='__main__':main()
