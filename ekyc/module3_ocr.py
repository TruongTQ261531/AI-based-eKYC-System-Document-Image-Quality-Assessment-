"""Module 3: ScanOCR/VietOCR field extraction and verified ID face crop."""
import re
import unicodedata
from datetime import datetime


def normalize(text):
    return ''.join(c for c in unicodedata.normalize('NFD', text.lower().replace('đ', 'd')) if not unicodedata.combining(c))


def parse_lines(lines):
    fields = dict(id_number=None, full_name=None, dob=None, gender=None, address=None)
    patterns = {
        'id_number': r'\b(?:id\s*(?:number|no)|document\s*(?:number|no)|passport\s*(?:number|no)|cccd|so)\b\s*[:.]?\s*([A-Z0-9][A-Z0-9 -]{5,20})',
        'full_name': r'\b(?:full\s*name|ho va ten|name)\b\s*[:.]\s*(.+)',
        'dob': r'\b(?:date of birth|birth date|dob|ngay sinh)\b\s*[:.]?\s*(\d{1,4}[./-]\d{1,2}[./-]\d{1,4})',
        'address': r'\b(?:address|noi thuong tru|noi cu tru)\b\s*[:.]\s*(.+)',
        'gender': r'\b(?:sex|gender|gioi tinh)\b\s*[:.]?\s*(female|male|nam|nu|m|f)\b',
    }
    for line in lines:
        text = line['text'].strip()
        folded = normalize(text)
        for field, pattern in patterns.items():
            match = re.search(pattern, folded, re.I)
            if match and fields[field] is None and (field != 'id_number' or any(c.isdigit() for c in match.group(1))):
                # Build an index map so combining accents do not shift source slices.
                indices = [i for i, char in enumerate(text) for _ in normalize(char)]
                fields[field] = text[indices[match.start(1)]:indices[match.end(1)-1]+1].strip()
    return fields


def form_fields(fields):
    """Unknown values stay blank; a form edit is not a verified OCR observation."""
    result = {key: fields.get(key) or '' for key in ('full_name','id_number','dob','gender','address')}
    date = result['dob']
    result['dob'] = ''
    for format in ('%d/%m/%Y','%d.%m.%Y','%d-%m-%Y','%Y-%m-%d'):
        try:
            result['dob'] = datetime.strptime(date, format).date().isoformat()
            break
        except ValueError:
            pass
    result['gender'] = {'nam':'Nam','male':'Nam','m':'Nam','nu':'Nữ','female':'Nữ','f':'Nữ'}.get(normalize(result['gender']), '')
    return result


def parse_regions(lines, *, generic_ids=False):
    """Use the detector's field labels; preserve Vietnamese accents and leading zeroes."""
    fields = dict(id_number=None, full_name=None, dob=None, gender=None, address=None,nationality=None,hometown=None)
    prefixes = {
        'id_number': r'^(?:(?:so|id|number|no|cccd|cmnd)\s*[/.:]*\s*)+',
        'full_name': r'^(?:(?:ho va ten|ho ten|full name)\s*[/.:]*\s*)+',
        'dob': r'^(?:(?:ngay sinh|date of birth|dob)\s*[/.:]*\s*)+',
        'gender': r'^(?:(?:gioi tinh|sex|gender)\s*[/.:]*\s*)+',
        'address': r'^(?:(?:noi thuong tru|noi cu tru|dia chi|place of residence|address)\s*[/.:]*\s*)+',
        'nationality':r'^(?:(?:quoc tich|nationality)\s*[/.:]*\s*)+',
        'hometown':r'^(?:(?:que quan|nguyen quan|place of origin|hometown)\s*[/.:]*\s*)+',
    }
    values = {key: [] for key in fields}
    # Detector crops are line regions. Sort by top edge, then left edge.
    ordered = sorted(lines, key=lambda line: (min(p[1] for p in line['box']), min(p[0] for p in line['box'])))
    for line in ordered:
        key = line.get('field')
        if key not in fields:
            continue
        text = unicodedata.normalize('NFC', ' '.join(line['text'].split()))
        prefix = re.match(prefixes[key], normalize(text))
        if prefix:
            indices = [i for i, char in enumerate(text) for _ in normalize(char)]
            text = text[indices[prefix.end()-1]+1:].strip()
        if not text:
            continue
        if key == 'id_number':
            text = re.sub(r'\s+', '', text)
            pattern=r'[A-Za-z0-9][A-Za-z0-9./_-]{1,39}' if generic_ids else r'(?:\d{9}|\d{12})'
            if not re.fullmatch(pattern, text) or not any(c.isdigit() for c in text):
                continue  # Never repair OCR letters into digits or invent missing digits.
        if key == 'dob' and not form_fields({'dob':text})['dob']:
            continue
        if key == 'gender':
            text = form_fields({'gender':text})['gender']
            if not text:
                continue
        if text not in values[key]:
            values[key].append(text)
    for key, parts in values.items():
        if key in ('full_name', 'address','hometown'):
            fields[key] = ' '.join(parts) or None
        elif len(parts) == 1:
            fields[key] = parts[0]
        # Conflicting scalar readings remain blank for the user to review.
    return fields


class OCRExtraction:
    def __init__(self, model_dir, min_confidence=0.65):
        from .scanocr import ScanOCRReader
        self.reader = ScanOCRReader(model_dir)
        self.min_confidence = min_confidence

    def run_unlocalized(self,image):
        return self.run(image,None,extract_portrait=False)

    def run(self, card, face_engine, *, extract_portrait=True):
        from .io import StageError
        crop = embedding = detection = None
        face_error = None
        if extract_portrait:
            try:
                card, crop, embedding, detection = face_engine.extract_document(card)
            except StageError as error:
                face_error = getattr(error, 'code', 'id_face_unavailable')
        else: face_error='id_face_unavailable'
        lines = self.reader.read(card)
        lines.sort(key=lambda line: (min(p[1] for p in line['box']), min(p[0] for p in line['box'])))
        accepted = [line for line in lines if line['confidence'] >= self.min_confidence and line['text'].strip()]
        from .document_fields import observed_information
        specialized=parse_regions([line for line in accepted if line.get('field')],generic_ids=True)
        fields,items,kind=observed_information(accepted,specialized)
        result = dict(engine='scanocr_vietocr_generic', fields=fields, document_fields=items,document_type=kind,
                      raw_lines=lines, accepted_line_count=len(accepted),requires_review=True)
        # OCR JSON remains available even when there is no usable portrait.
        if embedding is not None:
            result['face'] = detection
            return result, crop, embedding
        result['face_error'] = face_error
        result['requires_review'] = True
        return result, None, None
