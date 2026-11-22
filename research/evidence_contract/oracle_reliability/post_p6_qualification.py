"""Private evidence joins and aggregate-only post-P6 C2 technical qualification."""
import argparse
from collections import Counter, defaultdict
from pathlib import Path
from html import escape
import os

import cv2
import numpy as np
from PIL import Image, ImageOps

from ..reviewer_tools.strict import digest, need
from ..task55.data import EC, ROOT, read, save_new, sha
from . import c2_inventory, pixel_lineage_audit as pixel, reference_registry
from .c2_evidence_audit import CONDITIONS, classify
from .corpus_audit import provider_templates
from .p2_audit import HISTORY
from .post_p6_geometry import mapped_sources, region_impact, regions, replay_mutation, same_lineage

DATA = ROOT/'research/data'
P2 = EC/'execution/master_01/p2_20261120'
FROZEN = '088ab3bf7cb21ecfb44eb2ba8f0335648c2d64f64a1ec6106c8e897c4d1782c8'
STATES = ('PASS','FAIL','UNKNOWN')


def inputs(p2run):
    need(p2run.name not in ('.','..') and p2run.parent == EC/'local/p2_20261120', 'P2 run scope')
    agg = read(P2/'aggregate.json')
    need(sha(P2/'aggregate.json') == read(P2/'verification.json')['aggregate_sha256'], 'P2 receipt')
    hist = EC/'local'/HISTORY
    receipts = {str(hist/k):v for k,v in read(EC/'execution'/HISTORY/'receipt.json')['private_outputs'].items()}
    receipts.update({str(p2run/k):v for k,v in agg['private_manifest_sha256'].items()})
    for name,h in receipts.items():
        need(sha(Path(name)) == h, 'Private evidence hash mismatch: '+Path(name).name)
    candidates = read(hist/'c2_candidates.json')
    rebuilt, _ = c2_inventory.build(ROOT,read(hist/'lineage.json'))
    templates, archive_sha = provider_templates(ROOT)
    need(candidates == rebuilt and digest(candidates) == agg['c2']['candidate_inventory_digest'] == FROZEN,
         'Frozen candidate inventory')
    need({r['source_artifact_sha256'] for r in candidates} == {archive_sha}, 'Archive identity')
    priority = read(p2run/'c2_private.json')
    need([g['candidate_id'] for g in priority] == [c['candidate_id'] for c in candidates], 'Priority join')
    selected = [r for r,g in zip(candidates,priority) if g['followup_group']=='image_and_parent_link']
    need(len(selected)==110 and len({c['physical_instance'] for c in selected})==40, 'Priority roster')
    px = read(p2run/'pixel_private.json')
    for rel,h in px['manifests'].items():
        pixel.safe_path(DATA/rel,DATA)
        need(sha(DATA/rel)==h, 'P2 metadata changed: '+rel)
    return selected, templates, px, dict(archive=archive_sha, p2=sha(P2/'aggregate.json'),
        p2_receipt=sha(P2/'verification.json'), historical_receipt=sha(EC/'execution'/HISTORY/'receipt.json'),
        private_hashes={Path(k).name:v for k,v in receipts.items()}, p2_metadata=digest(px['manifests']))


def records(rel):
    obj = read(DATA/rel)
    return [r for group in obj.values() if isinstance(group,list) for r in group] if isinstance(obj,dict) else obj


def sources_and_children(ids, manifests):
    sources, children = defaultdict(list), defaultdict(list)
    hashes = dict(manifests)
    for rel in ('recovery_v4/midv/selection.json','midv2020/selection.json',
                'vlm_lora_v2/sources.json','vlm_lora_v2_r2/sources.json'):
        hashes[rel] = sha(DATA/rel)
        for index,row in enumerate(records(rel)):
            pid = row.get('physical_id') or 'midv2020/'+row['code']+'/'+Path(row['filename']).stem
            if pid in ids:
                path = row.get('path') or (DATA/rel).parent/row['code']/row['filename']
                sources[pid].append(dict(row,physical_id=pid,path=(ROOT/path).relative_to(DATA).as_posix(),
                    file=row.get('source_sha256') or row['image_sha256'],manifest=rel, index=index))
    for rel in sorted(manifests):
        for index,row in enumerate(records(rel)):
            if not isinstance(row,dict) or row.get('physical_id') not in ids or not row.get('input_sha256'):
                continue
            pid = row['physical_id']
            children[pid].append(dict(row,manifest=rel,index=index))
    return sources,children,hashes


def forensic_key(row):
    return dict(manifest=row['manifest'],index=row['index'])


def checked_images(ids, rows, sources):
    wanted = {s['path'] for ss in sources.values() for s in ss}
    for row in rows:
        if any(m.get('physical_id') in ids for m in row['records']):
            wanted.add(row['path'])
    cache, images = {}, {}
    for row in rows:
        if row['path'] in wanted:
            f = DATA/row['path']
            current = pixel.inspect(f,DATA,cache)
            ok = 'pixel' in current and all(current.get(k)==row.get(k) for k in ('file','pixel'))
            images[row['path']] = dict(file=row.get('file'),pixel=row.get('pixel'),ok=ok,
                                       error=None if ok else current.get('error','hash_mismatch'),
                                       size=row.get('size'),parents=row['bound_parent_files'])
    return images


def rgb(rel):
    with Image.open(DATA/rel) as img:
        return np.array(ImageOps.exif_transpose(img).convert('RGB'))


def geometry_for_id(pid, template, ss, children, images):
    data, accepted, rejected = [], [], Counter()
    for source in ss:
        im = images.get(source['path'],{})
        if not im.get('ok') or source['file'] != im['file']:
            rejected['source_missing_or_changed'] += 1
            continue
        geometry = mapped_sources(template,source)
        width,height = im['size']
        geometry = {i:q for i,q in geometry.items() if all(0<=x<width and 0<=y<height for x,y in q)}
        if not geometry:
            rejected['native_mapping_unverified'] += 1
        data.append(dict(source=source,geometry=geometry))
    # Identical path and hash may occur in multiple original acquisitions. Keep witnesses,
    # replay each transformation once, using its own full field list where available.
    full = {(r['manifest'],r.get('source_sha256')):r['fields'] for r in children
            if r.get('capture') == 'full' and r.get('fields')}
    seen = set()
    for item in data:
        source = item['source']
        path, parent = source['path'], None
        for r in children:
            child = (ROOT/r['path']).relative_to(DATA).as_posix()
            if r.get('capture') not in ('value_mask','field_clip','corner_clip','pair_a','pair_b','pair_mask'):
                continue
            if not same_lineage(source,r):
                rejected['other_parent_or_identity'] += 1
                continue
            im = images.get(child,{})
            if not im.get('ok') or im['file']!=r['input_sha256'] or source['file'] not in im['parents']:
                rejected['child_or_parent_hash_unbound'] += 1
                continue
            key = (source['file'],child)
            if key in seen:
                continue
            if parent is None:
                parent = rgb(path)
            child_image = rgb(child)
            transform = replay_mutation(parent,child_image,r,full.get((r['manifest'],source['file'])))
            if transform is None and 'original_sha256' in r:
                # Recovery generated PNG children with OpenCV's EXIF-aware JPEG decoder.
                raw = cv2.imdecode(np.fromfile(DATA/path,np.uint8),cv2.IMREAD_COLOR)
                transform = replay_mutation(cv2.cvtColor(raw,cv2.COLOR_BGR2RGB),child_image,r,None)
            if transform is None:
                rejected['mutation_replay_unverified'] += 1
                continue
            seen.add(key)
            accepted.append(dict(before=path,after=child,source_sha256=source['file'],
                input_sha256=r['input_sha256'],before_pixel=images[path]['pixel'],after_pixel=im['pixel'],
                capture=r['capture'],mutation_record=forensic_key(r),transform=transform))
    return data,accepted,dict(rejected)


def inspect_candidate(c,template,originals,edges):
    mapped, options = {}, []
    for item in originals:
        s = item['source']
        quads = regions(c,template,item['geometry'])
        if quads:
            mapped[s['path']] = dict(quads=quads, record=forensic_key(s), file=s['file'])
    for i,edge in enumerate(edges):
        if edge['before'] not in mapped:
            continue
        q = mapped[edge['before']]['quads']
        impact = {k:region_impact(v,edge['transform']) for k,v in q.items()}
        if any(v is None for v in impact.values()):
            continue
        primary = impact[c['primary_source_id']]
        backup = max(v for k,v in impact.items() if k != c['primary_source_id'])
        # Prefer a fully removed primary and intact backup, then partial or collateral hits.
        options.append(dict(edge=i, impact=impact, primary=primary,backup=backup))
    options.sort(key=lambda v:(-(v['primary']==1 and v['backup']==0),-(v['primary']>0 and v['backup']==0),
                               -v['primary'],v['backup'],v['edge']))
    best = options[0] if options else None
    status = dict.fromkeys(CONDITIONS,'UNKNOWN')
    status.update(reference_approved='FAIL',provenance_verified='PASS' if best else 'UNKNOWN')
    decisions, eligible = classify(c['primary_source_id'],c['backup_source_id'],status)
    reasons = {k:'human_source_readability_pending' for k in CONDITIONS[:4]}
    reasons.update(provenance_verified='hash_geometry_mutation_replayed' if best else 'no_verified_region_pair',
        distinct_sources='distinct_native_body_and_MRZ_regions', semantic_equality_approved='candidate_semantic_review_pending',
        reference_approved='empty_production_registry_and_missing_D10')
    return dict(candidate_id=c['candidate_id'],physical_instance=c['physical_instance'],field=c['field'],
        primary=c['primary_source_id'],backup=c['backup_source_id'],mechanical=c['mechanical_comparison'],
        template_sha256=c['source_artifact_sha256'],source_files=sorted({x['source']['file'] for x in originals}),
        source_regions=mapped,paired=options,best=best,conditions=decisions,reasons=reasons,eligible=eligible,
        authority='NO_CANDIDATE_PROPOSALS_ADJUDICATION_RIGHTS_OR_APPROVAL')


def review_package(dest,rows,by_id):
    folder = dest/'crops'
    folder.mkdir()
    html = ['<!doctype html><meta charset="utf-8"><title>Private C2 region inspection</title>',
            '<h1>C2 — private source inspection</h1><p>Measured geometry. Readability, semantics and rights require human review.</p>']
    current = None
    for r in rows:
        html.append('<h2>'+escape(r['candidate_id'])+'</h2><p>'+escape(r['field'])+'</p>')
        if not r['best']:
            html.append('<p>Corresponding mutation regions unresolved.</p>')
            continue
        edge = by_id[r['physical_instance']]['edges'][r['best']['edge']]
        quads = r['source_regions'][edge['before']]['quads']
        r['inspection'] = []
        for side in ('before','after'):
            path = edge[side]
            if current != path:
                pixels = rgb(path)
                current = path
            im = Image.fromarray(pixels)
            href = Path(os.path.relpath(DATA/path,dest)).as_posix()
            html.append('<p>'+escape(edge['capture']+' · '+r['primary']+' / '+r['backup'])+'</p>')
            html.append('<p><a href="'+escape(href,quote=True)+'">'+side+' — full image</a> SHA-256 '+edge['source_sha256' if side=='before' else 'input_sha256']+'</p>')
            offset = edge['transform']['origin'] if side=='after' else [0,0]
            for name,q in quads.items():
                shifted = np.array(q)-offset
                lo = np.maximum(0,np.floor(shifted.min(axis=0)).astype(int))
                hi = np.minimum(im.size,np.ceil(shifted.max(axis=0)).astype(int)+1)
                item = dict(side=side,region=name,quad=shifted.tolist(),full_file=edge['source_sha256' if side=='before' else 'input_sha256'],
                            full_pixel=edge[side+'_pixel'])
                if np.all(hi > lo):
                    rect = [int(i) for i in (*lo,*hi)]
                    target = folder/(digest([r['candidate_id'],side,name])+'.png')
                    im.crop(rect).save(target)
                    item.update(box=rect,crop=target.relative_to(dest).as_posix(),sha256=sha(target))
                    html.append('<figure><img loading="lazy" width="300" src="'+item['crop']+'"><figcaption>'+
                                escape(side+' '+name+' · '+item['sha256'])+'</figcaption></figure>')
                else:
                    item['absence'] = 'outside_child_frame'
                    html.append('<p>'+escape(name)+' outside frame</p>')
                r['inspection'].append(item)
    with (dest/'index.html').open('x',encoding='utf8') as f:
        f.write('\n'.join(html))


def calculate(rows):
    def counts(group):
        ids = {r['physical_instance'] for r in group}
        metrics = dict(source=lambda r:bool(r['source_files']), before_regions=lambda r:bool(r['source_regions']),
            paired_regions=lambda r:r['best'] is not None,
            primary_affected=lambda r:any(p['primary']>0 for p in r['paired']),
            primary_fully_removed_backup_intact=lambda r:any(p['primary']==1 and p['backup']==0 for p in r['paired']),
            eligible=lambda r:r['eligible'])
        return dict(candidates=len(group),physical_ids=len(ids),**{k:dict(candidates=sum(fn(r) for r in group),
            physical_ids=len({r['physical_instance'] for r in group if fn(r)})) for k,fn in metrics.items()})
    return dict(all=counts(rows),by_field={k:counts([r for r in rows if r['field']==k]) for k in sorted({r['field'] for r in rows})},
        condition_counts={k:{s:sum(r['conditions'][k]==s for r in rows) for s in STATES} for k in (*CONDITIONS,'distinct_sources')},
        mechanical=dict(Counter(r['mechanical'] for r in rows)),reason_counts=dict(Counter(v for r in rows for v in r['reasons'].values())))


def run(dest,p2run):
    need(not reference_registry.production_trust()['authorities'] and not reference_registry.approved_ids(),'Trust changed')
    candidates,templates,px,hashes = inputs(p2run)
    ids = {r['physical_instance'] for r in candidates}
    sources,children,metadata = sources_and_children(ids,px['manifests'])
    images = checked_images(ids,px['rows'],sources)
    by_id,rows = {},[]
    for pid in sorted(ids):
        orig,edges,rejects = geometry_for_id(pid,templates[pid],sources[pid],children[pid],images)
        by_id[pid] = dict(edges=edges,replay_diagnostics=rejects,
            original_witnesses=[dict(path=e['source']['path'],record=forensic_key(e['source'])) for e in orig])
        for c in candidates:
            if c['physical_instance']==pid:
                rows.append(inspect_candidate(c,templates[pid],orig,edges))
    review_package(dest,rows,by_id)
    save_new(dest/'evidence.json',dict(candidates=rows,physical_instances=by_id,images=images,
        metadata_sha256=metadata, inputs=hashes))
    summary=calculate(rows)
    summary.update(inputs=hashes,candidate_inventory_digest=FROZEN, verified_image_files=sum(i['ok'] for i in images.values()),
        unresolved_image_files=sum(not i['ok'] for i in images.values()),distinct_replayed_edges=sum(len(v['edges']) for v in by_id.values()),
        crop_files=len(list((dest/'crops').iterdir())),candidate_evidence_sha256=sha(dest/'evidence.json'),
        review_index_sha256=sha(dest/'index.html'),production_authorities=0,approved_references=0,
        scope='Priority image/parent leads only',scientific_gate='NO_GO_SUPERIORITY')
    save_new(dest/'c2.json',summary)


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('run')
    p.add_argument('p2_run')
    a=p.parse_args()
    need(all(Path(s).name==s and s not in ('.','..') for s in (a.run,a.p2_run)),'Expected run names')
    dest=EC/'local/post_p6'/a.run/'qualification'
    dest.mkdir(parents=True,exist_ok=False)
    run(dest,EC/'local/p2_20261120'/a.p2_run)
