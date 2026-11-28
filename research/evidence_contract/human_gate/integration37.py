"""G03.5A: read the named sealed panel. Public output consists only of counts and group digests."""
from collections import defaultdict
from dataclasses import asdict, dataclass
import json

from ..cloud_g01_g03.c2_37_fixture_v2 import CONDITIONS
from ..oracle_reliability import g04_5_compatibility as audit, policy, reference_registry
from ..oracle_reliability.mrz_ablation_v1 import PROFILES
from ..oracle_reliability.semantic_registry import proposal
from ..reviewer_tools.strict import digest, loads, need, sha_bytes
from ..task55.data import EC, ROOT, sha

RECEIPTS = EC/'human_gate/receipts'
COMPATIBILITY = RECEIPTS/'g04_5_20261128/compatibility.json'
G04_PIN = 'b56649ff9bc7dd125771f12423338a0da04680f5a8d44866ccb3d618a3343d5b'
CACHE_PIN = 'a299554981a063dd2b807aa366c28aef5ee27b8329d29a66f83143b40368d3c0'


def sealed_json(path, expected):
    raw = path.read_bytes()
    need(sha_bytes(raw) == expected, 'Sealed input changed')
    return loads(raw)


@dataclass(frozen=True)
class Case:
    candidate_id: str
    physical_id: str
    template: str
    field: str
    native_key: str
    primary_source: str
    backup_source: str
    body_precision: str
    mrz_precision: str
    item_digest: str
    before_file: str
    after_file: str
    before_pixel: str
    after_pixel: str
    compatibility: str


def bind_case(item, regions):
    """Bind the locked native body region to the literal allowed by the frozen field profile."""
    field, native = item['field'], item['native_key']
    attrs = [r['region_attributes'] for r in regions]
    keys = [a['field_name'] for a in attrs]
    need(field in PROFILES and proposal(native) == item['proposed_mapping'] and
         item['proposed_mapping']['proposed_field'] == field, 'Locked field mapping mismatch')
    need(all(keys.count(k) == 1 for k in (native, *audit.MRZ_KEYS)) and
         item['primary_source'] == f'region_{keys.index(native)}' and
         item['backup_source'] == '+'.join(audit.MRZ_KEYS), 'Source region mismatch')
    precision = item['source_precision']
    identifier = field == 'id_number'
    need(precision == dict(body='LITERAL_IDENTIFIER' if identifier else 'DAY_MONTH_FOUR_DIGIT_YEAR',
                           mrz='TD3_LITERAL_IDENTIFIER' if identifier else 'YYMMDD_CENTURY_UNSPECIFIED'),
         'Locked precision mismatch')
    literal = {name: attrs[keys.index(key)]['value']
               for name, key in zip(('line1', 'line2'), audit.MRZ_KEYS, strict=True)}
    # Ask about the locked kind. No projection, fallback field or century rule.
    kind = 'identifier' if identifier else 'date_full'
    value, reason = policy.td3_value(literal, field, kind)
    if reason == 'mrz_field_or_precision_unsupported':
        status = 'UNSUPPORTED_PRECISION'
    elif value is None:
        status = 'UNSUPPORTED_LITERAL_PROFILE'
    elif value != policy.canonical(attrs[keys.index(native)]['value'], kind):
        status = 'UNSUPPORTED_SOURCE_SLOT'
    else:
        status = 'STRUCTURALLY_COMPATIBLE'
    before, after = (item['full'][side] for side in ('before', 'after'))
    pid = item['physical_id']
    return Case(item['candidate_id'], pid, pid.split('/')[1], field, native, item['primary_source'],
                item['backup_source'], precision['body'], precision['mrz'], digest(item), before['file'],
                after['file'], before['pixel'], after['pixel'], status)


def verify_manifest(folder, role, expected, queue):
    manifest = loads((folder/(role+'_manifest.json')).read_bytes())
    need(digest(manifest) == expected, 'Wrong assessor manifest')
    assets = {h for item in queue for h in item['allowed_evidence_sha256']}
    files = {path: h for path, h in manifest.items() if path.startswith('assets/')}
    need(set(files.values()) == assets and len(files) == len(assets) and
         manifest.keys() == files.keys() | {'index.html'}, 'Asset membership mismatch')
    for path, h in files.items():
        need(sha(folder/role/path) == h, 'Asset byte hash mismatch')
    # Never traverse the reviewer workspace or open a form.
    for item in queue:
        need(all(item['full'][side]['file'] in item['evidence_by_side'][side] and
                 set(item['evidence_by_side'][side]) <= assets for side in ('before', 'after')),
             'Unbound frame')


def input_blockers(compatibility, rights, reference, paired_output):
    """Technical input accounting only. Truth and C2 relation qualification are separate axes."""
    tests = ((compatibility == 'STRUCTURALLY_COMPATIBLE', 'D4_INCOMPATIBLE'),
             (rights == 'PERMITTED', 'RIGHTS_MISSING'), (reference == 'APPROVED', 'REFERENCE_MISSING'),
             (paired_output == 'VERIFIED_PAIR', 'PAIRED_OUTPUT_MISSING'))
    return tuple(reason for ok, reason in tests if not ok)


def count(cases):
    return dict(candidates=len(cases), physical_ids=len({c.physical_id for c in cases}))


def load_panel():
    """Return ordered private bindings for local Python callers; never serialize these rows publicly."""
    g04 = sealed_json(COMPATIBILITY, G04_PIN)
    scope = sealed_json(RECEIPTS/audit.RUN/'aggregate.json', g04['scope_aggregate_sha256'])
    need(scope['queue_sha256'] == g04['queue_sha256'] and scope['package_sha256'] == g04['manifest_digests'],
         'G04 scope mismatch')
    folder = EC/'local/human_gate'/audit.RUN
    queue = sealed_json(folder/'queue.json', g04['queue_sha256'])
    need(sha(folder/'selection.json') == scope['selection_sha256'] and
         sha(folder/'artifact_rights.json') == scope['rights_file_sha256'], 'Selection or rights file changed')
    need(len(queue) == len({i['candidate_id'] for i in queue}) == 37, 'Duplicate or missing candidate')
    selected = {i['physical_id'] for i in queue}
    need(len(selected) == 18 and all(p.split('/')[1] in audit.TEMPLATES for p in selected), 'Scope mismatch')
    for role in ('R02', 'R03'):
        verify_manifest(folder, role, scope['package_sha256'][role], queue)
    archive = ROOT/'research/data/midv2020/template_head.bin'
    need(sha(archive) == g04['provider_header_sha256'], 'Wrong annotation version')
    templates = audit.scoped_templates(archive, selected)
    for source, pin in g04['d4_pins'].items():
        need(sha(EC/'oracle_reliability'/source) == pin, 'Frozen D4 changed')
    cases = [bind_case(item, templates[item['physical_id']]) for item in queue]
    compatibility = {k: count([c for c in cases if c.compatibility == k]) for k in audit.TECHNICAL}
    need(compatibility == g04['groups']['technical'] and count(cases) == g04['enrolled'],
         'G04.5 replay mismatch')
    return tuple(cases), scope, compatibility


def snapshot():
    cases, scope, compatibility = load_panel()
    # At this seal each condition has one state shared by the entire panel.
    # A mixed aggregate cannot be disaggregated back into candidate-level evidence.
    sealed = scope['selected']
    conditions = {}
    need(set(sealed['conditions']) == set(CONDITIONS), 'Unexpected C2 conditions')
    for name, distribution in sealed['conditions'].items():
        states = [s for s, n in distribution.items() if n == count(cases)]
        need(len(states) == 1 and all(n == count([]) for s, n in distribution.items() if s != states[0]),
             'Mixed evidence needs a case-level reconciliation')
        conditions[name] = states[0]
    eligible = all(v == 'PASS' for v in conditions.values())
    need(not eligible and sealed['eligible'] == sealed['approved'] == count([]) and
         sealed['missing_d10'] == count(cases) and scope['assessor_sharing'] == 'REVIEW_ACCESS_PENDING',
         'Sealed human gate differs')
    trust = reference_registry.production_trust()
    need(not trust['authorities'] and trust['owner_protocol_approval_sha256'] is None and
         trust['expected_journal_head_sha256'] is None and not reference_registry.approved_ids(),
         'Changed production trust requires a separate authorized reconciliation')
    need(sha(EC/'C2_37_OCR_CACHE_PREFLIGHT_VI.md') == CACHE_PIN, 'Unrecognized historical cache preflight')
    groups = defaultdict(list)
    input_frame = []
    for case in cases:
        reasons = input_blockers(case.compatibility, 'PENDING', 'MISSING', 'NO_VERIFIED_PAIR')
        if not reasons:
            input_frame.append(case)
        for reason in reasons:
            groups[reason].append(case)
    return dict(schema='g03.5a-local-integration/1', scope='PREPARATORY_ONLY', enrolled=count(cases),
                ordered_binding_digest=digest([asdict(c) for c in cases]), compatibility=compatibility,
                pins=dict(g04_5=G04_PIN, cache_preflight=CACHE_PIN, queue=scope['queue_sha256'],
                          selection=scope['selection_sha256'], rights=scope['rights_file_sha256'],
                          manifests=scope['package_sha256']),
                conditions_at_seal=conditions, c2_eligible_at_seal=sealed['eligible'],
                d10_pending_at_seal=sealed['missing_d10'], approved_references_at_seal=sealed['approved'],
                verified_pairs_at_cache_preflight=count([]), truth_not_supplied=count(cases),
                input_blockers={reason: count(cs) for reason, cs in groups.items()},
                d4_input_frame=count(input_frame),
                pointwise_metrics=None, relation_metrics=None, real_forms_opened=0, real_d4_calls=0,
                authority_status=trust['status'], scientific_gate=scope['scientific_gate'])


if __name__ == '__main__':
    print(json.dumps(snapshot(), sort_keys=True, indent=2))
