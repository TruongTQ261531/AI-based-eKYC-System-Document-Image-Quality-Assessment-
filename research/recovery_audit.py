"""Re-score from private predictions and verify every released native/selector row."""
import gzip
import json
import math
from collections import defaultdict

from research.benchmark import digest,save
from research.e2e_benchmark import hash_json
from research.e2e_eval import score
from research.recovery_data import load_samples
from research.recovery_runtime import POLICIES,READERS
from research.recovery_selection import choose,combined_cost
from research.recovery_study import CACHE,OUT,METHODS,prepared,panel,path_for
from research.recovery_validate import canonical


def inspect(value):
    forbidden={'text','truth','recognized_text','ground_truth_text','_private_predictions','_private_semantic'}
    if isinstance(value,dict):
        if forbidden.intersection(value):raise ValueError('Raw personal-text key in public artifact')
        for x in value.values():inspect(x)
    elif isinstance(value,list):
        for x in value:inspect(x)


def repeat_checks(rows):
    groups=defaultdict(list)
    for row in rows:groups[(row['uid'],row['method'])].append(row)
    repeated=[items for items in groups.values() if len(items)>1]
    return dict(repeated_image_method_groups=len(repeated),
        canonical_prediction_mismatches=sum(len({r['prediction_sha256'] for r in items})>1 for items in repeated),
        score_mismatches=sum(len({json.dumps(r['score'],sort_keys=True) for r in items})>1 for items in repeated),
        repeated_images_are_not_additional_independent_documents=True)


def main():
    samples=load_samples();signature,_=prepared(samples)
    manifest=json.loads((OUT/'manifest.json').read_text(encoding='utf-8'));model=json.loads((OUT/'selector_models.json').read_text(encoding='utf-8'))
    lock=json.loads((OUT/'selector_lock.json').read_text(encoding='utf-8'))
    if signature!=manifest['signature'] or model['signature']!=signature or digest(OUT/'selector_models.json')!=lock['model_sha256']:
        raise ValueError('Immutable signature/model lock mismatch')
    roles=defaultdict(set);image_roles=defaultdict(set)
    for s in samples:roles[s['role']].add(s['physical_id']);image_roles[s['input_sha256']].add(s['role'])
    if roles['test']&(roles['development']|roles['calibration']) or roles['development']&roles['calibration']:
        raise ValueError('Cross-role identity leakage')
    if any(len(role)>1 for role in image_roles.values()):raise ValueError('Identical image bytes in different roles')
    with gzip.open(OUT/'per_image.jsonl.gz','rt') as stream:published=[json.loads(line) for line in stream]
    actual={(r['repeat'],r['uid'],r['engine'],r['policy']):r for r in published}
    public_row_count=len(published)
    expected_count=588*len(READERS)*(len(POLICIES)+len(METHODS))
    if len(actual)!=len(published) or len(actual)!=expected_count:raise ValueError('Missing/duplicate published rows')
    checked=0;costs=0;hashes=[];calls=0
    for repeat,group in ((1,samples),(2,panel(samples)),(3,panel(samples))):
        for sample in group:
            path=path_for(repeat,sample['uid']);case=json.loads(path.read_text(encoding='utf-8'))
            if case['signature']!=signature or case['input_sha256']!=digest(sample['path']):raise ValueError('Source/checkpoint mismatch')
            if len({(r['engine'],r['policy']) for r in case['rows']})!=len(READERS)*len(POLICIES):raise ValueError('Missing candidate')
            calls+=case['unique_ocr_executions'];hashes.append(dict(repeat=repeat,uid=sample['uid'],sha256=digest(path)))
            for reader in READERS:
                private={r['policy']:r for r in case['rows'] if r['engine']==reader}
                for policy,row in private.items():
                    public=actual[(repeat,sample['uid'],reader,policy)]
                    recomputed=score(sample,row['_private_predictions'],row['routed'])
                    if public['score']!=recomputed or public['prediction_sha256']!=canonical(row['_private_predictions']):
                        raise ValueError('Score or canonical prediction differs')
                    if any(public[k]!=v for k,v in row.items() if not k.startswith('_private') and k!='score'):
                        raise ValueError('Published native field differs from private record')
                    total=row['ocr_wall']+row['probe_wall']+row['localize_wall']+row['transform_wall']+row['semantic_map_wall']
                    if not math.isclose(total,row['total_wall'],abs_tol=1e-8):raise ValueError('Native wall-time sum mismatch')
                    cpu=row['ocr_cpu']+row['localize_cpu']+row['transform_cpu']+row['semantic_map_cpu']
                    if row['probe_wall']:cpu+=private['raw']['ocr_cpu']
                    if not math.isclose(cpu,row['total_cpu'],abs_tol=1e-8):raise ValueError('Native CPU-time sum mismatch')
                    checked+=1
                for method in METHODS:
                    chosen,cost=choose(private,method,model['selectors'][reader]['models']);row=actual[(repeat,sample['uid'],reader,method)]
                    if row['chosen_policy']!=chosen or row['score']!=actual[(repeat,sample['uid'],reader,chosen)]['score']:
                        raise ValueError('Published selector differs from locked decision')
                    if not math.isclose(row['estimated_trace_wall'],cost,abs_tol=1e-8):raise ValueError('Selector cost differs')
                    expected_review=not (private[chosen]['routed'] and private[chosen]['features'][6]>=model['review_thresholds'][reader][method])
                    if row['review_recommended']!=expected_review:raise ValueError('Review threshold differs')
                    costs+=1
    for row in published:inspect(row)
    for path in OUT.glob('*.json'):inspect(json.loads(path.read_text(encoding='utf-8')))
    validation_counts={};supplement_repeats={}
    if (OUT/'online_traces.json').exists():
        public=json.loads((OUT/'online_traces.json').read_text(encoding='utf-8'))['rows']
        by_key={(r['repeat'],r['uid'],r['method']):r for r in public}
        for repeat in (1,2,3):
            for i,s in enumerate(panel(samples)):
                for method in ('primary_cascade','fixed_completion'):
                    p=CACHE/'online'/f'{repeat}_{i}_{method}.json';r=json.loads(p.read_text(encoding='utf-8'))
                    published=by_key[(repeat,s['uid'],method)]
                    if r['score']!=score(s,r['_private_predictions'],True):raise ValueError('Online rescore mismatch')
                    if {k:v for k,v in r.items() if not k.startswith('_private')}!=published:raise ValueError('Online publication mismatch')
        validation_counts['online_rescored']=len(public)
    if (OUT/'legacy_panel.json').exists():
        public=json.loads((OUT/'legacy_panel.json').read_text(encoding='utf-8'))['rows'];by_key={(r['uid'],r['reader']):r for r in public}
        for i,s in enumerate(panel(samples),1):
            r=json.loads((CACHE/'legacy'/f'{i}.json').read_text(encoding='utf-8'))
            for item in r['rows']:
                if by_key[(s['uid'],item['reader'])]['score']!=score(s,item['_private_predictions'],True):raise ValueError('Legacy rescore mismatch')
        validation_counts['legacy_rescored']=len(public)
    if (OUT/'up_external.json').exists():
        from pathlib import Path
        external=json.loads(Path('research/data/midv_up/samples.json').read_text(encoding='utf-8'))
        public=json.loads((OUT/'up_external.json').read_text(encoding='utf-8'))['rows'];by_key={(r['repeat'],r['uid'],r['method']):r for r in public}
        for repeat in (1,2):
            for i,s in enumerate(external):
                for method in ('raw','fixed_completion','primary_cascade'):
                    item=json.loads((CACHE/'up_external'/f'{repeat}_{i}_{method}.json').read_text(encoding='utf-8'))
                    published=by_key[(repeat,s['uid'],method)]
                    if published['score']!=score(s,item['_private_predictions'],True):raise ValueError('UP rescore mismatch')
                    if {k:v for k,v in item.items() if not k.startswith('_private')}!=published:raise ValueError('UP publication mismatch')
        validation_counts['external_up_rescored']=len(public)
        supplement_repeats['midv_up']=repeat_checks(public)
    if (OUT/'layout_stress.json').exists():
        from pathlib import Path
        from research.recovery_data import seed
        from research.recovery_visible_eval import score_visible
        from research.recovery_semantic_eval import score_semantics
        stress=json.loads(Path('research/data/layout_stress/samples.json').read_text(encoding='utf-8'))
        lookup={s['uid']:s for s in stress}
        public=json.loads((OUT/'layout_stress.json').read_text(encoding='utf-8'))['rows']
        if len(public)!=288:raise ValueError('Incomplete layout stress run')
        for published in public:
            s=lookup[published['uid']]
            path=CACHE/'layout_stress'/(str(published['repeat'])+'_'+str(seed(s['uid']))+'_'+published['method']+'.json')
            item=json.loads(path.read_text(encoding='utf-8'))
            if digest(s['path'])!=s['input_sha256']:raise ValueError('Stress input changed')
            if published['score']!=score(s,item['_private_predictions'],True):raise ValueError('Stress rescore mismatch')
            if published['visible_score']!=score_visible(s,item['_private_predictions']):raise ValueError('Stress visible rescore mismatch')
            if 'semantic_score' in published and published['semantic_score']!=score_semantics(s,item['_private_semantic']):
                raise ValueError('Stress semantic rescore mismatch')
            if {k:v for k,v in item.items() if not k.startswith('_private')}!=published:raise ValueError('Stress publication mismatch')
        validation_counts['external_layout_rescored']=len(public)
        supplement_repeats['spatial_layout']=repeat_checks(public)
    if (OUT/'layout_kie.json').exists():
        from pathlib import Path
        from research.layout_kie import extract,to_view
        from research.recovery_data import seed
        from research.recovery_semantic_eval import score_semantics
        from research.layout_kie_study import signature as kie_signature
        extra=json.loads(Path('research/data/layout_stress/samples.json').read_text(encoding='utf-8'))
        lookup={s['uid']:s for s in samples+extra}
        result=json.loads((OUT/'layout_kie.json').read_text(encoding='utf-8'))
        if result['signature']!=kie_signature() or len(result['rows'])!=440:raise ValueError('KIE source/count mismatch')
        for published in result['rows']:
            s=lookup[published['uid']]
            item=json.loads((CACHE/'layout_kie'/('case_'+str(seed(s['uid']))+'.json')).read_text(encoding='utf-8'))
            if s['source']=='authored_specimen':
                original=json.loads(path_for(1,s['uid']).read_text(encoding='utf-8'))
                original=next(r for r in original['rows'] if r['engine']=='rapid_latin_v5' and r['policy']=='completion')
            else:
                original=json.loads((CACHE/'layout_stress'/('1_'+str(seed(s['uid']))+'_fixed_completion.json')).read_text(encoding='utf-8'))
            if item['_private_base_fields']!=original['_private_semantic']:raise ValueError('KIE baseline changed')
            framed=to_view(original['_private_predictions'],item['_private_inverse'])
            if canonical(framed)!=canonical(item['_private_framed_predictions']):raise ValueError('KIE frame replay mismatch')
            if extract(framed)[0]!=item['_private_graph_fields']:raise ValueError('KIE predictor replay mismatch')
            if published['baseline']!=score_semantics(s,item['_private_base_fields']):raise ValueError('KIE baseline rescore mismatch')
            if published['layout_assignment']!=score_semantics(s,item['_private_graph_fields']):raise ValueError('KIE assignment rescore mismatch')
            if {k:v for k,v in item.items() if not k.startswith('_private')}!=published:raise ValueError('KIE publication mismatch')
        validation_counts['kie_cases_replayed_and_rescored']=len(result['rows'])
    events=[json.loads(s) for s in (CACHE/'events.jsonl').read_text(encoding='utf-8').splitlines()]
    save(OUT/'independent_audit.json',dict(signature=signature,code_sha256=digest(__file__),
        native_rows_rescored=checked,selector_decisions_replayed=costs,public_rows=public_row_count,
        score_mismatches=0,publication_mismatches=0,wall_sum_mismatches=0,cpu_sum_mismatches=0,
        cross_role_identity_overlap=0,cross_role_image_hash_overlap=0,unique_ocr_executions=calls,
        failure_events=[r for r in events if r['event']=='failure'],checkpoint_hashes=hashes,
        model_sha256=lock['model_sha256'],raw_text_in_public_json=False,additional_validation=validation_counts,
        supplement_repeats=supplement_repeats,
        limitations='Shares the frozen spatial evaluator; not independent human ground-truth verification'))
    print('RECOVERY_INDEPENDENT_AUDIT_PASS',checked,costs,public_row_count,flush=True)


if __name__=='__main__':main()
