"""Portable private annotations; verified targets require actual external review."""
import argparse
import datetime
from collections import Counter
from research.labels_common import *
from research.labels_review import export_verified,export_single
from research.labels_issues import active as active_issues

def export(mode='annotations'):
    if mode not in ('annotations','single','verified','issues'):raise ValueError('Unknown export mode')
    folder=DATA/'exports';folder.mkdir(parents=True,exist_ok=True)
    dest=folder/(mode+'.jsonl');tmp=dest.with_suffix('.tmp');images=0;fields=0
    with tmp.open('w',encoding='utf-8',newline='\n') as stream:
        if mode=='issues':
            rows=active_issues()
            for row in rows:stream.write(canonical(row)+'\n')
            images=len({r['sample_uid'] for r in rows})
        elif mode in ('single','verified'):
            registry=read(DATA/'reviewer_registry.json') if (DATA/'reviewer_registry.json').exists() else {}
            rows=export_verified(registry=registry) if mode=='verified' else export_single(registry=registry)
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
        exported_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        images=images,fields=fields,contains_private_reference_text=mode=='annotations',published_to_git=False,
        requires_independent_consensus=mode=='verified',single_reviewer_not_consensus=mode=='single',
        empty_verified_export_is_not_a_successful_human_annotation_study=mode=='verified' and not fields)
    if mode=='single':
        plan=read(OUT/'human_review_plan.json') if (OUT/'human_review_plan.json').exists() else {}
        task_ids=set(plan.get('task_ids',[]))
        manifest[mode].update(latest_review_events=len({r['review_event'] for r in rows}),
            pilot_images=len({r['sample_uid'] for r in rows if uid(r['sample_uid']) in task_ids}),
            assessment_states=dict(Counter(r['field']['status'] for r in rows)),
            blinded_field_assessments=sum(r['independent_from_answers_self_declared'] for r in rows),
            evidence_is_single_reviewer_not_consensus=True)
    if mode=='issues':manifest[mode].update(active_issue_requests=len(rows),categories=dict(Counter(r['category'] for r in rows)),
        main_benchmark_cases_removed=0,readability_labels_created=0,free_text_reasons_are_private=True)
    save(OUT/'exports.json',manifest);print('LABEL_EXPORT',mode,images,fields,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--mode',choices=['annotations','single','verified','issues'],default='annotations');mode=p.parse_args().mode
    export(mode)
    if mode=='verified':export('single');export('issues')
