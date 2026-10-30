"""Reproducible authored specimens and attributed MIDV partial-capture views."""
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image,ImageDraw,ImageFont

from research.benchmark import save,digest
from research.e2e_eval import target_fields
from research.support_regions import area,intersection,frame_polygon

ROOT=Path('research/data/recovery_v4')
FONTS=Path('research/cache/upstream/fonts')
CAPTURES=('full','corner_clip','field_clip','blur_glare')
LABELS_EN={'full_name':'Full name','id_number':'ID number','dob':'Date of birth','gender':'Sex','address':'Address',
           'student_id':'Student ID','school':'School name','course':'Course','license_class':'License class','expiry_date':'Expiry date'}
LABELS_VI={'full_name':'Họ và tên','id_number':'Số giấy tờ','dob':'Ngày sinh','gender':'Giới tính','address':'Địa chỉ',
           'student_id':'Mã sinh viên','school':'Tên trường','course':'Khóa học','license_class':'Hạng giấy phép','expiry_date':'Ngày hết hạn'}


def seed(value):return int.from_bytes(hashlib.sha256(value.encode()).digest()[:8],'big')


def mapped(quad,matrix):return cv2.perspectiveTransform(np.float32(quad)[None],matrix)[0].tolist()


def geometry_visibility(quad,width,height):
    return min(1.,area(intersection(quad,frame_polygon(width,height)))/max(area(quad),1e-8))


def mark_visibility(sample):
    for field in sample['fields']:
        field['geometric_visibility']=geometry_visibility(field['quad'],sample['width'],sample['height'])
        if 'characters' in field:
            for char in field['characters']:
                char['geometric_visibility']=geometry_visibility(char['quad'],sample['width'],sample['height'])
            field['visible_reference']=''.join(c['text'] for c in field['characters'] if c['geometric_visibility']>=.995)
    return sample


def render_card(layout,index):
    rng=np.random.default_rng(seed(f'card/{layout}/{index}'))
    vi=layout in (1,3,5);family=('citizen','student','licence')[index%3]
    values={'full_name':('LÊ','TRẦN','PHẠM','ĐỖ')[index%4]+' '+('MINH AN','THU HÀ','BẢO NAM','THẢO VY')[int(rng.integers(4))],
            'id_number':f'000{layout:01d}{index:08d}','dob':f'{int(rng.integers(1,28)):02d}/{int(rng.integers(1,13)):02d}/{int(rng.integers(1970,2008))}',
            'gender':('NỮ' if index%2 else 'NAM') if vi else ('FEMALE' if index%2 else 'MALE'),
            'address':f'{int(rng.integers(1,999))} '+('ĐƯỜNG MẪU, THÀNH PHỐ THỬ' if vi else 'SAMPLE ROAD, TEST CITY'),
            'student_id':f'SV{layout}{index:07d}','school':('TRƯỜNG THỰC NGHIỆM' if vi else 'SPECIMEN COLLEGE'),
            'course':f'{2020+index%6}-{2024+index%6}','license_class':('A1','B2','C')[index%3],
            'expiry_date':f'15/06/{2030+index%9}'}
    if not vi:
        import unicodedata
        values['full_name']=''.join(c for c in unicodedata.normalize('NFD',values['full_name']) if not unicodedata.combining(c)).replace('Đ','D')
    keys=(['full_name','id_number','dob','gender','address'] if family=='citizen' else
          ['full_name','student_id','school','course','dob'] if family=='student' else
          ['full_name','id_number','dob','license_class','expiry_date'])
    if layout>=4:keys=keys[2:]+keys[:2]
    image=Image.new('RGB',(1000,640),(242,247,246));draw=ImageDraw.Draw(image)
    color=[(13,103,116),(53,75,137),(122,70,92)][index%3]
    draw.rectangle((0,0,1000,94),fill=color)
    fontfile=FONTS/('NotoSerif-Regular.ttf' if layout>=4 else 'NotoSans-Regular.ttf')
    def font(size):return ImageFont.truetype(str(fontfile),size)
    titles={'citizen':'MOCK ID CARD','student':'STUDENT SPECIMEN','licence':'MOCK DRIVING LICENCE'}
    draw.text((32,20),titles[family],font=font(32),fill='white')
    draw.text((32,65),'SPECIMEN - NOT A VALID DOCUMENT',font=font(16),fill='white')
    draw.rounded_rectangle((28,142,205,370),radius=15,fill=(210,225,225),outline=color,width=3)
    draw.ellipse((77,175,157,260),fill=(166,183,188));draw.ellipse((47,267,187,397),fill=(166,183,188))
    draw.rectangle((28,340,205,375),fill=(210,225,225))
    draw.text((30,396),'SYNTHETIC',font=font(19),fill=color)
    fields=[];labels=LABELS_VI if vi else LABELS_EN
    for j,key in enumerate(keys):
        x=240+(20 if layout%2 else 0);y=143+j*86
        draw.text((x,y),labels[key]+':',font=font(19),fill=(57,77,87),anchor='ls')
        value=values[key];size=28
        while font(size).getlength(value)>720 and size>17:size-=1
        f=font(size);baseline=y+37;draw.text((x,baseline),value,font=f,fill=(15,27,38),anchor='ls')
        left,top,right,bottom=draw.textbbox((x,baseline),value,font=f,anchor='ls')
        chars=[]
        for k,char in enumerate(value):
            cx=x+f.getlength(value[:k]);l,t,r,b=f.getbbox(char,anchor='ls')
            # Advance rectangles are geometric support proxies, not pixel masks
            # or human judgements of character legibility.
            cw=max(1,r-l);ch=max(1,b-t)
            chars.append(dict(text=char,quad=[[cx+l,baseline+t],[cx+l+cw,baseline+t],
                         [cx+l+cw,baseline+t+ch],[cx+l,baseline+t+ch]]))
        fields.append(dict(key=key,text=value,quad=[[left,top],[right,top],[right,bottom],[left,bottom]],characters=chars))
    draw.text((28,602),'DỮ LIỆU TỔNG HỢP / SYNTHETIC RESEARCH DATA',font=font(16),fill=color)
    return cv2.cvtColor(np.asarray(image),cv2.COLOR_RGB2BGR),fields,family,vi


def capture(image,fields,gt,uid,kind):
    rng=np.random.default_rng(seed('capture/'+uid+'/'+kind));h,w=image.shape[:2]
    x1=y1=0
    if kind=='corner_clip':
        points=np.asarray(gt);xs=np.sort(points[:,0]);ys=np.sort(points[:,1])
        # Crop near the extreme corner rather than assuming the model will see
        # exactly three corners. The resulting true count is published.
        x1=int(np.clip(xs[0]+max(12,.45*(xs[1]-xs[0])),0,w-32))
    elif kind=='field_clip':
        first=next((f for f in fields if f['key']=='full_name'),fields[0]);q=np.asarray(first['quad'])
        x1=int(np.clip(q[:,0].min()+.35*(q[:,0].max()-q[:,0].min()),0,w-32))
    output=image[y1:,x1:].copy();shift=np.array([[1.,0.,-x1],[0.,1.,-y1],[0.,0.,1.]])
    if kind=='blur_glare':
        output=cv2.GaussianBlur(output,(5,5),1.1)
        yy,xx=np.indices(output.shape[:2]);cx=.70*output.shape[1];cy=.40*output.shape[0]
        glow=np.exp(-((xx-cx)**2+(yy-cy)**2)/(2*(.16*output.shape[1])**2))*.55
        output=np.uint8(np.clip(output*(1-glow[...,None])+255*glow[...,None],0,255))
    mapped_fields=[]
    for f in fields:
        row=dict(f,quad=mapped(f['quad'],shift))
        if 'characters' in f:row['characters']=[dict(c,quad=mapped(c['quad'],shift)) for c in f['characters']]
        mapped_fields.append(row)
    return output,mapped_fields,mapped(gt,shift),dict(crop_origin=[x1,y1],blur_glare=kind=='blur_glare')


def build_synthetic():
    output=[];dest=ROOT/'synthetic';dest.mkdir(parents=True,exist_ok=True)
    for layout in range(6):
        for index in range(15):
            role=('development' if index<5 else 'calibration' if index<10 else 'test') if layout<4 else 'test'
            identity=f'specimen/L{layout}/{index:02d}';card,fields,family,vi=render_card(layout,index)
            rng=np.random.default_rng(seed(identity));scene=np.full((760,1160,3),(82,98,110),np.uint8)
            noise=rng.normal(0,4,scene.shape[:2]);scene=np.uint8(np.clip(scene+noise[...,None],0,255))
            quad=np.float32([[80+rng.uniform(-18,35),70+rng.uniform(-20,35)],
                             [1080+rng.uniform(-35,18),80+rng.uniform(-25,25)],
                             [1060+rng.uniform(-25,25),700+rng.uniform(-20,20)],
                             [90+rng.uniform(-25,25),690+rng.uniform(-20,25)]])
            H=cv2.getPerspectiveTransform(np.float32([[0,0],[999,0],[999,639],[0,639]]),quad)
            warped=cv2.warpPerspective(card,H,(1160,760));mask=cv2.warpPerspective(np.full((640,1000),255,np.uint8),H,(1160,760))
            scene[mask>0]=warped[mask>0]
            projected=[dict(f,quad=mapped(f['quad'],H),characters=[dict(c,quad=mapped(c['quad'],H)) for c in f['characters']]) for f in fields]
            for kind in CAPTURES:
                image,ff,gg,transform=capture(scene,projected,quad,identity,kind)
                uid=identity+'/'+kind;path=dest/(uid.replace('/','_')+'.png');cv2.imwrite(str(path),image)
                output.append(mark_visibility(dict(uid=uid,physical_id=identity,source='authored_specimen',role=role,
                    layout=layout,unseen_layout=layout>=4,language='vi' if vi else 'en',family=family,capture=kind,
                    width=image.shape[1],height=image.shape[0],gt=gg,fields=ff,path=str(path),
                    input_sha256=digest(path),capture_transform=transform,quality_label=kind)))
    save(ROOT/'synthetic_samples.json',output);return output


def build_midv():
    records=json.loads((ROOT/'midv/selection.json').read_text(encoding='utf-8'));samples=[]
    dest=ROOT/'midv_views';dest.mkdir(parents=True,exist_ok=True)
    for r in records:
        image=cv2.imdecode(np.fromfile(str(ROOT/'midv'/r['code']/r['filename']),np.uint8),cv2.IMREAD_COLOR)
        if image is None or image.shape[:2]!=(r['height'],r['width']):raise ValueError('MIDV EXIF geometry mismatch')
        for kind in CAPTURES[:3]:
            result,fields,gt,transform=capture(image,r['fields'],r['gt'],r['physical_id'],kind)
            uid=r['physical_id']+'/'+kind;path=dest/(uid.replace('/','_')+'.png');cv2.imwrite(str(path),result)
            samples.append(mark_visibility(dict(uid=uid,physical_id=r['physical_id'],source='midv2020_derived',role=r['role'],
                layout=r['code'],unseen_layout=False,language='mixed',capture=kind,width=result.shape[1],height=result.shape[0],
                gt=gt,fields=fields,path=str(path),input_sha256=digest(path),capture_transform=transform,quality_label=kind,
                original_sha256=r['image_sha256'])))
    save(ROOT/'midv_samples.json',samples);return samples


def load_samples():
    result=json.loads((ROOT/'samples.json').read_text(encoding='utf-8'))
    if len(result)!=540:raise ValueError('Expected complete540-case sample')
    return result


def main():
    ROOT.mkdir(parents=True,exist_ok=True)
    synthetic=build_synthetic();midv=build_midv();samples=sorted(synthetic+midv,key=lambda s:s['uid'])
    assert len(synthetic)==360 and len(midv)==180
    roles={role:{s['physical_id'] for s in samples if s['role']==role} for role in ('development','calibration','test')}
    assert not (roles['development']&roles['calibration'] or roles['test']&(roles['development']|roles['calibration']))
    save(ROOT/'samples.json',samples)
    public=[]
    for s in samples:
        targets,excluded=target_fields(s)
        public.append({**{k:s[k] for k in ('uid','physical_id','source','role','layout','unseen_layout','language','capture','input_sha256','width','height')},
            'eligible_fields':len(targets),'excluded_fields':excluded,
            'true_visible_corners':sum(0<=x<s['width'] and 0<=y<s['height'] for x,y in s['gt']),
            'partial_fields':sum(f['geometric_visibility']<.995 for f in s['fields'])})
    out=Path('research/results/recovery_v4');save(out/'dataset_manifest.json',public)
    save(out/'dataset_card.json',dict(images=540,identities=150,authored_specimens=360,derived_midv=180,
        physical_ids_by_role={k:len(v) for k,v in roles.items()},generator_sha256=digest(__file__),
        font_sha256={p.name:digest(p) for p in FONTS.glob('*.ttf')},
        geometric_visibility_is_human_legibility=False,midv_pretraining_unseen=False,
        new_real_world_camera_collection=False,authored_text_is_synthetic=True,
        license='Authored code MIT under repository licence; authored specimen images CC BY4.0; MIDV derivatives CC BY-SA2.5; fonts OFL1.1, not redistributed'))
    print('DATASET_BUILT',len(samples),'images',len(set(s['physical_id'] for s in samples)),'identities',flush=True)


if __name__=='__main__':main()
