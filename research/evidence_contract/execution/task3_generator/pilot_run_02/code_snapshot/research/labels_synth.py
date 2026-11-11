"""A paired layout/value-font panel with exact rendered glyph support."""
import math
import random
import unicodedata
from functools import lru_cache
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from fontTools.ttLib import TTFont
from research.labels_common import *
from research.labels_schema import field

FONT_PAIRS=((ROOT/'research/cache/upstream/fonts/NotoSans-Regular.ttf',Path('C:/Windows/Fonts/tahoma.ttf')),
            (ROOT/'research/cache/upstream/fonts/NotoSerif-Regular.ttf',Path('C:/Windows/Fonts/times.ttf')))
LABEL_FONT=FONT_PAIRS[0][0]
LABELS=dict(full_name='Họ và tên',id_number='Số giấy tờ',dob='Ngày sinh',gender='Giới tính',address='Địa chỉ',
            student_id='Mã học sinh',school='Trường học',course='Niên khóa',license_class='Hạng bằng lái',expiry_date='Ngày hết hạn')
CONDITIONS=('seen_layout_seen_font','new_layout_seen_font','seen_layout_new_font','new_layout_new_font')

@lru_cache(maxsize=8)
def cmap(path):
    with TTFont(path) as font:return set(font.getBestCmap())

def ensure_glyphs(path,text):
    missing=sorted({ord(c) for c in text if not c.isspace() and ord(c) not in cmap(str(path))})
    if missing:raise ValueError('Font lacks required Unicode glyphs: '+','.join(hex(c) for c in missing))

def specification(index):
    identity=f'ocr-labels-v1-fictional-{index:03}'
    rng=random.Random(int(uid(identity)[:16],16))
    name=' '.join((rng.choice(['ĐINH','ĐOÀN','TÔ','LƯU','CAO','MAI']),rng.choice(['NGỌC','VĨNH','GIA','DIỆU']),
                  rng.choice(['BẢO','KHANG','UYÊN','QUỲNH','HUỆ','THIỆN'])))
    number='MT'+''.join(str(rng.randrange(10)) for _ in range(10))
    values=dict(full_name=name,id_number=number,dob=f'{rng.randrange(1,28):02}/{rng.randrange(1,13):02}/{rng.randrange(1971,2007)}',
                gender=rng.choice(['NAM','NỮ']),address=f'{rng.randrange(1,900)} ĐƯỜNG MÂY TÍM, PHƯỜNG SÔNG ĐÊM',
                student_id='MHSV'+''.join(str(rng.randrange(10)) for _ in range(8)),
                school=rng.choice(['TRƯỜNG MẪU BÌNH YÊN','TRƯỜNG MẪU TRĂNG SÁNG','TRƯỜNG MẪU HƯỚNG DƯƠNG']),
                course=f'{rng.randrange(2019,2023)}-{rng.randrange(2027,2032)}',license_class=rng.choice(['A1','A2','B1','B2','C']),
                expiry_date=f'{rng.randrange(1,28):02}/{rng.randrange(1,13):02}/{rng.randrange(2032,2042)}')
    kinds=(('full_name','id_number','dob','gender','address'),('full_name','student_id','school','course','dob'),
           ('full_name','id_number','dob','license_class','expiry_date'))
    keys=list(kinds[index%3]);rng.shuffle(keys)
    widths=[895]*5
    for j,w in enumerate([520,510,410,400,1140]):widths[j]=min(widths[j],w)
    pair=FONT_PAIRS[index%2];sizes={}
    for key,width in zip(keys,widths):
        value=unicodedata.normalize('NFC',values[key]);values[key]=value
        for path in pair:ensure_glyphs(path,value)
        size=34
        while max(ImageFont.truetype(str(path),size).getlength(value) for path in pair)>width-12 and size>18:size-=1
        if max(ImageFont.truetype(str(path),size).getlength(value) for path in pair)>width-12:raise ValueError('Value does not fit either controlled font')
        sizes[key]=size
    return dict(physical_id=identity,index=index,role='development' if index<8 else 'test',keys=keys,
                values={key:values[key] for key in keys},font_sizes=sizes,font_pair=index%2,
                masked_key=sorted(keys)[int(uid('mask/'+identity)[:8],16)%len(keys)])

def anchors(new_layout):
    return [(30,155,520),(660,155,510),(30,340,410),(770,340,400),(30,655,1140)] if new_layout else [(265,143+j*112,895) for j in range(5)]

def ink_patch(text,font):
    ascent,descent=font.getmetrics();width=math.ceil(font.getlength(text))+16
    mask=Image.new('L',(width,ascent+descent+16));glyphs=[]
    for i,c in enumerate(text):
        advance=font.getlength(text[:i+1])-font.getlength(c)
        one=Image.new('L',mask.size);d=ImageDraw.Draw(one)
        d.text((8+advance,8+ascent),c,font=font,fill=255,anchor='ls')
        box=one.getbbox()
        if box:glyphs.append(dict(index=i,character=c,box=list(box)))
        mask=Image.fromarray(np.maximum(np.asarray(mask),np.asarray(one)))
    if not mask.getbbox():raise ValueError('No actual glyph ink')
    return mask,glyphs

def render(spec,condition,capture):
    if condition not in CONDITIONS or capture not in ('full','value_mask'):raise ValueError('Unregistered render condition')
    new_layout=condition.startswith('new_layout');new_font=condition.endswith('new_font')
    fontpath=FONT_PAIRS[spec['font_pair']][int(new_font)]
    image=Image.new('RGB',(1200,800),(242,246,238));d=ImageDraw.Draw(image)
    d.rectangle((0,0,1200,100),fill=(27,85,104))
    label_font=ImageFont.truetype(str(LABEL_FONT),23)
    for text in ('GIẤY TỜ MẪU / OCR LABEL STUDY','FICTITIOUS DATA / KHÔNG CÓ GIÁ TRỊ XÁC THỰC'):
        ensure_glyphs(LABEL_FONT,text)
    d.text((28,20),'GIẤY TỜ MẪU / OCR LABEL STUDY',font=ImageFont.truetype(str(LABEL_FONT),30),fill='white',anchor='lt')
    portrait=(480,300,720,600) if new_layout else (25,140,225,405)
    d.rounded_rectangle(portrait,radius=12,fill=(199,213,216),outline=(27,85,104),width=3)
    x0,y0,x1,y1=portrait;cx=(x0+x1)//2
    d.ellipse((cx-38,y0+30,cx+38,y0+126),fill=(143,166,172))
    d.ellipse((x0+25,y0+140,x1-25,y1-20),fill=(143,166,172))
    fields=[];supports=[]
    for key,(x,y,width) in zip(spec['keys'],anchors(new_layout)):
        label=LABELS[key]+':'
        ensure_glyphs(LABEL_FONT,label);d.text((x,y),label,font=label_font,fill=(55,65,70),anchor='lt')
        font=ImageFont.truetype(str(fontpath),spec['font_sizes'][key])
        mask,glyphs=ink_patch(spec['values'][key],font);px,py=x-8,y+35-8
        image.paste((16,26,34),(px,py),mask)
        a,b,c,e=mask.getbbox();quad=[[px+a,py+b],[px+c,py+b],[px+c,py+e],[px+a,py+e]]
        chars=[dict(index=g['index'],character=g['character'],polygon=[[px+g['box'][0],py+g['box'][1]],
                [px+g['box'][2],py+g['box'][1]],[px+g['box'][2],py+g['box'][3]],[px+g['box'][0],py+g['box'][3]]]) for g in glyphs]
        value=field(key,spec['values'][key],quad,1200,800,origin='renderer_ink',annotation_ref=dict(renderer='labels_synth_v1',identity=spec['physical_id']),
                    semantic_key=key,extra=dict(field_id=key,label_box=list(d.textbbox((x,y),label,font=label_font,anchor='lt')),
                    glyphs=chars,font_sha256=sha(fontpath),font_size=spec['font_sizes'][key],
                    ink_support_sha256=hashlib.sha256(mask.tobytes()).hexdigest(),
                    construction_visibility=dict(status='ink_visible',visible_ink_fraction=1.,observed_text=spec['values'][key]),
                    anchor=[x,y,width]))
        fields.append(value);supports.append((px,py,mask))
    d=ImageDraw.Draw(image);d.text((28,764),'FICTITIOUS DATA / KHÔNG CÓ GIÁ TRỊ XÁC THỰC',font=ImageFont.truetype(str(LABEL_FONT),18),fill=(27,85,104),anchor='lt')
    full=np.asarray(image).copy();mask_regions=[]
    if capture=='value_mask':
        selected=next(f for f in fields if f['raw_key']==spec['masked_key']);q=np.asarray(selected['polygon'])
        a,b=np.floor(q.min(axis=0)).astype(int)-2;c,e=np.ceil(q.max(axis=0)).astype(int)+2
        region=[[int(a),int(b)],[int(c),int(b)],[int(c),int(e)],[int(a),int(e)]]
        d.rectangle((a,b,c,e),fill=(36,44,51));mask_regions.append(region)
        selected['construction_visibility']=dict(status='ink_masked',visible_ink_fraction=0.,observed_text='')
        for f,(px,py,support) in zip(fields,supports):
            if f['raw_key']==spec['masked_key']:continue
            box=support.getbbox();x,y,w,h=box
            if not np.array_equal(full[py+y:py+h,px+x:px+w],np.asarray(image)[py+y:py+h,px+x:px+w]):
                raise ValueError('Mask changes another value region')
    return image,fields,dict(mask_regions=mask_regions,font_sha256=sha(fontpath),
        layout_anchor_signature=digest(anchors(new_layout)),layout='center_portrait_perimeter' if new_layout else 'prior_vertical_body',
        condition=condition,capture=capture,independent_human_legibility=False)

def build():
    fonts=[]
    for pair in FONT_PAIRS:
        for path in pair:
            if not path.is_file():raise FileNotFoundError(path)
            fonts.append(dict(name=path.name,sha256=sha(path),bytes=path.stat().st_size,new_to_local_training=path in (FONT_PAIRS[0][1],FONT_PAIRS[1][1]),redistributed=False))
    save(OUT/'fonts.json',dict(files=fonts,label_font_sha256=sha(LABEL_FONT),scope='New value fonts relative to local training; pretraining exposure unknown'))
    records=[];specs=[]
    for index in range(32):
        spec=specification(index);specs.append(spec)
        for condition in CONDITIONS:
            for capture in ('full','value_mask'):
                native=spec['physical_id']+'/'+condition+'/'+capture;path=DATA/'images'/('synth_'+uid(native)+'.png')
                image,fields,meta=render(spec,condition,capture)
                path.parent.mkdir(parents=True,exist_ok=True);image.save(path)
                records.append(dict(uid=native,physical_id=spec['physical_id'],role=spec['role'],source='authored',
                    device='renderer',layout=meta['layout'],font_sha256=meta['font_sha256'],condition=condition,
                    capture=capture,path=path.relative_to(ROOT).as_posix(),input_sha256=sha(path),width=1200,height=800,
                    coordinate_mode='raw_pixels',fields=fields,render=meta,masked_keys=[spec['masked_key']] if capture=='value_mask' else [],
                    target={f['semantic_key']:f['reference_text'] for f in fields if f['construction_visibility']['visible_ink_fraction']==1.},
                    accepted_values={f['semantic_key']:[f['reference_text']] for f in fields if f['construction_visibility']['visible_ink_fraction']==1.},
                    source_refs={f['semantic_key']:[dict(value=f['reference_text'],kind='body',source=f['raw_key'],priority=0)] for f in fields if f['construction_visibility']['visible_ink_fraction']==1.}))
        progress('synthetic_render',index+1,32)
    save(DATA/'render_specs.json',specs)
    return records

if __name__=='__main__':save(DATA/'authored.json',build())
