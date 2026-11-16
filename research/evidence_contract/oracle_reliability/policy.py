"""Conservative reference policy v2. No model, graph, label or approval creation.

FAULT is an oracle field/relation decision, never proof of a software root cause.
TD3 support is deliberately limited to ordinary passport number, DOB and expiry;
not a complete ICAO implementation, document authenticator or OCR repair tool.
"""
from datetime import date
import re
import unicodedata

from ..master.reference_policy import PairContext, seal_reference, load_reference
from ..normalized_output import require_sha
from ..source_graph import digest

SCHEMA = 'bound-field-reference/2'
POLICY = 'oracle-reliability/2'
KINDS = {'text', 'identifier', 'date_full', 'date_yymmdd'}
ENDPOINTS = ('pointwise', 'relation', 'structure')
STATES = {'FAULT', 'NO_FAULT', 'UNKNOWN', 'INVALID_TEST', 'STRUCTURAL_ERROR'}


def canonical(value, kind):
    if not isinstance(value, str) or kind not in KINDS:
        return None
    value = unicodedata.normalize('NFC', value).strip()
    if not value:
        return None
    if kind == 'text':
        return kind, ' '.join(value.split()).casefold()
    if kind == 'identifier':
        return kind, value
    iso = re.fullmatch(r'([0-9]{4})-([0-9]{2})-([0-9]{2})', value)
    local = re.fullmatch(r'([0-9]{1,2})/([0-9]{1,2})/([0-9]{4})', value)
    short = re.fullmatch(r'([0-9]{2})([0-9]{2})([0-9]{2})', value)
    if kind == 'date_full' and iso:
        year, month, day = map(int, iso.groups())
    elif kind == 'date_full' and local:
        day, month, year = map(int, local.groups())
    elif kind == 'date_yymmdd' and short:
        year, month, day = map(int, short.groups())
        if (year, month, day) == (0, 2, 29):
            return None  # Leap-day validity depends on an unknown century.
    else:
        return None
    try:
        date(year if kind == 'date_full' else 2000 + year, month, day)
    except ValueError:
        return None
    return kind, year, month, day  # Short dates retain two-digit precision.


def check_digit(value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Z0-9<]+', value):
        return None
    codes = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    return str(sum((0 if c == '<' else codes.index(c)) * (7, 3, 1)[i % 3]
                   for i, c in enumerate(value)) % 10)


def td3_value(mrz, key, kind):
    """Recompute literal checks; never accept asserted checksum=True as evidence."""
    profiles = {'id_number': (0, 9, 'identifier'), 'dob': (13, 19, 'date_yymmdd'),
                'expiry_date': (21, 27, 'date_yymmdd')}
    if key not in profiles or profiles[key][2] != kind:
        return None, 'mrz_field_or_precision_unsupported'
    if not isinstance(mrz, dict) or set(mrz) != {'line1', 'line2'}:
        return None, 'mrz_literal_missing'
    first, second = mrz['line1'], mrz['line2']
    if (not isinstance(first, str) or not isinstance(second, str)
            or not re.fullmatch(r'P[A-Z<][A-Z]{3}[A-Z<]{39}', first)
            or not re.fullmatch(r'[A-Z0-9<]{9}[0-9][A-Z<]{3}[0-9]{6}[0-9][MF<]'
                                r'[0-9]{6}[0-9][A-Z0-9<]{14}[0-9<][0-9]', second)):
        return None, 'mrz_format_unsupported'
    if any(canonical(second[a:b], 'date_yymmdd') is None for a, b in [(13, 19), (21, 27)]):
        return None, 'mrz_date_invalid_or_ambiguous'
    checks = [(second[:9], second[9]), (second[13:19], second[19]),
              (second[21:27], second[27]), (second[:10] + second[13:20] + second[21:43], second[43])]
    if any(check_digit(value) != digit for value, digit in checks):
        return None, 'mrz_checksum_failed'
    optional_ok = (second[28:42] == '<' * 14 and second[42] in '<0'
                   or check_digit(second[28:42]) == second[42])
    if not optional_ok:
        return None, 'mrz_optional_checksum_failed'
    start, end, _ = profiles[key]
    literal = second[start:end].rstrip('<')
    if key == 'id_number' and ('<' in literal or not literal):
        return None, 'mrz_number_extension_unsupported'
    return canonical(literal, kind), 'td3_literal_checks_pass'


def decision(state, reason, grade=0):
    return dict(state=state, alarm=state in {'FAULT', 'STRUCTURAL_ERROR'}, reason=reason, grade=grade)


def validate(reference, context):
    keys = {'schema', 'policy', 'scope', 'field_key', 'value_kind', 'provenance',
            'mutation_sha256', 'main_source_id', 'before', 'after', 'reference_id'}
    if not isinstance(reference, dict) or set(reference) != keys:
        raise ValueError('reference_schema')
    if (reference['schema'] != SCHEMA or reference['policy'] != POLICY
            or reference['scope'] not in {'constructed_control', 'external_reference'}
            or reference['value_kind'] not in KINDS
            or not isinstance(reference['provenance'], str) or not reference['provenance'].strip()
            or not isinstance(reference['main_source_id'], str)):
        raise ValueError('reference_policy_or_provenance')
    if digest({k: v for k, v in reference.items() if k != 'reference_id'}) != reference['reference_id']:
        raise ValueError('reference_content_hash')
    if reference['field_key'] != context.key or reference['mutation_sha256'] != context.mutation_sha256:
        raise ValueError('reference_key_or_mutation_binding')
    for side, expected in [('before', context.before_pixel_sha256), ('after', context.after_pixel_sha256)]:
        frame = reference[side]
        if (not isinstance(frame, dict) or set(frame) != {'pixel_sha256', 'inventory_complete', 'sources'}
                or type(frame['inventory_complete']) is not bool or not isinstance(frame['sources'], list)):
            raise ValueError('frame_schema')
        if frame['pixel_sha256'] != expected:
            raise ValueError('reference_image_binding')
        seen = set()
        for source in frame['sources']:
            if not isinstance(source, dict) or set(source) != {
                    'source_id', 'semantic_key', 'kind', 'state', 'value', 'conditions', 'mrz'}:
                raise ValueError('source_schema')
            sid = source['source_id']
            if not isinstance(sid, str) or not sid.strip() or sid in seen:
                raise ValueError('duplicate_or_empty_source')
            seen.add(sid)
            if (source['semantic_key'] != context.key or source['kind'] not in {'body', 'duplicated_body', 'mrz', 'other'}
                    or source['state'] not in {'SUPPORTED', 'REMOVED', 'UNKNOWN'} or not isinstance(source['value'], str)):
                raise ValueError('source_key_kind_or_state')
            flags = source['conditions']
            if (not isinstance(flags, dict) or set(flags) != {'semantic_link', 'integrity', 'context_present'}
                    or any(v is not None and type(v) is not bool for v in flags.values())
                    or (source['kind'] != 'mrz' and source['mrz'] is not None)):
                raise ValueError('source_conditions')


def resolve(frame, key, kind):
    supported, removed, unresolved = [], [], []
    for source in frame['sources']:
        flags = source['conditions']; sid = source['source_id']
        if flags['semantic_link'] is not True or flags['integrity'] is not True:
            unresolved.append('source_link_or_integrity_unverified'); continue
        if source['state'] == 'REMOVED':
            removed.append(sid); continue
        if source['state'] != 'SUPPORTED' or flags['context_present'] is not True:
            unresolved.append('source_or_context_unverified'); continue
        value = canonical(source['value'], kind)
        if value is None:
            unresolved.append('reference_value_invalid_or_ambiguous'); continue
        mrz_checked = False
        if source['kind'] == 'mrz':
            extracted, reason = td3_value(source['mrz'], key, kind)
            if extracted is None or extracted != value:
                unresolved.append(reason if extracted is None else 'mrz_literal_reference_mismatch'); continue
            mrz_checked = True
        supported.append((sid, value, mrz_checked))
    result = dict(state='UNKNOWN', value=None, grade=0, supported_ids=[], removed_ids=sorted(removed))
    if len({v[1] for v in supported}) > 1:
        return dict(result, reason='conflicting_supported_sources')
    if unresolved:
        return dict(result, reason=sorted(set(unresolved))[0])
    if supported:
        # Evidence tier is a declared policy, not calibrated probability or independent witnesses.
        grade = 2 if len(supported) >= 2 or any(v[2] for v in supported) else 1
        return dict(result, state='SUPPORTED', value=supported[0][1], grade=grade,
                    supported_ids=sorted(v[0] for v in supported), reason='declared_support_checked')
    if frame['inventory_complete'] and removed and len(removed) == len(frame['sources']):
        return dict(result, state='REMOVED', grade=2, reason='complete_inventory_removed')
    return dict(result, reason='support_or_exhaustive_absence_unverified')


def field_decision(output, key, kind, resolved):
    if resolved['state'] == 'UNKNOWN':
        return decision('UNKNOWN', resolved['reason'])
    emitted = output.fields.get(key, '')
    present = isinstance(emitted, str) and bool(emitted.strip())
    if resolved['state'] == 'REMOVED':
        return decision('FAULT' if present else 'NO_FAULT', 'unsupported_assertion' if present else 'appropriate_empty', resolved['grade'])
    if not present:
        return decision('FAULT', 'supported_omission', resolved['grade'])
    return decision('NO_FAULT' if canonical(emitted, kind) == resolved['value'] else 'FAULT',
                    'typed_value_comparison', resolved['grade'])


def evaluate(reference, context, before, after, *, approved_external_ids=frozenset(), minimum_grade=1, flat=False):
    if type(minimum_grade) is not int or minimum_grade not in {1, 2}:
        raise ValueError('Only the two declared evidence tiers are supported')
    result = {key: decision('UNKNOWN', 'reference_pending') for key in ENDPOINTS}
    result.update(policy=POLICY, reference_accepted=False, independent_gold=False, software_fault_confirmed=False)
    if (before.input_pixel_sha256 != context.before_pixel_sha256 or after.input_pixel_sha256 != context.after_pixel_sha256
            or before.reader_fingerprint != after.reader_fingerprint or before.output_origin != after.output_origin):
        return dict(result, **{k: decision('INVALID_TEST', 'output_binding') for k in ENDPOINTS})
    result['structure'] = decision('NO_FAULT' if after.json_validity['usable_for_contracts'] is True else 'STRUCTURAL_ERROR', 'normalized_structure')
    try:
        validate(reference, context)
        if not isinstance(approved_external_ids, (set, frozenset)):
            raise ValueError('approval_registry_type')
        for reference_id in approved_external_ids:
            require_sha(reference_id)
        if reference['scope'] == 'constructed_control' and after.output_origin != 'oracle_unit_injected':
            raise ValueError('constructed_reference_for_actual_model')
        if reference['scope'] == 'external_reference' and reference['reference_id'] not in approved_external_ids:
            raise ValueError('external_reference_not_approved')
    except (ValueError, TypeError, KeyError, AttributeError):
        return dict(result, pointwise=decision('UNKNOWN', 'reference_rejected'), relation=decision('UNKNOWN', 'reference_rejected'))
    result['reference_accepted'] = True
    if context.validity != 'VALID':
        gate = decision('INVALID_TEST' if context.validity == 'INVALID_TEST' else 'UNKNOWN', 'mutation_gate')
        return dict(result, pointwise=gate, relation=dict(gate))
    if result['structure']['state'] == 'STRUCTURAL_ERROR':
        return dict(result, pointwise=decision('UNKNOWN', 'structure_unusable'), relation=decision('UNKNOWN', 'structure_unusable'))
    kind = reference['value_kind']
    original = resolve(reference['before'], context.key, kind)
    followup = resolve(reference['after'], context.key, kind)
    if (context.contract == 'C1' and followup['state'] == 'REMOVED'
            and {s['source_id'] for s in reference['before']['sources']}
            != {s['source_id'] for s in reference['after']['sources']}):
        followup = dict(followup, state='UNKNOWN', value=None, grade=0,
                        reason='C1_source_inventory_transition_mismatch')
    classifier = flat_field_decision if flat else field_decision
    point = classifier(after, context.key, kind, followup)
    relation = dict(point)
    if context.contract == 'C1':
        before_ids = {s['source_id'] for s in reference['before']['sources']}
        after_ids = {s['source_id'] for s in reference['after']['sources']}
        if original['state'] != 'SUPPORTED' or followup['state'] != 'REMOVED' or before_ids != after_ids:
            relation = decision('UNKNOWN', 'C1_complete_transition_unverified')
    elif context.contract == 'C2':
        main = reference['main_source_id']
        backup = (set(original['supported_ids']) & set(followup['supported_ids'])) - {main}
        if (not main or main not in original['supported_ids'] or main not in followup['removed_ids']
                or not backup or original['value'] != followup['value']):
            relation = decision('UNKNOWN', 'C2_main_removal_and_backup_unverified')
    elif context.contract == 'C4' and context.operator not in {'identity', 'translate_pad'}:
        relation = decision('UNKNOWN', 'operator_not_supported')
    elif original['state'] != 'SUPPORTED' or followup['state'] != 'SUPPORTED' or original['value'] != followup['value']:
        relation = decision('UNKNOWN', 'preserved_semantic_reference_unverified')
    elif (before.json_validity['usable_for_contracts'] is not True
          or classifier(before, context.key, kind, original)['state'] != 'NO_FAULT'):
        relation = decision('UNKNOWN', 'original_wrong_or_unverified')
    if relation['state'] in {'FAULT', 'NO_FAULT'}:
        relation['grade'] = min(original['grade'], followup['grade'])
    for name, value in [('pointwise', point), ('relation', relation)]:
        result[name] = (decision('UNKNOWN', 'evidence_tier_below_policy', value['grade'])
                        if value['state'] in {'FAULT', 'NO_FAULT'} and value['grade'] < minimum_grade else value)
    return result


def flat_field_decision(output, key, kind, resolved):
    """Flat value predicate with the identical shared validation boundary.

    Deliberately not an independent truth validator. This prevents a graph or
    an oracle name receiving credit for information withheld from its baseline.
    """
    if resolved['state'] not in {'SUPPORTED', 'REMOVED'}:
        return decision('UNKNOWN', resolved['reason'])
    raw = output.fields.get(key, '')
    present = isinstance(raw, str) and bool(raw.strip())
    acceptable = (not present if resolved['state'] == 'REMOVED'
                  else present and canonical(raw, kind) == resolved['value'])
    return decision('NO_FAULT' if acceptable else 'FAULT', 'flat_typed_predicate', resolved['grade'])
