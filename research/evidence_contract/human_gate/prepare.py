"""Prepare the verified C2-45 scope in a fresh organizer-private run."""
import argparse
from collections import Counter
from pathlib import Path
import re
import subprocess

from ..oracle_reliability.corpus_audit import provider_templates
from ..oracle_reliability.p2_audit import HISTORY
from ..oracle_reliability.reference_registry import production_trust, approved_ids
from ..oracle_reliability.semantic_registry import proposal
from ..oracle_reliability.verify_post_p6 import verify_rows
from ..reviewer_tools.strict import digest, need
from ..task55.data import EC, ROOT, read, save_new, sha
from .closure import BASE, SOURCE, PUBLIC, frozen, signed_packet
from .package import render

SOURCE_Q = SOURCE/'qualification'
RIGHTS_DOCS = ROOT/'research/results/recovery_v4/dataset_source_documents.json'
TRUST = EC/'oracle_reliability/production_trust.json'
SCOPES = ('internal_use','assessor_sharing','review_retention','aggregate_release','image_release')
PENDING = dict(internal_use='INTERNAL_USE_PERMITTED',assessor_sharing='REVIEW_ACCESS_PENDING',
               review_retention='RETENTION_PENDING',aggregate_release='AGGREGATE_ONLY_PERMITTED',
               image_release='RELEASE_PENDING')


def private_run(name):
    need(re.fullmatch(r'[A-Za-z0-9_-]+',name) is not None,'Expected one run name')
    return EC/'local/human_gate'/name


def protected_snapshot():
    """Compare only pre-existing execution paths, allowing later additive dated receipts."""
    prefix='research/evidence_contract/execution'
    diff=subprocess.check_output(['git','diff','--name-only','--diff-filter=DMRT',BASE,'--',prefix],cwd=ROOT)
    need(not diff.strip(),'Changed historical execution')
    names=subprocess.check_output(['git','ls-tree','-r','--name-only',BASE,'--',prefix],cwd=ROOT).decode().splitlines()
    for rel,h in read(EC/'execution/master_01/p2_20261120/baseline.json')['protected_files'].items():
        need(sha(ROOT/rel)==h,'Protected historical artifact changed')
    return dict(historical_execution_paths=len(names),protected_p2_byte_hashes=84,
                execution_tree=subprocess.check_output(['git','rev-parse',BASE+':'+prefix],cwd=ROOT,text=True).strip())


def preflight():
    draft,_=frozen()
    old=read(PUBLIC/'aggregate.json')
    check=read(PUBLIC/'verification.json')
    need(sha(PUBLIC/'aggregate.json')==check['aggregate_sha256'],'Prior aggregate receipt')
    baseline=old['c2']
    need(read(SOURCE/'round.json')==old['round1'] and read(SOURCE_Q/'c2.json')==baseline,'Private summaries changed')
    need(sha(SOURCE_Q/'evidence.json')==baseline['candidate_evidence_sha256'] and
         sha(SOURCE_Q/'index.html')==baseline['review_index_sha256'],'Original qualification package')
    e=read(SOURCE_Q/'evidence.json')
    need(e['inputs']==baseline['inputs'],'Input receipt mismatch')
    for rel,h in e['metadata_sha256'].items():
        need(sha(ROOT/'research/data'/rel)==h,'Changed image metadata')
    for rel,image in e['images'].items():
        need(image['ok'] and sha(ROOT/'research/data'/rel)==image['file'],'Changed frozen frame')
    hist=EC/'local'/HISTORY
    p2=EC/'local/p2_20261120/audit21_1795225290150'
    for name,h in baseline['inputs']['private_hashes'].items():
        path=(p2 if name in ('pixel_private.json','c2_private.json') else hist)/name
        need(sha(path)==h,'Private P2 or inventory input changed')
    need(verify_rows(SOURCE_Q,baseline,e)==check['private_crop_hash_and_pixel_checks'],'Source crop replay')
    for k in ('targeted','full'):
        need(read(SOURCE/(k+'.json'))==read(PUBLIC/(k+'_tests.json')) and
             sha(SOURCE/(k+'.log'))==read(PUBLIC/(k+'_tests.json'))['log_sha256'],'Prior test receipt')
    queue=read(SOURCE/'organizer_queue.json')
    need(sha(SOURCE/'organizer_queue.json')=='d46efeeb913a0bab120cf972d79e05c5b8de40d7eb467467ad3efc92dd15eda7'
         and queue['coherence']==read(EC/'local/master_01/reviewer_intake_20261120_r03_phase2/r03_coherence_details.json'),
         'Organizer queue or coherence detail differs')
    licenses={}
    for row in read(RIGHTS_DOCS):
        name=Path(row['source']).name
        path=ROOT/'research/cache/upstream'/('midv2020_'+name)
        need(sha(path)==row['sha256'] and path.stat().st_size==row['bytes'],'Upstream rights evidence changed')
        licenses[name]=row['sha256']
    return e,baseline,draft,dict(protected=protected_snapshot(),raw_submissions=6,immutable_views=3,
        source_ledger=sha(SOURCE_Q/'evidence.json'),source_html=sha(SOURCE_Q/'index.html'),source_crops=check['private_crop_hash_and_pixel_checks'],
        organizer_queue_sha256=sha(SOURCE/'organizer_queue.json'),phase1_queue=len(queue['phase1']),
        phase2_queue=len(queue['phase2']),coherence_flags=sum(len(r['coherence_flags']) for r in queue['coherence']),
        upstream_rights=licenses)


def precision(field,literal):
    if field=='id_number':
        return 'LITERAL_IDENTIFIER'
    if re.fullmatch(r'\d{2}\.\d{2}\.\d{4}\.?',literal):
        return 'DAY_MONTH_FOUR_DIGIT_YEAR'
    if re.fullmatch(r'\d{2} [A-Za-z]{3} \d{2}',literal):
        return 'DAY_MONTH_NAME_TWO_DIGIT_YEAR'
    return 'UNRESOLVED_NATIVE_DATE_FORMAT'


def item_for(row,edge,template,assets):
    regs=template['regions']
    attrs=regs[int(row['primary'][7:])]['region_attributes']
    mapping=proposal(attrs['field_name'])
    need(mapping['proposed_field']==row['field'] and not mapping['human_approved'],'Unexpected semantic mapping')
    sides={'before':[],'after':[]}
    full={}
    for side,k in [('before','source_sha256'),('after','input_sha256')]:
        h=edge[k]
        assets[h]=ROOT/'research/data'/edge[side]
        sides[side].append(h)
        full[side]=dict(file=h,pixel=edge[side+'_pixel'])
    regions=[]
    for raw in row['inspection']:
        details={k:v for k,v in raw.items() if k!='crop'}
        details['native_key']=regs[int(raw['region'][7:])]['region_attributes']['field_name']
        if 'crop' in raw:
            assets[raw['sha256']]=SOURCE_Q/raw['crop']
            sides[raw['side']].append(raw['sha256'])
        regions.append(details)
    return dict(schema='c2-issued-item/1',candidate_id=row['candidate_id'],physical_id=row['physical_instance'],
        field=row['field'],primary_source=row['primary'],backup_source=row['backup'],native_key=attrs['field_name'],
        source_precision=dict(body=precision(row['field'],attrs['value']),mrz='TD3_LITERAL_IDENTIFIER' if row['field']=='id_number' else 'YYMMDD_CENTURY_UNSPECIFIED'),
        proposed_mapping=mapping,full=full,regions=regions,mutation=edge['capture'],impact=row['best']['impact'],
        transform=edge['transform'],template_sha256=row['template_sha256'],evidence_by_side=sides,
        allowed_evidence_sha256=sorted(set(sides['before']+sides['after'])),rights=dict(PENDING))


def cluster_metrics(rows,issued):
    def pair(subset):
        return dict(candidates=len(subset),physical_ids=len({r['physical_instance'] for r in subset}))
    conditions={k:{s:pair([r for r in rows if r['conditions'][k]==s]) for s in ('PASS','FAIL','UNKNOWN')}
                for k in rows[0]['conditions']}
    ready=[r for r in rows if r['candidate_id'] in issued]
    # This snapshot has no incoming C2 observations, signed proposals, rights decisions or journal.
    # A subsequent evidence import requires a new versioned reconciliation.
    return dict(scope=pair(rows),prepared=pair(ready),shareable=pair([]),two_proposals=pair([]),
        waiting_one=pair([]),waiting_both_prepared=pair(ready),without_any_proposals=pair(rows),
        observations_received=pair([]),semantic_approval_missing=pair([r for r in rows if r['conditions']['semantic_equality_approved']!='PASS']),
        missing_d10=pair(rows),adjudicated=pair([]),approved=pair([]),
        eligible=pair([r for r in rows if all(v=='PASS' for v in r['conditions'].values())]),conditions=conditions)


def prepare(dest, signed=None):
    evidence,baseline,draft,checks=preflight()
    trust=production_trust()
    packet=signed_packet(signed) if signed is not None else None
    # This run prepares the empty human-evidence baseline. Never silently discard a live reference journal.
    need(not approved_ids() and trust['expected_journal_head_sha256'] is None,'Live registry requires journal reconciliation')
    templates,archive=provider_templates(ROOT)
    need(archive==baseline['inputs']['archive'],'Unbound template archive')
    all_rows=evidence['candidates']
    selected=[r for r in all_rows if r['best'] and r['best']['primary']==1 and r['best']['backup']==0]
    need(len(selected)==45 and len({r['physical_instance'] for r in selected})==24,'Frozen 45 scope')
    items,assets=[],{}
    for row in selected:
        pid=row['physical_instance']
        edge=evidence['physical_instances'][pid]['edges'][row['best']['edge']]
        items.append(item_for(row,edge,templates[pid],assets))
    dest.mkdir(parents=True,exist_ok=False)
    if packet is not None:
        save_new(dest/'signed_round1.json',dict(envelope=signed,packet=packet,signed_envelope_sha256=digest(signed)))
    save_new(dest/'queue.json',items)
    sets={k:set() for k in ('provider_annotations','original_frames','derived_frames','region_crops','review_workspaces')}
    sets['provider_annotations'].add(archive)
    for item in items:
        for side,key in [('before','original_frames'),('after','derived_frames')]:
            sets[key].add(item['full'][side]['file'])
        sets['region_crops'].update(r['sha256'] for r in item['regions'] if 'sha256' in r)
    packages={}
    for role in ('R02','R03'):
        manifest=render(dest/role,role,items,assets)
        save_new(dest/(role+'_manifest.json'),manifest)
        packages[role]=digest(manifest)
        sets['review_workspaces'].add(packages[role])
    rights=[dict(artifact=k,version_digest=digest(sorted(v)),members=sorted(v),decisions=dict(PENDING),
                 authority_of_record=None,required_approver='PROJECT_OWNER_D10',evidence=checks['upstream_rights'])
            for k,v in sets.items()]
    save_new(dest/'artifact_rights.json',rights)
    # A fresh directory holds only unissued preparation artifacts; no IFV adjudications are imported.
    issued={r['candidate_id'] for r in items}
    left=[r for r in all_rows if r['candidate_id'] not in issued]
    summary=dict(schema='c2-human-evidence-gate/1',baseline=BASE,checks=checks,
        closure=dict(status='SIGNED_CLOSURE_VERIFIED' if packet else 'SIGNATURE_PENDING',
            pending_digest=digest(draft),authority_roles=dict(Counter(v['role'] for v in trust['authorities'].values())),
            signed_records=int(packet is not None),adjudicated=0),
        rights=[{k:v for k,v in r.items() if k!='members'}|dict(unique_members=len(r['members'])) for r in rights],
        rights_file_sha256=sha(dest/'artifact_rights.json'),queue_sha256=sha(dest/'queue.json'),package_sha256=packages,
        selected=cluster_metrics(selected,issued),all_priority=cluster_metrics(all_rows,issued),
        deferred=dict(candidates=len(left),physical_ids=len({r['physical_instance'] for r in left}),
            primary_touched=sum(any(o['primary']>0 for o in r['paired']) for r in left),
            primary_untouched=sum(not any(o['primary']>0 for o in r['paired']) for r in left)),
        source_precision=dict(Counter(i['source_precision']['body'] for i in items)),
        registry_approved=len(approved_ids()),scientific_gate='NO_GO_SUPERIORITY')
    save_new(dest/'aggregate.json',summary)
    return summary


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('run')
    p.add_argument('--signed-closure',type=Path)
    args=p.parse_args()
    prepare(private_run(args.run),read(args.signed_closure) if args.signed_closure else None)
