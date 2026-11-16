"""Versioned lexical mapping proposals, never semantic/source approval."""
from pathlib import Path

from ..reviewer_tools.strict import loads, need
from .policy import canonical

REGISTRY = loads(Path(__file__).with_suffix('.json').read_bytes())


def field_for_alias(value):
    if not isinstance(value, str):
        return None
    key = value.strip().casefold()
    matches = [field for field, rule in REGISTRY['fields'].items() if key in rule['aliases']]
    need(len(matches) <= 1, 'Ambiguous registry alias')
    return matches[0] if matches else None


def proposal(native_key):
    field = field_for_alias(native_key)
    return dict(native_key=native_key, proposed_field=field,
                state='LEXICAL_MAPPING_ONLY' if field else 'AMBIGUOUS_OR_UNSUPPORTED',
                alternatives=REGISTRY['ambiguous_native_keys'].get(native_key, []), human_approved=False)


def normalize(value, field, *, source='body', precision=None):
    rule = REGISTRY['fields'].get(field)
    if rule is None or source not in rule['sources']:
        return None
    kind = rule['kind']
    if source == 'mrz_td3':
        if field in {'dob', 'expiry_date'}:
            if precision != 'date_yymmdd':
                return None
            kind = precision
        elif field != 'id_number':
            return None
    elif precision not in (None, kind):
        return None
    return canonical(value, kind)
