"""Create an explicitly fictional, out-of-study web input; no expected-output API."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from research.v3_common import OUT,read,DATA,save,sha

def make():
    font=Path('C:/Windows/Fonts/arial.ttf')
    if not font.exists():raise ValueError('Windows Arial font is required for this local demonstration')
    def face(size):return ImageFont.truetype(str(font),size)
    # These strings are input pixels only. They are never returned by inference.
    fields=[('Họ và tên','MẪU KIỂM THỬ MỚI'),('Mã sinh viên','WEB-20261101-001'),
            ('Ngày sinh','12/09/2003'),('Tên trường','TRƯỜNG MÔ PHỎNG'),('Khóa học','2026-2030')]
    train_text=str([r['target'] for r in read(DATA/'samples.json') if r['role']=='train'])
    if fields[1][1] in train_text:raise ValueError('Fresh demonstration ID already occurs in training labels')
    im=Image.new('RGB',(1280,800),'#f8f4e8');d=ImageDraw.Draw(im)
    d.rectangle((0,0,1280,106),fill='#1a5c4b');d.text((35,22),'SPECIMEN / GIẤY TỜ MẪU',font=face(44),fill='white')
    d.rounded_rectangle((35,160,290,520),radius=16,fill='#d6e0e0',outline='#4d7775',width=3)
    d.ellipse((112,210,212,310),fill='#8ca4a7');d.ellipse((65,326,260,510),fill='#8ca4a7')
    for i,(label,value) in enumerate(fields):
        y=140+i*113;d.text((340,y),label+':',font=face(27),fill='#44605c')
        d.text((340,y+34),value,font=face(41),fill='#142d31')
    d.text((35,742),'KHÔNG CÓ GIÁ TRỊ ĐỊNH DANH · MẪU THỬ CHỨC NĂNG, KHÔNG TÍNH ĐIỂM BENCHMARK',font=face(20),fill='#44605c')
    path=OUT/'ui/new_specimen.png';path.parent.mkdir(parents=True,exist_ok=True);im.save(path)
    save(OUT/'new_demo_provenance.json',dict(image_sha256=sha(path),authored_fictional_input=True,used_for_training=False,
        used_for_model_selection=False,used_for_test_accuracy=False,expected_output_served_by_API=False,training_ID_occurrences=0))
    print('FRESH_WEB_SPECIMEN_READY',sha(path))

if __name__=='__main__':make()
