"""Read-only local metadata/exposure audit. No acquisition or cohort selection."""
from collections import Counter, defaultdict
from pathlib import Path
import re
import tarfile

from ..reviewer_tools.strict import digest, loads, sha_bytes
from .semantic_registry import proposal

HASH_KEYS = {'input_sha256', 'input_file_sha256', 'file_sha256', 'image_sha256',
             'source_sha256', 'pixel_sha256', 'input_pixel_sha256'}


def provider_templates(root):
    path = Path(root)/'research/data/midv2020/template_head.bin'
    before = sha_bytes(path.read_bytes()); rows = {}
    with tarfile.open(path, mode='r:') as archive:
        for entry in archive:
            if entry.name.rstrip('/') == 'images':
                break
            if not entry.name.endswith('.json'):
                continue
            doc_type = Path(entry.name).stem
            data = loads(archive.extractfile(entry).read(), max_bytes=10000000)
            for row in data['_via_img_metadata'].values():
                identity = canonical_id('midv2020/'+doc_type+'/'+Path(row['filename']).stem)
                if identity in rows:
                    raise ValueError('Duplicate provider identity')
                rows[identity] = row
    if len(rows) != 1000 or before != sha_bytes(path.read_bytes()):
        raise ValueError('Provider header incomplete or changed')
    return rows, before


def canonical_id(value):
    if not isinstance(value, str):
        return None
    match = re.fullmatch(r'midv2020/([a-z0-9_]+)/([0-9]{1,3})', value)
    if not match or not 0 <= int(match[2]) < 100:
        return None
    return 'midv2020/'+match[1]+'/'+str(int(match[2])).zfill(2)


def exposure_state(witnesses):
    # Absence from any number of inspected logs never certifies unseen status.
    return 'EXPOSED_CONFIRMED' if witnesses else 'EXPOSURE_UNKNOWN'


def objects(value):
    stack = [value]
    while stack:
        node = stack.pop()
        if isinstance(node, dict):
            yield node
            stack.extend(v for v in node.values() if isinstance(v, (dict, list)))
        elif isinstance(node, list):
            stack.extend(v for v in node if isinstance(v, (dict, list)))


def scan(root):
    root = Path(root).resolve(); templates, template_sha = provider_templates(root)
    witnesses = {pid: set() for pid in templates}
    hashes_to_ids = defaultdict(set); cache_links = []; files = {}; errors = Counter()
    scopes = ('research/data', 'research/results', 'research/cache')
    for scope in scopes:
        for path in sorted((root/scope).rglob('*.json')):
            rel = path.relative_to(root).as_posix(); raw = path.read_bytes(); h = sha_bytes(raw)
            files[rel] = h
            try:
                value = loads(raw, max_bytes=100000000)
            except ValueError:
                errors['strict_json_rejected'] += 1
                continue
            for row in objects(value):
                pid = canonical_id(row.get('physical_id'))
                if pid is None and 'code' in row and 'filename' in row and any(k in row for k in ('image_sha256', 'source_sha256')):
                    pid = canonical_id('midv2020/'+str(row['code'])+'/'+Path(str(row['filename'])).stem)
                recorded = {v for k, v in row.items() if k in HASH_KEYS and isinstance(v, str) and re.fullmatch('[a-f0-9]{64}', v)}
                if pid in witnesses:
                    witnesses[pid].add((rel, h, 'EXPLICIT_STUDY_RECORD'))
                    for recorded_hash in recorded: hashes_to_ids[recorded_hash].add(pid)
                if scope == 'research/cache':
                    for recorded_hash in recorded: cache_links.append((rel, h, recorded_hash))
            if sha_bytes(path.read_bytes()) != h:
                raise ValueError('Audit input changed during read')
    for rel, h, recorded in cache_links:
        for pid in hashes_to_ids.get(recorded, ()):
            witnesses[pid].add((rel, h, 'CACHE_INPUT_HASH_LINK'))
    lineage = []
    for pid, row in sorted(templates.items()):
        doc_type = pid.split('/')[1]
        lineage.append(dict(physical_instance=pid, document_type=doc_type, template_family=doc_type,
            provider='MIDV-2020', provider_artifact='templates.tar annotation prefix; full archive checksum unverified',
            artifact_sha256=template_sha, license_source='https://zenodo.org/records/18786808/files/license.txt?download=1',
            modality='template_metadata', historical_exposure=exposure_state(witnesses[pid]),
            evidence=[dict(path=p, sha256=h, basis=b) for p, h, b in sorted(witnesses[pid])],
            exposure_confidence='RECORDED_STUDY_OR_CACHE_LINK' if witnesses[pid] else 'UNKNOWN',
            metadata_scanned_in_this_audit=True, pixel_lineage_completeness='UNKNOWN',
            image_bytes_rehashed=False, pretraining_exposure='UNKNOWN', confirmatory_eligible=False))
    by_type = {}
    for doc_type in sorted({r['document_type'] for r in lineage}):
        by_type[doc_type] = dict(Counter(r['historical_exposure'] for r in lineage if r['document_type'] == doc_type))
    native = Counter(r['region_attributes']['field_name'] for item in templates.values() for r in item['regions'])
    mapping = [dict(proposal(key), regions=count) for key, count in sorted(native.items())]
    aggregate = dict(schema='corpus-exposure-audit/1', status='PREPARATORY_ONLY',
        scope=list(scopes), files_scanned=len(files), input_inventory_digest=digest(files),
        provider_template_header_sha256=template_sha, physical_instances=len(lineage), by_type=by_type,
        exposure_states=dict(Counter(r['historical_exposure'] for r in lineage)),
        evidence_links=sum(len(r['evidence']) for r in lineage),
        cache_hash_links=sum(e['basis'] == 'CACHE_INPUT_HASH_LINK' for r in lineage for e in r['evidence']),
        cross_instance_recorded_hash_collisions=sum(len(v) > 1 for v in hashes_to_ids.values()),
        parse_exclusions=dict(errors), semantic_mapping=mapping,
        total_project_history_complete=False, unknown_pretraining_overlap=True,
        other_datasets='MIDV-500/2019, MIDV-UP and renderer identities are outside this MIDV-2020 classifier; no unseen claim',
        new_cohort_selected=False, downloads=0, model_calls=0, human_approvals=0)
    return aggregate, lineage, files
