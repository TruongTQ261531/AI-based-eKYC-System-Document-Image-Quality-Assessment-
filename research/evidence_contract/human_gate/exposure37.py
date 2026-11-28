"""Record C2-37 exposure context using the sealed panel and historical lineage."""

import argparse
from collections import Counter
import json

from .integration37 import load_panel, sealed_json
from .review import PROPS
from ..oracle_reliability.g04_5_compatibility import RUN
from ..oracle_reliability.p2_audit import HISTORY
from ..reviewer_tools.strict import digest, loads, need, sha_bytes
from ..task55.data import EC, read, save_new


PANEL = EC / 'local/human_gate' / RUN
LOCAL_LEDGER = PANEL / 'owner_d11_20261128' / 'historical_exposure_ledger.json'
UNKNOWN = 'EXPOSURE_UNKNOWN'
DECLARATION_STATES = {
    'PREVIOUSLY_SEEN': 'EXPOSED',
    'NO_KNOWN_EXPOSURE': UNKNOWN,
    'UNCERTAIN': UNKNOWN,
}


def build_ledger():
    cases, scope, _ = load_panel()
    queue = sealed_json(PANEL / 'queue.json', scope['queue_sha256'])
    lineage_sha = read(EC / 'execution' / HISTORY / 'receipt.json')['private_outputs']['lineage.json']
    raw = (EC / 'local' / HISTORY / 'lineage.json').read_bytes()
    need(sha_bytes(raw) == lineage_sha, 'Historical exposure lineage hash mismatch')
    entries = loads(raw, max_bytes=10_000_000)
    lineage = {entry['physical_instance']: entry for entry in entries}
    need(len(lineage) == len(entries), 'Repeated physical ID in historical lineage')
    need(DECLARATION_STATES.keys() == set(PROPS['exposure']['enum']), 'Review schema exposure options changed')

    document_ids = {}
    records = []
    for case, item in zip(cases, queue, strict=True):
        need(case.candidate_id == item['candidate_id'] and case.item_digest == digest(item), 'Wrong sealed case')
        history = lineage[case.physical_id]
        recorded = history['historical_exposure']
        need(recorded in ('EXPOSED_CONFIRMED', UNKNOWN), 'Unexpected historical exposure state')
        document_ids[case.physical_id] = {
            'historical_state_raw': recorded,
            'historical_state': 'EXPOSED' if recorded == 'EXPOSED_CONFIRMED' else UNKNOWN,
            'provider_metadata_scanned': history['metadata_scanned_in_this_audit'],
            'pretraining_exposure_raw': history['pretraining_exposure'],
        }
        sources = []
        for side in ('before', 'after'):
            stage_regions = [region for region in item['regions'] if region['side'] == side]
            primary = [region for region in stage_regions if region['region'] == case.primary_source]
            backup = [region for region in stage_regions if region['native_key'] in case.backup_source.split('+')]
            need(len(primary) == 1 and sorted(r['native_key'] for r in backup) ==
                 sorted(case.backup_source.split('+')), 'Wrong source scope or duplicate region')
            for role, key, regions in [('primary', case.primary_source, primary),
                                       ('backup', case.backup_source, backup)]:
                sources.append({
                    'role': role,
                    'source': key,
                    'stage': side,
                    'frame': item['full'][side],
                    'regions': [{'native_key': r['native_key'], 'region': r['region'],
                                 'crop_sha256': r.get('sha256')} for r in regions],
                    'direct_exposure': UNKNOWN,
                })
        records.append({
            'candidate_id': case.candidate_id,
            'physical_id': case.physical_id,
            'sealed_item_digest': case.item_digest,
            'template': case.template,
            'field': case.field,
            'mutation': item['mutation'],
            'precision': item['source_precision'],
            'direct_exposure': UNKNOWN,
            'sources': sources,
        })
    return {
        'schema': 'c2-37-historical-exposure-ledger/1',
        'scope': 'HISTORICAL_LINEAGE_AND_SOURCE_BINDINGS',
        'queue_sha256': scope['queue_sha256'],
        'lineage_sha256': lineage_sha,
        'physical_ids': document_ids,
        'candidates': records,
    }


def aggregate(ledger):
    candidates = ledger['candidates']
    ids = ledger['physical_ids']
    sources = [source for row in candidates for source in row['sources']]
    return {
        'schema': 'c2-37-d11-technical-check/1',
        'panel': {'candidates': len(candidates), 'physical_ids': len(ids)},
        'historical_physical_id_exposure': dict(Counter(row['historical_state'] for row in ids.values())),
        'candidate_direct_exposure': dict(Counter(row['direct_exposure'] for row in candidates)),
        'source_stage_direct_exposure': dict(Counter(row['direct_exposure'] for row in sources)),
        'source_stage_bindings': len(sources),
        'source_stage_bindings_with_missing_crop': sum(
            any(region['crop_sha256'] is None for region in source['regions']) for source in sources),
        'reviewer_declared_exposure_mapping': DECLARATION_STATES,
        'reviewer_submissions_opened': 0,
        'private_ledger_sha256_canonical': digest(ledger),
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--record-local', action='store_true', help='Create the private ledger once')
    args = parser.parse_args()
    ledger = build_ledger()
    if args.record_local:
        save_new(LOCAL_LEDGER, ledger)
    print(json.dumps(aggregate(ledger), indent=2, sort_keys=True))
