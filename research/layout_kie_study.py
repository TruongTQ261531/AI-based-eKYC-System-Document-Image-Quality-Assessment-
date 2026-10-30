"""Separate exploratory KIE comparison on identical fixed completion OCR."""
import argparse
import json
import time
from pathlib import Path

import cv2
import numpy as np

from research.benchmark import save,digest
from research.e2e_benchmark import atomic_json,hash_json
from research.layout_kie import extract,to_view
from research.recovery_data import load_samples,seed
from research.recovery_runtime import RecoveryEngine,make_view
from research.recovery_study import OUT,CACHE,path_for,process_lock
from research.recovery_semantic_eval import score_semantics
from research.recovery_validate import canonical


def signature():
    return hash_json(dict(parser=digest('research/layout_kie.py'),runner=digest(__file__),
        protocol=digest('research/LAYOUT_KIE_PROTOCOL.md'),mentor_parser=digest('ekyc/document_fields.py'),
        model=digest(OUT/'selector_models.json'),primary_manifest=digest(OUT/'manifest.json')))


def run(development_only):
    sig=signature()
    if not development_only:
        lock=json.loads((OUT/'layout_kie_lock.json').read_text(encoding='utf-8'))
        if lock['signature']!=sig:raise ValueError('Exploratory KIE source lock changed')
    samples=[s for s in load_samples() if s['source']=='authored_specimen' and
        (s['role']=='development' if development_only else s['role']!='development')]
    if not development_only:
        samples+=json.loads(Path('research/data/layout_stress/samples.json').read_text(encoding='utf-8'))
    engine=RecoveryEngine();rows=[]
    for index,sample in enumerate(samples,1):
        path=CACHE/'layout_kie'/('case_'+str(seed(sample['uid']))+'.json')
        if path.exists():
            row=json.loads(path.read_text(encoding='utf-8'))
            if row['signature']!=sig:raise ValueError('KIE checkpoint changed')
        else:
            if digest(sample['path'])!=sample['input_sha256']:raise ValueError('KIE source image changed')
            if sample['source']=='authored_specimen':
                record=json.loads(path_for(1,sample['uid']).read_text(encoding='utf-8'))
                original=next(r for r in record['rows'] if r['engine']=='rapid_latin_v5' and r['policy']=='completion')
                predictions=original['_private_predictions'];baseline=original['_private_semantic']
            else:
                saved=CACHE/'layout_stress'/('1_'+str(seed(sample['uid']))+'_fixed_completion.json')
                original=json.loads(saved.read_text(encoding='utf-8'))
                predictions=original['_private_predictions'];baseline=original['_private_semantic']
            image=cv2.imread(sample['path']);tw=time.perf_counter();tc=time.process_time()
            loc=engine.locate(image);_,inverse,_,_=make_view(image,loc,'completion')
            framed=to_view(predictions,inverse)
            setup_wall=time.perf_counter()-tw;setup_cpu=time.process_time()-tc
            tw=time.perf_counter();tc=time.process_time();fields,labels,metadata=extract(framed)
            parser_wall=time.perf_counter()-tw;parser_cpu=time.process_time()-tc
            if fields!=extract(framed)[0]:raise ValueError('Repeated parser output changed')
            row=dict(signature=sig,uid=sample['uid'],physical_id=sample['physical_id'],role=sample['role'],source=sample['source'],
                input_sha256=sample['input_sha256'],ocr_prediction_sha256=canonical(predictions),
                baseline=score_semantics(sample,baseline),layout_assignment=score_semantics(sample,fields),
                all_fields_geometrically_visible=all(f['geometric_visibility']>=.995 for f in sample['fields']),
                baseline_predicted_keys=len(baseline),layout_assignment_predicted_keys=len(fields),
                baseline_unexpected_keys=sum(k not in {f['key'] for f in sample['fields']} for k in baseline),
                layout_assignment_unexpected_keys=sum(k not in {f['key'] for f in sample['fields']} for k in fields),
                setup_wall=setup_wall,setup_cpu=setup_cpu,parser_wall=parser_wall,parser_cpu=parser_cpu,
                extra_ocr_calls=0,deterministic_parser_repeat=True,metadata=metadata,
                _private_base_fields=baseline,_private_graph_fields=fields,
                _private_framed_predictions=framed,_private_inverse=inverse.tolist())
            atomic_json(path,row)
        rows.append({k:v for k,v in row.items() if not k.startswith('_private')})
        print('KIE_DEV' if development_only else 'KIE_EVAL',index,'/',len(samples),flush=True)
    if development_only:
        save(OUT/'layout_kie_development.json',dict(signature=sig,rows=rows,test_predictions_evaluated=False))
        base=sum(r['baseline']['canonical_exact'] for r in rows)
        graph=sum(r['layout_assignment']['canonical_exact'] for r in rows)
        save(OUT/'layout_kie_lock.json',dict(signature=sig,development_cases=len(rows),source_locked_before_supplement_evaluation=True,
            main_test_comparison_is_post_hoc=True,development_correct=dict(baseline=base,layout_assignment=graph),
            deployment_approved_on_development=graph>=base,
            protocol_sha256=digest('research/LAYOUT_KIE_PROTOCOL.md')))
    else:
        dev=json.loads((OUT/'layout_kie_development.json').read_text(encoding='utf-8'))['rows']
        intervals=[]
        for source,role in (('authored_specimen','test'),('authored_layout_stress','external_layout')):
            grouped={}
            for row in rows:
                if row['source']!=source or row['role']!=role:continue
                n=row['baseline']['eligible_fields']
                if n:grouped.setdefault(row['physical_id'],[]).append((row['layout_assignment']['canonical_exact']-row['baseline']['canonical_exact'])/n)
            delta=np.asarray([np.mean(values) for values in grouped.values()])
            rng=np.random.default_rng(20261031);boot=delta[rng.integers(0,len(delta),(2000,len(delta)))].mean(axis=1)
            intervals.append(dict(source=source,role=role,document_ids=len(delta),mean_delta=float(delta.mean()),
                ci95=np.quantile(boot,[.025,.975]).tolist(),exploratory=True,bootstrap_resamples=2000,
                weighting='Equal per-document mean of per-image semantic accuracy differences'))
        save(OUT/'layout_kie.json',dict(signature=sig,rows=dev+rows,cases=len(dev)+len(rows),
            additional_ocr_calls=0,main_comparison_post_hoc=True,parser_repeat_mismatches=0,
            paired_intervals=intervals,
            timing_scope='Parser only; separate setup includes redundant localization/transform for cached-source-box reconstruction',
            source_hashes=dict(parser=digest('research/layout_kie.py'),runner=digest(__file__))))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=('development','evaluate'));args=parser.parse_args()
    # Cached OCR is read-only, so this does not share the OCR process lock.
    # A distinct lock prevents competing writers of this extractor study.
    with process_lock(CACHE/'layout_kie_process.lock'):run(args.phase=='development')
