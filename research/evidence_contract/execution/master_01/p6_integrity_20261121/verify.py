"""Separate retrospective verifier with a public mode and a membership replay on the authorized host."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import random
import subprocess

ROOT=Path(__file__).resolve().parents[5]
HERE=Path(__file__).resolve().parent
EC=ROOT/'research/evidence_contract'
BASE='6ff44ed9d7a9001e31778c2abb814e0705fb4e11'
STATES={'CONFIRMED_SAME_CHECKPOINT_OVERLAP','RECORDED_CROSS_COLLECTION_REUSE','NO_OVERLAP_VERIFIED','UNKNOWN_LINEAGE','OUT_OF_SCOPE'}


def require(ok,note):
    if not ok:
        raise ValueError(note)


def load(p):
    return json.loads(p.read_bytes())


def digest(p):
    with p.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def release_check(data, forbidden=()):
    """Reject row-level membership, private paths, identity values and raw payloads."""
    prohibited={'path','uid','physical_id','members','records','bound_parent_files','input_sha256','file_sha256',
                'decoded_pixel','raw_text','predicted_fields','fields','reference_payload','target','truth','source_id','training_state'}
    def visit(node):
        if isinstance(node,dict):
            require(not prohibited.intersection(node),'Private row or payload key')
            for k,v in node.items():
                visit(k)
                visit(v)
        elif isinstance(node,list):
            for value in node:
                visit(value)
        elif isinstance(node,str):
            norm=node.replace('\\','/').lower()
            require(':/' not in norm and not norm.startswith('/') and '/local/' not in norm
                    and '/cache/' not in norm and node not in forbidden,'Private path, member or fingerprint')
    visit(data)


def verify_d4(data):
    d4=EC/'execution/master_01/d4_development_20261117'
    rows=load(d4/'controls_01/control_results.json')
    expected=Counter()
    gate_counts=Counter()
    no_literal=Counter()
    for row in rows:
        for tier,s in row['panels'].items():
            aa=s['arms']['mrz_metadata_asserted']
            cc=s['arms']['checked_v2']
            ref=row['shared_input']['reference']
            key=row['shared_input']['context']['key']
            kind=ref['value_kind'] if ref else 'unavailable'
            kind=kind if isinstance(kind,str) else 'malformed_value_kind'
            sources='+'.join(sorted({src['kind'] if isinstance(src,dict) and isinstance(src.get('kind'),str)
                                      else 'malformed_source' for src in ref['after']['sources']})) if ref else ''
            dims=(int(tier),key,kind,sources or 'unavailable')
            reason=cc['pointwise']['reason']
            gate=reason if reason in ('output_binding','reference_rejected','structure_unusable','mutation_gate') else 'entered_resolver'
            gate_counts[int(tier),gate]+=1
            no_literal[int(tier)]+=s['cost']['arms']['checked_v2']['literal_td3_calls']==0
            for ep in ('pointwise','relation'):
                expected[dims+(ep,aa[ep]['state'],cc[ep]['state'],aa[ep]['reason'],cc[ep]['reason'])]+=1
    observed=Counter()
    gates=Counter()
    skipped=Counter()
    for s in data['strata']:
        gates[s['tier'],s['shared_gate']]+=s['count']
        if s['after_literal']=='not_called_on_pair':
            skipped[s['tier']]+=s['count']
        for ep in ('pointwise','relation'):
            key=tuple(s[k] for k in ('tier','field','value_kind','after_sources'))+(
                ep,s[ep+'_asserted'],s[ep+'_checked'],s[ep+'_asserted_reason'],s[ep+'_checked_reason'])
            observed[key]+=s['count']
            for source,metric in [('FAULT','withdrawn_alarms'),('NO_FAULT','withdrawn_no_fault')]:
                require(s[ep+'_'+metric]==s['count']*int(s[ep+'_asserted']==source and s[ep+'_checked'] in ('INVALID_TEST','UNKNOWN')),'Withdrawal reason')
    require(expected==observed and sum(s['count'] for s in data['strata'])==144,'D4 strata or reason mismatch')
    require(gates==gate_counts and no_literal==skipped,'Shared gates or literal calls')
    history=load(d4/'historical_01/summary.json')
    require(data['replay']=={k:history[k] for k in data['replay']} and history['truth_labels_used'] is False
            and data['missed_true_faults'] is None and data['real_fault_sensitivity'] is None,'Historical truth denominator')
    for tier in ('1','2'):
        require(data['withdrawals'][tier]=={'pointwise':{'FAULT':6,'NO_FAULT':2},'relation':{'FAULT':4,'NO_FAULT':1}},'Tier withdrawals')


def verify_public(folder):
    manifest=load(folder/'manifest.json')
    agg=load(folder/'aggregate.json')
    require(manifest['baseline']==BASE,'Baseline')
    for f,meta in manifest['public_inputs'].items():
        require(f and not Path(f).is_absolute() and '..' not in Path(f).parts,'Unscoped artifact')
        data=subprocess.check_output(['git','show',BASE+':'+f],cwd=ROOT)
        require(hashlib.sha256(data).hexdigest()==meta['git_bytes_sha256'],'Historical blob changed')
    release_check(agg)
    require(set(agg['status_counts'])==STATES and sum(agg['status_counts'].values())==agg['groups']==24,'Status accounting')
    roles=load(EC/'execution/master_01/p2_20261120/verification.json')['cross_role_exact_pixel_patterns']
    want={next(x['role'] for x in r['collection_roles'] if x['collection']=='recovery_v4'):r['pixel_groups'] for r in roles}
    require(want==agg['by_role'],'P2 split totals')
    recovery=agg['recovery']
    results=ROOT/'research/results'
    v4=load(results/'recovery_v4/manifest.json')
    require(sorted(v4['readers'])==recovery['readers'] and v4['signature']==recovery['signature'],'V4 readers and run')
    expected=load(results/'recovery_v4/selector_lock.json')['model_sha256']
    require(digest(results/'recovery_v4/selector_models.json')==expected==recovery['selector_sha256'],'Selector lock')
    for run in agg['local_adapters']:
        train=load(results/run['collection']/(run['run']+'.json'))
        h=train['selected_adapter_sha256']
        require(h==run['adapter_sha256'] and run['first_step_utc']>recovery['end_utc'] and h not in recovery['components'].values(),'Run lineage or chronology')
        for ev in run['evaluations']:
            lock=load(results/ev['collection']/'test_lock.json')
            evaluated=load(ROOT/ev['file'])
            require(lock['models'][ev['arm']]['sha256']==h and all(r['model_sha256']==h for r in evaluated['rows'])
                    and len(evaluated['rows'])==ev['rows'],'Checkpoint use in evaluation')
    verify_d4(agg['d4'])
    return dict(public_source_artifacts=len(manifest['public_inputs']),candidate_groups=24,
                local_adapter_runs=len(agg['local_adapters']),paired_D4_evaluations=144)


def verify_private(folder,local):
    from PIL import Image,ImageOps
    agg=load(folder/'aggregate.json')
    manifest=load(folder/'manifest.json')
    for name,h in manifest['private_receipts'].items():
        require(digest(local/name)==h,'Private join receipt')
    inventory=load(local/'sources_private.json')
    snapshot=next(ROOT/m['path'] for m in inventory if m['path'].endswith('/pixel_private.json'))
    index=next(ROOT/m['path'] for m in inventory if m['path'].endswith('/duplicate_groups.json'))
    p0=load(EC/'execution/master_01/checklist_20261121/baseline_replay.json')
    require(digest(index)==p0['private_group_index_sha256'] and digest(snapshot)==load(index)['lineage_sha256'],'Private snapshot seal')
    rows=load(snapshot)['rows']
    bins=defaultdict(list)
    for row in rows:
        if 'pixel' in row:
            bins[row['pixel']].append(row)
    groups={}
    for h,rs in bins.items():
        roles={(rec['dataset'],rec.get('role')) for r in rs for rec in r['records']}
        if any(c=='recovery_v4' and s in ('development','calibration','test') for c,s in roles) and any(c!='recovery_v4' and s=='train' for c,s in roles):
            groups[h]=rs
    private=load(local/'membership_private.json')
    by_pixel={g['pixel']:g for g in private}
    require(groups.keys()==by_pixel.keys() and len(private)==24,'Independent pixel groups')
    mapped={r['file']:r['pixel'] for r in rows if 'pixel' in r}
    forbidden=set(groups)
    fit=load(ROOT/'research/results/recovery_v4/selector_models.json')['selectors']
    legacy=load(ROOT/'research/results/recovery_v4/legacy_panel.json')['rows']
    online=load(ROOT/'research/results/recovery_v4/online_traces.json')['rows']
    for h,rs in groups.items():
        g=by_pixel[h]
        ev=g['evaluation']
        cp=ROOT/'research/cache/recovery_v4/pass1'/(hashlib.sha256(ev['uid'].encode()).hexdigest()[:24]+'.json')
        rec=load(cp)
        require(digest(cp)==ev['record_sha256'] and rec['role']==g['role'] and rec['input_sha256']==ev['file']
                and rec['physical_id']==ev['physical_id'] and set(ev['engines'])=={x['engine'] for x in rec['rows']},'V4 case linkage')
        require({m['path'] for m in g['members']}=={m['path'] for m in rs},'Missing member')
        require(all((ev['physical_id'] in s['training_ids'])==ev['selector_fit_id'] for s in fit.values())
                and ev['selector_fit_id']==(g['role']=='development'),'Selector fit membership')
        require(ev['legacy_readers']==sorted({x['reader'] for x in legacy if x['uid']==ev['uid']})
                and ev['online_rows']==sum(x['uid']==ev['uid'] for x in online),'Auxiliary panel membership')
        forbidden.update([ev['uid'],ev['physical_id'],ev['record_sha256']])
        for m in rs:
            f=ROOT/'research/data'/m['path']
            require(digest(f)==m['file'],'File bytes')
            with Image.open(f) as image:
                rgb=ImageOps.exif_transpose(image).convert('RGB')
                prefix=f'rgb-exif/1|RGB|{rgb.width}x{rgb.height}|'.encode()
                require(hashlib.sha256(prefix+rgb.tobytes()).hexdigest()==h,'Pixel bytes')
            forbidden.update([m['file'],m['path'],*m['bound_parent_files']])
    used=defaultdict(set)
    scored=defaultdict(set)
    for run in agg['local_adapters']:
        coll=run['collection']
        log=load(ROOT/'research/results'/coll/(run['run']+'.json'))
        path=ROOT/log['selected_checkpoint']
        require(digest(path/'adapter_model.safetensors')==run['adapter_sha256'],'Local adapter bytes')
        rows_file=ROOT/'research/data'/coll/('train.json' if coll=='fair_controls_v1' else 'samples.json')
        sample=load(rows_file)
        arm=run['run'].split('_')[1]
        if isinstance(sample,dict):
            pool=sample[arm]
        else:
            pool=[x for x in sample if x['role']=='train' and (coll=='hard_pairs_v1' or
                  x['variant']==(arm if coll=='vlm_lora_v2_r2' else 'partial'))]
        # A full permutation per epoch proves exposure of every row twice.
        require(2*len(pool)==log['presentations'],'Epochs')
        ordered=[]
        for epoch in range(2):
            order=list(range(len(pool)))
            random.Random(log['seed']+epoch).shuffle(order)
            ordered.extend(pool[i] for i in order)
        slot_hash=hashlib.sha256(json.dumps([x['physical_id']+'/'+str(x['slot']) for x in ordered],ensure_ascii=False).encode()).hexdigest()
        require(slot_hash==log['identity_slot_sequence_sha256'],'Exposure order')
        counter=Counter(mapped[x['input_sha256']] for x in ordered)
        matches={h:n for h,n in counter.items() if h in groups}
        for h in matches:
            used[h].add(run['adapter_sha256'])
        require(len(matches)==run['candidate_training_groups'] and sum(matches.values())==run['candidate_presentations'],'Training membership')
        for h,g in by_pixel.items():
            require(g['training'].get(run['adapter_sha256'],{}).get('presentations',0)==matches.get(h,0),'Per-group train join')
        for ev in run['evaluations']:
            actual=load(ROOT/ev['file'])['rows']
            evaluated={mapped[x['input_sha256']] for x in actual} & groups.keys()
            for h in evaluated:
                scored[h].add(run['adapter_sha256'])
            require(len(evaluated)==ev['candidate_pixel_groups'] and len(evaluated&matches.keys())==ev['confirmed_candidate_overlap'],'Exact evaluation overlap')
    independent={}
    for h in groups:
        if used[h] & scored[h]:
            independent[h]='CONFIRMED_SAME_CHECKPOINT_OVERLAP'
        elif used[h] and not used[h].intersection(agg['recovery']['components'].values()):
            independent[h]='RECORDED_CROSS_COLLECTION_REUSE'
        else:
            independent[h]='UNKNOWN_LINEAGE'
        require(by_pixel[h]['status']==independent[h] and by_pixel[h]['upstream_pretraining']=='UNKNOWN_LINEAGE','Verdict per group')
    tallies=Counter(independent.values())
    require(all(tallies[k]==v for k,v in agg['status_counts'].items()),'Group verdict totals')
    release_check(agg,forbidden)
    release_check(manifest,forbidden)
    return dict(exact_groups_checked=len(groups),member_files_redecoded=sum(map(len,groups.values())),
                independent_membership_and_training_replay=True,private_token_release_scan='PASS')


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('folder',type=Path)
    cli.add_argument('--private',type=Path)
    args=cli.parse_args()
    result=dict(status='PASS',public=verify_public(args.folder))
    if args.private:
        result['private']=verify_private(args.folder,args.private)
    print(json.dumps(result,indent=2))
