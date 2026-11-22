"""Reconcile per-candidate status for the unissued, unsigned C2-45 snapshot."""
from collections import Counter
from .closure import SOURCE
from .prepare import private_run
from .review import QUESTIONS
from ..oracle_reliability.reference_registry import approved_ids, production_trust
from ..reviewer_tools.strict import need
from ..task55.data import read, save_new, sha


def reconcile(dest):
    recorded=read(dest/'aggregate.json')
    ledger=read(SOURCE/'qualification/evidence.json')
    queue=read(dest/'queue.json')
    rights=read(dest/'artifact_rights.json')
    need(sha(dest/'artifact_rights.json')==recorded['rights_file_sha256'] and
         sha(dest/'queue.json')==recorded['queue_sha256'],'State inputs changed')
    rights_by_member={h:r for r in rights for h in r['members']}
    by_id={i['candidate_id']:i for i in queue}
    # These are the two issued-format organizer workspaces. Any returned assessment
    # requires a new intake snapshot and must not silently disappear into this baseline.
    returns=[p for who in ('R02','R03') for p in (dest/who).rglob('*.json')]
    need(not returns,'Return found: seal and verify it before a new reconciliation')
    trust=production_trust()
    need(not trust['authorities'] and not trust['expected_journal_head_sha256'] and
         not approved_ids(),'Authority changed: reconcile the actual production journal')
    need(not (dest/'signed_round1.json').exists(),'A signed closure requires versioned reconciliation')
    rows=[]
    for prior in ledger['candidates']:
        cid=prior['candidate_id']
        item=by_id.get(cid)
        required_rights=set()
        if item:
            required_rights.update([item['template_sha256'],*item['allowed_evidence_sha256'],
                                    *recorded['package_sha256'].values()])
        rights_ok=bool(required_rights) and all(
            rights_by_member[h]['authority_of_record'] is not None and
            rights_by_member[h]['decisions']['assessor_sharing']=='REVIEW_ACCESS_PERMITTED' for h in required_rights)
        conditions=dict(prior['conditions'])
        need(all(conditions[k]=='UNKNOWN' for k in QUESTIONS) and conditions['reference_approved']=='FAIL',
             'Frozen human or reference state changed')
        rows.append(dict(candidate_id=cid,physical_id=prior['physical_instance'],field=prior['field'],
            group='C2_45' if item else 'DEFERRED_65',required_rights_versions=sorted({
                rights_by_member[h]['version_digest'] for h in required_rights}),
            d10_complete=rights_ok,proposal_receipts=[],signed_adjudication=None,approved_reference=None,
            observations={who:'AWAITING_PROPOSAL' if item else 'OUTSIDE_CURRENT_REVIEW' for who in ('R02','R03')},
            conditions=conditions,eligible=all(v=='PASS' for v in conditions.values())))
    path=dest/'candidate_state.json'
    if path.exists():
        need(read(path)==rows,'Candidate matrix changed')
    else:
        save_new(path,rows)
    for label,subset in [('selected',[r for r in rows if r['group']=='C2_45']),('all_priority',rows)]:
        group=recorded[label]
        checks={'shareable':[r for r in subset if r['d10_complete']], 'two_proposals':[r for r in subset if len(r['proposal_receipts'])==2],
                'adjudicated':[r for r in subset if r['signed_adjudication']], 'approved':[r for r in subset if r['approved_reference']],
                'eligible':[r for r in subset if r['eligible']], 'missing_d10':[r for r in subset if not r['d10_complete']]}
        for k,part in checks.items():
            need(group[k]==dict(candidates=len(part),physical_ids=len({r['physical_id'] for r in part})),'Matrix count '+k)
    return dict(schema='c2-state-matrix-receipt/1',matrix_sha256=sha(path),rows=len(rows),unissued_forms=2*len(queue),
                raw_returns_furnished=len(returns),configured_authorities=len(trust['authorities']),
                verified_production_proposals=sum(len(r['proposal_receipts']) for r in rows),
                rights_approved_versions=sum(r['authority_of_record'] is not None for r in rights),
                phases=dict(Counter(r['group'] for r in rows)))


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument('run')
    dest=private_run(p.parse_args().run)
    receipt=reconcile(dest)
    target=dest/'matrix_receipt.json'
    if target.exists():
        need(read(target)==receipt,'Matrix receipt differs')
    else:
        save_new(target,receipt)
    print(receipt['rows'])
