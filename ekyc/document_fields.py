"""Extract observed label/value pairs without a mandatory document template."""
import hashlib
import re
import unicodedata
from datetime import datetime

CORE_KEYS=('full_name','id_number','dob','gender','address')
LABELS=dict(full_name='Họ tên',id_number='Số giấy tờ',dob='Ngày sinh',gender='Giới tính',
    address='Địa chỉ',nationality='Quốc tịch',hometown='Quê quán',expiry_date='Ngày hết hạn',
    issue_date='Ngày cấp',issue_place='Nơi cấp',student_id='Mã học sinh / sinh viên',
    school='Trường',class_name='Lớp',course='Khóa học',license_class='Hạng giấy phép',
    vehicle_type='Loại phương tiện')
PATTERNS={
 'full_name':r'\b(?:ho(?:\s+va)?\s+ten|full\s*name|name\s+and\s+surname|name)\b',
 'dob':r'\b(?:ngay\s+sinh|date\s+of\s+birth|birth\s+date|dob)\b',
 'gender':r'\b(?:gioi\s+tinh|sex|gender)\b',
 'nationality':r'\b(?:quoc\s+tich|nationality)\b',
 'hometown':r'\b(?:que\s+quan|nguyen\s+quan|place\s+of\s+origin|hometown)\b',
 'address':r'\b(?:noi\s+thuong\s+tru|noi\s+cu\s+tru|dia\s+chi|place\s+of\s+residence|permanent\s+address|address)\b',
 'expiry_date':r'\b(?:co\s+gia\s+tri\s+den|co\s+gia\s+tri\s+toi|ngay\s+het\s+han|valid\s+until|date\s+of\s+expiry|expiry\s+date)\b',
 'issue_date':r'\b(?:ngay\s+cap|date\s+of\s+issue|issue\s+date)\b',
 'issue_place':r'\b(?:noi\s+cap|place\s+of\s+issue|issuing\s+authority)\b',
 'student_id':r'\b(?:ma\s+(?:hoc\s+sinh|sinh\s+vien|hs|sv)|mssv|mshs|student\s+(?:id|number|no)|so\s+the)\b',
 'id_number':r'\b(?:so\s+(?:cccd|cmnd|dinh\s+danh|giay\s+phep|gplx|ho\s+chieu)|id\s*(?:number|no)|passport\s*(?:number|no)|licen[cs]e\s*(?:number|no)|document\s*(?:number|no))\b|\b(?:so|no\.?)\s*(?=[:./\s]*[0-9])',
 'class_name':r'\b(?:lop|class)\b',
 'course':r'\b(?:khoa\s+hoc|nien\s+khoa|course|academic\s+year)\b',
 'school':r'\b(?:ten\s+truong|school(?:\s+name)?|truong\s+(?:thpt|thcs|tieu\s+hoc|dai\s+hoc))\b',
 'license_class':r'\b(?:hang\s*(?:gplx|giay\s+phep)?|licen[cs]e\s+class|category)\b',
 'vehicle_type':r'\b(?:loai\s+xe|loai\s+phuong\s+tien|vehicle\s+type)\b',
}


def fold(text):
    return ''.join(c for c in unicodedata.normalize('NFD',text.lower().replace('đ','d')) if not unicodedata.combining(c))


def date_value(value):
    for fmt in ('%d/%m/%Y','%d.%m.%Y','%d-%m-%Y','%Y-%m-%d'):
        try: return datetime.strptime(value.strip(),fmt).date().isoformat()
        except ValueError: pass
    return ''


def document_type(lines):
    text=fold(' '.join(line['text'] for line in lines))
    for kind,label,pattern in (
        ('student_card','Thẻ học sinh / sinh viên',r'the (?:hoc sinh|sinh vien)|student (?:card|id)|mssv|mshs'),
        ('driver_license','Giấy phép lái xe',r'giay phep lai xe|driv(?:er|ing).*licen[cs]e|gplx'),
        ('passport','Hộ chiếu',r'ho chieu|passport'),
        ('identity_card','Căn cước / giấy tờ định danh',r'can cuoc|chung minh nhan dan|citizen identity|identity card')):
        if re.search(pattern,text): return dict(key=kind,label=label,source='ocr_text')
    return dict(key='unknown',label='Giấy tờ khác / chưa xác định',source='ocr_text')


def text_rows(lines):
    """Join labels and values split into separate boxes on the same text row."""
    groups=[]
    for line in sorted(lines,key=lambda l:(min(p[1] for p in l['box']),min(p[0] for p in l['box']))):
        ys=[p[1] for p in line['box']]; center=(min(ys)+max(ys))/2; height=max(ys)-min(ys)
        group=next((g for g in reversed(groups[-3:]) if abs(g['center']-center)<=max(3,min(g['height'],height)*.48)),None)
        if group is None:
            groups.append(dict(center=center,height=height,lines=[line]))
        else: group['lines'].append(line)
    return [' '.join(line['text'].strip() for line in sorted(g['lines'],key=lambda l:min(p[0] for p in l['box']))) for g in groups]


def extract_labelled(lines):
    values={}; labels=dict(LABELS); pending=None; continuations=0
    generic=[line for line in lines if not line.get('field')]
    for text in text_rows(generic):
        text=unicodedata.normalize('NFC',' '.join(text.split()))
        normalized=fold(text)
        index=[i for i,char in enumerate(text) for _ in fold(char)]
        found=[]
        for key,pattern in PATTERNS.items():
            for match in re.finditer(pattern,normalized): found.append((match.start(),match.end(),key))
        found.sort(key=lambda item:(item[0],-(item[1]-item[0])))
        matches=[]
        for item in found:
            if matches and item[0]<matches[-1][1]: continue
            matches.append(item)
        if not matches:
            custom=re.match(r'^([^:：]{2,60})[:：]\s*(\S.+)$',text)
            if custom:
                label,value=custom.groups(); key='extra_'+hashlib.sha256(fold(label).encode()).hexdigest()[:12]
                labels[key]=label.strip(); values.setdefault(key,[]).append(value.strip());pending=None
            elif pending and continuations<2 and text and not re.search(r'the (hoc sinh|sinh vien)|can cuoc|giay phep|cong hoa',normalized):
                values.setdefault(pending,[]).append(text.strip(' /:.-'))
                continuations+=1
                if pending not in ('address','hometown'): pending=None
            continue
        pending=None; continuations=0
        for n,(start,end,key) in enumerate(matches):
            stop=matches[n+1][0] if n+1<len(matches) else len(normalized)
            value=text[index[end-1]+1:index[stop] if stop<len(index) else len(text)].strip(' /:.-')
            # A second bilingual label contributes the value, not two copies.
            if value: values.setdefault(key,[]).append(value)
            if n==len(matches)-1 and (not value or key in ('address','hometown')):
                pending=key
    fields={}
    for key,parts in values.items():
        parts=list(dict.fromkeys(part for part in parts if part))
        if not parts: continue
        if key in ('address','hometown','full_name'): fields[key]=' '.join(parts)
        elif len(parts)==1: fields[key]=parts[0]
        else: fields[key]=None
    return fields,labels


def observed_information(lines, specialized):
    fields,labels=extract_labelled(lines)
    # Explicit labels on arbitrary documents override a specialized model's
    # guess; detector classes remain useful when a printed label is not read.
    for key,value in specialized.items():
        if value and key not in fields: fields[key]=value
        elif value and fields.get(key) and key in ('address','hometown'):
            # A generic row can contain another column's expiry label before
            # the address continuation. A dedicated multi-line region can
            # complete that observed prefix without inventing missing text.
            words=set(re.findall(r'\w+',fold(fields[key])))
            candidate=set(re.findall(r'\w+',fold(value)))
            if len(value)>len(fields[key]) and words and len(words&candidate)/len(words)>=.8:
                fields[key]=value
    cleaned={}
    for key,value in fields.items():
        if not value: continue
        value=' '.join(value.split()).strip(' /:')
        if key in ('dob','expiry_date','issue_date'):
            value=date_value(value)
        elif key=='gender':
            value={'nam':'Nam','male':'Nam','m':'Nam','nu':'Nữ','female':'Nữ','f':'Nữ'}.get(fold(value),'')
        elif key in ('id_number','student_id'):
            value=re.sub(r'\s+','',value)
            if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9./_-]{1,39}',value) or not any(c.isdigit() for c in value): value=''
        if value and len(value)<=500: cleaned[key]=value
    if cleaned.get('student_id') and cleaned.get('id_number')==cleaned['student_id']:
        cleaned.pop('id_number')
    items=[dict(key=key,label=labels.get(key,key),value=value,source='ocr',
                input_type='date' if key in ('dob','expiry_date','issue_date') else 'text') for key,value in cleaned.items()]
    return cleaned,items,document_type(lines)
