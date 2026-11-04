"""Import all requested originals without converting quality classes into OCR truth."""
import csv
from collections import Counter
from pathlib import Path
import re
import cv2
import numpy as np
from PIL import Image
from research.labels_common import *
from research.labels_schema import field

def split_for(physical_id):
    ids=sorted(range(1,51),key=lambda i:uid('ocr-labels-split-20261104/'+str(i)))
    return 'train' if physical_id in ids[:30] else 'development' if physical_id in ids[30:40] else 'test'

def source_records():
    manifest_path=ROOT/'data/manifest.csv'
    with manifest_path.open(encoding='utf-8-sig',newline='') as f:manifest=list(csv.DictReader(f))
    if len(manifest)!=21050:raise ValueError('Exactly 21,050 requested originals required')
    indexed={r['relative_path']:r for r in manifest}
    if len(indexed)!=len(manifest):raise ValueError('Duplicate original path')
    acquisition=read(ROOT/'research/data/sources.json')
    if acquisition['failures'] or len(acquisition['records'])!=100:raise ValueError('All 100 author annotation archives required')
    seen=set();provenance=[]
    for source in sorted(acquisition['records'],key=lambda r:(r['source'],r['path'])):
        family=source['source'];name=Path(source['path']).stem;pid=int(name[:2])
        ann=ROOT/'research/data'/f'{family}_{name}.json'
        if sha(ann)!=source['normalized_sha256']:raise ValueError('Author annotation hash differs')
        entries=read(ann)
        templates=[(k,v) for k,v in entries.items() if 'quad' not in v]
        if len(templates)!=1:raise ValueError('Unique author template required')
        template_key,template=templates[0]
        ref=(ROOT/'full_dataset_original/midv500_dataset'/name/'images'/(name+'.tif') if family=='midv500'
             else ROOT/'full_dataset_original/midv2019_dataset'/(name+'.tif'))
        with Image.open(ref) as im:rw,rh=im.size
        provenance.append(dict(source=family,document=name,annotation_sha256=sha(ann),template_image_sha256=sha(ref),
                               template_dimensions=[rw,rh],whole_archive_checksum_verified=False))
        frame_rows=[]
        for filename,value in entries.items():
            if 'quad' not in value:continue
            suffix=Path(filename.split('ground_truth/',1)[1]).with_suffix('.tif')
            relative=(Path('full_dataset_original/midv500_dataset')/name/'images'/suffix if family=='midv500'
                      else Path('full_dataset_original/midv2019_dataset')/suffix)
            frame_rows.append((relative.as_posix(),value['quad'],filename,False))
        if family=='midv2019':frame_rows.append((ref.relative_to(ROOT).as_posix(),[[0,0],[rw-1,0],[rw-1,rh-1],[0,rh-1]],template_key,True))
        for relative,quad,entry,is_reference in frame_rows:
            if relative not in indexed:raise ValueError('Author image not in original inventory: '+relative)
            if relative in seen:raise ValueError('Repeated original')
            seen.add(relative);label=indexed[relative];native=f'{family}/'+('reference/'+name if is_reference else Path(relative).stem)
            yield dict(native_uid=native,physical_id='midv_legacy_document/'+str(pid),source=family,
                quality=label['label'],role=split_for(pid),path=relative,template=template,template_dimensions=[rw,rh],
                card_quad=quad,annotation_ref=dict(file=ann.relative_to(ROOT).as_posix(),entry=entry,template_entry=template_key),
                reference=is_reference,mapping_kind=label['mapping_kind'],quality_origin=label['origin'])
    if seen!=set(indexed):raise ValueError('Requested originals missing annotations')
    save(OUT/'author_sources.json',dict(records=provenance,manifest_sha256=sha(manifest_path),
        author_archive_index_sha256=sha(ROOT/'research/data/sources.json'),quality_labels_are_not_OCR_labels=True))

def annotation_for(record,width,height):
    rw,rh=record['template_dimensions'];quad=np.float32(record['card_quad'])
    if quad.shape!=(4,2) or not np.isfinite(quad).all():raise ValueError('Invalid author card quadrilateral')
    H=cv2.getPerspectiveTransform(np.float32([[0,0],[rw-1,0],[rw-1,rh-1],[0,rh-1]]),quad)
    fields=[];nontext=0
    for key,item in sorted(record['template'].items()):
        if not isinstance(item,dict) or not isinstance(item.get('value'),str) or 'quad' not in item:
            nontext+=1;continue
        q=cv2.perspectiveTransform(np.float32([item['quad']]),H)[0]
        ref=dict(record['annotation_ref'],field=key)
        value=field(key,item['value'],q,width,height,origin='author_template' if record['reference'] else 'author_template_projection',annotation_ref=ref)
        value['field_id']=key;fields.append(value)
    if not fields:raise ValueError('No author text fields')
    return fields,nontext

def run():
    freeze_previous();cv2.setNumThreads(1)
    conn=connect(True);create_tables(conn)
    contract=dict(manifest=sha(ROOT/'data/manifest.csv'),annotations=sha(ROOT/'research/data/sources.json'),version=1)
    old=conn.execute('SELECT value FROM metadata WHERE key=?',('legacy_contract',)).fetchone()
    if old and read_json(old[0])!=contract:raise ValueError('Original corpus contract changed; use another release')
    conn.execute('INSERT OR IGNORE INTO metadata VALUES (?,?)',('legacy_contract',canonical(contract)));conn.commit()
    stats=Counter();visibility=Counter();scripts=Counter();reference_count=0;resumed=0
    for index,record in enumerate(source_records(),1):
        key=uid(record['native_uid']);path=ROOT/record['path'];stat=path.stat()
        existing=conn.execute('SELECT bytes,mtime_ns FROM images WHERE uid=?',(key,)).fetchone()
        if existing:
            if tuple(existing)!=(stat.st_size,stat.st_mtime_ns):raise ValueError('Original bytes/mtime changed during resume')
            resumed+=1
        else:
            with Image.open(path) as im:width,height=im.size;orientation=int(im.getexif().get(274,1))
            fields,nontext=annotation_for(record,width,height)
            meta={k:record[k] for k in ('card_quad','annotation_ref','reference','mapping_kind','quality_origin','template_dimensions')}
            meta.update(exif_orientation=orientation,font='unknown_author_font',semantic_mapping='native_fields_preserved',nontext_regions=nontext)
            conn.execute('INSERT INTO images VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                (key,record['native_uid'],record['physical_id'],record['source'],record['quality'],record['role'],record['path'],
                 sha(path),stat.st_size,stat.st_mtime_ns,width,height,'raw_pixels',canonical(meta)))
            conn.executemany('INSERT INTO fields VALUES (?,?,?,?,?)',
                [(key,f['field_id'],f['raw_key'],f['reference_text'],canonical(f)) for f in fields])
        stats[record['source']]+=1;reference_count+=record['reference']
        if index%32==0:conn.commit();progress('legacy_import',index,21050,resumed=resumed)
    conn.commit()
    count=conn.execute('SELECT COUNT(*) FROM images WHERE source IN (?,?)',('midv500','midv2019')).fetchone()[0]
    if count!=21050 or reference_count!=50:raise ValueError('Original/reference coverage differs')
    for row in conn.execute('SELECT annotation FROM fields'):
        f=read_json(row[0]);visibility[f['frame_visibility']['status']]+=1;scripts.update(f['scripts'])
    groups={}
    for row in conn.execute('SELECT physical_id,COUNT(DISTINCT role) AS roles FROM images GROUP BY physical_id'):
        if row['roles']!=1:raise ValueError('Same physical document crosses OCR roles')
    fields=conn.execute('SELECT COUNT(*) FROM fields').fetchone()[0]
    original_bytes=conn.execute('SELECT SUM(bytes) FROM images').fetchone()[0]
    quality_counts=dict(conn.execute('SELECT quality,COUNT(*) FROM images GROUP BY quality').fetchall())
    conn.execute('PRAGMA wal_checkpoint(TRUNCATE)');conn.close()
    save(OUT/'corpus_release.json',dict(version='ocr_labels_v1',images=count,physical_document_groups=50,fields=fields,
        sources=dict(stats),extra_midv2019_references=reference_count,extra_reference_quality='Clean',
        annotation_database_sha256=sha(DB),original_encoded_bytes=original_bytes,quality_counts=quality_counts,
        human_readability_labels=0,readability_unassessed_fields=fields,frame_visibility=dict(visibility),scripts=dict(scripts),
        native_keys_preserved=True,semantic_keys_not_inferred_from_position=True,
        quality_labels_never_substitute_transcripts=True,positions='Author template polygons projected by author card corners; not independently annotated per-frame text boxes',
        split='Fixed SHA rank of50 physical documents:30 train/10 development/10 test; both MIDV families and references grouped',
        historical_exposure='Legacy dataset used by quality and prior geometry/OCR studies; this is not a newly unseen test for existing systems',
        raw_text_and_images_published_to_git=False))
    progress('legacy_import',21050,21050,resumed=resumed)

def read_json(value):return json.loads(value)

if __name__=='__main__':run()
