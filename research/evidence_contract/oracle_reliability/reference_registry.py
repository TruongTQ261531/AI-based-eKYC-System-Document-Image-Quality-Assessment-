"""Verify human-supplied signed decisions; no signing, key generation or approval CLI.

Production trust and the current journal checkpoint must be designated outside
this verifier. Empty configuration keeps all actual evaluations unapproved.
A signature authenticates a key's assertion, not human independence or truth.
"""
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from ..reviewer_tools.strict import bound, canonical, digest, exact, loads, need, sha_value, text, timestamp
from . import policy

VERSION = 'reference-registry/1'
TRUST_PATH = Path(__file__).with_name('production_trust.json')
ROLES = {'REVIEW_PROPOSED':'reviewer', 'ADJUDICATED_ACCEPT':'adjudicator',
         'ADJUDICATED_REJECT':'adjudicator', 'ADJUDICATED_UNRESOLVED':'adjudicator',
         'OWNER_APPROVED':'reference_approver', 'REVOKED':'reference_approver', 'SUPERSEDED':'reference_approver'}


def production_trust():
    config = loads(TRUST_PATH.read_bytes())
    exact(config, {'schema','mode','authorities','expected_journal_head_sha256','owner_protocol_approval_sha256','status'})
    need(config['schema'] == 'reference-trust-configuration/1' and config['mode'] == 'PRODUCTION', 'Production trust configuration')
    need(isinstance(config['authorities'], dict), 'Authority map')
    return config


def verify_signed(envelope, keys, *, mode, schema, role):
    exact(envelope, {'payload','signature_hex'})
    payload = envelope['payload']
    need(isinstance(payload, dict) and payload.get('schema') == schema and payload.get('mode') == mode, 'Signed domain/schema')
    authority = payload.get('authority_id'); text(authority, nonempty=True)
    need(isinstance(keys, dict), 'Authority map required')
    entry = keys.get(authority)
    need(isinstance(entry, dict) and entry.get('role') == role and payload.get('authority_role') == role, 'Authority not designated for role')
    need(entry.get('mode') == mode, 'Synthetic authority cannot enter production')
    timestamp(payload.get('timestamp'))
    try:
        key = Ed25519PublicKey.from_public_bytes(bytes.fromhex(entry['public_key_hex']))
        key.verify(bytes.fromhex(envelope['signature_hex']), canonical(payload))
    except (InvalidSignature, ValueError, TypeError, KeyError) as exc:
        raise ValueError('Invalid decision signature') from exc
    return payload


def candidate(reference, context, *, physical_instance_sha256, source_artifact_sha256, source_version,
              author_id, precision, rights_record_sha256=None, mode='PRODUCTION'):
    policy.validate(reference, context)
    need(reference['scope'] == 'external_reference', 'Constructed references cannot become production candidates')
    need(mode in {'PRODUCTION','SYNTHETIC'}, 'Candidate mode')
    for value in (physical_instance_sha256, source_artifact_sha256): sha_value(value)
    if rights_record_sha256 is not None: sha_value(rights_record_sha256)
    for value in (source_version, author_id, precision): text(value, nonempty=True)
    value = dict(schema='reference-candidate/1', registry_version=VERSION, mode=mode,
        reference=reference, context=context.__dict__, physical_instance_sha256=physical_instance_sha256,
        source_artifact_sha256=source_artifact_sha256, source_version=source_version, author_id=author_id,
        precision=precision, rights_record_sha256=rights_record_sha256, mechanical_state='MECHANICALLY_VALIDATED',
        semantic_approved=False)
    return dict(value, candidate_id=digest(value))


def validate_candidate(value):
    exact(value, {'schema','registry_version','mode','reference','context','physical_instance_sha256',
        'source_artifact_sha256','source_version','author_id','precision','rights_record_sha256',
        'mechanical_state','semantic_approved','candidate_id'})
    bound(value, 'candidate_id')
    rebuilt = candidate(value['reference'], policy.PairContext(**value['context']),
        **{key:value[key] for key in ('physical_instance_sha256','source_artifact_sha256','source_version','author_id','precision','rights_record_sha256','mode')})
    need(rebuilt == value, 'Candidate version/state mismatch')


def bindings(value):
    ref = value['reference']
    return dict(reference_id=ref['reference_id'], physical_instance_sha256=value['physical_instance_sha256'],
        source_artifact_sha256=value['source_artifact_sha256'],source_version=value['source_version'],
        field=ref['field_key'],kind=ref['value_kind'],precision=value['precision'],
        value_sha256=digest([ref['before'],ref['after']]),rights_record_sha256=value['rights_record_sha256'])


def replay(candidates, events, *, keys, mode):
    """Pure journal verifier. Production callers use approved_ids(), not test keys."""
    records = {}; states = {}; proposals = {}; adjudicators = {}; previous = '0'*64; last_time = None; reference_ids = set()
    for item in candidates:
        validate_candidate(item); cid = item['candidate_id']
        need(item['mode'] == mode and cid not in records, 'Candidate mode/duplication')
        rid = item['reference']['reference_id']
        need(rid not in reference_ids, 'Duplicate reference version across candidates')
        reference_ids.add(rid)
        records[cid] = item; states[cid] = 'MECHANICALLY_VALIDATED'; proposals[cid] = set()
    for sequence, envelope in enumerate(events, 1):
        exact(envelope, {'payload','signature_hex'})
        payload = envelope['payload']; need(isinstance(payload, dict), 'Decision payload object required')
        action = payload.get('action'); need(isinstance(action, str) and action in ROLES, 'Unknown registry action')
        payload = verify_signed(envelope, keys, mode=mode, schema='reference-decision/1', role=ROLES[action])
        exact(payload, {'schema','mode','registry_version','candidate_id','bindings','action','authority_id',
            'authority_role','timestamp','basis_sha256','sequence','previous_event_sha256','supersedes_id'})
        need(payload['registry_version'] == VERSION and type(payload['sequence']) is int and payload['sequence'] == sequence, 'Journal version/sequence')
        need(payload['previous_event_sha256'] == previous, 'Journal chain')
        now = timestamp(payload['timestamp']); need(last_time is None or now >= last_time, 'Journal time order'); last_time = now
        cid = payload['candidate_id']; sha_value(cid); need(cid in records, 'Unknown candidate')
        item = records[cid]; need(payload['bindings'] == bindings(item), 'Reference/instance/field binding')
        need(isinstance(payload['basis_sha256'], list) and bool(payload['basis_sha256']), 'Human decision basis required')
        for basis in payload['basis_sha256']: sha_value(basis)
        actor = payload['authority_id']; state = states[cid]
        need(state not in {'REVOKED','SUPERSEDED','REJECTED'}, 'Terminal candidate cannot be reapproved')
        if action == 'REVIEW_PROPOSED':
            need(state in {'MECHANICALLY_VALIDATED','REVIEWER_PROPOSED'}, 'Review out of order')
            need(actor != item['author_id'] and actor not in proposals[cid], 'Distinct external proposals required')
            proposals[cid].add(actor); states[cid] = 'REVIEWER_PROPOSED'
        elif action.startswith('ADJUDICATED_'):
            # Two proposals is the declared development workflow guard, not a
            # statistical sufficiency claim. Production still needs owner protocol.
            need(state == 'REVIEWER_PROPOSED' and len(proposals[cid]) >= 2, 'Independent proposals pending')
            need(actor not in proposals[cid] and actor != item['author_id'], 'Independent adjudicator required')
            states[cid] = {'ADJUDICATED_ACCEPT':'ADJUDICATED','ADJUDICATED_REJECT':'REJECTED','ADJUDICATED_UNRESOLVED':'UNRESOLVED'}[action]
            adjudicators[cid] = actor
        elif action == 'OWNER_APPROVED':
            need(state == 'ADJUDICATED' and item['rights_record_sha256'] is not None, 'Adjudication/rights pending')
            need(actor != adjudicators[cid] and actor not in proposals[cid], 'Approval authority distinct from evidence assessors')
            states[cid] = 'OWNER_APPROVED'
        else:
            need(state == 'OWNER_APPROVED', 'Only approved reference may be revoked/superseded')
            if action == 'SUPERSEDED':
                sha_value(payload['supersedes_id'])
                need(payload['supersedes_id'] in records and payload['supersedes_id'] != cid, 'Replacement candidate required')
            states[cid] = action
        if action != 'SUPERSEDED': need(payload['supersedes_id'] is None, 'Unexpected supersession field')
        previous = digest(envelope)
    return dict(states=states, head=previous, approved_reference_ids=sorted(records[cid]['reference']['reference_id']
        for cid, state in states.items() if state == 'OWNER_APPROVED'), semantic_truth_verified=False)


def approved_ids(candidates=(), events=()):
    config = production_trust()
    if not config['authorities'] or not config['owner_protocol_approval_sha256'] or not config['expected_journal_head_sha256']:
        return frozenset()
    sha_value(config['owner_protocol_approval_sha256']);sha_value(config['expected_journal_head_sha256'])
    result = replay(candidates, events, keys=config['authorities'], mode='PRODUCTION')
    need(result['head'] == config['expected_journal_head_sha256'], 'Journal rollback or unapproved checkpoint')
    return frozenset(result['approved_reference_ids'])


def evaluate_production(reference, context, before, after, *, candidates=(), events=(), minimum_grade=1, flat=False):
    ids = approved_ids(candidates, events)
    return policy.evaluate(reference, context, before, after, approved_external_ids=ids, minimum_grade=minimum_grade, flat=flat)


def public_projection(result):
    return dict(registry_version=VERSION, candidate_count=len(result['states']),
        approved_count=len(result['approved_reference_ids']), state_counts={state:list(result['states'].values()).count(state)
        for state in sorted(set(result['states'].values()))}, journal_head_sha256=result['head'],
        semantic_truth_verified=False)
