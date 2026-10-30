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


def main():
    samples=load_samples();signature,_=prepared(samples)
    manifest=json.loads((OUT/'manifest.json').read_text());model=json.loads((OUT/'selector_models.json').read_text())
    lock=json.loads((OUT/'selector_lock.json').read_text())
    if signature!=manifest['signature'] or model['signature']!=signature or digest(OUT/'selector_models.json')!=lock['model_sha256']:
        raise ValueError('Immutable signature/model lock mismatch')
    roles=defaultdict(set);image_roles=defaultdict(set)
    for s in samples:roles[s['role']].add(s['physical_id']);image_roles[s['input_sha256']].add(s['role'])
    if roles['test']&(roles['development']|roles['calibration']) or roles['development']&roles['calibration']:
        raise ValueError('Cross-role identity leakage')
    if any(len(role)>1 for role in image_roles.values()):raise ValueError('Identical image bytes in different roles')
    with gzip.open(OUT/'per_image.jsonl.gz','rt') as stream:published=[json.loads(line) for line in stream]
    actual={(r['repeat'],r['uid'],r['engine'],r['policy']):r for r in published}
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
    events=[json.loads(s) for s in (CACHE/'events.jsonl').read_text().splitlines()]
    save(OUT/'independent_audit.json',dict(signature=signature,code_sha256=digest(__file__),
        native_rows_rescored=checked,selector_decisions_replayed=costs,public_rows=len(published),
        score_mismatches=0,publication_mismatches=0,wall_sum_mismatches=0,cpu_sum_mismatches=0,
        cross_role_identity_overlap=0,cross_role_image_hash_overlap=0,unique_ocr_executions=calls,
        failure_events=[r for r in events if r['event']=='failure'],checkpoint_hashes=hashes,
        model_sha256=lock['model_sha256'],raw_text_in_public_json=False,
        limitations='Shares the frozen spatial evaluator; not independent human ground-truth verification'))
    print('RECOVERY_INDEPENDENT_AUDIT_PASS',checked,costs,len(published),flush=True)


if __name__=='__main__':main()
