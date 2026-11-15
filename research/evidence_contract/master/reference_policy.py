"""Development reference boundary, separate from the frozen A/B3 implementations.

Hashes bind an explicit reference to its images, key, mutation and policy; they
do not establish honesty or readability. Constructed references can only score
injected control outputs. Real outputs require an external reference whose exact
ID was approved outside this module. No approval or human gold is manufactured.
"""
from dataclasses import dataclass
from datetime import date
import json
from pathlib import Path
import re
import unicodedata

from ..normalized_output import require_sha
from ..source_graph import digest

SCHEMA = 'bound-field-reference/1'
POLICY = 'conservative-field-values/1'
KINDS = {'text', 'identifier', 'date_full', 'date_yymmdd'}
CONDITIONS = {'semantic_link', 'integrity', 'format_valid', 'field_checksum', 'composite_checksum'}


@dataclass(frozen=True)
class PairContext:
    contract: str
    key: str
    before_pixel_sha256: str
    after_pixel_sha256: str
    mutation_sha256: str
    validity: str
    operator: str

    def __post_init__(self):
        if self.contract not in {'C1', 'C2', 'C3', 'C4'} or not self.key:
            raise ValueError('Unknown contract or empty key')
        if self.validity not in {'VALID', 'INVALID_TEST', 'INCONCLUSIVE'}:
            raise ValueError('Unknown validity')
        for value in (self.before_pixel_sha256, self.after_pixel_sha256, self.mutation_sha256):
            require_sha(value)


def canonical_value(value, kind):
    """Explicit project policy: NFC text, case-sensitive identifiers, no O/0 repair.

    Full dates accept YYYY-MM-DD or DD/MM/YYYY. Partial dates accept YYMMDD.
    Their distinct tuple types prevent guessing a century or silently discarding
    precision. Calendar checks do not supply missing source evidence.
    """
    if not isinstance(value, str) or kind not in KINDS:
        return None
    text = unicodedata.normalize('NFC', value).strip()
    if not text:
        return None
    if kind == 'text':
        return ('text', ' '.join(text.split()).casefold())
    if kind == 'identifier':
        return ('identifier', text)
    if kind == 'date_full':
        iso = re.fullmatch(r'([0-9]{4})-([0-9]{2})-([0-9]{2})', text)
        local = re.fullmatch(r'([0-9]{1,2})/([0-9]{1,2})/([0-9]{4})', text)
        if iso:
            year, month, day = map(int, iso.groups())
        elif local:
            day, month, year = map(int, local.groups())
        else:
            return None
    else:
        partial = re.fullmatch(r'([0-9]{2})([0-9]{2})([0-9]{2})', text)
        if not partial:
            return None
        year, month, day = map(int, partial.groups())
    try:
        date(year if kind == 'date_full' else 2000 + year, month, day)
    except ValueError:
        return None
    return kind, year, month, day


def seal_reference(payload):
    if 'reference_id' in payload:
        raise ValueError('Reference already sealed; create an explicit new amendment')
    return dict(payload, reference_id=digest(payload))


def load_reference(path):
    def unique(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('Duplicate reference key')
            result[key] = value
        return result
    return json.loads(Path(path).read_text(encoding='utf-8'), object_pairs_hook=unique)


def _validate(reference, context):
    keys = {'schema', 'policy', 'scope', 'field_key', 'value_kind', 'provenance',
            'mutation_sha256', 'before', 'after', 'reference_id'}
    if not isinstance(reference, dict) or set(reference) != keys:
        raise ValueError('reference_schema')
    if (reference['schema'] != SCHEMA or reference['policy'] != POLICY
            or reference['scope'] not in {'constructed_control', 'external_reference'}
            or reference['value_kind'] not in KINDS
            or not isinstance(reference['provenance'], str) or not reference['provenance'].strip()):
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
            if not isinstance(source, dict) or set(source) != {'source_id', 'semantic_key', 'kind', 'state', 'value', 'conditions'}:
                raise ValueError('source_schema')
            sid = source['source_id']
            if not isinstance(sid, str) or not sid.strip() or sid in seen:
                raise ValueError('duplicate_or_empty_source')
            seen.add(sid)
            if (source['semantic_key'] != context.key or source['kind'] not in {'body', 'duplicated_body', 'mrz', 'other'}
                    or source['state'] not in {'SUPPORTED', 'REMOVED', 'UNKNOWN'} or not isinstance(source['value'], str)):
                raise ValueError('source_key_kind_or_state')
            conditions = source['conditions']
            if (not isinstance(conditions, dict) or not set(conditions) <= CONDITIONS
                    or any(value is not None and type(value) is not bool for value in conditions.values())):
                raise ValueError('condition_schema')


def resolve(frame, kind):
    """Resolve only the supplied inventory; never use an output as reference."""
    supported = []
    for source in frame['sources']:
        required = {'semantic_link', 'integrity'}
        if source['kind'] == 'mrz':
            required |= {'format_valid', 'field_checksum', 'composite_checksum'}
        if source['state'] == 'SUPPORTED' and all(source['conditions'].get(key) is True for key in required):
            value = canonical_value(source['value'], kind)
            if value is None:
                return dict(state='UNKNOWN', reason='invalid_reference_value', value=None)
            supported.append(value)
    if supported:
        if len(set(supported)) != 1:
            return dict(state='UNKNOWN', reason='conflicting_supported_references', value=None)
        return dict(state='SUPPORTED', reason='verified_declared_support', value=supported[0])
    if (frame['inventory_complete'] and frame['sources']
            and all(source['state'] == 'REMOVED' and source['conditions'].get('semantic_link') is True
                    and source['conditions'].get('integrity') is True for source in frame['sources'])):
        return dict(state='REMOVED', reason='complete_declared_inventory_removed', value=None)
    return dict(state='UNKNOWN', reason='support_or_exhaustive_absence_unverified', value=None)


def check(verdict, reason, assessment=None):
    return dict(verdict=verdict, alarm=verdict == 'CANDIDATE_VIOLATION',
                reason=reason, assessment=assessment)


def assess(fields, key, kind, reference):
    if reference['state'] == 'UNKNOWN':
        return check('INCONCLUSIVE', reference['reason'])
    value = fields.get(key, '')
    present = isinstance(value, str) and bool(value.strip())
    if reference['state'] == 'REMOVED':
        return check('CANDIDATE_VIOLATION' if present else 'PASS', 'complete_removal_check',
                     'unsupported_assertion' if present else 'appropriate_empty')
    if not present:
        return check('CANDIDATE_VIOLATION', 'supported_field_missing', 'omitted')
    correct = canonical_value(value, kind) == reference['value']
    return check('PASS' if correct else 'CANDIDATE_VIOLATION', 'bound_typed_reference',
                 'correct' if correct else 'wrong_or_precision_mismatch')


def evaluate(reference, context, before, after, *, approved_external_ids=frozenset()):
    """Return pointwise/relation/format lanes; no predictor or frozen A call."""
    pending = check('INCONCLUSIVE', 'reference_pending')
    result = dict(pointwise=pending, relation=pending, format=pending,
                  reference_accepted=False, reference_scope=None,
                  human_readability_verified=False, software_fault_confirmed=False)
    if (before.input_pixel_sha256 != context.before_pixel_sha256
            or after.input_pixel_sha256 != context.after_pixel_sha256
            or before.reader_fingerprint != after.reader_fingerprint or before.output_origin != after.output_origin):
        blocked = check('INVALID_TEST', 'output_image_reader_or_origin_binding')
        return dict(result, pointwise=blocked, relation=blocked, format=blocked)
    result['format'] = check('PASS' if after.json_validity['usable_for_contracts'] else 'CANDIDATE_VIOLATION',
                             'structured_output_usable' if after.json_validity['usable_for_contracts'] else 'unusable_structured_output')
    try:
        _validate(reference, context)
        scope = reference['scope']
        if scope == 'constructed_control' and after.output_origin != 'oracle_unit_injected':
            raise ValueError('constructed_reference_cannot_score_real_model')
        if scope == 'external_reference' and reference['reference_id'] not in approved_external_ids:
            raise ValueError('external_reference_not_approved')
    except (ValueError, TypeError, KeyError):
        blocked = check('INCONCLUSIVE', 'reference_rejected_or_not_approved')
        return dict(result, pointwise=blocked, relation=blocked)
    result.update(reference_accepted=True, reference_scope=scope, reference_id=reference['reference_id'])
    if context.validity != 'VALID':
        blocked = check('INVALID_TEST' if context.validity == 'INVALID_TEST' else 'INCONCLUSIVE', 'common_mutation_gate')
        return dict(result, pointwise=blocked, relation=blocked)
    if not after.json_validity['usable_for_contracts']:
        blocked = check('INCONCLUSIVE', 'field_undetermined_structured_output_invalid')
        return dict(result, pointwise=blocked, relation=blocked)
    kind = reference['value_kind']
    original = resolve(reference['before'], kind)
    followup = resolve(reference['after'], kind)
    result['pointwise'] = assess(after.fields, context.key, kind, followup)
    if context.contract == 'C1':
        result['relation'] = result['pointwise'] if followup['state'] == 'REMOVED' else check('INCONCLUSIVE', 'C1_complete_removal_unverified')
    elif context.contract == 'C2':
        result['relation'] = result['pointwise'] if followup['state'] == 'SUPPORTED' else check('INCONCLUSIVE', 'C2_valid_backup_unverified')
    elif context.contract == 'C4' and context.operator not in {'identity', 'translate_pad'}:
        result['relation'] = check('INCONCLUSIVE', 'operator_policy_not_declared')
    elif (original['state'] != 'SUPPORTED' or followup['state'] != 'SUPPORTED'
          or original['value'] != followup['value']):
        result['relation'] = check('INCONCLUSIVE', 'preserved_semantic_reference_unverified')
    elif (not before.json_validity['usable_for_contracts']
          or assess(before.fields, context.key, kind, original)['assessment'] != 'correct'):
        result['relation'] = check('INCONCLUSIVE', 'original_already_wrong_or_unverified')
    else:
        result['relation'] = result['pointwise']
    return result
