"""Paired all-declared-source masking with a whole neighboring body field."""
import collections
import copy
import hashlib
import math
import random
import cv2
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageOps
from research.hp_common import *
from research.v2_common import DATA as R2DATA, seed, HELD_LAYOUTS
from research.v2_data import mapped_fields,augment,mock
from research.vlm_data import LABELS
from research.v3_sources import source_graph,visible_realizations
from research.v3_metrics import reference_precision
from research.priority_progress import bbox,gap


def rect_quad(box):
    a,b,c,d=box;return [[a,b],[c,b],[c,d],[a,d]]


def nodes_for(full,source=None):
    if source is not None:
        nodes=source_graph(source)[0]
        return [dict(n,mask_components=n['components']) for n in nodes]
    result=[]
    for f in full['fields']:
        pieces=[f['quad']]
        if 'label_box' in f:pieces.append(rect_quad(f['label_box']))
        result.append(dict(key=f['key'],value=f['value'],components=pieces,
            mask_components=[f['quad']],kind='body',priority=0,author_source='authored/'+f['key']))
    return result


def refs_for(nodes,masks,width,height,H=None):
    refs,evidence,masked=visible_realizations(nodes,np.eye(3) if H is None else H,masks,width,height)
    target={key:sorted(values,key=lambda r:(-reference_precision(r) if key in ('dob','expiry_date','issue_date') else 0,r['priority']))[0]['value'] for key,values in refs.items()}
    return dict(target=target,source_refs=refs,source_evidence=evidence,masked_keys=sorted(masked))


def regions_for(nodes,key):
    masks=[]
    for node in nodes:
        if node['key']!=key:continue
        for q0 in node.get('mask_components',node['components']):
            q=np.float32(q0);center=q.mean(axis=0);masks.append((q-center)*1.04+center)
    return masks


def pair_for(nodes,width,height,pid,error_keys=None):
    error_keys=error_keys or {};original=refs_for(nodes,[],width,height)['source_refs']
    keys=sorted(k for k,refs in original.items() if any(r['kind'].startswith('body') for r in refs))
    after={k:refs_for(nodes,regions_for(nodes,k),width,height)['source_refs'] for k in keys}
    boxes={k:[bbox(n['components'][0]) for n in nodes if n['key']==k and n['kind'].startswith('body')
              and n['author_source'] in {r['source'] for r in original[k]}] for k in keys}
    ranked=[]
    for index,a in enumerate(keys):
        for b in keys[index+1:]:
            if a in after[a] or b in after[b]:continue
            if b not in after[a] or a not in after[b]:continue
            if not any(r['kind'].startswith('body') for r in after[a][b]):continue
            if not any(r['kind'].startswith('body') for r in after[b][a]):continue
            distance=min(gap(x,y) for x in boxes[a] for y in boxes[b])/math.hypot(width,height)
            if distance>.08:continue
            ranked.append((-(error_keys.get(a,0)+error_keys.get(b,0)),distance,
                           hashlib.sha256((pid+'/'+a+'/'+b).encode()).hexdigest(),a,b))
    if not ranked:return None
    best=min(ranked);return dict(a=best[3],b=best[4],normalized_gap=best[1])


def image_for(full):
    path=ROOT/full['path']
    if sha(path)!=full['input_sha256']:raise ValueError('Base input changed')
    with Image.open(path) as im:return np.asarray(ImageOps.exif_transpose(im).convert('RGB')).copy()


def masked_capture(image,full,nodes,hidden,kept):
    masks=regions_for(nodes,hidden);result=image.copy();fields=copy.deepcopy(full['fields'])
    for q in masks:cv2.fillConvexPoly(result,np.rint(q).astype(np.int32),(35,38,42))
    for f in fields:f['occluded']=any(cv2.intersectConvexConvex(np.float32(f['quad']),m)[0]>.05 for m in masks)
    refs=refs_for(nodes,masks,image.shape[1],image.shape[0])
    if hidden in refs['target'] or kept not in refs['target'] or not any(r['kind'].startswith('body') for r in refs['source_refs'][kept]):
        raise ValueError('Pair did not hide/retain the declared evidence')
    return result,fields,refs,[q.tolist() for q in masks]


def write_capture(full,nodes,capture,uid,hidden=None,kept=None):
    image=image_for(full);H=np.eye(3);masks=[]
    if capture in ('pair_a','pair_b','pair_mask'):
        result,fields,refs,masks=masked_capture(image,full,nodes,hidden,kept)
    else:
        result,fields=augment(image,full['fields'],full['physical_id'],capture)
        if capture=='field_clip':H[1,2]=fields[0]['quad'][0][1]-full['fields'][0]['quad'][0][1]
        if capture=='value_mask':
            rng=random.Random(seed(full['physical_id']+'/'+capture))
            for i in rng.sample(range(len(full['fields'])),rng.randrange(1,len(full['fields'])+1)):
                q=np.float32(full['fields'][i]['quad']);center=q.mean(axis=0);masks.append((q-center)*1.04+center)
        refs=refs_for(nodes,masks,result.shape[1],result.shape[0],H)
        masks=[np.asarray(q).tolist() for q in masks]
    path=DATA/'images'/(hashlib.sha256(uid.encode()).hexdigest()+'.png');path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        with Image.open(path) as old:
            if not np.array_equal(np.asarray(old.convert('RGB')),result):raise ValueError('Existing paired raster has different pixels')
    else:Image.fromarray(result).save(path,compress_level=1)
    row={k:v for k,v in full.items() if k not in ('target','source_refs','source_evidence','masked_keys','accepted_values','body_target','fields')}
    row.update(uid=uid,path=path.relative_to(ROOT).as_posix(),input_sha256=sha(path),capture=capture,
        fields=fields,width=result.shape[1],height=result.shape[0],mask_regions=masks,**refs)
    if hidden is not None:row.update(pair_hidden_key=hidden,pair_kept_key=kept)
    return row


def new_authored(index):
    pid=f'hard_pairs_v1/test/{index:03}'
    _,old_fields,_,_=mock(pid,index,'development')
    font_path=Path('C:/Windows/Fonts/calibri.ttf' if index%2==0 else 'C:/Windows/Fonts/cambria.ttc')
    def font(n):return ImageFont.truetype(str(font_path),n)
    im=Image.new('RGB',(1200,800),(241,244,235));draw=ImageDraw.Draw(im);color=(25,80,88)
    draw.rectangle((0,0,1200,103),fill=color)
    draw.text((30,20),'SPECIMEN / GIẤY TỜ MẪU MỚI',font=font(34),fill='white')
    draw.text((30,65),'FICTIONAL RESEARCH DATA - NOT VALID FOR IDENTIFICATION',font=font(20),fill='white')
    layout='hp_columns' if index%2==0 else 'hp_rows';fields=[]
    for j,old in enumerate(old_fields):
        x,y,width=(35+(j%2)*600,145+(j//2)*185,545) if index%2==0 else (260,140+j*118,900)
        label=LABELS[old['key']][0 if index%3 else 1]+':'
        draw.text((x,y),label,font=font(23),fill=(50,60,65),anchor='lt')
        label_box=list(draw.textbbox((x,y),label,font=font(23),anchor='lt'));size=33
        while font(size).getlength(old['value'])>width and size>14:size-=1
        draw.text((x,y+35),old['value'],font=font(size),fill=(12,20,26),anchor='lt')
        value_box=draw.textbbox((x,y+35),old['value'],font=font(size),anchor='lt')
        fields.append(dict(key=old['key'],value=old['value'],quad=rect_quad(value_box),label_box=label_box))
    box=(990,575,1170,735) if index%2==0 else (30,145,220,390)
    draw.rounded_rectangle(box,radius=12,fill=(192,208,211),outline=color,width=2)
    draw.text((30,765),'MẪU GIẢ LẬP / KHÔNG CÓ GIÁ TRỊ ĐỊNH DANH',font=font(19),fill=color)
    path=DATA/'authored_sources'/f'{index:03}.png';path.parent.mkdir(parents=True,exist_ok=True)
    im.save(path,compress_level=1)
    return dict(physical_id=pid,uid=pid+'/base',role='test',source='authored',device='renderer',layout=layout,
        held_layout=True,font_sha256=sha(font_path),font_file=font_path.name,path=path.relative_to(ROOT).as_posix(),
        input_sha256=sha(path),fields=fields,width=1200,height=800,capture='full')


def build():
    preserve()
    if (DATA/'samples.json').exists():
        card=read(OUT/'dataset_card.json')
        if sha(DATA/'samples.json')!=card['samples_sha256'] or card['derivation_code_sha256']!=sha(Path(__file__)):
            raise ValueError('Prepared data/code differs; preserve it and register an amendment')
        print('HP_DATA_ALREADY_VERIFIED',card['rows']);return
    old=read(OLD_DATA/'samples.json');sources={r['physical_id']:r for r in read(R2DATA/'sources.json')}
    full={r['physical_id']:r for r in old if r['capture']=='full' and (r['role']!='train' or r['variant']=='partial')}
    nodes={pid:nodes_for(r,sources.get(pid)) for pid,r in full.items()}
    inventory=read(ROOT/'research/cache/current_progress/hard_case_inventory.json')
    selected={r['physical_id'] for r in inventory['selected_train']}
    if len(selected)!=32 or not selected<={r['physical_id'] for r in old if r['role']=='train'}:raise ValueError('Unexpected hard-case IDs')
    frequencies=collections.Counter(k for r in inventory['development_errors'][inventory['model']]
        for kind in ('hidden_output_keys','neighbor_omission_keys','neighbor_wrong_keys') for k in r[kind])
    pairs={pid:pair_for(nodes[pid],full[pid]['width'],full[pid]['height'],pid,frequencies) for pid in selected}
    rows=[];changes=[];fallbacks=[]
    for r in old:
        if r['role']!='train' or r['variant']!='partial':continue
        pid=r['physical_id'];pair=pairs.get(pid)
        if pid in selected and pair and r['slot'] in (3,4):
            hidden,kept=(pair['a'],pair['b']) if r['slot']==3 else (pair['b'],pair['a'])
            new=write_capture(full[pid],nodes[pid],'pair_a' if r['slot']==3 else 'pair_b',r['uid'],hidden,kept)
            new.update(variant='partial',slot=r['slot']);rows.append(new)
            changes.append(dict(uid=r['uid'],physical_id=pid,source=r['source'],old_sha256=r['input_sha256'],new_sha256=new['input_sha256']))
        else:rows.append(copy.deepcopy(r))
    for pid,pair in pairs.items():
        if pair is None:fallbacks.append(dict(role='train',physical_id=pid,reason='no_whole_nearby_counterfactual_pair'))
    rows.extend(copy.deepcopy(r) for r in old if r['role']=='development')
    new_bases=[]
    for source in read(DATA/'sources.json'):
        row=dict(physical_id=source['physical_id'],uid=source['physical_id']+'/base',role='test',source='midv2020',
            device=source['device'],layout=source['code'],held_layout=source['code'] in HELD_LAYOUTS,
            path=source['path'],input_sha256=source['source_sha256'],width=source['width'],height=source['height'],
            fields=mapped_fields(source),capture='full')
        full[row['physical_id']]=row;nodes[row['physical_id']]=nodes_for(row,source);new_bases.append(row)
    for i in range(24):
        row=new_authored(i);full[row['physical_id']]=row;nodes[row['physical_id']]=nodes_for(row);new_bases.append(row)
    for base in [r for r in full.values() if r['role']=='development']+new_bases:
        pid=base['physical_id'];pair=pair_for(nodes[pid],base['width'],base['height'],pid)
        captures=('pair_mask',) if base['role']=='development' else ('full','field_clip','value_mask','pair_mask')
        for kind in captures:
            uid=pid+'/hp/'+kind
            if kind=='pair_mask' and pair:
                a,b=(pair['a'],pair['b']) if seed(pid+'/pair-direction')%2==0 else (pair['b'],pair['a'])
                sample=write_capture(base,nodes[pid],kind,uid,a,b)
            else:
                actual='value_mask' if kind=='pair_mask' else kind
                sample=write_capture(base,nodes[pid],actual,uid)
                if kind=='pair_mask':
                    sample['capture']='pair_mask';sample['pair_fallback']=True
                    fallbacks.append(dict(role=base['role'],physical_id=pid,reason='no_whole_nearby_counterfactual_pair'))
            rows.append(sample)
    ids={role:{r['physical_id'] for r in rows if r['role']==role} for role in ('train','development','test')}
    if any(ids[a]&ids[b] for a in ids for b in ids if a!=b):raise ValueError('Role document overlap')
    if len(ids['test'])!=48 or len([r for r in rows if r['role']=='test'])!=192:raise ValueError('Incomplete new test')
    old_ids={r['physical_id'] for r in old}
    if ids['test']&old_ids:raise ValueError('New test reused old document')
    old_hashes={r['input_sha256'] for r in old};new_hashes={r['input_sha256'] for r in rows if r['role']=='test'}
    if old_hashes&new_hashes:raise ValueError('New test reused old raster')
    old_fingerprints={stable_hash(r['target']) for r in old if r['capture']=='full'}
    if any(stable_hash(r['target']) in old_fingerprints for r in rows if r['role']=='test' and r['capture']=='full'):
        raise ValueError('New full-document answers duplicate previous complete answers')
    save(DATA/'samples.json',rows)
    save(DATA/'base_graphs.json',[dict(base=r,nodes=nodes[r['physical_id']]) for r in full.values()])
    manifest=[{k:r[k] for k in ('uid','physical_id','role','source','device','layout','capture','input_sha256','width','height')} for r in rows]
    save(OUT/'dataset_manifest.json',manifest)
    save(OUT/'training_changes.json',dict(changed_slots=len(changes),changed_document_instances=len({r['physical_id'] for r in changes}),
        selected_instances=32,source_counts=dict(collections.Counter(r['source'] for r in changes)),rows=changes,fallbacks=fallbacks))
    save(OUT/'dataset_card.json',dict(rows=len(rows),samples_sha256=sha(DATA/'samples.json'),base_graphs_sha256=sha(DATA/'base_graphs.json'),
        derivation_code_sha256=sha(Path(__file__)),roles={role:dict(identities=len(ids[role]),images=sum(r['role']==role for r in rows)) for role in ids},
        changed_train_slots=len(changes),train_id_slot_order_matches_V3=True,
        test_previous_role_overlap=0,test_previous_raster_overlap=0,complete_answer_fingerprint_overlap=0,
        test_source_counts=dict(collections.Counter(r['source'] for r in new_bases)),
        photo_device_counts=dict(collections.Counter(r['device'] for r in new_bases if r['source']=='midv2020')),
        font_hashes=sorted({r['font_sha256'] for r in new_bases if r['source']=='authored'}),
        pair_fallbacks=len(fallbacks),human_legibility_labels=False,independent_camera_collection=False))
    print('HP_DATA_READY',len(rows),'changed_train_slots',len(changes),'fallbacks',len(fallbacks),flush=True)


if __name__=='__main__':build()
