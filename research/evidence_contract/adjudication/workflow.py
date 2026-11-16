"""Blind-review closure, provenance, pairwise agreement and explicit adjudication.

No majority vote, label replacement, reference approval or message sending.
Production authority keys come only from the separate designated trust config.
"""
from collections import defaultdict
from itertools import combinations

from ..reviewer_tools.intake import validate
from ..reviewer_tools.strict import digest, exact, need, sha_value
from ..oracle_reliability.reference_registry import verify_signed, production_trust


def normalized_view(raw, bundle, identity_map, *, phase1_seal=None, synthetic=False):
    value, receipt = validate(raw, bundle, phase1_seal=phase1_seal, synthetic=synthetic)
    need(bundle['job']['phase'] == 'phase2', 'This workflow covers phase-2 categorical observations')
    need(set(identity_map) == {c['case_id'] for c in bundle['packet']['cases']}, 'Complete organizer join required')
    for identity in identity_map.values(): sha_value(identity)
    need(len(set(identity_map.values())) == len(identity_map), 'Duplicate comparison identity in join')
    return dict(schema='adjudication-review-view/1', mode='SYNTHETIC' if synthetic else 'PRODUCTION',
        reviewer_id=bundle['job']['reviewer_id'],raw_sha256=receipt['raw_sha256'],
        normalized_sha256=receipt['normalized_sha256'],job_id=bundle['job']['job_id'],
        join_sha256=digest(identity_map),complete=receipt['complete'],
        items=[dict(identity=identity_map[item['case_id']],judgment={key:item[key] for key in (
            'test_validity','before_reading','after_reading','absence_check')}) for item in value['items']])


def build_packet(views, closure, *, synthetic_keys=None):
    mode = 'SYNTHETIC' if synthetic_keys is not None else 'PRODUCTION'
    keys = synthetic_keys if synthetic_keys is not None else production_trust()['authorities']
    payload = verify_signed(closure, keys, mode=mode, schema='review-round-closure/1', role='round_owner')
    exact(payload, {'schema','mode','authority_id','authority_role','timestamp','round_id','view_sha256','cutoff_basis'})
    need(payload['view_sha256'] == sorted(digest(v) for v in views), 'Closure must bind every immutable view')
    need(isinstance(payload['cutoff_basis'], str) and payload['cutoff_basis'].strip(), 'Explicit cutoff decision required')
    reviewers = [v['reviewer_id'] for v in views]
    need(len(reviewers) >= 2 and len(set(reviewers)) == len(reviewers), 'Distinct reviewers required')
    by_item = defaultdict(dict)
    for view in views:
        need(view['mode'] == mode and view['complete'] is True, 'Independent review still open/incomplete')
        sha_value(view['raw_sha256']);sha_value(view['normalized_sha256']);sha_value(view['join_sha256'])
        for item in view['items']:
            need(view['reviewer_id'] not in by_item[item['identity']], 'Duplicate observation identity')
            by_item[item['identity']][view['reviewer_id']] = item['judgment']
    agreement = []
    for first, second in combinations(sorted(reviewers), 2):
        common = [v for v in by_item.values() if first in v and second in v]
        equal = sum(v[first] == v[second] for v in common)
        agreement.append(dict(pair_sha256=digest([first,second]),matched=equal,denominator=len(common),
                              value=equal/len(common) if common else None))
    items = []
    for identity, judgments in sorted(by_item.items()):
        statuses = {digest(v) for v in judgments.values()}
        uncertain = any(any(v[key] == 'uncertain' for key in ('before_reading','after_reading','test_validity'))
                        for v in judgments.values())
        state = 'UNRESOLVED' if uncertain else 'AGREEMENT' if len(statuses) == 1 and len(judgments) == len(reviewers) else 'DISAGREEMENT'
        items.append(dict(identity=identity,state=state,observations=list(judgments.values())))
    packet = dict(schema='adjudication-packet/1',mode=mode,round_id=payload['round_id'],closure_sha256=digest(closure),
        view_sha256=payload['view_sha256'],reviewer_ids=sorted(reviewers),pre_adjudication_exact_agreement=agreement,items=items)
    return dict(packet,packet_id=digest(packet))


def record_decision(packet, envelope, *, synthetic_keys=None):
    mode = 'SYNTHETIC' if synthetic_keys is not None else 'PRODUCTION'
    keys = synthetic_keys if synthetic_keys is not None else production_trust()['authorities']
    need(packet['mode'] == mode and digest({k:v for k,v in packet.items() if k!='packet_id'}) == packet['packet_id'], 'Packet hash/domain')
    payload = verify_signed(envelope, keys, mode=mode, schema='adjudication-decision/1', role='adjudicator')
    exact(payload, {'schema','mode','authority_id','authority_role','timestamp','packet_id','identity','disposition',
        'candidate_id','basis_sha256'})
    need(payload['authority_id'] not in packet['reviewer_ids'], 'Adjudicator cannot be an input reviewer')
    need(payload['packet_id'] == packet['packet_id'] and payload['identity'] in {i['identity'] for i in packet['items']}, 'Decision provenance binding')
    need(payload['disposition'] in {'ACCEPT','REJECT','UNRESOLVED'}, 'Explicit disposition required')
    need(isinstance(payload['basis_sha256'], list) and bool(payload['basis_sha256']), 'Decision basis required')
    for value in payload['basis_sha256']:sha_value(value)
    if payload['disposition'] == 'ACCEPT':sha_value(payload['candidate_id'])
    else:need(payload['candidate_id'] is None, 'No candidate may be approved from unresolved/rejected evidence')
    return dict(schema='adjudication-record/1',mode=mode,packet_id=packet['packet_id'],decision_sha256=digest(envelope),
        identity=payload['identity'],disposition=payload['disposition'],candidate_id=payload['candidate_id'],
        registry_approval=False,labels_replaced=0)
