"""Independently reconcile C2-37 against the sealed forms, source types and public C2-45 receipt."""
import argparse
from collections import Counter
from html import escape
import re
import stat

from ..oracle_reliability.corpus_audit import provider_templates
from ..oracle_reliability.reference_registry import production_trust
from ..reviewer_tools.strict import digest, need
from ..task55.data import EC, ROOT, read, save_new, sha
from .closure import SOURCE
from .prepare import PENDING, precision, private_run
from .verify import CODES, Page, check_group, verify as verify_master

MASTER = 'human_20261122144027Z'
BASELINE = '10177b1dc72dde35d98a943c92022c5416851744'
MASTER_AGGREGATE = 'e905d29584e5579047a3834fe5089ba19bf6034cc162a44ce49ddbf74cd6a2a4'
TYPES = {'aze_passport': '05', 'grc_passport': '25', 'lva_passport': '32', 'srb_passport': '41'}
ACQUISITION = ROOT/'research/results/vlm_lora_v2/acquisition.json'
ACQUISITION_SHA = '6e5a137282fde408fbb6f620eb2adb928ab35cf0ed9d747c8774ea60a57f9f9c'


def split_master(master):
    """Match image SHA to an acquisition row, then match its identity to provider VIA metadata."""
    need(sha(ACQUISITION) == ACQUISITION_SHA, 'Historical acquisition receipt changed')
    sources = read(ACQUISITION)['sources']
    by_hash = {r['source_sha256']: r for r in sources}
    need(len(by_hash) == len(sources), 'Ambiguous acquisition image hash')
    templates, archive = provider_templates(ROOT)
    readme = (ROOT/'research/cache/upstream/midv2020_readme.txt').read_text(encoding='utf8')
    for code, number in TYPES.items():
        need(re.search(r'^\|\s*\d+\s*\|\s*'+code+r'\s*\|[^|]+\|\s*'+number+r'\s*\|', readme, re.M),
             'Document type mapping changed')
    selected, held = [], []
    for item in master:
        src = by_hash[item['full']['before']['file']]
        pid = item['physical_id']
        need(src['physical_id'] == pid and src['code'] in TYPES and pid in templates and
             archive == item['template_sha256'], 'Source document identity or archive mismatch')
        region = templates[pid]['regions'][int(item['primary_source'].removeprefix('region_'))]['region_attributes']
        need(region['field_name'] == item['native_key'] and
             precision(item['field'], region['value']) == item['source_precision']['body'], 'Native source precision')
        (held if TYPES[src['code']] == '25' else selected).append(item)
    return selected, held


def family_members(items):
    return {
        'provider_annotations': {i['template_sha256'] for i in items},
        'original_frames': {i['full']['before']['file'] for i in items},
        'derived_frames': {i['full']['after']['file'] for i in items},
        'region_crops': {r['sha256'] for i in items for r in i['regions'] if 'sha256' in r},
    }


def image_members(families):
    return families['original_frames'] | families['derived_frames'] | families['region_crops']


def check_html(html, sealed_html, items, excluded_terms, code):
    """Exact comparison with the original case sections also catches cross-case link swaps."""
    begin = '<details><summary>'
    master_header, original = sealed_html.split(begin, 1)
    header, rest = html.split(begin, 1)
    need(header.startswith(master_header), 'Changed sealed instructions')
    credit = header[len(master_header):].strip()
    need(re.fullmatch(r'(?:<p>[^<>]+</p>\s*)+', credit), 'Expected plain offline credit paragraphs')
    need(all(word in credit for word in ('Generated Photos', 'Azerbaijan', 'Latvia', 'Serbia')),
         'Scope-specific credits missing')
    need(all(term not in html for term in excluded_terms) and
         CODES[1-CODES.index(code)] not in html, 'Excluded identifier, hash or assessor present')
    original_cases, original_script = original.split('<script>')
    new_cases, new_script = rest.split('<script>')
    need(new_script == original_script, 'Offline export script changed')
    original_sections = {}
    for section in original_cases.split(begin):
        heading, body = section.split('</summary>\n', 1)
        original_sections[heading.split(' · ')[-1]] = body
    for n, (item, section) in enumerate(zip(items, new_cases.split(begin), strict=True), 1):
        cid = item['candidate_id']
        expected = f'{n}/{len(items)} · {escape(item["field"])} · {cid}</summary>\n'+original_sections[cid]
        need(section == expected, 'Changed case binding, image reference, response control or summary')
    page = Page()
    page.feed(html)
    page.close()
    need(list(page.forms) == [i['candidate_id'] for i in items], 'Form order or membership')
    return page.assets


def check_workspace(dest, master, code, selected, images, forbidden):
    root = dest/code
    for p in (root, *root.rglob('*')):
        attributes = getattr(p.lstat(), 'st_file_attributes', 0)
        need(not p.is_symlink() and not (attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT), 'External workspace link')
    inventory = {p.relative_to(root).as_posix(): sha(p) for p in root.rglob('*') if p.is_file()}
    manifest = read(dest/(code+'_manifest.json'))
    need(inventory == manifest, 'Workspace file missing, extra or changed')
    original_manifest = read(master/(code+'_manifest.json'))
    expected = {path: h for path, h in original_manifest.items() if path.startswith('assets/') and h in images}
    need(set(expected.values()) == images and inventory == expected | {'index.html': inventory['index.html']},
         'Missing or unreferenced image, crop or manifest member')
    html = (root/'index.html').read_text(encoding='utf8')
    sealed_html = (master/code/'index.html').read_text(encoding='utf8')
    need(check_html(html, sealed_html, selected, forbidden, code) == expected.keys(), 'HTML asset references')
    return digest(manifest)


def verify(dest):
    master = private_run(MASTER)
    public = EC/'human_gate/receipts'/MASTER
    need(dest.resolve() != master.resolve(), 'Historical run is immutable')
    need(sha(master/'aggregate.json') == sha(public/'aggregate.json') == MASTER_AGGREGATE and
         verify_master(master) == read(public/'verification.json'), 'Historical 45 replay differs')
    need(production_trust()['expected_journal_head_sha256'] is None and
         not any(master.parent.glob('*/signed_round1.json')), 'Live decisions require reconciliation')
    original = read(master/'queue.json')
    selected, held = split_master(original)
    keep_ids = {i['physical_id'] for i in selected}
    hold_ids = {i['physical_id'] for i in held}
    need(not keep_ids & hold_ids and (len(selected), len(held), len(keep_ids), len(hold_ids)) == (37, 8, 18, 6),
         'Rights-only partition differs')
    need(read(dest/'queue.json') == selected, 'Changed case, order, precision or scope')
    selection = read(dest/'selection.json')
    excluded = {i['candidate_id'] for i in held}
    for name, values in [('included_physical_ids', keep_ids), ('excluded_physical_ids', hold_ids),
                         ('excluded_candidates', excluded)]:
        need(selection[name] == sorted(values), 'Private selection receipt differs')
    families = family_members(selected)
    images = image_members(families)
    held_images = image_members(family_members(held))
    need(not images & held_images, 'Retained and held artifacts overlap')
    forbidden = held_images | hold_ids | excluded | {digest(i) for i in held}
    packages = {code: check_workspace(dest, master, code, selected, images, forbidden) for code in CODES}
    need(len(set(packages.values())) == 2, 'Assessor isolation')
    families['review_workspaces'] = set(packages.values())
    aggregate = read(dest/'aggregate.json')
    need(aggregate['baseline'] == BASELINE and aggregate['scope'] == 'C2_37_PROPOSED' and
         aggregate['master_aggregate_sha256'] == MASTER_AGGREGATE and
         aggregate['acquisition_sha256'] == ACQUISITION_SHA and
         aggregate['type_mapping_sha256'] == digest(TYPES), 'Scope baseline')
    need(aggregate['scientific_gate'] == 'GO_PREPARATORY_ONLY' and aggregate['owner_approval'] is None and
         aggregate['assessor_sharing'] == 'REVIEW_ACCESS_PENDING' and
         aggregate['images_per_workspace'] == len(images) and aggregate['forms_per_workspace'] == len(selected)
         and aggregate['held'] == dict(candidates=len(held), physical_ids=len(hold_ids)), 'Scope counts or gates')
    for key, filename in [('queue_sha256','queue.json'), ('selection_sha256','selection.json'),
                          ('rights_file_sha256','artifact_rights.json')]:
        need(aggregate[key] == sha(dest/filename), 'Unbound aggregate')
    need(aggregate['package_sha256'] == packages and aggregate['source_precision'] ==
         dict(Counter(i['source_precision']['body'] for i in selected)), 'Aggregate package or precision')
    ledger = read(SOURCE/'qualification/evidence.json')
    selected_ids = {i['candidate_id'] for i in selected}
    check_group(aggregate['selected'], [r for r in ledger['candidates'] if r['candidate_id'] in selected_ids], selected_ids)
    rights = read(dest/'artifact_rights.json')
    need(len(rights) == len(families) == len(aggregate['rights']) and
         {r['artifact'] for r in rights} == families.keys(), 'Rights family coverage')
    upstream = read(master/'aggregate.json')['checks']['upstream_rights']
    for name, h in upstream.items():
        need(sha(ROOT/'research/cache/upstream'/('midv2020_'+name)) == h, 'Source text bytes changed')
    for r, summary in zip(rights, aggregate['rights'], strict=True):
        members = sorted(families[r['artifact']])
        need(r['members'] == members and r['version_digest'] == digest(members), 'Rights membership')
        need(r['decisions'] == PENDING and r['authority_of_record'] is None and
             r['required_approver'] == 'PROJECT_OWNER_D10' and r['evidence'] == upstream, 'Rights or authority')
        need(summary == {k:v for k,v in r.items() if k != 'members'} | {'unique_members':len(members)},
             'Rights aggregate')
    return dict(status='VERIFIED_TECHNICAL_37', aggregate_sha256=sha(dest/'aggregate.json'),
                verified_master_aggregate_sha256=MASTER_AGGREGATE,
                retained_candidates=len(selected), retained_physical_ids=len(keep_ids),
                excluded_candidates=len(held), excluded_physical_ids=len(hold_ids),
                rights_versions_checked=len(rights), images_per_workspace=len(images),
                asset_files_per_workspace=len(images)+1, forms_per_workspace=len(selected),
                total_forms=len(selected)*len(CODES), package_manifests_checked=len(packages),
                excluded_asset_or_form_matches=0, review_access='REVIEW_ACCESS_PENDING')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('run')
    dest = private_run(parser.parse_args().run)
    result = verify(dest)
    path = dest/'verification.json'
    if path.exists():
        need(result == read(path), 'Verification receipt differs')
    else:
        save_new(path, result)
    print(result['status'])
