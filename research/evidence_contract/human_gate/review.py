"""Validate a private assessor observation against its organizer-issued item."""
import argparse
import json
from pathlib import Path

from ..task55.data import EC, read, sha
from ..oracle_reliability import reference_registry as registry
from ..reviewer_tools.strict import digest, exact, loads, need, sha_value, text

SCHEMA = loads(Path(__file__).with_name('review.schema.json').read_bytes())
PROPS = SCHEMA['properties']
QUESTIONS = tuple(PROPS['observations']['required'])


def validate(observation, item, assessor):
    exact(observation, SCHEMA['required'])
    for k in ('schema','role'):
        need(observation[k] == PROPS[k]['const'], 'Invalid observation domain')
    need(assessor in PROPS['assessor']['enum'] and observation['assessor']==assessor, 'Assessor mismatch')
    sha_value(item['candidate_id'])
    need(observation['candidate_id']==item['candidate_id'] and observation['item_sha256']==digest(item),
         'Candidate or issued item mismatch')
    for k in ('exposure','semantic_judgment','precision_judgment'):
        need(observation[k] in PROPS[k]['enum'], 'Missing or invalid '+k)
    exact(observation['observations'], QUESTIONS)
    for k,v in observation['observations'].items():
        need(v in PROPS['observations']['properties'][k]['enum'], 'Missing explicit source observation')
    text(observation['rationale'],nonempty=True)
    refs=observation['basis_sha256']
    need(isinstance(refs,list) and refs, 'Evidence citations required')
    for ref in refs:
        sha_value(ref)
    need(len(set(refs))==len(refs) and set(refs)<=set(item['allowed_evidence_sha256']), 'Unbound or duplicate citation')
    # Require evidence from each temporal side. A cropped-away region can cite the full child.
    for side in ('before','after'):
        need(set(refs).intersection(item['evidence_by_side'][side]), 'Cite both stages')
    return dict(schema='c2-review-content-receipt/1',assessor=assessor,observation_sha256=digest(observation),
                item_sha256=digest(item),exposure=observation['exposure'],signature_verified=False,
                authority_status='CONTENT_VALIDATED_ONLY',approved_reference=False)


def registry_receipt(observation,item,assessor,records,events,assignment=None):
    """Authenticate an observation cited by an actual, checkpointed reviewer proposal.

    When authority IDs differ from the fixed assessor codes, verify the owner-supplied binding.
    Inventory and registry candidate IDs are deliberately separate namespaces.
    """
    receipt=validate(observation,item,assessor)
    trust=registry.production_trust()
    need(trust['owner_protocol_approval_sha256'] and trust['expected_journal_head_sha256'],
         'Production journal authority pending')
    actor=assessor
    if assignment is not None:
        binding=registry.verify_signed(assignment,trust['authorities'],mode='PRODUCTION',
            schema='c2-assessor-assignments/1',role='round_owner')
        exact(binding,{'schema','mode','timestamp','authority_role','authority_id','assessors','baseline'})
        exact(binding['assessors'],{'R02','R03'})
        from .closure import BASE
        need(binding['baseline']==BASE and len(set(binding['assessors'].values()))==2,'Invalid assessor roster')
        for actor_id in binding['assessors'].values():
            need(trust['authorities'].get(actor_id,{}).get('role')=='reviewer','Assessor key not designated')
        actor=binding['assessors'][assessor]
    approved=registry.approved_ids(records,events)
    matches=[e for e in events if e['payload']['action']=='REVIEW_PROPOSED' and
             e['payload']['authority_id']==actor and receipt['observation_sha256'] in e['payload']['basis_sha256']]
    need(len(matches)==1,'Unique signed proposal from assigned reviewer required')
    event=matches[0]['payload']
    candidate=next(c for c in records if c['candidate_id']==event['candidate_id'])
    ref=candidate['reference']
    need(candidate['physical_instance_sha256']==digest(item['physical_id']) and
         ref['field_key']==item['field'] and ref['main_source_id']==item['primary_source'] and
         all(ref[k]['pixel_sha256']==item['full'][k]['pixel'] for k in ('before','after')),
         'Registry item has different physical instance, source, field or pixels')
    return dict(receipt,signature_verified=True,authority_status='SIGNED_PROPOSAL_VERIFIED',
                registry_candidate_id=candidate['candidate_id'],journal_event_sha256=digest(matches[0]),
                registry_reference_approved=ref['reference_id'] in approved)


if __name__=='__main__':
    from .prepare import private_run
    parser=argparse.ArgumentParser()
    parser.add_argument('run')
    parser.add_argument('assessor',choices=['R02','R03'])
    parser.add_argument('observation',type=Path)
    parser.add_argument('--journal',type=Path,help='Authenticated PRODUCTION journal with candidates and events')
    parser.add_argument('--assignment',type=Path,help='Owner-signed roster if authority IDs differ from assessor codes')
    args=parser.parse_args()
    need(not args.assignment or args.journal,'Assignment requires journal')
    form=loads(args.observation.read_bytes())
    need(isinstance(form,dict),"Expected one candidate observation object")
    issued=EC/'human_gate/receipts/human_20261122144027Z/aggregate.json'
    source=private_run(args.run)/'queue.json'
    need(sha(source)==read(issued)['queue_sha256'],'Queue differs from the published issue receipt')
    queue=loads(source.read_bytes(),max_bytes=10_000_000)
    item=next((i for i in queue if i['candidate_id']==form.get('candidate_id')),None)
    need(item is not None,'Unissued candidate')
    receipt=validate(form,item,args.assessor)
    if args.journal:
        journal=loads(args.journal.read_bytes(),max_bytes=20_000_000)
        receipt=registry_receipt(form,item,args.assessor,journal['candidates'],journal['events'],
                                 loads(args.assignment.read_bytes()) if args.assignment else None)
    print(json.dumps(receipt,sort_keys=True))
