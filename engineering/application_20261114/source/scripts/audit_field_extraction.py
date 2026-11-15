"""Offline parser regression on authored OCR-token inputs, without model calls.

This checks application behavior, not independent human labels or OCR accuracy.
An optional preserved source file provides a reproducible before/after witness.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

from ekyc import document_fields


CASES = (
    dict(case='student_fields', text=['THẺ HỌC SINH', 'Họ và tên: NGUYỄN VĂN AN',
        'Mã học sinh: HS20260042', 'Lớp: 12A3', 'Niên khóa: 2024 - 2027'],
        fields=dict(full_name='NGUYỄN VĂN AN', student_id='HS20260042',
                    class_name='12A3', course='2024 - 2027'), absent=['id_number', 'dob']),
    dict(case='license_dates', text=['GIẤY PHÉP LÁI XE', 'License number: A1234567',
        'Hạng: B2', 'Ngày cấp: 02/03/2024', 'Có giá trị đến: 02/03/2034'],
        fields=dict(id_number='A1234567', license_class='B2', issue_date='2024-03-02',
                    expiry_date='2034-03-02'), absent=['dob']),
    dict(case='conflicting_names', text=['Họ và tên: NGUYỄN VĂN AN', 'Họ và tên: TRẦN THỊ LAN'],
        fields={}, absent=['full_name']),
    dict(case='conflicting_names_with_detector_guess',
        text=['Họ và tên: NGUYỄN VĂN AN', 'Họ và tên: TRẦN THỊ LAN'],
        specialized=dict(full_name='NGUYỄN VĂN AN'), fields={}, absent=['full_name']),
    dict(case='repeated_same_name', text=['Họ và tên: NGUYỄN VĂN AN', 'Full name: NGUYỄN VĂN AN'],
        fields=dict(full_name='NGUYỄN VĂN AN'), absent=[]),
    dict(case='split_name_label', text=['Họ và tên:', 'NGUYỄN VĂN AN'],
        fields=dict(full_name='NGUYỄN VĂN AN'), absent=[]),
    dict(case='one_character_custom_value', text=['Đơn vị: A'], fields={}, absent=[],
        labelled_items={'Đơn vị': 'A'}),
    dict(case='fullwidth_colon_custom_value', text=['Nhóm： B'], fields={}, absent=[],
        labelled_items={'Nhóm': 'B'}),
    dict(case='conflicting_birth_dates', text=['Ngày sinh: 01/01/2000', 'Ngày sinh: 02/02/2000'],
        specialized=dict(dob='01/01/2000'), fields={}, absent=['dob']),
    dict(case='leading_zero_id', text=['ID number: 001234567890'],
        fields=dict(id_number='001234567890'), absent=[]),
    dict(case='multiline_address', text=['Địa chỉ: 12 ĐƯỜNG MẪU', 'PHƯỜNG THỬ', 'THÀNH PHỐ DEMO'],
        fields=dict(address='12 ĐƯỜNG MẪU PHƯỜNG THỬ THÀNH PHỐ DEMO'), absent=[]),
    dict(case='unknown_document_without_labels', text=['THẺ THƯ VIỆN', 'Thông tin chưa có nhãn'],
        fields={}, absent=['full_name', 'id_number', 'address', 'dob']),
)


def checksum(path):
    with Path(path).open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()


def token_lines(texts):
    return [dict(text=text, confidence=.99, source='authored_regression_tokens',
                 box=[[0, n*25], [600, n*25], [600, n*25+18], [0, n*25+18]])
            for n, text in enumerate(texts)]


def audit(module):
    results=[]
    for case in CASES:
        tokens=token_lines(case['text'])
        specialized=case.get('specialized', {})
        fields, items, kind=module.observed_information(tokens, specialized)
        labelled={item['label']: item['value'] for item in items}
        failures=[]
        for key, expected in case['fields'].items():
            if fields.get(key)!=expected: failures.append('field_value:'+key)
        failures.extend('unexpected_field:'+key for key in case['absent'] if key in fields)
        for label, expected in case.get('labelled_items', {}).items():
            if labelled.get(label)!=expected: failures.append('labelled_value:'+label)
        if not case['fields'] and not case.get('labelled_items') and fields:
            failures.append('unexpected_observed_fields')
        payload=json.dumps(dict(lines=tokens, specialized=specialized),
                           ensure_ascii=False, sort_keys=True).encode('utf-8')
        results.append(dict(case=case['case'], input_sha256=hashlib.sha256(payload).hexdigest(),
            passed=not failures, failures=failures, actual_fields=fields,
            labelled_items=labelled, document_type=kind['key']))
    return dict(source_sha256=checksum(module.__file__), cases=len(results),
                passed=sum(r['passed'] for r in results), results=results)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--baseline-source', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args=parser.parse_args()
    report=dict(schema='application-field-regression/1', stage='OCR tokens to semantic fields',
                evidence='Authored synthetic OCR tokens; not human IFV or model accuracy.',
                model_calls=0, training_steps=0, current=audit(document_fields))
    if args.baseline_source:
        spec=importlib.util.spec_from_file_location('preserved_field_parser', args.baseline_source)
        baseline=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(baseline)
        report['baseline']=audit(baseline)
        report['fixed_cases']=[after['case'] for before, after in zip(
            report['baseline']['results'], report['current']['results'])
            if not before['passed'] and after['passed']]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print(json.dumps(dict(current_passed=report['current']['passed'], cases=len(CASES),
        baseline_passed=report.get('baseline', {}).get('passed'),
        fixed_cases=report.get('fixed_cases', [])), ensure_ascii=True))
    return 0 if report['current']['passed']==len(CASES) else 1


if __name__=='__main__':
    raise SystemExit(main())
