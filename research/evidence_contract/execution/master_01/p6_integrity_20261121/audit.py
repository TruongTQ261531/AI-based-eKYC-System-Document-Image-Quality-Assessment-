"""P6 retrospective joins. Reads artifacts only. All generator output goes under local/."""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import random
import subprocess

from ....oracle_reliability import pixel_lineage_audit as pixel
from .characterize import summarize

ROOT = Path(__file__).resolve().parents[5]
RES = ROOT/'research/results'
DATA = ROOT/'research/data'
EC = ROOT/'research/evidence_contract'
LOCAL = EC/'local'
EXEC = EC/'execution/master_01'
BASE = '6ff44ed9d7a9001e31778c2abb814e0705fb4e11'
COLLECTIONS = ('vlm_lora_v2','vlm_lora_v2_r2','source_visibility_v3','hard_pairs_v1','fair_controls_v1')
STATES = ('CONFIRMED_SAME_CHECKPOINT_OVERLAP','RECORDED_CROSS_COLLECTION_REUSE','NO_OVERLAP_VERIFIED','UNKNOWN_LINEAGE','OUT_OF_SCOPE')


def sha(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f,'sha256').hexdigest()


def stable(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False).encode()).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def check(condition, message):
    if not condition:
        raise ValueError(message)


def save(path,data):
    with path.open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(data,stream,ensure_ascii=False,indent=2,allow_nan=False)
        stream.write('\n')


def classify(*,in_scope=True, pixel_equal=False, training_included=None, trained_sha=None,
             evaluated_sha=None, exact_evaluated=False, reuse=False, upstream_unknown=False, provenance_consistent=True):
    """For one stated lineage question. Negative proof requires complete membership."""
    if not in_scope:
        return STATES[4]
    if upstream_unknown or not provenance_consistent or not evaluated_sha or not trained_sha or training_included is None:
        return STATES[3]
    if trained_sha == evaluated_sha and training_included and exact_evaluated and pixel_equal:
        return STATES[0]
    if reuse and trained_sha != evaluated_sha:
        return STATES[1]
    if trained_sha == evaluated_sha and not training_included and exact_evaluated:
        return STATES[2]
    return STATES[3]


def links(member, evaluation):
    """Independent signals: an image, a document, and a declared parent can differ."""
    return dict(exact_pixel=member.get('pixel')==evaluation['decoded_pixel'] and bool(member.get('pixel')),
                same_file=member.get('file')==evaluation['file'],
                same_physical_id=any(r.get('physical_id')==evaluation['physical_id'] for r in member['records']),
                evaluation_file_declared_parent=evaluation['file'] in member['bound_parent_files'])


def locate(pattern,digest):
    for p in sorted(LOCAL.glob(pattern)):
        if sha(p)==digest:
            return p
    raise FileNotFoundError('Missing private snapshot with receipt hash for '+pattern)


class Sources:
    def __init__(self):
        self.paths=set()

    def get(self,p):
        self.paths.add(p)
        return read(p)

    def manifest(self):
        paths=sorted(self.paths)
        rel=[p.relative_to(ROOT).as_posix() for p in paths if p.is_relative_to(ROOT)]
        tracked=set(subprocess.check_output(['git','ls-tree','-r','--name-only',BASE],cwd=ROOT,text=True).splitlines())
        tracked_paths=sorted(tracked.intersection(rel))
        history=subprocess.check_output(['git','log',BASE,'--format=@@%H %cI','--name-only','--',*tracked_paths],
                                        cwd=ROOT,text=True,encoding='utf8')
        last={}
        commit=None
        for line in history.splitlines():
            if line.startswith('@@'):
                commit,date=line[2:].split()
            elif line in tracked:
                last.setdefault(line,(commit,date))
        public={}
        private=[]
        for p in paths:
            key=p.relative_to(ROOT).as_posix() if p.is_relative_to(ROOT) else p.as_posix()
            item=dict(sha256=sha(p),bytes=p.stat().st_size,
                      filesystem_mtime_utc=datetime.fromtimestamp(p.stat().st_mtime,timezone.utc).isoformat())
            if key in tracked:
                commit,date=last[key]
                # Git may normalize line endings in root project documents.
                blob=subprocess.check_output(['git','show',BASE+':'+key],cwd=ROOT)
                check(blob.replace(b'\r\n',b'\n')==p.read_bytes().replace(b'\r\n',b'\n'),'Tracked input differs: '+key)
                public[key]=dict(item,git_commit=commit,git_commit_time=date,git_bytes_sha256=hashlib.sha256(blob).hexdigest())
            else:
                private.append(dict(item,path=key))
        return public,private


def find_groups(src):
    receipt=src.get(EXEC/'checklist_20261121/baseline_replay.json')
    index=src.get(locate('checklist*/duplicate_groups.json',receipt['private_group_index_sha256']))
    snapshot=src.get(locate('p2_20261120/*/pixel_private.json',index['lineage_sha256']))
    for f,h in snapshot['manifests'].items():
        path=DATA/f
        check(sha(path)==h,'P2 metadata changed')
        src.paths.add(path)
    rows=snapshot['rows']
    by_file={row['file']:row['pixel'] for row in rows if 'file' in row and 'pixel' in row}
    groups=[]
    for image,indices in sorted(index['pixel'].items()):
        members=[rows[i] for i in indices]
        roles={(r['dataset'],r.get('role')) for m in members for r in m['records']}
        v4={role for coll,role in roles if coll=='recovery_v4' and role in ('development','test','calibration')}
        if not v4 or not any(role=='train' for coll,role in roles if coll!='recovery_v4'):
            continue
        check(len(v4)==1 and {c for c,s in roles if s=='train'}==set(COLLECTIONS),'Unexpected P2 collection roles')
        for m in members:
            path=DATA/m['path']
            observed=pixel.inspect(path,DATA)
            check((observed.get('file'),observed.get('pixel'))==(m['file'],image),'Changed candidate image')
            src.paths.add(path)
        groups.append(dict(pixel=image,role=v4.pop(),members=[{k:m[k] for k in ('path','file','pixel','records','bound_parent_files')} for m in members]))
    check(Counter(g['role'] for g in groups)==dict(test=10,development=8,calibration=6),'P2 exact candidate universe')
    return groups,by_file


def recovery(src,groups,by_file):
    folder=RES/'recovery_v4'
    def get(f):return src.get(folder/(f+'.json'))
    manifest=get('manifest')
    sig=manifest['signature']
    check(stable({k:v for k,v in manifest.items() if k!='signature'})==sig,'V4 signature')
    audit=get('independent_audit')
    execution=get('execution')
    models=get('selector_models')
    lock=get('selector_lock')
    check(all(record['signature']==sig for record in (audit,execution,models,lock)),'V4 signature linkage')
    check(sha(folder/'selector_models.json')==lock['model_sha256']==audit['model_sha256'],'Selector artifact')
    check(execution['expected_cases']==588 and execution['exit_status']=='complete','V4 completion')
    for file,h in (manifest['code_sha256']|manifest['shared_code_sha256']).items():
        path=ROOT/'research'/file
        check(sha(path)==h,'V4 code drift')
        src.paths.add(path)
    src.get(folder/'analysis_provenance.json')
    dm=get('dataset_manifest')
    check(manifest['inputs']==[{k:x[k] for k in ('uid','physical_id','role','input_sha256')} for x in dm],'V4 input list')
    check(len(dm)==540,'V4 frame')
    checkpoints={(x['uid'],x['repeat']):x['sha256'] for x in audit['checkpoint_hashes']}
    cache=ROOT/'research/cache/recovery_v4'
    events=cache/'events.jsonl'
    src.paths.add(events)
    timeline=[json.loads(line) for line in events.read_text().splitlines()]
    times={(x['uid'],x['repeat']):x['time_utc'] for x in timeline if x['event']=='case_complete'}
    legacy=get('legacy_panel')
    online=get('online_traces')
    assets=manifest['assets']
    up=ROOT/'research/cache/upstream'
    weights={}
    def weight(label,file,expected):
        src.paths.add(file)
        check(sha(file)==expected,'V4 component bytes '+label)
        weights[label]=expected
    for f,h in assets['files_sha256'].items():
        if f.endswith('.onnx'):
            weight(Path(f).name,up/'rapid144'/f,h)
    weight('latin_PP-OCRv5_rec_mobile',up/'latin_PP-OCRv5_rec_mobile.onnx',assets['latin_model_sha256'])
    weight('lcnet100',up/'lcnet100.onnx',assets['lcnet_sha256'])
    fast_src=ROOT/'research/neural_baseline.py'
    import ast
    tree=ast.parse(fast_src.read_text(encoding='utf8'))
    fast=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='MODEL_SHA' for t in n.targets))
    src.paths.add(fast_src)
    weight('fastvit_sa24',ROOT/'research/cache/docaligner/fastvit_sa24.onnx',fast)
    for item in legacy['models']:
        if item['file'].endswith('.pth'):
            weight('legacy/'+Path(item['file']).name,ROOT.parents[1]/'models'/item['file'],item['sha256'])
    fit_ids={x['physical_id'] for x in dm if x['role']=='development'}
    cal_ids={x['physical_id'] for x in dm if x['role']=='calibration'}
    test_ids={x['physical_id'] for x in dm if x['role']=='test'}
    check(not(fit_ids & test_ids or fit_ids & cal_ids or cal_ids & test_ids),'V4 ID split')
    check(all(set(s['training_ids'])==fit_ids for s in models['selectors'].values()),'Selector fit IDs')
    fit_pixels={by_file[x['input_sha256']] for x in dm if x['role']=='development'}
    cal_pixels={by_file[x['input_sha256']] for x in dm if x['role']=='calibration'}
    eval_pixels={by_file[x['input_sha256']] for x in dm if x['role']=='test'}
    check(not ((fit_pixels|cal_pixels)&eval_pixels or fit_pixels&cal_pixels),'V4 decoded-pixel split')
    readers=set(manifest['readers'])
    legacy_hits=online_hits=0
    for g in groups:
        matches=[x for x in dm if by_file[x['input_sha256']]==g['pixel'] and x['role']==g['role']]
        check(len(matches)==1,'Ambiguous candidate evaluation')
        x=matches[0]
        uid=x['uid']
        raw=cache/'pass1'/(hashlib.sha256(uid.encode()).hexdigest()[:24]+'.json')
        cp=src.get(raw)
        check(sha(raw)==checkpoints[uid,1] and cp['signature']==sig and cp['repeat']==1 and
              all(cp[k]==x[k] for k in ('uid','role','physical_id','input_sha256')),'Private evaluation receipt')
        check({z['engine'] for z in cp['rows']}==readers,'Actual V4 readers')
        legacy_readers=sorted({y['reader'] for y in legacy['rows'] if y['uid']==uid})
        online_records=[y for y in online['rows'] if y['uid']==uid]
        check(all(y['signature']==sig and y['model_sha256']==lock['model_sha256'] for y in online_records),'Online selector seal')
        legacy_hits+=bool(legacy_readers)
        online_hits+=bool(online_records)
        g['evaluation']=dict(uid=uid,physical_id=x['physical_id'],file=x['input_sha256'],decoded_pixel=g['pixel'],
                             split=x['role'],run_signature=sig,record_sha256=sha(raw),event_utc=times[uid,1],
                             engines=sorted(readers),selector_fit_id=x['physical_id'] in fit_ids,
                             selector_fit_pixel=g['pixel'] in fit_pixels,legacy_readers=legacy_readers,online_rows=len(online_records))
    return dict(signature=sig,readers=sorted(readers),components=weights,selector_sha256=lock['model_sha256'],
                role_ids=dict(development=len(fit_ids),calibration=len(cal_ids),test=len(test_ids)),
                train_test_physical_id_intersection=len(fit_ids&test_ids),train_test_pixel_intersection=len(fit_pixels&eval_pixels),
                calibration_test_pixel_intersection=len(cal_pixels&eval_pixels),legacy_panel_groups=legacy_hits,online_panel_groups=online_hits,
                start_utc=next(x['time_utc'] for x in timeline if x['event']=='start'),
                end_utc=next(x['time_utc'] for x in timeline if x['event']=='inference_complete'))


def sequence(rows,seed,count):
    result=[]
    for epoch in range((count+len(rows)-1)//len(rows)):
        order=list(rows)
        random.Random(seed+epoch).shuffle(order)
        result.extend(order)
    return result[:count]


def checkpoint_gap(log_path):
    """A missing file or a conflicting identity breaks that individual train link."""
    if not log_path.is_file():
        return 'missing_training_log'
    rec=read(log_path)
    if not rec.get('selected_checkpoint') or not rec.get('selected_adapter_sha256'):
        return 'missing_selected_checkpoint_identity'
    cp=ROOT/rec['selected_checkpoint']
    seal=cp/'complete.json'
    if not seal.is_file():
        return 'missing_checkpoint_manifest'
    state=read(seal)
    if any(not (cp/f).is_file() for f in (*state.get('sha256',{}),'adapter_model.safetensors')):
        return 'missing_checkpoint_bytes'
    if (state.get('signature')!=rec.get('signature') or
            state.get('sha256',{}).get('adapter_model.safetensors')!=rec['selected_adapter_sha256']
            or sha(cp/'adapter_model.safetensors')!=rec['selected_adapter_sha256']):
        return 'checkpoint_provenance_mismatch'
    return None


def train_and_evaluate(src,groups,by_file):
    runs={}
    gaps=[]
    arms={'vlm_lora_v2_r2':('control','partial'),'source_visibility_v3':('source',),
          'hard_pairs_v1':('hard',),'fair_controls_v1':('random','repeat')}
    group_by_pixel={g['pixel']:g for g in groups}
    for g in groups:
        g['training']={}
        g['adapter_evaluations']=[]
    # The pilot has preparation/probe evidence. The R2 run has its own membership and weights.
    for collection in COLLECTIONS:
        folder=RES/collection
        dataset=src.get(folder/'dataset_manifest.json')
        card=src.get(folder/'dataset_card.json')
        if collection=='vlm_lora_v2':
            src.get(folder/'probe_raw2.json')
            continue
        fair=collection=='fair_controls_v1'
        path=DATA/collection/('train.json' if fair else 'samples.json')
        samples=src.get(path)
        check(sha(path)==card['train_sha256' if fair else 'samples_sha256'],'Train data seal')
        for log in sorted(folder/f'train_{arm}_{seed}.json' for arm in arms[collection] for seed in (42,31415)):
            gap=checkpoint_gap(log)
            if gap:
                gaps.append(dict(collection=collection,run=log.stem,status=STATES[3],reason=gap))
                continue
            rec=src.get(log)
            arm=log.stem.split('_')[1]
            rows=samples[arm] if fair else [x for x in samples if x['role']=='train' and
                 (collection=='hard_pairs_v1' or x.get('variant')==(arm if collection=='vlm_lora_v2_r2' else 'partial'))]
            cp=ROOT/rec['selected_checkpoint']
            complete=src.get(cp/'complete.json')
            digest=rec['selected_adapter_sha256']
            for f,h in complete['sha256'].items():
                check(sha(cp/f)==h,'Checkpoint component differs')
                src.paths.add(cp/f)
            check(complete['sha256']['adapter_model.safetensors']==digest and complete['signature']==rec['signature']
                  and complete['cursor']==rec['presentations']==1280 and complete['step']==rec['steps']==320
                  and complete['seed']==rec['seed'],'Training completion binding')
            order=sequence(rows,rec['seed'],complete['cursor'])
            slots=stable([x['physical_id']+'/'+str(x['slot']) for x in order])
            check(slots==rec['identity_slot_sequence_sha256'] and len({(r['physical_id'],r['slot']) for r in rows})==len(rows)==640,'ID-slot seal')
            files=stable([x['input_sha256'] for x in order])
            if 'pixel_sequence_sha256' in rec:
                check(files==rec['pixel_sequence_sha256'],'Raster order seal')
            check([ev['step'] for ev in rec['events']]==list(range(1,321)),'Training events')
            hits=Counter()
            source_ids={r['physical_id'] for r in order}
            for group in groups:
                if group['evaluation']['physical_id'] in source_ids:
                    group.setdefault('training_physical_id_matches',[]).append(digest)
            for x in order:
                h=by_file.get(x['input_sha256'])
                if h in group_by_pixel:
                    hit=group_by_pixel[h]['training'].setdefault(digest,dict(rows=[],presentations=0))
                    hit['presentations']+=1
                    entry={k:x[k] for k in ('physical_id','uid','slot','input_sha256')}
                    if entry not in hit['rows']:
                        hit['rows'].append(entry)
                    hits[h]+=1
            check(digest not in runs,'Duplicate training run identifier')
            runs[digest]=dict(collection=collection,run=log.stem,adapter_sha256=digest,train_signature=rec['signature'],
                membership_basis='sealed ID/slot order and sealed dataset' if 'pixel_sequence_sha256' not in rec else 'sealed ID/slot and raster sequences',
                candidate_training_groups=len(hits),candidate_presentations=sum(hits.values()),steps=320,
                first_step_utc=rec['events'][0]['time_utc'],last_step_utc=rec['events'][-1]['time_utc'],evaluations=[])
        # Reused adapters at later milestones are linked by digest across collections below.
    for collection in COLLECTIONS[1:]:
        folder=RES/collection
        lock=src.get(folder/'test_lock.json')
        frame=src.get(folder/'dataset_manifest.json')
        for key,binding in lock['models'].items():
            digest=binding['sha256']
            if digest not in runs:
                continue
            for role in ('development','test'):
                file=folder/f'{role}_{key}.json'
                record=src.get(file)
                actual=record['rows']
                expected={(r['uid'],r['physical_id'],r['input_sha256']) for r in frame if r['role']==role}
                observed={(r['uid'],r['physical_id'],r['input_sha256']) for r in actual}
                check(observed==expected and len(actual)==len(expected),'Evaluation frame mismatch')
                check(record['signature']==lock['signature'] and record.get('model_sha256',digest)==digest
                      and all(r['model_sha256']==digest for r in actual),'Evaluation checkpoint mismatch')
                # Missing P2 pixel mapping cannot serve as evidence of absence.
                check(all(r['input_sha256'] in by_file for r in actual),'Missing evaluation pixel lineage')
                pixels={by_file[r['input_sha256']] for r in actual}
                evaluation_ids={r['physical_id'] for r in actual}
                same=0
                for image in pixels & group_by_pixel.keys():
                    g=group_by_pixel[image]
                    g['adapter_evaluations'].append(dict(collection=collection,split=role,adapter_sha256=digest,
                         evaluation_sha256=sha(file),in_training=digest in g['training']))
                    same+=int(digest in g['training'])
                runs[digest]['evaluations'].append(dict(collection=collection,split=role,arm=key,rows=len(actual),
                    file=file.relative_to(ROOT).as_posix(),candidate_pixel_groups=len(pixels&group_by_pixel.keys()),
                    candidate_physical_ids=sum(g['evaluation']['physical_id'] in evaluation_ids for g in groups),
                    confirmed_candidate_overlap=same))
    return list(runs.values()),gaps


def auxiliary(src,groups,by_file):
    v1=RES/'vlm_lora_v1'
    assets=src.get(v1/'assets.json')
    base=src.get(v1/'training_environment.json')['model_sha256']
    source=next(item for item in assets['model'] if item['file']=='model.safetensors')
    base_file=ROOT/'research/cache/vlm_lora_v1/model/model.safetensors'
    check(source['sha256']==base and sha(base_file)==base,'Original VLM bytes')
    src.paths.add(base_file)
    old=src.get(v1/'train_seed_42.json')
    folder=ROOT/old['selected_checkpoint']
    complete=src.get(folder/'complete.json')
    path=folder/'adapter_model.safetensors'
    adapter=old['selected_adapter_sha256']
    check(sha(path)==adapter==complete['sha256'][path.name] and complete['signature']==old['signature'],'Imported V1 bytes')
    src.paths.add(path)
    samples=DATA/'vlm_lora_v1/samples.json'
    card=src.get(v1/'dataset_card.json')
    check(sha(samples)==card['data_sha256'],'V1 dataset changed')
    pool=[x for x in src.get(samples) if x['role']=='train']
    pixels={by_file[x['input_sha256']] for x in sequence(pool,42,complete['cursor'])}
    targets={g['pixel'] for g in groups}
    results=[]
    for coll in ('vlm_lora_v2_r2','source_visibility_v3'):
        lock=src.get(RES/coll/'test_lock.json')
        for name,h in [('original',base),('v1',adapter)]:
            check(lock['models'][name]['sha256']==h,'Imported model lock')
            for role in ('development','test'):
                record=src.get(RES/coll/f'{role}_{name}.json')
                check(record['model_sha256']==h and all(r['model_sha256']==h for r in record['rows']),'Imported model evaluation')
                overlap={by_file[r['input_sha256']] for r in record['rows']}&targets
                results.append(dict(collection=coll,model=name,role=role,candidate_groups=len(overlap)))
    return dict(base=assets['model_id'],revision=assets['revision'],base_sha256=base,pretraining=STATES[3],
                imported_v1_adapter_sha256=adapter,imported_v1_selected_step=complete['step'],
                imported_v1_candidate_training_groups=len(pixels&targets),evaluations=results)


def main(output):
    output=output.resolve()
    check(output.is_relative_to(LOCAL.resolve()) and output!=LOCAL.resolve(),'Output must be a new private local subdirectory')
    output.mkdir(parents=True,exist_ok=False)
    src=Sources()
    groups,by_file=find_groups(src)
    v4=recovery(src,groups,by_file)
    runs,gaps=train_and_evaluate(src,groups,by_file)
    imported=auxiliary(src,groups,by_file)
    check(all(r['adapter_sha256'] not in v4['components'].values() and r['first_step_utc']>v4['end_utc'] for r in runs),
          'Review chronology or checkpoint match before release')
    for g in groups:
        for member in g['members']:
            member['links_to_evaluation']=links(member,g['evaluation'])
        matched=next((x for x in g['adapter_evaluations'] if x['in_training']),None)
        digest=matched['adapter_sha256'] if matched else next(iter(g['training']),None)
        g['status']=classify(pixel_equal=True,training_included=True if digest else None,trained_sha=digest,
            evaluated_sha=matched['adapter_sha256'] if matched else v4['components']['latin_PP-OCRv5_rec_mobile'],
            exact_evaluated=True,reuse=True)
        g['upstream_pretraining']=STATES[3]
        g['scope']='P2 candidate, archived V4 and linked local adapter evaluation frames'
    counts=Counter(g['status'] for g in groups)
    d4=EXEC/'d4_development_20261117'
    results=src.get(d4/'controls_01/control_results.json')
    history=src.get(d4/'historical_01/summary.json')
    characterization=summarize(results,history,src.get(d4/'controls_01/summary.json')['counterexamples'])
    for p in ('expected_controls.json','divergences.json','manifest.json','guard_matrix.json'):
        src.get(d4/'controls_01'/p)
    for name in ('AGENTS.md','PROJECT_SYNC_POLICY.md','PROJECT_HANDOFF_20261120_VI.md','research/RECOVERY_RESULTS_VI.md','research/RESEARCH_V4_PROTOCOL.md'):
        src.paths.add(ROOT/name)
    for name in ('NEXT_ACTIONS.md','P2_AUDIT_VI.md','P5B_STATISTICAL_CALIBRATION_VI.md','D4_MECHANISM_BOUNDS_VI.md','B_PROTOCOL_V4_CANDIDATE.md'):
        src.paths.add(EC/name)
    for name in ('vlm_train','v2_study','v2_common','v3_study','v3_common','hp_common','hp_study','fc_common','fc_study'):
        src.paths.add(ROOT/'research'/(name+'.py'))
    for collection, filenames in [('vlm_lora_v1',['assets','training_environment','train_seed_42']),('vlm_lora_v2',['pretrain_checks']),('fair_controls_v1',['training_state_inventory','pixel_manifest']),('vlm_lora_v2_r2',['pretrain_checks']),('source_visibility_v3',['audit']),('hard_pairs_v1',['training_changes'])]:
        for f in filenames:
            src.get(RES/collection/(f+'.json'))
    public,private=src.manifest()
    save(output/'membership_private.json',groups)
    save(output/'sources_private.json',private)
    save(output/'checkpoint_lineage_private.json',dict(runs=runs,groups={g['pixel']:dict(evaluation=g['evaluation'],training=g['training'],adapter_evaluations=g['adapter_evaluations']) for g in groups}))
    aggregate=dict(groups=len(groups),by_role=dict(Counter(g['role'] for g in groups)),
        missing_lineage={'external_ocr_geometry_pretraining':dict(status='UNKNOWN_LINEAGE',groups=len(groups)),
            'original_vlm_pretraining':dict(status='UNKNOWN_LINEAGE',unit='checkpoint',count=1),
            'v2_pilot_to_v4_checkpoint':dict(status='OUT_OF_SCOPE',basis='preparation and development probes, no main V4 reader link'),
            'imported_checkpoints':dict(unit='model evaluation',note='same digest can be reused across studies; separate train and evaluation signatures'),
            'independent_truth_at_D4':dict(status='BLOCKED_INDEPENDENT_TRUTH',missed_true_faults=None)},
        status_counts={s:counts[s] for s in STATES},checkpoint_pretraining_unknown_groups=len(groups),
        group_training_adapter_count=dict(sorted(Counter(str(len(g['training'])) for g in groups).items())),
        by_role_and_status={r:dict(Counter(g['status'] for g in groups if g['role']==r)) for r in ('development','calibration','test')},
        distinct_candidate_physical_ids=len({g['evaluation']['physical_id'] for g in groups}),
        candidate_member_files=sum(len(g['members']) for g in groups),
        groups_with_bound_parent=sum(any(m['bound_parent_files'] for m in g['members']) for g in groups),
        recovery=v4,local_adapters=runs,local_checkpoint_gaps=gaps,imported_vlm=imported,d4=characterization)
    save(output/'aggregate.json',aggregate)
    save(output/'manifest.json',dict(baseline=BASE,public_inputs=public,
        private_receipts={f:sha(output/f) for f in ('membership_private.json','sources_private.json','checkpoint_lineage_private.json')},
        private_source_files=len(private),status='historical artifact join only'))


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('output',type=Path)
    main(cli.parse_args().output)
