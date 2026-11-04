"""Portable private annotations; verified targets require actual external review."""
import argparse
from research.labels_common import *
from research.labels_review import export_verified

def export(mode='annotations'):
    if mode not in ('annotations','verified'):raise ValueError('Unknown export mode')
    folder=DATA/'exports';folder.mkdir(parents=True,exist_ok=True)
    dest=folder/(mode+'.jsonl');tmp=dest.with_suffix('.tmp');images=0;fields=0
    with tmp.open('w',encoding='utf-8',newline='\n') as stream:
        if mode=='verified':
            registry=read(DATA/'reviewer_registry.json') if (DATA/'reviewer_registry.json').exists() else {}
            rows=export_verified(registry=registry)
            for row in rows:stream.write(canonical(row)+'\n');fields+=1
            images=len({r['sample_uid'] for r in rows})
        else:
            with connect() as conn:
                for row in conn.execute('SELECT * FROM images ORDER BY native_uid'):
                    item=dict(row);item['metadata']=json.loads(item['metadata'])
                    item['fields']=[json.loads(f[0]) for f in conn.execute('SELECT annotation FROM fields WHERE image_uid=? ORDER BY field_id',(row['uid'],))]
                    item['reference_is_not_observed_transcription']=True
                    stream.write(canonical(item)+'\n');images+=1;fields+=len(item['fields'])
                    if images%256==0:progress('private_annotation_export',images,21050)
    tmp.replace(dest)
    manifest=read(OUT/'exports.json') if (OUT/'exports.json').exists() else {}
    manifest[mode]=dict(private_path=dest.relative_to(ROOT).as_posix(),sha256=sha(dest),bytes=dest.stat().st_size,
        images=images,fields=fields,contains_private_reference_text=mode=='annotations',published_to_git=False,
        confirmed_human_training_targets=mode=='verified',empty_verified_export_is_not_a_successful_human_annotation_study=mode=='verified' and not fields)
    save(OUT/'exports.json',manifest);print('LABEL_EXPORT',mode,images,fields,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--mode',choices=['annotations','verified'],default='annotations');export(p.parse_args().mode)
