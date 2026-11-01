"""Separate paths and immutable contracts for the second local VLM study."""
import hashlib
import json
from pathlib import Path
from research.vlm_setup import ROOT, sha, save

PILOT_CACHE = ROOT/'research/cache/vlm_lora_v2'
PILOT_DATA = ROOT/'research/data/vlm_lora_v2'
CACHE = ROOT/'research/cache/vlm_lora_v2_r2'
DATA = ROOT/'research/data/vlm_lora_v2_r2'
OUT = ROOT/'research/results/vlm_lora_v2_r2'
HELD_LAYOUTS = ('fin_id', 'lva_passport')
CONFIG = dict(seeds=[42,31415], steps=320, gradient_accumulation=4,
              checkpoint_every=80, rank=8, alpha=16, learning_rate=0.0002,
              generation_max_new_tokens=384, train_mock_ids=96, train_photo_ids=32,
              development_mock_ids=16, development_photo_ids=8,
              test_mock_ids=24, test_photo_ids=24)
KEYS = ('full_name','first_name','last_name','id_number','personal_number','dob',
        'gender','address','nationality','birth_place','issue_date','expiry_date',
        'authority','student_id','school','course','license_class')
PROMPT = ('Đọc tất cả thông tin thực sự nhìn thấy trên giấy tờ. Chỉ trả về JSON object. '
          'Các khóa nếu có: '+', '.join(KEYS)+'. '
          'name/given names là first_name; surname là last_name; document number là id_number; '
          'personal number là personal_number. Chỉ xuất trường có giá trị nhìn thấy đầy đủ, '
          'giữ nguyên chữ, số và ngày tháng. Bỏ trường bị che hoặc cắt mất một phần giá trị. '
          'Không đoán, không điền trường mặc định. Không đọc được gì thì trả về {}.')
FIELD_MAP = dict(name='first_name', surname='last_name', number='id_number',
                 id_number='personal_number', birth_date='dob', gender='gender',
                 nationality='nationality', birth_place='birth_place',
                 issue_date='issue_date', expiry_date='expiry_date', authority='authority')
FIELD_MAP.update(name_eng='first_name',surname_eng='last_name',birth_place_eng='birth_place',
    authority_eng='authority',nationality_eng='nationality',birth_date_2='dob',birth_date_22='dob',
    expiry_date2='expiry_date',expiry_date_2='expiry_date')
FIELD_MAP['nationality/nationality_eng']='nationality'

def read(path): return json.loads(Path(path).read_text(encoding='utf-8'))
def seed(text): return int.from_bytes(hashlib.sha256(text.encode()).digest()[:8],'big')
def stable_hash(value): return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
def load(role=None,variant='partial'):
    if (OUT/'dataset_card.json').exists() and sha(DATA/'samples.json')!=read(OUT/'dataset_card.json')['samples_sha256']:
        raise ValueError('Private dataset differs from the published dataset hash')
    rows=read(DATA/'samples.json')
    return [r for r in rows if (role is None or r['role']==role) and
            (r['role']!='train' or r['variant']==variant)]

def signature():
    names=['v2_common.py','v2_acquire.py','v2_data.py','v2_inputs.py','v2_runtime.py','v2_metrics.py',
           'v2_study.py','V2_PROTOCOL.md']
    hashes={n:sha(ROOT/'research'/n) for n in names}
    hashes['frozen_v1_index']=sha(ROOT/'research/results/vlm_lora_v1/artifact_index.json')
    for n in ('dataset_card.json','input_choice.json'):
        if not (OUT/n).exists(): raise ValueError('V2 preparation incomplete: '+n)
        hashes[n]=sha(OUT/n)
    return stable_hash(hashes)

def preserve_v1():
    index=read(ROOT/'research/results/vlm_lora_v1/artifact_index.json')
    bad=[r['path'] for r in index['files'] if sha(ROOT/r['path'])!=r['sha256']]
    if bad: raise ValueError('Frozen V1 artifacts changed: '+str(bad))
    return len(index['files'])
