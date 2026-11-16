"""Synthetic-only end-to-end workflow. Ephemeral test keys never enter production."""
from copy import deepcopy
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from ..reviewer_tools import synthetic
from ..reviewer_tools.strict import canonical, digest
from ..oracle_reliability import reference_registry as registry
from ..oracle_reliability.controls import make_controls, inputs
from ..oracle_reliability import policy
from . import workflow


def test_keys():
    roles = {'SYNTHETIC_A':'reviewer','SYNTHETIC_B':'reviewer','SYNTHETIC_ADJ':'adjudicator',
             'SYNTHETIC_OWNER':'reference_approver','SYNTHETIC_ROUND':'round_owner'}
    private = {name:Ed25519PrivateKey.generate() for name in roles}
    public = {name:dict(public_key_hex=key.public_key().public_bytes_raw().hex(), role=roles[name], mode='SYNTHETIC')
              for name, key in private.items()}
    return private, public


def sign(payload, private):
    return dict(payload=payload, signature_hex=private[payload['authority_id']].sign(canonical(payload)).hex())


def synthetic_candidate():
    case = deepcopy(make_controls()[0]);case['reference_payload']['scope']='external_reference'
    ref,ctx,before,after=inputs(case)
    value=registry.candidate(ref,ctx,physical_instance_sha256=digest('SYNTHETIC_INSTANCE'),
        source_artifact_sha256=digest('SYNTHETIC_ARTIFACT'),source_version='SYNTHETIC/1',author_id='SYNTHETIC_AUTHOR',
        precision='literal_identifier',rights_record_sha256=digest('SYNTHETIC_RIGHTS_ONLY'),mode='SYNTHETIC')
    return value,(ref,ctx,before,after)


def event(candidate, action, actor, previous, private, *, basis=None):
    payload=dict(schema='reference-decision/1',mode='SYNTHETIC',registry_version=registry.VERSION,
        candidate_id=candidate['candidate_id'],bindings=registry.bindings(candidate),action=action,authority_id=actor,
        authority_role=registry.ROLES[action],timestamp='2026-11-17T00:00:00+07:00',
        basis_sha256=basis or [digest('SYNTHETIC_EVIDENCE')],sequence=len(previous)+1,
        previous_event_sha256=digest(previous[-1]) if previous else '0'*64,supersedes_id=None)
    return sign(payload,private)


def run():
    private,keys=test_keys();candidate,args=synthetic_candidate();views=[]
    for judge in ('SYNTHETIC_A','SYNTHETIC_B'):
        bundle, value=synthetic.fixture('phase2',reviewer=judge)
        # Three explicitly symbolic observations: agreement, disagreement, unresolved.
        bundle['packet']['cases']=[dict(case_id='SYNTHETIC_'+str(i),field_key='id_number') for i in range(3)]
        bundle['packet'].pop('packet_id');bundle['packet']['packet_id']=digest(bundle['packet'])
        bundle['job']['canonical_packet_id']=bundle['packet']['packet_id'];bundle['job']['portable_view_sha256']=digest(bundle['packet'])
        bundle['job'].pop('job_id');bundle['job']['job_id']=digest(bundle['job'])
        value['packet_id']=bundle['packet']['packet_id'];item=value['items'][0];value['items']=[]
        for i in range(3):
            current=dict(item,case_id='SYNTHETIC_'+str(i),test_validity='valid',before_reading='correct',after_reading='correct')
            if i==1 and judge=='SYNTHETIC_B':current.update(after_reading='wrong_value',output_note='SYNTHETIC_DISAGREEMENT')
            if i==2:current['after_reading']='uncertain'
            value['items'].append(current)
        identities={c['case_id']:digest(['SYNTHETIC_COMPARISON',c['case_id']]) for c in bundle['packet']['cases']}
        seal=dict(snapshot_id=bundle['job']['phase1_snapshot'],reviewer_id=judge,complete=True)
        views.append(workflow.normalized_view(canonical(value),bundle,identities,phase1_seal=seal,synthetic=True))
    closure=sign(dict(schema='review-round-closure/1',mode='SYNTHETIC',authority_id='SYNTHETIC_ROUND',authority_role='round_owner',
        timestamp='2026-11-17T00:00:00+07:00',round_id='SYNTHETIC_ROUND_ONLY',view_sha256=sorted(digest(v) for v in views),
        cutoff_basis='SYNTHETIC_COMPLETE_FIXTURES_ONLY'),private)
    packet=workflow.build_packet(views,closure,synthetic_keys=keys)
    decisions=[]
    for item in packet['items']:
        disposition='UNRESOLVED' if item['state']=='UNRESOLVED' else 'ACCEPT'
        signed=sign(dict(schema='adjudication-decision/1',mode='SYNTHETIC',authority_id='SYNTHETIC_ADJ',authority_role='adjudicator',
            timestamp='2026-11-17T00:00:00+07:00',packet_id=packet['packet_id'],identity=item['identity'],
            disposition=disposition,candidate_id=candidate['candidate_id'] if disposition=='ACCEPT' else None,
            basis_sha256=[digest('SYNTHETIC_BASIS_ONLY')]),private)
        decisions.append(workflow.record_decision(packet,signed,synthetic_keys=keys))
    events=[]
    for action,actor in [('REVIEW_PROPOSED','SYNTHETIC_A'),('REVIEW_PROPOSED','SYNTHETIC_B'),
                         ('ADJUDICATED_ACCEPT','SYNTHETIC_ADJ'),('OWNER_APPROVED','SYNTHETIC_OWNER')]:
        events.append(event(candidate,action,actor,events,private,basis=[decisions[0]['decision_sha256']]))
    before=registry.replay([candidate],events,keys=keys,mode='SYNTHETIC')
    events.append(event(candidate,'REVOKED','SYNTHETIC_OWNER',events,private))
    after=registry.replay([candidate],events,keys=keys,mode='SYNTHETIC')
    assert len(before['approved_reference_ids'])==1 and after['approved_reference_ids']==[]
    assert registry.approved_ids([candidate],events)==frozenset()
    assert registry.evaluate_production(*args,candidates=[candidate],events=events)['pointwise']['state']=='UNKNOWN'
    return dict(status='PASS_SYNTHETIC_ONLY',synthetic_views=len(views),synthetic_cases=len(packet['items']),
        packet_states={s:sum(i['state']==s for i in packet['items']) for s in ('AGREEMENT','DISAGREEMENT','UNRESOLVED')},
        exact_agreement=packet['pre_adjudication_exact_agreement'],explicit_decisions=len(decisions),
        synthetic_approved_before_revocation=1,synthetic_approved_after_revocation=0,production_approved=0,
        actual_labels_changed=0,actual_reviewers_created=0,model_calls=0,training_runs=0,
        production_gate_still_unknown=True,independent_truth_established=False)


if __name__=='__main__':
    import json
    print(json.dumps(run(),indent=2))
