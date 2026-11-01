"""Paired complete/partial training and sealed identity/layout-disjoint evaluation."""
import collections
import hashlib
import random
from pathlib import Path
import cv2
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageOps
from research.v2_common import *
from research.vlm_data import LABELS

def mapped_fields(source):
    result=[]
    for f in source['fields']:
        if f['author_key'] in FIELD_MAP:
            result.append(dict(key=FIELD_MAP[f['author_key']],value=f['value'],quad=f['quad']))
    if len({f['key'] for f in result})!=len(result): raise ValueError('Ambiguous author field mapping')
    return result

def mock(identity,index,role):
    rng=random.Random(seed(identity));style=index%6 if role=='train' else index%6 if role=='development' else 6+index%2
    fontfile=(ROOT/'research/cache/upstream/fonts'/('NotoSans-Regular.ttf' if index%2==0 else 'NotoSerif-Regular.ttf'))
    if role=='test': fontfile=Path('C:/Windows/Fonts/arial.ttf')
    def font(n): return ImageFont.truetype(str(fontfile),n)
    names=['HÀ','PHÚC','DŨNG','LINH','HẢI','SƠN','HIẾU','CHÂU','THẢO','BÌNH','ĐỨC','TÚ']
    full_name=' '.join([rng.choice(['TRẦN','NGÔ','LÊ','ĐẶNG','PHAN','NGUYỄN','DƯƠNG','VÕ']),rng.choice(['THỊ','MINH','QUANG','VĂN','NGỌC']),rng.choice(names)])
    values=dict(full_name=full_name,id_number=''.join(str(rng.randrange(10)) for _ in range(12)),
        dob=f'{rng.randrange(1,28):02}/{rng.randrange(1,13):02}/{rng.randrange(1968,2008)}',
        gender=rng.choice(['NAM','NỮ']),address=f'{rng.randrange(1,999)} '+rng.choice(['ĐƯỜNG HOA LAN','PHỐ SÔNG XANH','ĐƯỜNG BÌNH MINH','PHƯỜNG CẨM TÚ']),
        student_id='SV'+str(rng.randrange(10**7,10**8)),school=rng.choice(['TRƯỜNG HÒA BÌNH','TRƯỜNG ÁNH DƯƠNG','TRƯỜNG SAO MAI']),
        course=f'{rng.randrange(2018,2025)}-{rng.randrange(2026,2032)}',license_class=rng.choice(['A1','A2','B1','B2','C']),
        expiry_date=f'{rng.randrange(1,28):02}/{rng.randrange(1,13):02}/{rng.randrange(2030,2041)}')
    keys=[['full_name','id_number','dob','gender','address'],['full_name','student_id','school','course','dob'],
          ['full_name','id_number','dob','license_class','expiry_date']][index%3][:]
    rng.shuffle(keys)
    im=Image.new('RGB',(1200,800),rng.choice([(241,245,233),(232,243,247),(248,239,229)]));d=ImageDraw.Draw(im)
    color=rng.choice([(18,84,99),(72,57,115),(128,62,76),(35,91,61)])
    d.rectangle((0,0,1200,108),fill=color)
    d.text((28,18),'SPECIMEN / GIẤY TỜ MẪU',font=font(30),fill='white')
    d.text((28,64),'SYNTHETIC DATA - NOT VALID FOR IDENTIFICATION',font=font(20),fill='white')
    photo_x=25 if style in (0,1,4) else 965
    d.rounded_rectangle((photo_x,140,photo_x+200,405),radius=12,fill=(199,213,216),outline=color,width=3)
    d.ellipse((photo_x+62,164,photo_x+140,260),fill=(143,166,172));d.ellipse((photo_x+30,270,photo_x+175,380),fill=(143,166,172))
    fields=[]
    for j,key in enumerate(keys):
        if style==0: x,y,width=265,143+j*112,895
        elif style==1: x,y,width=265+(j%2)*460,148+(j//2)*195,430
        elif style==2: x,y,width=35,145+j*112,875
        elif style==3: x,y,width=30+(j%2)*465,145+(j//2)*195,435
        elif style==4: x,y,width=(265,143,880) if j==0 else (30+((j-1)%2)*590,440+((j-1)//2)*132,550)
        elif style==5: x,y,width=30,140+j*116,875
        elif style==6: x,y,width=30+(j%3)*395,450+(j//3)*140,365
        else: x,y,width=(30+(j%2)*580,450+(j//2)*98,550) if j<4 else (30,130,880)
        vi=index%4!=3;label=LABELS[key][0 if vi else 1]+':'
        d.text((x,y),label,font=font(23),fill=(55,65,70),anchor='lt');labelbox=list(d.textbbox((x,y),label,font=font(23),anchor='lt'))
        size=34
        while font(size).getlength(values[key])>width and size>14: size-=1
        d.text((x,y+35),values[key],font=font(size),fill=(12,20,26),anchor='lt')
        a,b,c,e=d.textbbox((x,y+35),values[key],font=font(size),anchor='lt')
        fields.append(dict(key=key,value=values[key],quad=[[a,b],[c,b],[c,e],[a,e]],label_box=labelbox))
    d.text((28,764),'RESEARCH ONLY / DỮ LIỆU GIẢ LẬP',font=font(18),fill=color)
    return np.asarray(im),fields,style,sha(fontfile)

def shifted(fields,dx,dy):
    result=[]
    for f in fields:
        row=dict(f,quad=(np.asarray(f['quad'])+[dx,dy]).tolist())
        if 'label_box' in f:
            a,b,c,d=f['label_box'];row['label_box']=[a+dx,b+dy,c+dx,d+dy]
        result.append(row)
    return result

def target(fields,w,h):
    out={}
    for f in fields:
        q=np.asarray(f['quad']);whole=(q[:,0]>=0).all() and (q[:,1]>=0).all() and (q[:,0]<=w).all() and (q[:,1]<=h).all()
        if 'label_box' in f:
            a,b,c,d=f['label_box'];whole=whole and a>=0 and b>=0 and c<=w and d<=h
        if whole and not f.get('occluded',False):out[f['key']]=f['value']
    return out

def augment(image,fields,pid,kind):
    rng=random.Random(seed(pid+'/'+kind));image=image.copy();ff=[dict(f) for f in fields]
    h,w=image.shape[:2]
    if kind=='field_clip':
        # Cut through one value, not merely a card border. Retained values use full-region visibility.
        centers=sorted(float(np.asarray(f['quad'])[:,1].mean()) for f in fields)
        y=max(1,min(h-1,round(centers[len(centers)//2])))
        if rng.random()<.5:image=image[:y]
        else:image=image[y:];ff=shifted(ff,0,-y)
    elif kind=='value_mask':
        chosen=rng.sample(range(len(fields)),rng.randrange(1,len(fields)+1))
        masks=[]
        for i in chosen:
            q=np.asarray(fields[i]['quad'],np.float32);center=q.mean(axis=0);q=(q-center)*1.04+center
            masks.append(q);cv2.fillConvexPoly(image,np.rint(q).astype(np.int32),(35,38,42))
        for f in ff:
            q=np.asarray(f['quad'],np.float32)
            f['occluded']=any(cv2.intersectConvexConvex(q,m)[0]>.05 for m in masks)
    elif kind=='perspective':
        # Affine/projective resampling within a larger canvas; no text intentionally clipped.
        dst=np.float32([[.08*w,.10*h],[.94*w,.04*h],[.98*w,.94*h],[.04*w,.98*h]])
        H=cv2.getPerspectiveTransform(np.float32([[0,0],[w-1,0],[w-1,h-1],[0,h-1]]),dst)
        image=cv2.warpPerspective(image,H,(w,h),borderValue=(104,110,116))
        for f in ff:
            f['quad']=cv2.perspectiveTransform(np.float32([f['quad']]),H)[0].tolist()
            # Label region travels through the same transform, represented by enclosing bounds.
            if 'label_box' in f:
                a,b,c,d=f['label_box'];q=cv2.perspectiveTransform(np.float32([[[a,b],[c,b],[c,d],[a,d]]]),H)[0]
                f['label_box']=np.concatenate([q.min(axis=0),q.max(axis=0)]).astype(float).tolist()
    elif kind=='mild':image=np.uint8(np.clip(cv2.GaussianBlur(image,(3,3),.55)*.87+15,0,255))
    elif kind=='bright':image=np.uint8(np.clip(image*.90+24,0,255))
    elif kind=='contrast':image=np.uint8(np.clip((image.astype(float)-128)*.88+128,0,255))
    elif kind!='full': raise ValueError(kind)
    return image,ff

def canonicalize_shared(rows):
    shared={(r['physical_id'],r['slot']):r for r in rows if r['role']=='train' and r['variant']=='control' and r['slot']<3}
    corrected=0
    for r in rows:
        if r['role']!='train' or r['variant']!='partial' or r['slot']>=3:continue
        other=shared[r['physical_id'],r['slot']]
        if r['target']!=other['target']:raise ValueError('Common slot target differs')
        if r['input_sha256']!=other['input_sha256']:
            with Image.open(ROOT/r['path']) as a,Image.open(ROOT/other['path']) as b:
                if not np.array_equal(np.asarray(a),np.asarray(b)):raise ValueError('Common slot pixels differ')
            corrected+=1
        r['path']=other['path'];r['input_sha256']=other['input_sha256']
    return corrected

def build():
    preserve_v1();sources=read(DATA/'sources.json');rows=[];coverage=collections.Counter()
    bases=[]
    for role in ('train','development','test'):
        for i in range(CONFIG[role+'_mock_ids']):
            pid=f'vlm_v2/{role}/{i:03}'
            im,ff,style,font=mock(pid,i,role)
            bases.append((dict(physical_id=pid,role=role,source='authored',device='renderer',layout=str(style),font_sha256=font),im,ff))
        for r in [r for r in sources if r['role']==role]:
            with Image.open(ROOT/r['path']) as image: im=np.asarray(ImageOps.exif_transpose(image).convert('RGB'))
            coverage.update({k:sum(f['author_key']==k for f in r['fields']) for k in {f['author_key'] for f in r['fields']}})
            bases.append((dict(physical_id=r['physical_id'],role=role,source='midv2020',device=r['device'],layout=r['code'],
                              source_sha256=r['source_sha256'],held_layout=r['code'] in HELD_LAYOUTS),im,mapped_fields(r)))
    for info,im,ff in bases:
        variants=('control','partial') if info['role']=='train' else ('evaluation',)
        for variant in variants:
            kinds=('full','perspective','mild','bright','contrast') if variant=='control' else ('full','perspective','mild','field_clip','value_mask') if variant=='partial' else ('full','field_clip','value_mask')
            for slot,kind in enumerate(kinds):
                result,fields=augment(im,ff,info['physical_id'],kind)
                uid=info['physical_id']+'/'+variant+'/'+str(slot)
                path=DATA/'images'/(hashlib.sha256(uid.encode()).hexdigest()+'.png');path.parent.mkdir(parents=True,exist_ok=True)
                reusable=False
                if path.exists():
                    try:
                        with Image.open(path) as prior: reusable=np.array_equal(np.asarray(prior.convert('RGB')),result)
                        if not reusable:raise ValueError('Existing V2 raster has different pixels')
                    except OSError as exc:
                        save(DATA/'build_repair.json',dict(path=path.relative_to(ROOT).as_posix(),reason=str(exc),
                             context='Interrupted pre-training PNG encoding; source pixels regenerated deterministically'))
                if not reusable:Image.fromarray(result).save(path,compress_level=1)
                rows.append(dict(info,variant=variant,slot=slot,capture=kind,uid=uid,path=path.relative_to(ROOT).as_posix(),
                    input_sha256=sha(path),width=result.shape[1],height=result.shape[0],fields=fields,
                    target=target(fields,result.shape[1],result.shape[0])))
    canonicalize_shared(rows)
    save(DATA/'samples.json',rows)
    ids={role:{r['physical_id'] for r in rows if r['role']==role} for role in ('train','development','test')}
    if any(ids[a]&ids[b] for a in ids for b in ids if a!=b): raise ValueError('Identity leakage')
    old_ids={r['physical_id'] for r in read(ROOT/'research/data/recovery_v4/midv/selection.json')}
    old_ids|={'midv2020/'+r['code']+'/'+Path(r['filename']).stem for r in read(ROOT/'research/data/midv2020/selection.json')}
    if (ids['development']|ids['test'])&old_ids: raise ValueError('Earlier-study evaluation identity reused')
    hashes={role:{r['input_sha256'] for r in rows if r['role']==role} for role in ids}
    if any(hashes[a]&hashes[b] for a in hashes for b in hashes if a!=b):raise ValueError('Raster leakage')
    # Names can collide in synthetic generators; full identity values must not.
    fingerprints={role:set() for role in ids}
    for info,_,fields in bases:
        values={f['key']:f['value'] for f in fields}; fp=stable_hash(values)
        fingerprints[info['role']].add(fp)
    if any(fingerprints[a]&fingerprints[b] for a in ids for b in ids if a!=b):raise ValueError('Field identity collision')
    inventory=[]
    for source in ('midv500','midv2019'):
        files=sorted((ROOT/'research/data').glob(source+'_*.json'));count=0
        for file in files:
            for entry in read(file).values():count+=sum(isinstance(v,dict) and isinstance(v.get('value'),str) for v in entry.values())
        inventory.append(dict(source=source,annotation_files=len(files),author_text_fields=count,
                              semantic_key_names_available=False,used_as_semantic_kie_labels=False))
    manifest=[{k:v for k,v in r.items() if k not in ('fields','target','path')} for r in rows]
    save(OUT/'dataset_manifest.json',manifest)
    save(OUT/'dataset_card.json',dict(config=CONFIG,samples_sha256=sha(DATA/'samples.json'),images=len(rows),
        roles={r:dict(identities=len(ids[r]),images=sum(x['role']==r for x in rows)) for r in ids},
        train_images_per_arm=640,train_presentations_per_arm=1280,exposure_epochs=2,
        train_photos_previously_evaluated=True,development_test_prior_id_overlap=0,role_raster_overlap=0,
        held_layouts=list(HELD_LAYOUTS),held_mock_layouts=[6,7],mock_test_font_heldout=True,
        original_annotation_inventory=inventory,author_field_counts=dict(coverage),field_mapping=FIELD_MAP,
        visibility='Whole value polygon inside frame, no mask intersection; mock labels also whole',
        human_legibility_annotation=False,independent_camera_collection=False,
        source_counts=dict(collections.Counter((r['role']+'/'+r['source']) for r in manifest)),
        license='MIDV derivatives retain CC BY-SA 2.5; authored specimens CC BY 4.0; no font files redistributed'))
    print('V2_DATA_READY',len(rows),flush=True)

if __name__=='__main__': build()
