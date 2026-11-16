"""Read-only compatibility check of already-issued packages and received R02 phase 1.

Publishes only package/raw hashes and aggregate validation results. No re-import.
"""
import argparse
import json
from pathlib import Path

from research.evidence_contract.reviewer_tools.intake import package, validate, quarantine
from research.evidence_contract.reviewer_tools.strict import digest, loads, sha_bytes, need
from research.evidence_contract.task55.data import EC
from research.evidence_contract.task55 import ifv


def run(submission):
    raw=Path(submission).read_bytes(); before=sha_bytes(raw)
    receipts=loads((EC/'execution/master_01/development_20261116/reviewer_package_receipts_v2.json').read_bytes())
    phase2=loads((EC/'execution/master_01/reviewer_intake_20261116_r02/phase2_package_receipt.json').read_bytes())
    bundles={}
    for record in receipts['packages']+[phase2]:
        base='v2' if record['phase']=='phase1' else 'r02_20261116'
        path=EC/'local/reviewer_exports'/base/record['archive_name']
        bundles[(record['reviewer_id'],record['phase'])]=package(path,record['archive_sha256'],record['reviewer_id'])
    _,validation=validate(raw,bundles[('R02','phase1')])
    second=bundles[('R02','phase2')]
    sid=second['job']['phase1_snapshot'];_,seal,profile=ifv.sealed_phase1(sid)
    need(profile['reviewer_id']=='R02' and seal['missing_slots']==seal['incomplete_observations']==0,'Existing sealed phase 1')
    old=set()
    for name in ('observations.json','output_observations.json'):
        for base in (ifv.SUBMISSIONS,ifv.STAGE2):
            for path in base.rglob(name):old.add(digest(loads(path.read_bytes())))
    duplicate=False
    try:quarantine(raw,bundles[('R02','phase1')],EC/'local/reviewer_intake_v2',legacy_digests=old)
    except ValueError as exc:
        need('Already ingested' in str(exc),'Unexpected rejection');duplicate=True
    need(duplicate and before==sha_bytes(Path(submission).read_bytes()),'Duplicate/protection failure')
    return dict(status='PASS_READ_ONLY_COMPATIBILITY',issued_packages_checked=len(bundles),
        phase1_validation=validation,existing_phase1_seal_complete=True,phase2_cases=len(second['packet']['cases']),
        duplicate_import_rejected=True,raw_submission_unchanged=True,new_imports=0,labels_changed=0,
        new_reviews_created=0,review_round_closed=False)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('submission',type=Path)
    print(json.dumps(run(parser.parse_args().submission),indent=2))
