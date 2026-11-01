"""New, identity-disjoint SPECIMEN data for the local VLM LoRA experiment."""
import hashlib
import json
from pathlib import Path
import random

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from research.vlm_setup import ROOT, OUT, sha, save

DATA = ROOT / 'research/data/vlm_lora_v1'
COUNTS = dict(train=96, development=16, calibration=8, test=24)
LABELS = {
    'full_name': ('Họ và tên', 'Full name'), 'id_number': ('Số giấy tờ', 'ID number'),
    'dob': ('Ngày sinh', 'Date of birth'), 'gender': ('Giới tính', 'Sex'),
    'address': ('Địa chỉ', 'Address'), 'student_id': ('Mã sinh viên', 'Student ID'),
    'school': ('Tên trường', 'School name'), 'course': ('Khóa học', 'Course'),
    'license_class': ('Hạng giấy phép', 'License class'), 'expiry_date': ('Ngày hết hạn', 'Expiry date')}
PROMPT = ('Đọc thông tin thực sự nhìn thấy trên giấy tờ. Chỉ trả về một JSON object, không giải thích. '
          'Dùng khóa full_name, id_number, dob, gender, address, student_id, school, course, '
          'license_class, expiry_date tương ứng với nhãn được in; chỉ xuất các trường có trên ảnh. '
          'Giữ nguyên chữ, số và ngày tháng. Bỏ qua trường bị cắt mất nhãn hoặc một phần giá trị; '
          'không đoán phần thiếu. Nếu không đọc được trường nào, trả về {}.')


def number_seed(s): return int.from_bytes(hashlib.sha256(s.encode()).digest()[:8], 'big')


def field_target(fields, width, height):
    result = {}
    for f in fields:
        boxes = [f['label_box'], f['value_box']]
        if not f.get('occluded',False) and all(x1 >= 0 and y1 >= 0 and x2 <= width and y2 <= height for x1,y1,x2,y2 in boxes):
            result[f['key']] = f['value']
    return result


def card(identity, style, family, vi):
    rng = random.Random(number_seed(identity))
    surnames = ['NGUYỄN','TRẦN','LÊ','PHẠM','HOÀNG','HUỲNH','PHAN','VŨ','VÕ','ĐẶNG','BÙI','ĐỖ','HỒ','NGÔ','DƯƠNG','LÝ']
    middle = ['VĂN','THỊ','MINH','QUANG','THANH','NGỌC','BẢO','TUẤN','THU','HỮU','ĐỨC','KHÁNH']
    given = ['AN','BÌNH','CHÂU','DŨNG','GIANG','HÀ','HẢI','HÂN','HIẾU','HOA','HÙNG','HUY','KHANG','LAN','LINH','LONG','MAI','NAM','NHI','PHÚC','QUÂN','SƠN','TÂM','THẢO','TRANG','TRUNG','TÚ','VY']
    values = dict(full_name=' '.join([rng.choice(surnames),rng.choice(middle),rng.choice(given)]),
                  id_number=''.join(str(rng.randrange(10)) for _ in range(12)),
                  dob=f'{rng.randrange(1,28):02}/{rng.randrange(1,13):02}/{rng.randrange(1970,2008)}',
                  gender=rng.choice(['NAM','NỮ'] if vi else ['MALE','FEMALE']),
                  address=f'{rng.randrange(1,999)} ' + rng.choice(['ĐƯỜNG SEN','ĐƯỜNG TRE','ĐƯỜNG TRÚC','ĐƯỜNG MAI'] if vi else ['PINE STREET','CEDAR ROAD','MAPLE STREET','OAK ROAD']),
                  student_id='SV' + ''.join(str(rng.randrange(10)) for _ in range(8)),
                  school=rng.choice(['TRƯỜNG SEN','TRƯỜNG TRE','TRƯỜNG MAI'] if vi else ['PINE COLLEGE','CEDAR COLLEGE','MAPLE SCHOOL']),
                  course=f'{rng.randrange(2020,2025)}-{rng.randrange(2025,2030)}',
                  license_class=rng.choice(['A1','A2','B1','B2','C']),
                  expiry_date=f'{rng.randrange(1,28):02}/{rng.randrange(1,13):02}/{rng.randrange(2030,2041)}')
    if not vi:
        import unicodedata
        values['full_name']=''.join(c for c in unicodedata.normalize('NFD',values['full_name']) if not unicodedata.combining(c)).replace('Đ','D')
    keys = {'citizen':['full_name','id_number','dob','gender','address'],
            'student':['full_name','student_id','school','course','dob'],
            'licence':['full_name','id_number','dob','license_class','expiry_date']}[family][:]
    rng.shuffle(keys)
    image=Image.new('RGB',(1000,680),(246,248,240)); draw=ImageDraw.Draw(image)
    color=rng.choice([(12,92,109),(52,64,124),(115,61,91),(41,100,66)])
    draw.rectangle((0,0,1000,94),fill=color)
    fontfile=ROOT/'research/cache/upstream/fonts'/('NotoSans-Regular.ttf' if style<2 else 'NotoSerif-Regular.ttf')
    def font(n): return ImageFont.truetype(str(fontfile),n)
    draw.text((25,14),'SPECIMEN / '+family.upper(),font=font(30),fill='white')
    draw.text((25,56),'SYNTHETIC - NOT A VALID DOCUMENT',font=font(18),fill='white')
    draw.rounded_rectangle((24,135,190,351),radius=12,fill=(208,220,222),outline=color,width=3)
    draw.ellipse((74,160,144,245),fill=(153,173,177));draw.ellipse((46,250,171,340),fill=(153,173,177))
    draw.text((25,371),'MOCK FACE',font=font(18),fill=color)
    fields=[]
    for j,key in enumerate(keys):
        x,y=(230,137+j*100) if style%2==0 else (225+(j%2)*390,137+(j//2)*166)
        max_width=740 if style%2==0 else 365
        label=LABELS[key][0 if vi else 1]+':'
        draw.text((x,y),label,font=font(21),fill=(58,70,72),anchor='lt')
        label_box=list(draw.textbbox((x,y),label,font=font(21),anchor='lt'))
        size=31
        while font(size).getlength(values[key])>max_width: size-=1
        draw.text((x,y+36),values[key],font=font(size),fill=(14,24,30),anchor='lt')
        value_box=list(draw.textbbox((x,y+36),values[key],font=font(size),anchor='lt'))
        fields.append(dict(key=key,value=values[key],label_box=label_box,value_box=value_box))
    draw.text((25,642),'RESEARCH DATA / DỮ LIỆU GIẢ LẬP',font=font(17),fill=color)
    return np.asarray(image),fields


def capture(image, fields, identity, kind):
    rng=random.Random(number_seed(identity+'/'+kind)); image=image.copy()
    x1=y1=0; x2=image.shape[1]; y2=image.shape[0]
    if kind=='corner_clip':
        x1=rng.randrange(30,100)  # Does not deliberately remove text.
    elif kind=='field_clip':
        # Top/bottom crops retain a variable subset of whole fields; labels and
        # values are tracked separately. No hidden whole-card target is used.
        if rng.random()<.5: y1=rng.randrange(170,360)
        else: y2=rng.randrange(310,540)
    elif kind=='blur_glare':
        image=cv2.GaussianBlur(image,(3,3),.65)
        yy,xx=np.indices(image.shape[:2]); glow=np.exp(-((xx-750)**2+(yy-230)**2)/(2*115**2))*.22
        image=np.uint8(np.clip(image*(1-glow[...,None])+255*glow[...,None],0,255))
    masked=set()
    if kind=='value_mask':
        masked=set(rng.sample(range(len(fields)),rng.randrange(1,len(fields)+1)))
        for i in masked:
            a,b,c,d=fields[i]['value_box'];image[max(0,b-2):d+2,max(0,a-2):c+2]=(35,38,42)
    result=image[y1:y2,x1:x2]
    shifted=[]
    for i,f in enumerate(fields):
        row=dict(f,occluded=i in masked)
        for key in ('label_box','value_box'):
            a,b,c,d=f[key]; row[key]=[a-x1,b-y1,c-x1,d-y1]
        shifted.append(row)
    return result,shifted


def build():
    rows=[]; images=DATA/'images'; images.mkdir(parents=True,exist_ok=True)
    for role,count in COUNTS.items():
        for i in range(count):
            identity=f'vlm_lora_v1/{role}/{i:03}'
            style=i%4; vi=(i//4)%2==0; family=('citizen','student','licence')[i%3]
            image,fields=card(identity,style,family,vi)
            for kind in ('full','corner_clip','field_clip','blur_glare','value_mask'):
                result,ff=capture(image,fields,identity,kind)
                uid=identity+'/'+kind; path=images/(uid.replace('/','_')+'.png')
                Image.fromarray(result).save(path)
                rows.append(dict(uid=uid,physical_id=identity,role=role,capture=kind,language='vi' if vi else 'en',
                    family=family,style=style,path=path.relative_to(ROOT).as_posix(),input_sha256=sha(path),
                    width=result.shape[1],height=result.shape[0],fields=ff,
                    target=field_target(ff,result.shape[1],result.shape[0])))
    save(DATA/'samples.json',rows)
    ids={role:{x['physical_id'] for x in rows if x['role']==role} for role in COUNTS}
    if any(ids[a]&ids[b] for a in ids for b in ids if a!=b): raise ValueError('Identity overlap')
    all_hashes=[x['input_sha256'] for x in rows]
    if len(all_hashes)!=len(set(all_hashes)): raise ValueError('Duplicate raster')
    previous=set()
    for path in (ROOT/'research/data/recovery_v4/samples.json',ROOT/'research/data/layout_stress/samples.json'):
        if path.exists(): previous|={r['input_sha256'] for r in json.loads(path.read_text(encoding='utf-8'))}
    if set(all_hashes)&previous: raise ValueError('Prior study image reused')
    save(OUT/'dataset_manifest.json',[{k:v for k,v in r.items() if k not in ('fields','target','path')} for r in rows])
    save(OUT/'dataset_card.json',dict(images=len(rows),identities=sum(COUNTS.values()),roles=COUNTS,
        data_sha256=sha(DATA/'samples.json'),generator_sha256=sha(__file__),prior_image_hash_overlap=0,
        independent_camera_collection=False,human_legibility_labels=False,synthetic_only=True,
        layout_roles_disjoint=False,role_split='mock identity disjoint; same generator/styles',
        license='Authored specimen rasters CC BY 4.0; code MIT; Noto fonts OFL'))
    print('DATASET',len(rows),COUNTS,flush=True)
    return rows


def load(role=None):
    rows=json.loads((DATA/'samples.json').read_text(encoding='utf-8'))
    return [r for r in rows if role is None or r['role']==role]


if __name__=='__main__': build()
