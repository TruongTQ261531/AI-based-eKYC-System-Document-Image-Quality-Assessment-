"""Read the sealed C2-37 inputs only. stdout contains aggregate metadata, never case rows."""
from collections import defaultdict
from datetime import date
import json
from pathlib import Path
import re
import tarfile

import cv2
import numpy as np
from PIL import Image

from . import mrz_ablation_v1 as d4, policy
from .corpus_audit import canonical_id
from .post_p6_geometry import region_impact
from .semantic_registry import proposal
from ..reviewer_tools.strict import digest, loads, need
from ..task55.data import EC, ROOT, sha

RUN = 'c2_37_20261123'
TEMPLATES = {'aze_passport', 'lva_passport', 'srb_passport'}
TECHNICAL = ('STRUCTURALLY_COMPATIBLE', 'UNSUPPORTED_PRECISION', 'UNSUPPORTED_SOURCE_SLOT',
             'UNSUPPORTED_LITERAL_PROFILE', 'AMBIGUOUS_MAPPING')
MRZ_KEYS = ('mrz_line0', 'mrz_line1')


def classify(field, native, body, literal, number):
    """Return metadata diagnostics. Short-date comparison is not an eligibility rule."""
    info = {}
    if field not in d4.PROFILES or proposal(native)['proposed_field'] != field:
        return 'AMBIGUOUS_MAPPING', info
    start, end, kind = d4.PROFILES[field]
    extracted, reason = policy.td3_value(literal, field, kind)
    info['td3_native_precision'] = reason
    if kind == 'identifier':
        if extracted is None:
            return 'UNSUPPORTED_LITERAL_PROFILE', info
        info['number_vs_document_slot'] = ('MATCH' if policy.canonical(number, kind) == extracted
                                           else 'DIFFERENT_OR_MISSING')
        info['locked_identifier_vs_optional_data'] = (
            'MATCH_EXACT' if body == literal['line2'][28:42].rstrip('<') else 'DIFFERENT')
        if policy.canonical(body, kind) != extracted:
            return 'UNSUPPORTED_SOURCE_SLOT', info
        return 'STRUCTURALLY_COMPATIBLE', info

    full = re.fullmatch(r'([0-9]{2})\.([0-9]{2})\.([0-9]{4})\.?', body)
    need(full is not None, 'Unrecognized locked body date format')
    day, month, year = full.groups()
    date(int(year), int(month), int(day))
    need(policy.td3_value(literal, field, 'date_full')[1] == 'mrz_field_or_precision_unsupported',
         'Frozen precision guard changed')
    if extracted is not None:
        info['diagnostic_yymmdd_projection'] = (
            'MATCH' if year[-2:] + month + day == literal['line2'][start:end] else 'DIFFERENT')
    return 'UNSUPPORTED_PRECISION', info


def scoped_templates(archive, selected):
    rows = {}
    with tarfile.open(archive, 'r:') as tar:
        for member in tar:
            if member.name.rstrip('/') == 'images':
                break
            code = Path(member.name).stem
            if code not in TEMPLATES or member.name != f'annotations/{code}.json':
                continue
            metadata = loads(tar.extractfile(member).read(), max_bytes=10000000)
            for row in metadata['_via_img_metadata'].values():
                pid = canonical_id(f"midv2020/{code}/{Path(row['filename']).stem}")
                if pid in selected:
                    need(pid not in rows, 'Ambiguous template identity')
                    rows[pid] = row['regions']
    need(rows.keys() == selected, 'Incomplete selected template binding')
    return rows


def mrz_pixels(row, assets):
    with Image.open(assets[row['sha256']]) as im:
        crop = np.asarray(im.convert('RGB'))
    x, y, right, bottom = row['box']
    need(crop.shape[:2] == (bottom-y, right-x), 'Crop geometry mismatch')
    quad = np.rint(row['quad']).astype(np.int32) - [x, y]
    need(np.all(quad >= 0) and np.all(quad < [right-x, bottom-y]), 'MRZ footprint clipped')
    mask = np.zeros(crop.shape[:2], np.uint8)
    cv2.fillConvexPoly(mask, quad.astype(np.int32), 1)
    return crop[mask.astype(bool)]


def inspect(item, regions, assets):
    field, native = item['field'], item['native_key']
    source = item['primary_source']
    need(re.fullmatch(r'region_[0-9]+', source) and item['backup_source'] == '+'.join(MRZ_KEYS),
         'Unknown source binding')
    attrs = [r['region_attributes'] for r in regions]
    keys = [r['field_name'] for r in attrs]
    need(keys[int(source[7:])] == native and all(keys.count(k) == 1 for k in (native, *MRZ_KEYS, 'number')),
         'Ambiguous native region')
    mapping = proposal(native)
    need(mapping == item['proposed_mapping'] and not mapping['human_approved'], 'Mapping provenance mismatch')
    def value(k):
        return attrs[keys.index(k)]['value']
    literal = dict(line1=value(MRZ_KEYS[0]), line2=value(MRZ_KEYS[1]))
    status, info = classify(field, native, value(native), literal, value('number'))
    identifier = field == 'id_number'
    need(item['source_precision'] == dict(
        body='LITERAL_IDENTIFIER' if identifier else 'DAY_MONTH_FOUR_DIGIT_YEAR',
        mrz='TD3_LITERAL_IDENTIFIER' if identifier else 'YYMMDD_CENTURY_UNSPECIFIED'), 'Queue precision mismatch')

    before, after = {}, {}
    for row in item['regions']:
        side, key = row['side'], row['native_key']
        full = item['full'][side]
        need(key in (native, *MRZ_KEYS) and row['region'] == f'region_{keys.index(key)}' and
             (row['full_file'], row['full_pixel']) == (full['file'], full['pixel']), 'Crop binding mismatch')
        table = {'before': before, 'after': after}[side]
        need(key not in table, 'Duplicate crop binding')
        table[key] = row
    need(before.keys() == after.keys() == {native, *MRZ_KEYS}, 'Missing before/after region')
    transform = item['transform']
    impacts = {r['region']: region_impact(r['quad'], transform) for r in before.values()}
    need(impacts == item['impact'], 'Mutation footprint mismatch')
    for k in before:
        need(np.array_equal(np.array(before[k]['quad']) - transform['origin'], after[k]['quad']),
             'Shifted polygon mismatch')
    need(impacts[source] == 1 and all(impacts[before[k]['region']] == 0 for k in MRZ_KEYS),
         'Selected geometry differs from locked rule')
    byte_matches, pixel_matches = [], []
    for k in MRZ_KEYS:
        b, a = before[k], after[k]
        byte_matches.append(b['sha256'] == a['sha256'])
        # The polygon occupies the same translated coordinates; compare pixels in raster order.
        need(np.array_equal(np.rint(b['quad']) - transform['origin'], np.rint(a['quad'])),
             'Raster alignment differs')
        pixel_matches.append(np.array_equal(mrz_pixels(b, assets), mrz_pixels(a, assets)))
    info['both_mrz_crop_files'] = 'IDENTICAL' if all(byte_matches) else 'AT_LEAST_ONE_DIFFERS'
    info['both_mrz_polygon_pixels'] = 'IDENTICAL' if all(pixel_matches) else 'AT_LEAST_ONE_DIFFERS'
    return status, info


def audit():
    public = EC/'human_gate/receipts'/RUN
    folder = EC/'local/human_gate'/RUN
    verification = loads((public/'verification.json').read_bytes())
    raw = (public/'aggregate.json').read_bytes()
    aggregate = loads(raw)
    need(sha(public/'aggregate.json') == verification['aggregate_sha256'] and
         aggregate['scope'] == 'C2_37_PROPOSED', 'Scope receipt mismatch')
    need(sha(folder/'queue.json') == aggregate['queue_sha256'] and
         sha(folder/'selection.json') == aggregate['selection_sha256'], 'Unbound queue or selection')
    queue = loads((folder/'queue.json').read_bytes())
    selected = {i['physical_id'] for i in queue}
    need(len(queue) == len({i['candidate_id'] for i in queue}) == 37 and len(selected) == 18 and
         all(pid.split('/')[1] in TEMPLATES for pid in selected), 'Unexpected queue membership')
    acquisition = ROOT/'research/results/vlm_lora_v2/acquisition.json'
    need(sha(acquisition) == aggregate['acquisition_sha256'], 'Unbound acquisition')
    codes = {}
    for r in loads(acquisition.read_bytes())['sources']:
        if r['physical_id'] in selected:
            key = (r['physical_id'], r['source_sha256'])
            need(key not in codes, 'Duplicate acquisition key')
            codes[key] = r['code']
    archive = ROOT/'research/data/midv2020/template_head.bin'
    template_hash = sha(archive)
    need({i['template_sha256'] for i in queue} == {template_hash}, 'Unbound provider header')
    templates = scoped_templates(archive, selected)
    wanted = {h for i in queue for h in i['allowed_evidence_sha256']}
    assets = {}
    for role in ('R02', 'R03'):
        manifest = loads((folder/(role+'_manifest.json')).read_bytes())
        need(digest(manifest) == aggregate['package_sha256'][role], 'Manifest digest mismatch')
        files = {h: folder/role/path for path, h in manifest.items() if path.startswith('assets/')}
        need(set(files) == wanted and len(files) == len(manifest)-1 and
             all(sha(path) == h for h, path in files.items()), 'Missing or changed package asset')
        if role == 'R02':
            assets = files

    pins = loads((EC/'execution/master_01/d4_development_20261117/controls_01/manifest.json').read_bytes())
    for module in (policy, d4):
        path = Path(module.__file__)
        need(sha(path) == pins['sources'][path.name], 'Frozen D4 mismatch')
    groups = defaultdict(lambda: defaultdict(list))
    for state in TECHNICAL:
        groups['technical'][state] = []
    for i in queue:
        pid, field = i['physical_id'], i['field']
        code = codes[pid, i['full']['before']['file']]
        need(code == pid.split('/')[1], 'Acquisition/template mismatch')
        for side in ('before', 'after'):
            full = i['full'][side]['file']
            need(full in i['allowed_evidence_sha256'] and full in assets, 'Unbound full image')
        status, info = inspect(i, templates[pid], assets)
        facts = dict(technical=status, template=code, field=field, template_field=f'{code}/{field}',
                     mutation=i['mutation'], **info)
        if field != 'id_number':
            facts['body_precision'] = 'FOUR_DIGIT_YEAR'
        else:
            facts['body_precision'] = 'IDENTIFIER'
        for axis, label in facts.items():
            groups[axis][label].append(pid)
    counts = {axis: {label: dict(candidates=len(ids), physical_ids=len(set(ids)))
                     for label, ids in bins.items()} for axis, bins in groups.items()}
    return dict(schema='g04.5-c2-37-compatibility/1', evidence_domain='TECHNICAL_METADATA_AND_PIXELS',
                enrolled=aggregate['selected']['scope'], groups=counts,
                pending_human_evidence_at_seal=aggregate['selected']['semantic_approval_missing'],
                scientific_eligible_at_seal=aggregate['selected']['eligible'],
                gates='GO_PREPARATORY_ONLY / NO_GO_SUPERIORITY / P5B INFEASIBLE / TASK 6B/7B BLOCKED',
                scope_aggregate_sha256=verification['aggregate_sha256'], queue_sha256=aggregate['queue_sha256'],
                manifest_digests=aggregate['package_sha256'], provider_header_sha256=template_hash,
                d4_pins={k: pins['sources'][k] for k in ('policy.py', 'mrz_ablation_v1.py')},
                assets_per_manifest=len(wanted), assessor_results_opened=0, real_d4_evaluations=0)


if __name__ == '__main__':
    print(json.dumps(audit(), indent=2, sort_keys=True))
