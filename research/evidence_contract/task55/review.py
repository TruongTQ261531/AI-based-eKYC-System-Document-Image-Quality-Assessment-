"""Prepare a verdict/output-free census packet; validate future human exports.

No human labels are created by prepare(). No model output is loaded to select,
populate or validate a transcription. Import only freezes actual submitted
observations; it never issues a GoldLabel, certificate or confirmatory GO.
"""
from __future__ import annotations

from collections import defaultdict,Counter
import json
from pathlib import Path
import random
import shutil

from .data import EC,ROOT,OUT,PILOT,PUBLIC,read,sha,digest,save_new

PACKET_ROOT=EC/'local/task55_blind_review_v1'
LABELS={'id_number':'Số giấy tờ','school':'Tên trường','address':'Địa chỉ','full_name':'Họ và tên',
        'student_id':'Mã học sinh / sinh viên','dob':'Ngày sinh','gender':'Giới tính',
        'category':'Loại / nhóm','category_code':'Mã tương ứng loại / nhóm'}


def build_packet(destination=PACKET_ROOT):
    destination=Path(destination).resolve()
    if not destination.is_relative_to((EC/'local').resolve()):raise ValueError('Private packet must stay in local/')
    if destination.exists():raise FileExistsError('Keep existing packet/drafts; no overwrite')
    lock=read(PUBLIC/'pilot_lock.json')
    for name in ('inputs.json','scoring.json'):
        if sha(PILOT/name)!=lock['manifests'][name]:raise ValueError('Changed pilot input/reference manifest')
    requests=read(PILOT/'inputs.json')['inputs'];packs=read(PILOT/'scoring.json')['packs']
    fields=defaultdict(set);links=defaultdict(list)
    for raw in packs:
        if raw['graph']['role'] not in ('fixture','development') or raw['graph']['data_policy']!='fictional':
            raise ValueError('Packet cannot include private, real or confirmatory data')
        for pixel in (raw['pair']['original_pixel_sha256'],raw['pair']['input_pixel_sha256']):
            fields[pixel].update(f['key'] for f in raw['graph']['fields'])
            links[pixel].append(dict(pack_id=raw['pack_id'],arm=raw['arm'],stratum=raw['stratum'],
                                    contract=raw['pair']['contract_id']))
    # Census, not alarm-conditioned or favorable-case sampling. Every image has
    # inclusion probability1; pages are shuffled without method outputs.
    ordered=sorted(requests,key=lambda r:r['pixel_sha256']);random.Random(550086).shuffle(ordered)
    destination.mkdir(parents=True);(destination/'images').mkdir()
    pages=[];mapping={}
    for raw in ordered:
        source=Path(raw['path'])
        if raw['role'] not in ('fixture','development') or raw['data_policy']!='fictional' or sha(source)!=raw['file_sha256']:
            raise ValueError('Input provenance mismatch')
        image_id='IMG-'+digest(['task55-review-order/1',raw['pixel_sha256']])[:12]
        target=destination/'images'/(image_id+'.png')
        with source.open('rb') as src,target.open('xb') as dst:shutil.copyfileobj(src,dst)
        if sha(target)!=raw['file_sha256']:raise ValueError('Copied image bytes changed')
        slots=[dict(slot_id='F-'+digest([image_id,key])[:16],field_key=key,label=LABELS.get(key,key)) for key in sorted(fields[raw['pixel_sha256']])]
        pages.append(dict(image_id=image_id,image='images/'+target.name,file_sha256=raw['file_sha256'],fields=slots))
        mapping[image_id]=dict(pixel_sha256=raw['pixel_sha256'],links=links[raw['pixel_sha256']],source_path=str(source))
    packet=dict(schema='blind-reference-review/1',purpose='blind_review',pages=pages,
                selection='census_of_existing_development_pilot_unique_images',field_scope='annotated semantic keys, not a claim of complete document-field coverage')
    packet['packet_id']=digest(packet)
    save_new(destination/'packet_manifest.json',packet)
    for name in ('review_core.js','review_ui.js'):
        with (EC/'task55'/name).open('rb') as src,(destination/name).open('xb') as dst:shutil.copyfileobj(src,dst)
    template=(EC/'task55/review_template.html').read_text(encoding='utf-8')
    page=template.replace('<!--PACKET-->','<script>window.BLIND_PACKET='+json.dumps(packet,ensure_ascii=False).replace('</','<\\/')+';</script>')
    with (destination/'index.html').open('x',encoding='utf-8',newline='\n') as stream:stream.write(page)
    mapping_path=EC/'local/task55_analyst/review_mapping.json'
    save_new(mapping_path,dict(packet_id=packet['packet_id'],mapping=mapping))
    # Values are only used for a leak audit, never embedded or filled in answers.
    references={f['reference_value'] for raw in packs for f in raw['graph']['fields'] if len(f['reference_value'])>=8}
    leaks=[value for value in references if value in page]
    if leaks:raise ValueError('Author reference leaked into textual review interface')
    forbidden=('CANDIDATE_VIOLATION','predicted_fields','reference_value','expected_source_state','A_flat','B3_visible_reference')
    if any(word in page for word in forbidden):raise ValueError('Method information in blind interface')
    files={p.relative_to(destination).as_posix():sha(p) for p in destination.rglob('*') if p.is_file()}
    report=dict(status='BLOCKED_ON_HUMAN_REVIEW',packet_id=packet['packet_id'],image_count=len(pages),
        field_slots=sum(len(p['fields']) for p in pages),actual_human_observations=0,actual_reviewer_count=0,
        reviewed_images=0,selection='31-image census; no alarm-based exclusion; inclusion probability1',
        source_of_transcripts='human input only; all fields initially blank',file_hashes=files,
        author_values_or_model_outputs_embedded=False,author_reference_leak_count=0,
        model_output_access_by_packet_preparation=False,blindness_scope='per-image outputs/verdicts/author strings hidden; image mutations and prior personal exposure cannot be hidden',
        analyst_mapping_sha256=sha(mapping_path),
        packet_private_path=str(destination),analyst_mapping_outside_packet=True,confirmatory=False,
        independent_review_verified=False,model_calls=0)
    save_new(OUT/'review_packet_preparation.json',report)
    print(json.dumps({k:report[k] for k in ('status','image_count','field_slots','actual_human_observations','model_calls')}),flush=True)
    return packet


def validate_export(value,packet,*,allow_unit=False):
    if digest({k:v for k,v in packet.items() if k!='packet_id'})!=packet.get('packet_id'):
        raise ValueError('Modified packet manifest')
    if value.get('schema')!='blind-human-review/1' or value.get('packet_id')!=packet['packet_id']:
        raise ValueError('Wrong review schema/packet')
    if value.get('mode')!='human_entered' and not (allow_unit and value.get('mode')=='unit_injected'):
        raise ValueError('Synthetic/control exports are not human evidence')
    if value.get('packet_purpose')!='blind_review' and not allow_unit:raise ValueError('Not a human-review packet')
    if value.get('export_kind')!='reviewed_observations':raise ValueError('Draft is a backup, not submitted annotations')
    reviewer=value.get('reviewer',{})
    if (not isinstance(reviewer.get('reviewer_id'),str) or not reviewer['reviewer_id'].strip()
            or reviewer.get('role') not in ('project_author','external_reviewer','unknown')
            or reviewer.get('output_exposure') not in ('none','aggregate_only','per_image','unknown')
            or reviewer.get('independence_verified') is not False):
        raise ValueError('Reviewer self-attestation required; independence cannot be auto-certified')
    if not isinstance(value.get('items'),list):raise ValueError('Expected a list of field observations')
    slots={f['slot_id']:(p,f) for p in packet['pages'] for f in p['fields']}
    seen=set();complete=[];pending=[]
    for item in value.get('items',[]):
        slot=item.get('slot_id')
        if slot not in slots or slot in seen:raise ValueError('Unknown/duplicate review slot')
        seen.add(slot);page,field=slots[slot]
        if (item.get('image_id')!=page['image_id'] or item.get('image_sha256')!=page['file_sha256']
                or item.get('field_key')!=field['field_key']):raise ValueError('Image/field/hash mismatch')
        if item.get('touched') is not True:raise ValueError('Untouched default cannot be a human observation')
        for key in ('availability','readability','semantic_key_confirmed','observed_transcript','notes','prior_exposure'):
            if not isinstance(item.get(key),str):raise ValueError('Explicit observation strings required')
        if not isinstance(item.get('sources'),list):raise ValueError('Explicit source observations required')
        for source in item['sources']:
            if not isinstance(source,dict) or any(not isinstance(source.get(k,''),str) for k in (
                    'kind','location','availability','readability','observed_text','mrz_line_1','mrz_line_2')):
                raise ValueError('Invalid source observation shape')
        sources_complete=all(source.get('kind') in ('body','duplicated_body','mrz','other','uncertain')
            and source.get('location','').strip()
            and source.get('availability') in ('visible','partial','not_seen','uncertain')
            and source.get('readability') in ('readable','partial','unreadable','uncertain','language_unknown','unassessed')
            for source in item['sources'])
        valid=(item['availability'] in ('visible','partial','not_seen','uncertain')
            and item['readability'] in ('readable','partial','unreadable','uncertain','language_unknown','unassessed')
            and item['semantic_key_confirmed'] in ('yes','no','uncertain')
            and item['prior_exposure'] in ('no','yes','uncertain')
            and not(item['readability']=='readable' and not item['observed_transcript'].strip())
            and not(item['availability']=='not_seen' and (item['observed_transcript'].strip() or item['readability']=='readable'))
            and not(item['availability']=='visible' and not item['sources']) and sources_complete)
        (complete if valid else pending).append(item)
    if not complete:raise ValueError('No complete human observations; keep the draft for later')
    return dict(status='SINGLE_REVIEW_UNADJUDICATED',complete_observations=len(complete),
        incomplete_observations=len(pending),missing_slots=len(slots)-len(seen),reviewer_count=1,
        reviewer_independence_verified=False,inter_rater_agreement=None,human_readability_certificates_issued=0,
        model_failure_gold_labels_issued=0,usable_for_confirmatory=False,packet_id=packet['packet_id'],
        observation_snapshot_sha256=digest(value),complete_items=complete)


def import_export(path,packet_root=PACKET_ROOT):
    value=read(path);packet=read(Path(packet_root)/'packet_manifest.json')
    result=validate_export(value,packet)
    # Freeze human observations before any model/verdict join. No correctness
    # or source-completeness label is inferred from OCR or absent graph nodes.
    folder=EC/'local/task55_human_submissions'/result['observation_snapshot_sha256']
    if folder.exists():raise FileExistsError('This submission is already frozen')
    save_new(folder/'observations.json',value);save_new(folder/'validation.json',result)
    public={k:v for k,v in result.items() if k!='complete_items'}
    save_new(OUT/('human_import_'+result['observation_snapshot_sha256'][:12]+'.json'),public)
    print(json.dumps(public),flush=True)


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=('prepare','import'));parser.add_argument('--submission',type=Path);args=parser.parse_args()
    if args.action=='prepare':build_packet()
    elif args.submission:import_export(args.submission)
    else:parser.error('--submission is required for an actual human export')
