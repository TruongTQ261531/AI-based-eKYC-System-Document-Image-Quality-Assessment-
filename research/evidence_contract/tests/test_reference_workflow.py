from copy import deepcopy
import pytest

from research.evidence_contract.adjudication import synthetic_dry_run as unit
from research.evidence_contract.adjudication import workflow
from research.evidence_contract.oracle_reliability import reference_registry as registry
from research.evidence_contract.reviewer_tools.strict import digest


def journal():
    private,keys=unit.test_keys();candidate,args=unit.synthetic_candidate();events=[]
    for action,actor in [('REVIEW_PROPOSED','SYNTHETIC_A'),('REVIEW_PROPOSED','SYNTHETIC_B'),
                         ('ADJUDICATED_ACCEPT','SYNTHETIC_ADJ'),('OWNER_APPROVED','SYNTHETIC_OWNER')]:
        events.append(unit.event(candidate,action,actor,events,private))
    return private,keys,candidate,args,events


def test_signed_synthetic_workflow_has_no_production_authority():
    result=unit.run()
    assert result['packet_states']==dict(AGREEMENT=1,DISAGREEMENT=1,UNRESOLVED=1)
    assert result['production_approved']==result['actual_labels_changed']==0
    assert result['exact_agreement'][0]['matched']==2
    assert result['exact_agreement'][0]['denominator']==3


def test_candidate_cannot_approve_itself_or_supply_a_trusted_key():
    private,keys,candidate,args,events=journal()
    empty=registry.replay([candidate],[],keys=keys,mode='SYNTHETIC')
    assert empty['states'][candidate['candidate_id']]=='MECHANICALLY_VALIDATED'
    assert not empty['approved_reference_ids']
    assert not registry.approved_ids([candidate],events)
    # Forging a new key with the same display ID cannot authenticate to the designated key.
    forged,_=unit.test_keys()
    events[-1]=unit.sign(events[-1]['payload'],forged)
    with pytest.raises(ValueError,match='signature'):registry.replay([candidate],events,keys=keys,mode='SYNTHETIC')


@pytest.mark.parametrize('change',['missing_signature','wrong_version','wrong_instance','wrong_field','wrong_value','wrong_source','sequence','chain','order','role'])
def test_signed_but_invalid_approval_is_rejected(change):
    private,keys,candidate,args,events=journal();payload=deepcopy(events[-1]['payload'])
    if change=='missing_signature':events[-1]['signature_hex']='00';payload=None
    if change=='wrong_version':payload['registry_version']='reference-registry/0'
    if change=='wrong_instance':payload['bindings']['physical_instance_sha256']='f'*64
    if change=='wrong_field':payload['bindings']['field']='school'
    if change=='wrong_value':payload['bindings']['value_sha256']='f'*64
    if change=='wrong_source':payload['bindings']['source_artifact_sha256']='f'*64
    if change=='sequence':payload['sequence']=True
    if change=='chain':payload['previous_event_sha256']='0'*64
    if change=='role':payload['authority_role']='reviewer'
    if change=='order':
        events=[];payload=unit.event(candidate,'OWNER_APPROVED','SYNTHETIC_OWNER',events,private)['payload']
    if payload is not None:
        signed=unit.sign(payload,private)
        if events:events[-1]=signed
        else:events.append(signed)
    with pytest.raises(ValueError):registry.replay([candidate],events,keys=keys,mode='SYNTHETIC')


def test_revocation_is_terminal_and_missing_approval_abstains():
    private,keys,candidate,args,events=journal()
    events.append(unit.event(candidate,'REVOKED','SYNTHETIC_OWNER',events,private))
    assert not registry.replay([candidate],events,keys=keys,mode='SYNTHETIC')['approved_reference_ids']
    assert registry.evaluate_production(*args)['pointwise']['state']=='UNKNOWN'
    events.append(unit.event(candidate,'OWNER_APPROVED','SYNTHETIC_OWNER',events,private))
    with pytest.raises(ValueError,match='Terminal'):registry.replay([candidate],events,keys=keys,mode='SYNTHETIC')


def test_production_rejects_synthetic_keys_and_rollback_checkpoint(monkeypatch):
    private,keys,candidate,args,events=journal()
    with pytest.raises(ValueError):registry.replay([candidate],events,keys=keys,mode='PRODUCTION')
    # Config is injected only in this unit test, never written to production.
    config=dict(authorities=keys,owner_protocol_approval_sha256='a'*64,expected_journal_head_sha256='f'*64)
    monkeypatch.setattr(registry,'production_trust',lambda:config)
    monkeypatch.setattr(registry,'replay',lambda *a,**kw:dict(head='0'*64,approved_reference_ids=['b'*64]))
    with pytest.raises(ValueError,match='rollback'):registry.approved_ids([],[])


def test_same_reference_cannot_have_two_candidates_to_evade_revocation():
    private,keys,candidate,args,events=journal()
    second=deepcopy(candidate);second['source_version']='SYNTHETIC/2'
    second.pop('candidate_id');second['candidate_id']=digest(second)
    with pytest.raises(ValueError,match='Duplicate reference'):
        registry.replay([candidate,second],events,keys=keys,mode='SYNTHETIC')


def test_adjudication_cannot_open_without_signed_closure_or_choose_majority():
    with pytest.raises(ValueError):workflow.build_packet([],dict(payload={},signature_hex=''))
    private,keys=unit.test_keys()
    view=dict(schema='adjudication-review-view/1',mode='SYNTHETIC',reviewer_id='SYNTHETIC_A',complete=False,
        raw_sha256='a'*64,normalized_sha256='b'*64,join_sha256='c'*64,items=[])
    second=dict(view,reviewer_id='SYNTHETIC_B')
    closure=unit.sign(dict(schema='review-round-closure/1',mode='SYNTHETIC',authority_id='SYNTHETIC_ROUND',authority_role='round_owner',
        timestamp='2026-11-17T00:00:00+07:00',round_id='SYNTHETIC',view_sha256=sorted(digest(v) for v in (view,second)),cutoff_basis='SYNTHETIC'),private)
    with pytest.raises(ValueError,match='incomplete'):workflow.build_packet([view,second],closure,synthetic_keys=keys)
