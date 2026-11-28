"""In-memory G03.5A intake and pairing exercises. No production input, registry writes or loader."""
from . import review
from ..oracle_reliability import reference_registry as registry
from ..reviewer_tools.strict import digest, exact, loads, need, sha_bytes


def fixture_only(item):
    need(item.get('schema') == 'g03.5a-synthetic-item/1' and
         item['physical_id'].startswith('SYNTH_'), 'Synthetic issued item required')


def intake(item, manifest_digests, roster, keys, submissions, *, sharing, retention,
           candidates=(), events=(), journal_checkpoint=None):
    """The harness supplies trusted assignments, custody digests and fixture permissions separately."""
    fixture_only(item)
    need(sharing == 'PERMITTED' and retention == 'PERMITTED', 'Fixture sharing and retention required')
    exact(roster, ('R02', 'R03'))
    exact(manifest_digests, ('R02', 'R03'))
    need(len(set(manifest_digests.values())) == 2, 'Expected two distinct manifests')
    for role in roster:
        entry = keys.get(roster[role], {})
        need(entry.get('role') == 'reviewer' and entry.get('mode') == 'SYNTHETIC', 'Undesignated reviewer')
    need(len({bytes.fromhex(keys[actor]['public_key_hex']) for actor in roster.values()}) == 2,
         'Reviewer keys must be distinct')
    accepted = {}
    for role, raw, envelope in submissions:
        need(role in roster and role not in accepted, 'Unknown or duplicate assessor')
        form = loads(raw)
        receipt = review.validate(form, item, role)
        signed = registry.verify_signed(envelope, keys, mode='SYNTHETIC',
                                       schema='g03.5a-fixture-observation/1', role='reviewer')
        exact(signed, ('schema', 'mode', 'timestamp', 'authority_role', 'authority_id', 'assessor',
                       'item_sha256', 'manifest_sha256', 'observation_sha256'))
        need(signed['authority_id'] == roster[role] and signed['assessor'] == role and
             signed['manifest_sha256'] == manifest_digests[role] and
             signed['item_sha256'] == receipt['item_sha256'] and
             signed['observation_sha256'] == receipt['observation_sha256'], 'Signed intake binding mismatch')
        accepted[role] = receipt['observation_sha256']
    # A valid journal head is a custody check, never a case-specific reference decision.
    journal_status = 'CHECKPOINT_PENDING'
    if journal_checkpoint is not None:
        journal = registry.replay(candidates, events, keys=keys, mode='SYNTHETIC')
        need(journal['head'] == journal_checkpoint, 'Fixture journal checkpoint mismatch')
        journal_status = 'CHECKPOINT_VERIFIED'
    else:
        need(not candidates and not events, 'Uncheckpointed registry input')
    return dict(scope='SYNTHETIC_ONLY', verified_observations=accepted, journal_status=journal_status,
                approved_reference=False)


def paired_output(item, frozen_reader, records):
    """Exercise the expected join on opaque fixture bytes. A single-side cache is insufficient."""
    fixture_only(item)
    exact(frozen_reader, ('name', 'version', 'checkpoint', 'config', 'preprocessing', 'runtime'))
    need(all(isinstance(v, str) and v for v in frozen_reader.values()), 'Missing reader provenance')
    matched = set()
    for side, record, payload in records:
        need(side in ('before', 'after') and side not in matched, 'Unexpected or duplicate side')
        exact(record, ('reader', 'input', 'output_sha256'))
        need(record['reader'] == frozen_reader and record['input'] == item['full'][side] and
             record['output_sha256'] == sha_bytes(payload), 'Output binding mismatch')
        matched.add(side)
    return 'VERIFIED_PAIR' if len(matched) == 2 else 'NO_VERIFIED_PAIR'
