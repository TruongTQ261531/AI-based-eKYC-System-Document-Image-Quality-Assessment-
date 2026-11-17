"""Dated, auditable intake of the user-supplied R02 phase-2 export.

No inference, training, majority labels, adjudication, authority approval or round
closure. Original answers and historical methods/results stay immutable.
"""
from collections import Counter
from datetime import datetime, timezone
import argparse
import json
from pathlib import Path
import subprocess

from research.evidence_contract.task55 import ifv
from research.evidence_contract.task55.data import EC, ROOT, read, save_new, sha, digest
from research.evidence_contract.reviewer_tools.intake import package,validate,quarantine
from research.evidence_contract.reviewer_tools.strict import loads,need
from research.evidence_contract.reviewer_tools.phase2_comparison import build_view,compare
from research.evidence_contract.master.ifv_report import sealed_results
from research.evidence_contract.master.ifv_analysis import from_sealed
from research.evidence_contract.master.reviewer_intake_verify import verify as verify_old_intake

HERE=Path(__file__).resolve().parent
PRIVATE=EC/'local/master_01/reviewer_intake_20261117_r02_phase2'
SOURCE=Path('D:/App/ifv-output-1271b360edcd.json')
SOURCE_SHA='d1b9a1526767d98e52725f26ed554068be8c218b049febd068eb2da21ffe270d'
PRIOR=EC/'execution/master_01/reviewer_intake_20261116_r02'
AUTHOR=(ifv.STAGE2/'d7598ae874d735869d2505c30ac9f7348691c2450af2a70d45666f8b3293c223'
        /'submissions/812605bbab3940be838ac9da07ed903c0098717ace789f703f080869dde3267d/output_observations.json')
MUTABLE={'README.md',*[f'research/evidence_contract/{name}' for name in (
    'MASTER_EXECUTION_STATUS.md','NEXT_ACTIONS.md','REVISED_GO_NO_GO.md','EASE2027_ROADMAP_VI.md',
    'IFV_REVIEW_STATUS.md','REVIEWER_HANDOFF_VI.md','paper/SUBMISSION_READINESS.md')]}


def source_bundle():
    receipt=read(PRIOR/'phase2_package_receipt.json')
    bundle=package(EC/'local/reviewer_exports/r02_20261116/reviewer_R02_phase2.zip',receipt['archive_sha256'],'R02')
    sid=bundle['job']['phase1_snapshot'];_,validation,profile=ifv.sealed_phase1(sid)
    seal=dict(snapshot_id=sid,reviewer_id=profile['reviewer_id'],complete=validation['missing_slots']==validation['incomplete_observations']==0)
    need(seal['reviewer_id']=='R02' and seal['complete'],'Own complete phase 1 required')
    return bundle,seal


def prepare():
    need(not PRIVATE.exists() and not (HERE/'preflight.json').exists(),'Preserve existing preflight')
    need(sha(SOURCE)==SOURCE_SHA,'User attachment changed')
    bundle,seal=source_bundle();raw=SOURCE.read_bytes();_,validation=validate(raw,bundle,phase1_seal=seal)
    need(validation['complete'] and validation['observations']==46,'Expected complete R02 phase 2')
    previous=read(EC/'local/master_01/oracle_reliability_20261116/continuation_20261116_2347/protected_before.json')
    protected_paths={(EC/name).resolve() for name in previous}
    tracked=subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0')
    protected_paths.update((ROOT/name).resolve() for name in tracked if name and name not in MUTABLE)
    for base in (ifv.SUBMISSIONS,ifv.STAGE2,ifv.JOINS,EC/'local/reviewer_exports'):
        protected_paths.update(p.resolve() for p in base.rglob('*') if p.is_file())
    protected={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(protected_paths)}
    save_new(PRIVATE/'protected_before.json',protected)
    with (PRIVATE/'original_R02_phase2.json').open('xb') as stream:stream.write(raw)
    save_new(HERE/'preflight.json',dict(schema='phase2-intake-preflight/1',status='VALIDATED_COMPLETE',
        user_attribution='User supplied this export as R02 in the current conversation',raw_sha256=SOURCE_SHA,
        validation=validation,protected_files=len(protected),protected_manifest_sha256=sha(PRIVATE/'protected_before.json'),
        initial_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip(),
        received_at_utc=datetime.now(timezone.utc).isoformat(),source_bytes_preserved=True,round_status='OPEN'))
    print(json.dumps(dict(status='PREFLIGHT_COMPLETE',items=46,protected_files=len(protected),writes_private_only_for_raw=True)))


def ingest():
    need(not (HERE/'intake.json').exists(),'Preserve existing intake receipt')
    source=PRIVATE/'original_R02_phase2.json';need(sha(source)==SOURCE_SHA,'Original bytes changed')
    bundle,seal=source_bundle();raw=source.read_bytes()
    legacy={digest(read(p)) for base in (ifv.SUBMISSIONS,ifv.STAGE2) for name in ('observations.json','output_observations.json') for p in base.rglob(name)}
    q=quarantine(raw,bundle,EC/'local/reviewer_intake_v2',phase1_seal=seal,dry_run=False,legacy_digests=legacy)
    # Existing, frozen operational-label guards are applied to this review alone.
    result=ifv.import_stage2(source,seal['snapshot_id'])
    folder=ifv.STAGE2/digest(['reviewer-id/1','r02'])
    sealed=folder/'submissions'/result['phase2_export_sha256']/'output_observations.json'
    need(read(sealed)==loads(raw),'Submitted answers changed during legacy serialization')
    save_new(PRIVATE/'ingest_locations.json',dict(sealed_submission=sealed.relative_to(ROOT).as_posix(),
        quarantine=(EC/'local/reviewer_intake_v2'/q['normalized_sha256']).relative_to(ROOT).as_posix()))
    correction=read(PRIOR/'role_correction.json')
    need(correction['observation_snapshot_sha256']==seal['snapshot_id'] and correction['effective_role']=='external_reviewer','Role correction binding')
    save_new(HERE/'intake.json',dict(schema='R02-phase2-intake/1',status='PHASE2_COMPLETE_UNADJUDICATED',
        reviewer_code='R02',raw_sha256=SOURCE_SHA,canonical_export_sha256=q['normalized_sha256'],
        phase1_snapshot=seal['snapshot_id'],package_sha256=q['package_sha256'],job_id=q['job_id'],
        reviewed_cases=46,primary_cases=42,diagnostic_cases=4,source_raw_bytes_preserved=True,
        original_answers_changed=0,raw_declared_role=result['reviewer_role'],effective_role=correction['effective_role'],
        role_correction_sha256=sha(PRIOR/'role_correction.json'),independence_verified=False,
        effective_role_basis='Separate organizer clarification; no raw role or answers changed',
        phase2_completed_reviewers_total=2,phase2_external_completed_reviewers_per_organizer=1,
        phase1_completed_reviewers_total=2,round_status='OPEN',R03_status='PENDING',
        adjudicated_cases=0,independent_gold_created=False,approved_references=0,
        model_calls=0,training_runs=0,confirmatory=False,scientific_gate='NO_GO_SUPERIORITY'))
    print(json.dumps(dict(status='R02_PHASE2_IMPORTED',reviewed=46,total_phase2_reviewers=2,round_status='OPEN',adjudicated_cases=0)))


def sealed_view(path,code):
    report=sealed_results(path);folder=path.parents[2]
    export=read(path);links=read(ifv.JOINS/(folder.name+'.json'));labels=read(path.parent/'labels.json')
    return build_view(export,links,labels,code),report,links,labels


def analyze():
    need(not (HERE/'phase2_agreement.json').exists(),'Preserve prior analysis')
    location=read(PRIVATE/'ingest_locations.json');path=ROOT/location['sealed_submission']
    first,author_report,_,_=sealed_view(AUTHOR,'AUTHOR')
    second,r02_report,links,labels=sealed_view(path,'R02')
    need(author_report==read(EC/'execution/master_01/ifv_descriptive_ece01b67a2f6af39.json'),'Author historical report changed')
    agreement,details=compare(first,second)
    analysis,coherence=from_sealed(path)
    analysis['schema']='reviewer-specific-ifv-analysis/1'
    analysis['scope']='R02 external-per-organizer development pilot, own phase-1 evidence, unadjudicated'
    analysis['reviewer_code']='R02';analysis['effective_role']='external_reviewer'
    analysis['raw_declared_role']=r02_report['reviewer_role']
    analysis['role_correction_sha256']=sha(PRIOR/'role_correction.json')
    analysis['round_status']='OPEN'
    r02_public=dict(r02_report,raw_declared_role=r02_report['reviewer_role'],effective_role='external_reviewer',reviewer_code='R02')
    del r02_public['reviewer_role']
    status_by_contract={contract:{endpoint:dict(Counter(labels[cid][endpoint] for cid,v in links.items()
        if v['row']['stratum']=='primary' and v['row']['contract_id']==contract)) for endpoint in ('pointwise','relation')}
        for contract in ('C1','C2','C3','C4')}
    save_new(HERE/'r02_descriptive.json',r02_public)
    save_new(HERE/'r02_postreview_analysis.json',analysis)
    save_new(HERE/'r02_primary_status_by_contract.json',status_by_contract)
    save_new(HERE/'phase2_agreement.json',agreement)
    save_new(PRIVATE/'comparison_views.json',dict(first=first,second=second))
    save_new(PRIVATE/'comparison_differences.json',dict(status='PRIVATE_INTERIM_COMPARISON_NOT_ADJUDICATION',items=details))
    save_new(PRIVATE/'r02_coherence_details.json',coherence)
    print(json.dumps(dict(status='INTERIM_ANALYSIS_COMPLETE',cases=agreement['views']['all']['cases'],
        raw_after=agreement['views']['all']['raw']['after_reading'],
        primary_pointwise=agreement['views']['primary']['derived']['pointwise'],
        R02_coherence_flags=analysis['coherence']['flagged_cases'],round_closed=False,labels_pooled=False),indent=2))


def verify():
    need(sha(SOURCE)==sha(PRIVATE/'original_R02_phase2.json')==SOURCE_SHA,'Raw bytes changed')
    protected=read(PRIVATE/'protected_before.json')
    need(all((ROOT/p).is_file() and sha(ROOT/p)==expected for p,expected in protected.items()),'Historical artifact changed')
    bundle,seal=source_bundle();_,validation=validate((PRIVATE/'original_R02_phase2.json').read_bytes(),bundle,phase1_seal=seal)
    path=ROOT/read(PRIVATE/'ingest_locations.json')['sealed_submission']
    first,author,_,_=sealed_view(AUTHOR,'AUTHOR');second,r02,links,labels=sealed_view(path,'R02')
    need(author==read(EC/'execution/master_01/ifv_descriptive_ece01b67a2f6af39.json'),'Historical author report changed')
    projection=dict(r02,raw_declared_role=r02['reviewer_role'],effective_role='external_reviewer',reviewer_code='R02')
    del projection['reviewer_role']
    need(projection==read(HERE/'r02_descriptive.json'),'R02 descriptive projection changed')
    agreement,details=compare(first,second)
    need(agreement==read(HERE/'phase2_agreement.json'),'Agreement changed')
    need(details==read(PRIVATE/'comparison_differences.json')['items'],'Private differences changed')
    views=read(PRIVATE/'comparison_views.json');need(views==dict(first=first,second=second),'Private views changed')
    analysis,coherence=from_sealed(path);saved=read(HERE/'r02_postreview_analysis.json')
    for key in analysis:
        if key not in ('schema','scope'):need(saved[key]==analysis[key],'Analysis changed: '+key)
    need(saved['schema']=='reviewer-specific-ifv-analysis/1' and
         saved['scope']=='R02 external-per-organizer development pilot, own phase-1 evidence, unadjudicated' and
         saved['reviewer_code']=='R02' and saved['effective_role']=='external_reviewer' and
         saved['raw_declared_role']==r02['reviewer_role'] and saved['round_status']=='OPEN' and
         saved['role_correction_sha256']==sha(PRIOR/'role_correction.json'),'R02 metadata projection changed')
    by_contract={contract:{endpoint:dict(Counter(labels[cid][endpoint] for cid,v in links.items()
        if v['row']['stratum']=='primary' and v['row']['contract_id']==contract)) for endpoint in ('pointwise','relation')}
        for contract in ('C1','C2','C3','C4')}
    need(by_contract==read(HERE/'r02_primary_status_by_contract.json'),'Contract status changed')
    need(coherence==read(PRIVATE/'r02_coherence_details.json'),'Coherence details changed')
    quarantine_path=ROOT/read(PRIVATE/'ingest_locations.json')['quarantine']
    need(sha(quarantine_path/'raw.json')==SOURCE_SHA and read(path)==read(quarantine_path/'normalized.json'),'Intake copies diverged')
    prior=verify_old_intake()
    result=dict(status='PASS',protected_files_unchanged=len(protected),raw_bytes_and_answers_preserved=True,
        strict_phase2_items=validation['observations'],own_phase1_slots=86,canonical_pairs_compared=46,
        primary_pairs=42,primary_physical_instances=agreement['views']['primary']['physical_instances'],
        old_author_report_replayed=True,old_R02_phase1_package_replay=prior['status'],
        actual_phase2_reviewers=2,external_phase2_reviewers_per_organizer=1,independence_verified=False,
        round_status='OPEN',adjudicated_cases=0,labels_pooled=False,model_calls=0,training_runs=0)
    save_new(HERE/'verification.json',result)
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=('prepare','ingest','analyze','verify'))
    globals()[parser.parse_args().action]()
