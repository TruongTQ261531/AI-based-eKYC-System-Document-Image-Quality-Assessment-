"""Independent arithmetic, immutable evidence and deliverable verification. No model calls."""
import argparse
from collections import Counter
from functools import lru_cache
from itertools import combinations
from pathlib import Path
from hashlib import sha256
import subprocess

import cv2
import numpy as np
from PIL import Image, ImageOps

from ..reviewer_tools.strict import canonical, digest, need
from ..task55.data import EC, ROOT, read, save_new, sha
from ..task55 import agreement, ifv
from ..adjudication.post_p6_closure import ROSTER, originals
from .p2_audit import HISTORY
from .reference_registry import approved_ids, production_trust

BASE = 'c99e467ddf403afed5bd520a0b69d22d277a38d0'
MASTER = EC/'execution/master_01'
P2 = MASTER/'p2_20261120'


def verify_round(dest, a):
    views = read(dest/'review_views.json')
    phases, labels = {}, {}
    need(set(views)==set(a['members'])==set(ROSTER),'Owner roster')
    for name,(sid,output) in ROSTER.items():
        item=a['members'][name]
        (p1,h1),(p2,h2)=originals(name,sid,output)
        need([sha(p1),sha(p2)]==[h1,h2]==item['raw_sha256'],'Original review bytes')
        phases[name]=read(p1)
        need([digest(phases[name]),digest(read(p2))]==[sid,output]==item['snapshots'],'Review snapshots')
        need(item['complete']==[len(phases[name]['items']),len(read(p2)['items'])]==[86,46],'Completion counts')
        view=views[name]
        need(digest(view)==item['view_sha256'] and view['raw_sha256']==h2,'Immutable closure view')
        path,=ifv.STAGE2.glob('*/submissions/'+output+'/output_observations.json')
        jl=ifv.JOINS/(path.parents[2].name+'.json')
        need(sha(jl)==item['join_sha256'],'Historical case join')
        join={k:v['identity_sha256'] for k,v in read(jl).items()}
        need(digest(join)==view['join_sha256'],'View join binding')
        answers={i['case_id']:i for i in read(p2)['items']}
        actual={r['identity']:r['judgment'] for r in view['items']}
        need(all(actual[join[k]]=={dim:raw[dim] for dim in ('test_validity','before_reading','after_reading','absence_check')}
                 for k,raw in answers.items()),'View answers')
        labels[name]={join[k]:v for k,v in read(path.parent/'labels.json').items()}
        need(dict(Counter(i['prior_exposure'] for i in phases[name]['items']))==item['exposure'],'Exposure counts')
    pending=read(dest/'closure_payload.canonical.json')
    need((dest/'closure_payload.canonical.json').read_bytes()==canonical(pending) and
         sha(dest/'closure_payload.canonical.json')==a['pending_payload_sha256'] and
         pending['view_sha256']==sorted(digest(v) for v in views.values()) and
         pending['authority_id'] is None and pending['timestamp'] is None,'Unsigned closure binding')
    for first,second in combinations(ROSTER,2):
        pair=a['pairs'][first+'_'+second]
        one=agreement.compare([phases[first],phases[second]],read(agreement.PACKET_ROOT/'packet_manifest.json'))
        need(one['categorical']==pair['phase1'] and one['readable_transcript_exact_agreement']==pair['transcript'],'Phase 1 agreement')
        m,n=[{r['identity']:r['judgment'] for r in views[k]['items']} for k in (first,second)]
        need(m.keys()==n.keys() and sum(m[k]==n[k] for k in m)==pair['phase2_raw_exact'],'Phase 2 agreement')
        for col,matched in pair['endpoints'].items():
            need(sum(labels[first][k][col]==labels[second][k][col] for k in m)==matched,'Derived label count')
    queue=read(dest/'organizer_queue.json')
    need(len(queue['phase1'])==a['phase1_queue'] and len(queue['phase2'])==a['phase2_queue'],'Queue arithmetic')


@lru_cache(maxsize=2)
def displayed(path):
    with Image.open(path) as im:
        return ImageOps.exif_transpose(im).convert('RGB')


def verify_region_counts(edge, quads, impacts):
    """Independently draw each AFTER mask on the child canvas and count surviving source pixels."""
    w,h=edge['transform']['size']
    mask=np.zeros((h,w),np.uint8)
    for polygon in edge['transform']['masks']:
        cv2.fillConvexPoly(mask,np.rint(polygon).astype(np.int32),1)
    for name,quad in quads.items():
        pts=np.rint(np.asarray(quad)-edge['transform']['origin']).astype(np.int32)
        x,y,rw,rh=cv2.boundingRect(pts)
        native=np.zeros((rh,rw),np.uint8)
        cv2.fillConvexPoly(native,pts-np.int32([x,y]),1)
        left,top,right,bottom=max(0,x),max(0,y),min(w,x+rw),min(h,y+rh)
        visible=0
        if left<right and top<bottom:
            region=native[top-y:bottom-y,left-x:right-x]
            visible=np.count_nonzero(region & (1-mask[top:bottom,left:right]))
        need(abs(impacts[name]-(1-visible/np.count_nonzero(native)))<1e-12,'Independent region-area check')


def verify_rows(private, c2, evidence):
    items=evidence['candidates']
    need(len({r['candidate_id'] for r in items})==len(items)==110,'Unique candidates')
    historical=read(EC/'local'/HISTORY/'c2_candidates.json')
    need(digest(historical)==c2['candidate_inventory_digest']==read(P2/'aggregate.json')['c2']['candidate_inventory_digest'],'Historical inventory')
    # The original 110 leads form a fixed frame. Pin the private P2 group assignment
    # by the hash from its original public receipt before comparing the exact roster.
    frozen=read(P2/'aggregate.json')
    pixel_runs=EC/'local/p2_20261120'
    group_file=next((p for p in sorted(pixel_runs.glob('*/c2_private.json'))
                     if sha(p)==frozen['private_manifest_sha256']['c2_private.json']),None)
    need(group_file is not None,'Original group assignment unavailable')
    selected={r['candidate_id'] for r in read(group_file) if r['followup_group']=='image_and_parent_link'}
    need(selected=={r['candidate_id'] for r in items},'Priority membership')
    roster={r['candidate_id']:r for r in historical}
    per_id=evidence['physical_instances']
    pics=evidence['images']
    need(set(per_id)=={r['physical_instance'] for r in items} and
         sum(len(v['edges']) for v in per_id.values())==c2['distinct_replayed_edges'],'Edge census')
    need(sum(i['ok'] for i in pics.values())==c2['verified_image_files'] and
         sum(not i['ok'] for i in pics.values())==c2['unresolved_image_files'],'Image census')
    traced=set()
    keys=('source','before_regions','paired_regions','primary_affected','primary_fully_removed_backup_intact','eligible')
    flags={}
    for row in items:
        cid=row['candidate_id']
        original=roster[cid]
        need([original[k] for k in ('physical_instance','field','primary_source_id','backup_source_id')]==
             [row[k] for k in ('physical_instance','field','primary','backup')], 'Candidate mapping')
        edges=per_id[row['physical_instance']]['edges']
        targeted,clean=False,False
        for option in row['paired']:
            e=edges[option['edge']]
            before,after=pics[e['before']],pics[e['after']]
            need(before['ok'] and after['ok'] and before['file']==e['source_sha256'] in after['parents'] and
                 after['file']==e['input_sha256'] and before['pixel']==e['before_pixel'] and after['pixel']==e['after_pixel'],'Edge binding')
            need(e['before'] in row['source_regions'] and set(option['impact'])==set(row['source_regions'][e['before']]['quads']),'Mapped primary and backup')
            verify_region_counts(e,row['source_regions'][e['before']]['quads'],option['impact'])
            p=option['impact'][row['primary']]
            b=max(v for k,v in option['impact'].items() if k!=row['primary'])
            need(all(0<=v<=1 for v in option['impact'].values()) and p==option['primary'] and b==option['backup'],'Region summary')
            targeted |= p>0
            clean |= p==1 and b==0
        chosen=row['best']
        need(chosen==(row['paired'][0] if row['paired'] else None),'Preview selection')
        eligible=all(v=='PASS' for v in row['conditions'].values())
        expected_states=dict(primary_supported_before='UNKNOWN',primary_removed_after='UNKNOWN',
                             backup_supported_before='UNKNOWN',backup_supported_after='UNKNOWN',
                             semantic_equality_approved='UNKNOWN',provenance_verified='PASS' if chosen else 'UNKNOWN',
                             reference_approved='FAIL',distinct_sources='PASS')
        need(row['conditions']==expected_states and eligible==row['eligible'],'Eight evidence conditions')
        flags[cid]=dict(zip(keys,[bool(row['source_files']),bool(row['source_regions']),bool(row['paired']),targeted,clean,eligible]))
        inspection=row.get('inspection',[])
        need(len(inspection)==(6 if chosen else 0),'Two stages with three source polygons')
        for i in inspection:
            e=edges[chosen['edge']]
            if 'crop' in i:
                crop=private/i['crop']
                need(crop.resolve().parent==(private/'crops').resolve() and sha(crop)==i['sha256'],'Crop bytes')
                path=ROOT/'research/data'/e[i['side']]
                expected=displayed(path).crop(i['box'])
                with Image.open(crop) as saved:
                    need(saved.size==expected.size and saved.convert('RGB').tobytes()==expected.tobytes(),'Crop pixel replay')
                traced.add(i['crop'])
            else:
                need(i.get('absence')=='outside_child_frame' and i['side']=='after','Missing crop explanation')
    need(len(traced)==len(list((private/'crops').iterdir()))==c2['crop_files'],'Crop census')
    for col,states in c2['condition_counts'].items():
        need(states=={s:sum(r['conditions'][col]==s for r in items) for s in ('PASS','FAIL','UNKNOWN')},'Condition counts')
    need(c2['mechanical']==dict(Counter(r['mechanical'] for r in items)) and
         c2['reason_counts']==dict(Counter(s for r in items for s in r['reasons'].values())),'Reasons')
    groups={None:items,**{f:[r for r in items if r['field']==f] for f in {r['field'] for r in items}}}
    need(set(c2['by_field'])==set(groups)-{None},'Field universe')
    for f,rows in groups.items():
        stats=c2['all'] if f is None else c2['by_field'][f]
        need(stats['candidates']==len(rows) and stats['physical_ids']==len({r['physical_instance'] for r in rows}),'Field denominator')
        for metric in keys:
            yes=[r for r in rows if flags[r['candidate_id']][metric]]
            need(stats[metric]==dict(candidates=len(yes),physical_ids=len({r['physical_instance'] for r in yes})),'Counts by physical cluster')
    return len(traced)


def verify(dest,public):
    result=read(public/'aggregate.json')
    private=dest/'qualification'
    c2=read(private/'c2.json')
    need(c2==result['c2'] and read(dest/'round.json')==result['round1'],'Aggregate copy')
    verify_round(dest,result['round1'])
    evidence=read(private/'evidence.json')
    need(sha(private/'evidence.json')==c2['candidate_evidence_sha256'] and
         sha(private/'index.html')==c2['review_index_sha256'],'Private package hash')
    frozen=c2['inputs']
    need(frozen==evidence['inputs'] and sha(P2/'aggregate.json')==frozen['p2'] and
         sha(P2/'verification.json')==frozen['p2_receipt'] and
         sha(EC/'execution'/HISTORY/'receipt.json')==frozen['historical_receipt'] and
         sha(ROOT/'research/data/midv2020/template_head.bin')==frozen['archive'],'Frozen source hashes')
    for rel,h in evidence['metadata_sha256'].items():
        need(sha(ROOT/'research/data'/rel)==h,'Source metadata changed')
    for rel,row in evidence['images'].items():
        if row['ok']:
            need(sha(ROOT/'research/data'/rel)==row['file'],'Image bytes changed')
    for name,h in read(EC/'execution'/HISTORY/'receipt.json')['private_outputs'].items():
        need(sha(EC/'local'/HISTORY/name)==frozen['private_hashes'][name]==h,'Lineage or inventory bytes changed')
    crops=verify_rows(private,c2,evidence)
    need(not production_trust()['authorities'] and not approved_ids(),'Fail-closed production trust')
    protected=read(P2/'baseline.json')['protected_files']
    for p,h in protected.items():
        need(sha(ROOT/p)==h,'Protected P2 manifest changed')
    prefix='research/evidence_contract/execution'
    changes=subprocess.check_output(['git','diff','--name-only',BASE,'--',prefix],cwd=ROOT,text=True).splitlines()
    need(all((ROOT/p).is_relative_to(public) for p in changes),'Historical execution diff')
    old=subprocess.check_output(['git','ls-tree','-r','--name-only',BASE,'--',prefix],cwd=ROOT).splitlines()
    need(subprocess.run(['git','check-ignore','-q',str(dest.relative_to(ROOT))],cwd=ROOT).returncode==0,'Private output ignore')
    for k in ('targeted','full'):
        test=read(public/(k+'_tests.json'))
        need(test==read(dest/(k+'.json')) and test['exit_code']==0 and
             sha(dest/(k+'.log'))==test['log_sha256'],'Test receipt')
    return dict(status='VERIFIED',baseline=BASE,aggregate_sha256=sha(public/'aggregate.json'),
        code_hash_basis='UTF-8 source with LF line endings',code_sha256={p.name:sha256(p.read_text(encoding='utf8').encode('utf8')).hexdigest() for p in [Path(__file__), EC/'adjudication/post_p6_closure.py',
                     Path(__file__).with_name('post_p6_geometry.py'),Path(__file__).with_name('post_p6_qualification.py'),
                     EC/'tests/test_post_p6_qualification.py']},
        historical_execution_files=len(old),p2_protected_byte_hashes=len(protected),sealed_submissions_checked=6,
        original_joins_checked=3,private_crop_hash_and_pixel_checks=crops,public_counts_reconciled=True,
        independent_truth_approvals=0)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('run')
    parser.add_argument('public_run')
    parser.add_argument('--write-receipt',action='store_true')
    args=parser.parse_args()
    need(all(Path(s).name==s and s not in ('.','..') for s in (args.run,args.public_run)),'Run names')
    public=MASTER/args.public_run
    result=verify(EC/'local/post_p6'/args.run,public)
    if args.write_receipt:
        save_new(public/'verification.json',result)
    else:
        need(result==read(public/'verification.json'),'Verification receipt differs')
    print(result['status'])
