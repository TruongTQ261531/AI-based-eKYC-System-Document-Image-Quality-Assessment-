"""Re-score private outputs, verify timing/config and expose only hashes/counts."""
import gzip
import json
import math
from pathlib import Path

from research.benchmark import digest,save
from research.e2e_data import load_samples,replication_panel
from research.e2e_eval import score
from research.e2e_benchmark import OUT,CACHE,prepared_signature,checkpoint_path,ENGINES,hash_json
from research.e2e_pipeline import POLICIES
from research.e2e_eval import aggregate
from research.ocr_diagnostic import normalized


def result_key(row):
    return row['repeat'],row['uid'],row['policy'],row['engine']


def verify_public_rows(published,expected):
    """Every public value must equal its private checkpoint projection."""
    actual={result_key(row):row for row in published}
    if len(actual)!=len(published) or set(actual)!=set(expected):
        raise ValueError('Missing, duplicate or unexpected published result key')
    if any(actual[key]!=value for key,value in expected.items()):
        raise ValueError('Published value differs from private checkpoint')


def main():
    samples=load_samples();signature,manifest=prepared_signature(samples)
    public_manifest=json.loads((OUT/'manifest.json').read_text())
    if signature!=public_manifest['signature']:raise ValueError('Immutable source/input signature changed')
    inventory=[];rows=0;score_mismatches=[];timing_mismatches=[];calls=0;ocr_calls=0;expected={}
    for repeat in (1,2,3):
        for sample in samples if repeat==1 else replication_panel(samples):
            path=checkpoint_path(repeat,sample['uid']);record=json.loads(path.read_text(encoding='utf-8'))
            if (record['signature']!=signature or record['input_sha256']!=sample['input_sha256'] or
                record['repeat']!=repeat or record['uid']!=sample['uid']):raise ValueError('Checkpoint identity mismatch')
            if len(record['rows'])!=len(POLICIES)*len(ENGINES):raise ValueError('Incomplete image-policy-engine result')
            if {(r['policy'],r['engine']) for r in record['rows']}!={(p,e) for p in POLICIES for e in ENGINES}:
                raise ValueError('Checkpoint policy-engine combinations changed')
            calls+=record['localizer_calls'];ocr_calls+=record['unique_ocr_executions']
            for row in record['rows']:
                if row['repeat']!=repeat or row['uid']!=sample['uid']:raise ValueError('Row identity mismatch')
                canonical=[dict(box=[[round(float(x),6) for x in point] for point in p['box']],text=normalized(p['text']))
                           for p in row['_private_predictions']]
                if hash_json(canonical)!=row['prediction_sha256']:raise ValueError('Prediction hash mismatch')
                recomputed=score(sample,row['_private_predictions'],row['routed'])
                if recomputed!=row['score']:score_mismatches.append((repeat,row['uid'],row['policy'],row['engine']))
                for kind in ('wall','cpu'):
                    total=sum(row['timing'][f'{name}_{kind}'] for name in ('decode','localize','transform','detect','recognize','map_boxes'))
                    if not math.isclose(total,row['timing']['total_'+kind],abs_tol=1e-9):timing_mismatches.append(row['uid'])
                rows+=1
                expected[result_key(row)]={k:v for k,v in row.items() if not k.startswith('_private')}
            inventory.append(dict(repeat=repeat,uid=sample['uid'],private_checkpoint_sha256=digest(path),
                input_sha256=sample['input_sha256'],rows=len(record['rows'])))
    if score_mismatches or timing_mismatches:raise ValueError('Saved score/timing audit mismatch')
    forbidden_keys={'text','truth','recognized_text','ground_truth_text','_private_predictions'}
    def inspect(value):
        if isinstance(value,dict):
            if forbidden_keys.intersection(value):raise ValueError('Raw text found in public artifact')
            for child in value.values():inspect(child)
        elif isinstance(value,list):
            for child in value:inspect(child)
    with gzip.open(OUT/'per_image.jsonl.gz','rt',encoding='utf-8') as stream:
        published=[json.loads(line) for line in stream]
    if len(published)!=rows:raise ValueError('Missing or duplicate published row count')
    verify_public_rows(published,expected)
    for row in published:inspect(row)
    summaries=json.loads((OUT/'summary.json').read_text())
    summary_keys=set()
    for item in summaries:
        key=tuple(item[k] for k in ('repeat','policy','engine','stratum'))
        if key in summary_keys:raise ValueError('Duplicate summary key')
        summary_keys.add(key)
        selected=[r for r in published if (r['repeat'],r['policy'],r['engine'])==key[:3] and
                  (r['source']!='midv2020' if key[3]=='primary' else r['selection_stratum']==key[3])]
        recomputed=aggregate(selected)
        if {k:item[k] for k in recomputed}!=recomputed:raise ValueError('Published summary differs from re-aggregation')
    if len(summary_keys)!=3*len(POLICIES)*len(ENGINES)*4:raise ValueError('Incomplete summary')
    events=[json.loads(line) for line in (CACHE/'events.jsonl').read_text().splitlines()]
    failures=[r for r in events if r['event']=='failure']
    save(OUT/'audit.json',dict(signature=signature,code_sha256=digest(__file__),image_checkpoints=len(inventory),
        public_rows=rows,unique_localizer_calls=calls,unique_ocr_executions=ocr_calls,
        re_scored_rows=rows,score_mismatches=0,timing_sum_mismatches=0,raw_text_in_public_rows=False,
        public_rows_equal_private_projection=True,canonical_prediction_hash_mismatches=0,
        summary_rows_recomputed=len(summaries),
        error_events=failures,checkpoint_hashes=inventory,
        interpretation='Hashes support provenance/tamper detection, not mathematical proof of model correctness'))
    print('E2E_AUDIT_PASS',len(inventory),'image checkpoints',rows,'result rows')


if __name__=='__main__':main()
