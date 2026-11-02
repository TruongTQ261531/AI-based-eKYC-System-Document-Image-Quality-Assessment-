"""Development-only alias-position counts, without printing document values."""
import hashlib
import re
from collections import Counter
from research.v3_common import *
from research.v2_cpu import ALIASES,label,extract
from ekyc.document_fields import fold


def run():
    counts=Counter();embedded=Counter()
    for sample in load('development'):
        if sample['source']!='midv2020':continue
        token=hashlib.sha256(sample['uid'].encode()).hexdigest()
        for reader in ('rapid_v4','rapid_latin_v5'):
            raw=read(CACHE/'cpu_raw/development'/reader/(token+'.json'))['predictions']
            counts['images']+=1;counts['boxes']+=len(raw);counts['extracted_fields']+=len(extract(raw))
            for box in raw:
                prefix=label(box['text']);hits=[k for k,p in ALIASES.items() if re.search(p,fold(box['text']))]
                counts['prefix_label_boxes']+=bool(prefix);counts['embedded_only_label_boxes']+=bool(hits) and not prefix
                if hits and not prefix:embedded.update(hits)
    save(OUT/'cpu_label_development_diagnostic.json',dict(role='development',counts=dict(counts),
        embedded_alias_key_counts=dict(embedded),pattern_hits_are_not_verified_human_label_annotations=True,
        new_OCR_calls=0,code_sha256=sha(ROOT/'research/v3_cpu_label_diagnostic.py')))
    print('CPU_DEVELOPMENT_ALIAS_DIAGNOSTIC',dict(counts),flush=True)


if __name__=='__main__':run()
