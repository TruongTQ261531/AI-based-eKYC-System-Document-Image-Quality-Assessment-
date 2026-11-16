"""Shared strict JSON boundaries; no identity verification or semantic approval."""
from datetime import datetime
import hashlib
import json
import re


def need(condition, message):
    if not condition:
        raise ValueError(message)


def exact(value, required, optional=()):
    need(isinstance(value, dict), 'Expected an object')
    need(set(required) <= set(value) <= set(required) | set(optional), 'Missing or unexpected keys')


def text(value, *, nonempty=False):
    need(isinstance(value, str) and len(value) <= 20000, 'Expected a bounded string')
    need(not nonempty or bool(value.strip()), 'Empty required string')
    return value


def sha_bytes(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')


def digest(value):
    return sha_bytes(canonical(value))


def sha_value(value):
    need(isinstance(value, str) and re.fullmatch('[a-f0-9]{64}', value), 'Expected SHA256')
    return value


def timestamp(value):
    text(value, nonempty=True)
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError as exc:
        raise ValueError('Invalid timestamp') from exc
    need(parsed.tzinfo is not None, 'Timestamp requires timezone')
    return parsed


def loads(raw, *, max_bytes=2000000):
    need(isinstance(raw, bytes) and len(raw) <= max_bytes, 'Invalid JSON size/type')
    def unique(pairs):
        result = {}
        for key, value in pairs:
            need(key not in result, 'Duplicate JSON key')
            result[key] = value
        return result
    def invalid_constant(value):
        raise ValueError('Non-finite JSON constant')
    try:
        return json.loads(raw.decode('utf-8-sig'), object_pairs_hook=unique, parse_constant=invalid_constant)
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
        raise ValueError('Malformed JSON') from exc


def bound(value, key):
    need(isinstance(value, dict) and key in value, 'Missing bound ID')
    need(digest({k: v for k, v in value.items() if k != key}) == value[key], 'Content hash mismatch')
