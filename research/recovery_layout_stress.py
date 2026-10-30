"""Independent true spatial-layout stress set; primary dataset stays immutable."""
import argparse
import copy
import json
import time
from pathlib import Path

import cv2
import numpy as np
from PIL import Image,ImageDraw,ImageFont

from research.benchmark import save,digest
from research.e2e_benchmark import atomic_json,hash_json
from research.e2e_eval import score
from research.recovery_data import render_card,seed,mapped,capture,mark_visibility,FONTS,LABELS_EN,LABELS_VI,CAPTURES
from research.recovery_runtime import RecoveryEngine
from research.recovery_semantic_eval import score_semantics
from research.recovery_visible_eval import score_visible
from research.recovery_study import OUT,CACHE,process_lock
from research.recovery_validate import canonical

ROOT=Path('research/data/layout_stress')


def card(layout,index):
    vertical=layout=='portrait';number=1000+3*index+(1 if vertical else 0)
    _,original,_,_=render_card(5 if vertical else 0,number)
    values={f['key']:f['text'] for f in original};keys=['full_name','id_number','dob','license_class','expiry_date'] if vertical else ['full_name','student_id','dob','school','course']
    w,h=(730,1100) if vertical else (1100,690)
    image=Image.new('RGB',(w,h),(246,248,245));d=ImageDraw.Draw(image);fontpath=FONTS/('NotoSerif-Regular.ttf' if vertical else 'NotoSans-Regular.ttf')
    def font(size):return ImageFont.truetype(str(fontpath),size)
    d.rectangle((0,0,w,100),fill=(18,100,115));d.text((25,20),'MOCK LICENCE' if vertical else 'STUDENT SPECIMEN',font=font(30),fill='white')
    d.text((25,66),'SPECIMEN - NOT A VALID DOCUMENT',font=font(15),fill='white')
    if vertical:
        d.rounded_rectangle((270,132,460,335),radius=15,fill=(213,226,227));d.ellipse((325,161,405,244),fill=(159,183,188))
        positions=[(55,420+j*116) for j in range(5)];maxwidth=620;labels=LABELS_VI
    else:
        d.rounded_rectangle((35,145,205,362),radius=15,fill=(213,226,227));d.ellipse((80,180,160,264),fill=(159,183,188))
        positions=[(245,180),(670,180),(245,320),(670,320),(245,465)];maxwidth=380;labels=LABELS_EN
    fields=[]
    for key,(x,y) in zip(keys,positions):
        d.text((x,y),labels[key]+':',font=font(20),fill=(55,76,85),anchor='ls');value=values[key];size=29
        while font(size).getlength(value)>maxwidth and size>15:size-=1
        f=font(size);baseline=y+42;d.text((x,baseline),value,font=f,fill=(12,24,35),anchor='ls')
        l,t,r,b=d.textbbox((x,baseline),value,font=f,anchor='ls');characters=[]
        for j,c in enumerate(value):
            cx=x+f.getlength(value[:j]);cl,ct,cr,cb=f.getbbox(c,anchor='ls');cr=max(cl+1,cr);cb=max(ct+1,cb)
            characters.append(dict(text=c,quad=[[cx+cl,baseline+ct],[cx+cr,baseline+ct],[cx+cr,baseline+cb],[cx+cl,baseline+cb]]))
        fields.append(dict(key=key,text=value,quad=[[l,t],[r,t],[r,b],[l,b]],characters=characters))
    d.text((25,h-40),'SYNTHETIC RESEARCH DATA',font=font(17),fill=(18,100,115))
    return cv2.cvtColor(np.asarray(image),cv2.COLOR_RGB2BGR),fields


def build():
    ROOT.mkdir(exist_ok=True,parents=True);samples=[]
    for layout in ('two_column','portrait'):
        for i in range(10):
            identity=f'extra_specimen/{layout}/{i:02d}';im,fields=card(layout,i);h,w=im.shape[:2]
            sw,sh=(900,1300) if layout=='portrait' else (1200,850);rng=np.random.default_rng(seed(identity))
            scene=np.full((sh,sw,3),(105,110,112),np.uint8);noise=rng.normal(0,3,(sh,sw))
            scene=np.uint8(np.clip(scene+noise[...,None],0,255));scale=min((sw-120)/w,(sh-120)/h)
            ox=(sw-w*scale)/2;oy=(sh-h*scale)/2
            quad=np.float32([[ox,oy],[ox+w*scale,oy],[ox+w*scale,oy+h*scale],[ox,oy+h*scale]])
            quad+=rng.uniform(-18,18,quad.shape).astype(np.float32)
            H=cv2.getPerspectiveTransform(np.float32([[0,0],[w-1,0],[w-1,h-1],[0,h-1]]),quad)
            warp=cv2.warpPerspective(im,H,(sw,sh));mask=cv2.warpPerspective(np.full((h,w),255,np.uint8),H,(sw,sh));scene[mask>0]=warp[mask>0]
            ff=[dict(f,quad=mapped(f['quad'],H),characters=[dict(c,quad=mapped(c['quad'],H)) for c in f['characters']]) for f in fields]
            for kind in CAPTURES:
                pixels,fs,gt,trans=capture(scene,ff,quad,identity,kind);uid=identity+'/'+kind;path=ROOT/(uid.replace('/','_')+'.png')
                cv2.imwrite(str(path),pixels)
                samples.append(mark_visibility(dict(uid=uid,physical_id=identity,layout=layout,role='external_layout',source='authored_layout_stress',
                    width=pixels.shape[1],height=pixels.shape[0],fields=fs,gt=gt,path=str(path),input_sha256=digest(path),capture=kind)))
    save(ROOT/'samples.json',samples)
    save(OUT/'layout_stress_acquisition.json',dict(images=80,document_ids=20,spatial_layouts=2,
        original_generator_configs=6,original_language_font_order_groups=4,original_structural_aliases=[[0,2],[1,3]],
        protocol_sha256=digest('research/RECOVERY_LAYOUT_STRESS_PROTOCOL.md'),generator_sha256=digest(__file__),
        samples=[{k:s[k] for k in ('uid','physical_id','layout','capture','input_sha256')} for s in samples]))
    print('LAYOUT_STRESS_BUILT',len(samples),flush=True)


def fixed_raw(engine,image,reader):
    tw=time.perf_counter();tc=time.process_time();answer=engine.ocr(image,reader)
    return dict(predictions=answer['predictions'],fields={},actual_wall_seconds=time.perf_counter()-tw,
        actual_cpu_seconds=time.process_time()-tc,ocr_executions=1,review_recommended=not answer['predictions'],selected_policy='raw')


def run():
    model=json.loads((OUT/'selector_models.json').read_text());lock=json.loads((OUT/'selector_lock.json').read_text())
    if digest(OUT/'selector_models.json')!=lock['model_sha256']:raise ValueError('Selector model lock changed')
    samples=json.loads((ROOT/'samples.json').read_text(encoding='utf-8'));engine=RecoveryEngine();reader='rapid_latin_v5'
    baseline=copy.deepcopy(model);baseline['selectors'][reader]['primary_method']='forced_completion'
    baseline['selectors'][reader]['models']['forced_completion']=dict(regressor=dict(kind='stumps',base=-1.,stumps=[]),expected_fallback_wall={p:0. for p in ('raw','bbox','contour','lcnet')})
    baseline['review_thresholds'][reader]['forced_completion']=model['review_thresholds'][reader]['fixed_completion']
    chosen=[]
    for layout in ('two_column','portrait'):
        ids=sorted({s['physical_id'] for s in samples if s['layout']==layout},key=lambda v:seed('stress-panel/'+v))[:4]
        for identity in ids:chosen.append(min((s for s in samples if s['physical_id']==identity),key=lambda s:seed('stress-panel/'+s['uid'])))
    signature=hash_json(dict(code_sha256=digest(__file__),model_sha256=lock['model_sha256'],samples_sha256=digest(ROOT/'samples.json'),
        protocol_sha256=digest('research/RECOVERY_LAYOUT_STRESS_PROTOCOL.md')));rows=[]
    for repeat,group in ((1,samples),(2,chosen),(3,chosen)):
        for index,sample in enumerate(group):
            if digest(sample['path'])!=sample['input_sha256']:raise ValueError('Stress image changed')
            image=cv2.imread(sample['path']);methods=['raw','fixed_completion','primary_cascade']
            if (index+repeat)%2:methods.reverse()
            for method in methods:
                name=str(repeat)+'_'+str(seed(sample['uid']))+'_'+method;path=CACHE/'layout_stress'/(name+'.json')
                if path.exists():
                    row=json.loads(path.read_text(encoding='utf-8'))
                    if row['signature']!=signature:raise ValueError('Stale stress checkpoint')
                else:
                    answer=(fixed_raw(engine,image,reader) if method=='raw' else engine.online(image,model if method=='primary_cascade' else baseline,reader))
                    row=dict(signature=signature,uid=sample['uid'],physical_id=sample['physical_id'],layout=sample['layout'],capture=sample['capture'],method=method,repeat=repeat,
                        score=score(sample,answer['predictions'],True),visible_score=score_visible(sample,answer['predictions']),
                        actual_wall=answer['actual_wall_seconds'],actual_cpu=answer['actual_cpu_seconds'],ocr_executions=answer['ocr_executions'],
                        review_recommended=answer['review_recommended'],prediction_sha256=canonical(answer['predictions']),_private_predictions=answer['predictions'])
                    if method!='raw':row['semantic_score']=score_semantics(sample,answer['fields'])
                    atomic_json(path,row)
                rows.append({k:v for k,v in row.items() if not k.startswith('_private')});print('LAYOUT_STRESS',len(rows),'/288',flush=True)
    save(OUT/'layout_stress.json',dict(signature=signature,rows=rows,images=80,document_ids=20,panel_images=8,passes=[80,8,8],
        test_threshold_retuned=False,raw_semantic_not_evaluated=True,protocol_sha256=digest('research/RECOVERY_LAYOUT_STRESS_PROTOCOL.md')))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=('build','run'));args=parser.parse_args()
    if args.phase=='build':build()
    else:
        with process_lock(CACHE/'process.lock'):run()
