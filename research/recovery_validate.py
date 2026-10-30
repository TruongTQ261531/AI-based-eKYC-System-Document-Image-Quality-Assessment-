"""Fresh actual online traces and legacy-reader checks on the locked panel."""
import argparse
import copy
import json
import hashlib
import os
import time
from pathlib import Path

import cv2
import numpy as np

from research.benchmark import digest,save
from research.e2e_benchmark import atomic_json,hash_json
from research.e2e_data import MODELS
from research.e2e_eval import score
from research.e2e_pipeline import Engine as LegacyEngine,to_source
from research.ocr_diagnostic import normalized
from research.recovery_data import load_samples
from research.recovery_runtime import RecoveryEngine,make_view
from research.recovery_selection import choose
from research.recovery_study import CACHE,OUT,panel,prepared,path_for,process_lock
from research.recovery_semantic_eval import score_semantics


def canonical(predictions):
    return hash_json([dict(text=normalized(p['text']),box=np.round(p['box'],5).tolist()) for p in predictions])


def online():
    samples=load_samples();signature,_=prepared(samples)
    models=json.loads((OUT/'selector_models.json').read_text(encoding='utf-8'));model_sha=digest(OUT/'selector_models.json')
    lock=json.loads((OUT/'selector_lock.json').read_text(encoding='utf-8'))
    if lock['model_sha256']!=model_sha or models['signature']!=signature:raise ValueError('Model lock changed')
    engine=RecoveryEngine();baseline=copy.deepcopy(models);reader='rapid_latin_v5'
    baseline['selectors'][reader]['primary_method']='forced_completion'
    baseline['selectors'][reader]['models']['forced_completion']=dict(regressor=dict(kind='stumps',base=-1.,stumps=[]),
        expected_fallback_wall={p:0. for p in ('raw','bbox','contour','lcnet')})
    baseline['review_thresholds'][reader]['forced_completion']=models['review_thresholds'][reader]['fixed_completion']
    result=[];count=0
    for repeat in (1,2,3):
        scheduled=panel(samples);order=np.random.default_rng(991+repeat).permutation(len(scheduled))
        for i in order:
            sample=scheduled[int(i)];image=cv2.imread(sample['path'])
            methods=['primary_cascade','fixed_completion']
            if (int(i)+repeat)%2:methods.reverse()
            original=json.loads(path_for(1,sample['uid']).read_text(encoding='utf-8'))
            candidate={r['policy']:r for r in original['rows'] if r['engine']==reader}
            predicted_policy,_=choose(candidate,models['selectors'][reader]['primary_method'],models['selectors'][reader]['models'])
            for method in methods:
                name=f'{repeat}_'+str(i)+'_'+method;path=CACHE/'online'/(name+'.json')
                if path.exists():
                    saved=json.loads(path.read_text(encoding='utf-8'))
                    if saved['signature']!=signature or saved['model_sha256']!=model_sha:raise ValueError('Stale online checkpoint')
                else:
                    answer=engine.online(image,models if method=='primary_cascade' else baseline,reader)
                    expected=candidate[predicted_policy if method=='primary_cascade' else 'completion']
                    saved=dict(signature=signature,model_sha256=model_sha,uid=sample['uid'],physical_id=sample['physical_id'],
                        source=sample['source'],role=sample['role'],method=method,repeat=repeat,reader=reader,
                        actual_wall=answer['actual_wall_seconds'],actual_cpu=answer['actual_cpu_seconds'],
                        ocr_executions=answer['ocr_executions'],selected_policy=answer['selected_policy'],
                        canonical_output_matches_exhaustive=canonical(answer['predictions'])==expected['prediction_sha256'],
                        exhaustive_review_recommended=not (expected['routed'] and expected['features'][6]>=models['review_thresholds'][reader][
                            models['selectors'][reader]['primary_method'] if method=='primary_cascade' else 'fixed_completion']),
                        score=score(sample,answer['predictions'],True),review_recommended=answer['review_recommended'],
                        _private_predictions=answer['predictions'],_private_semantic=answer['fields'])
                    if sample['source']=='authored_specimen':saved['semantic_canonical']=score_semantics(sample,answer['fields'])
                    atomic_json(path,saved)
                result.append({k:v for k,v in saved.items() if not k.startswith('_private')});count+=1
                print('ONLINE',count,'/144',flush=True)
    save(OUT/'online_traces.json',dict(rows=result,reader=reader,fresh_request_units=144,
        output_mismatches=sum(not r['canonical_output_matches_exhaustive'] for r in result),
        maximum_ocr_executions=max(r['ocr_executions'] for r in result),
        review_gate_differences=sum(r['review_recommended']!=r['exhaustive_review_recommended'] for r in result),
        review_difference_scope='Online adds empty-output guard; exhaustive calibration gate is retained unchanged',
        cross_request_prediction_cache=False,models_resident=True,policy_order_counterbalanced=True,
        scope='Actual prediction pipeline wall time, not HTTP transfer/decode latency',
        code_sha256=digest(__file__),addendum_sha256=digest('research/RECOVERY_EVALUATION_ADDENDUM.md')))


def legacy():
    if not (OUT/'selector_lock.json').exists():raise RuntimeError('Lock selectors before opening panel test annotations')
    folder=Path(os.environ.get('EKYC_MODELS_DIR',str(MODELS)))
    sources=json.loads(Path('models/identity_model_sources.json').read_text(encoding='utf-8'));provenance=[]
    for name in ('base.yml','vgg-transformer.yml','vgg_transformer.pth'):
        path=folder/'scanocr'/name;expected=next(s for s in sources if s['file']=='scanocr/'+name)
        if digest(path)!=expected['sha256']:raise ValueError('Pinned legacy VietOCR asset mismatch')
        provenance.append(dict(file='scanocr/'+name,sha256=digest(path),source=expected['url']))
    import easyocr.config
    for name in ('craft','english_g2'):
        cfg=easyocr.config.detection_models[name] if name=='craft' else easyocr.config.recognition_models['gen2'][name]
        path=folder/'easyocr'/cfg['filename']
        with path.open('rb') as stream:md5=hashlib.file_digest(stream,'md5').hexdigest()
        if md5!=cfg['md5sum']:raise ValueError('Official legacy EasyOCR MD5 mismatch')
        provenance.append(dict(file='easyocr/'+path.name,sha256=digest(path),official_md5=md5,source=cfg['url']))
    samples=load_samples();signature,_=prepared(samples);engine=RecoveryEngine();legacy=LegacyEngine(folder);rows=[]
    for index,sample in enumerate(panel(samples),1):
        path=CACHE/'legacy'/(str(index)+'.json')
        if path.exists():
            record=json.loads(path.read_text(encoding='utf-8'))
            if record['signature']!=signature:raise ValueError('Legacy signature changed')
        else:
            image=cv2.imread(sample['path']);start=time.perf_counter();loc=engine.locate(image)
            pixels,inverse,mode,_=make_view(image,loc,'completion');geometry=time.perf_counter()-start
            answer=legacy.ocr(pixels);record=dict(signature=signature,uid=sample['uid'],rows=[])
            for name in ('easyocr_en','vietocr'):
                pred=to_source(answer['predictions'][name],inverse)
                record['rows'].append(dict(reader=name,score=score(sample,pred,True),
                    wall=geometry+answer['detection']['wall']+answer['recognition'][name]['wall'],
                    _private_predictions=pred))
            # A fixed colour-crop ablation, not replacement of locked gray runs.
            raw=answer['predictions']['easyocr_en'];native=engine.readers['rapid_latin_v5']
            start=time.perf_counter()
            boxes=np.asarray([p['box'] for p in raw],np.float32)
            crops=native.get_crop_img_list(pixels,boxes) if len(boxes) else []
            both=[cv2.cvtColor(c,cv2.COLOR_BGR2RGB) for c in crops]
            both+= [np.rot90(c,2).copy() for c in both]
            recognized=legacy.vietnamese.predict_many(both) if both else []
            predictions=[]
            for j,p in enumerate(raw):
                text,confidence=max((recognized[j],recognized[j+len(raw)]),key=lambda r:r[1])
                predictions.append(dict(box=p['box'],text=text,confidence=confidence))
            color_wall=time.perf_counter()-start;pred=to_source(predictions,inverse)
            record['rows'].append(dict(reader='vietocr_color',score=score(sample,pred,True),
                wall=geometry+answer['detection']['wall']+color_wall,_private_predictions=pred))
            atomic_json(path,record)
        for row in record['rows']:
            rows.append({**{k:v for k,v in row.items() if not k.startswith('_private')},
                **{k:sample[k] for k in ('uid','physical_id','source','role')}})
        print('LEGACY',index,'/24',flush=True)
    save(OUT/'legacy_panel.json',dict(rows=rows,images=24,reader_variants=3,models=provenance,
        full_540_case_run=False,shared_detector='CRAFT',views='Same native-decoder padded-completion pixels',
        white_vs_colour_crops='Grayscale normalization retained in original path; colour alternative additionally reported',
        code_sha256=digest(__file__)))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=('online','legacy'));args=parser.parse_args()
    with process_lock(CACHE/'process.lock'):{'online':online,'legacy':legacy}[args.phase]()


if __name__=='__main__':main()
