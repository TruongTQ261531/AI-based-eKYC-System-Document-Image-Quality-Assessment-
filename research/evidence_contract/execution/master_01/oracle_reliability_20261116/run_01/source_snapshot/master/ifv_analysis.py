"""Read-only post-review diagnostics; never edits observations or frozen labels.

The primary report is replayed unchanged. Literal cross-phase discrepancies
are context flags, not automatic adjudications. Withholding flagged cases is
an explicitly post-hoc sensitivity panel, not a replacement primary analysis.
No predictor, OCR loader, model, training code or new input generator is used.
"""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import argparse
import json
import unicodedata

from ..task55 import ifv
from ..task55.data import EC, digest, read, save_new, sha
from .ifv_report import KNOWN, METHODS, sealed_results, summarize
from .intake import EXECUTION, PRIVATE
from .statistics import rate


def literal_text(value):
    """Ignore Unicode composition, case and whitespace; preserve O/0 and dates."""
    return ' '.join(unicodedata.normalize('NFC', value).casefold().split())


def coherence_flags(case, item):
    flags=[]
    for side in ('before', 'after'):
        output=case[side+'_output']
        if not output['structured_output_usable']:
            continue
        evidence=case[side+'_evidence']
        reading=item[side+'_reading']
        emitted=bool(output['value'].strip())
        if reading=='readable_omission' and emitted:
            flags.append(side+'_nonempty_output_marked_omission')
        if reading in ('wrong_value', 'unsupported_verified') and not emitted:
            flags.append(side+'_empty_output_marked_value_error')
        if reading=='correct' and ifv.readable(evidence) and (
                literal_text(output['value'])!=literal_text(evidence['observed_transcript'])):
            flags.append(side+'_correct_disagrees_with_phase1_transcript')
    return flags


def gate_reasons(case, item):
    """Explain the frozen gate, without claiming to resolve an unknown source."""
    status=dict(zip(('pointwise','relation'), ifv.labels_for(case,item)))
    common=[]
    if item['test_validity']=='invalid':
        common=['reviewer_marked_invalid_test']
    elif item['test_validity']!='valid':
        common=['reviewer_validity_uncertain']
    elif not case['after_output']['structured_output_usable']:
        common=['followup_structure_unusable']
    elif case['contract']=='C1':
        if case['source_inventory_scope']!='complete': common.append('source_inventory_incomplete')
        if item['absence_check']!='all_sources_removed': common.append('all_source_removal_not_established')
        if not ifv.readable(case['before_evidence']): common.append('original_evidence_not_readable')
        if case['after_evidence']['availability']!='not_seen': common.append('followup_absence_not_recorded')
        if any(s['availability']!='not_seen' for s in case['after_evidence']['sources']):
            common.append('remaining_source_not_recorded_absent')
        emitted=bool(case['after_output']['value'].strip())
        if item['after_reading']!=('unsupported_verified' if emitted else 'correct'):
            common.append('absence_judgment_incompatible_with_emission')
    else:
        if not ifv.readable(case['after_evidence']): common.append('followup_evidence_not_readable')
        if case['contract']=='C2' and not ifv.supported_backup(case):
            common.append('backup_source_not_verified')
        emitted=bool(case['after_output']['value'].strip())
        reading=item['after_reading']
        compatible=(reading=='correct' and emitted) or (reading=='wrong_value' and emitted) or (
            reading=='readable_omission' and not emitted)
        if not compatible: common.append('field_judgment_incompatible_or_uncertain')
    result={endpoint:list(common) if label not in KNOWN else [] for endpoint,label in status.items()}
    if status['pointwise'] in KNOWN and status['relation']=='INCONCLUSIVE':
        original=case['before_evidence']
        if not ifv.readable(original): result['relation'].append('original_evidence_not_readable')
        if not case['before_output']['structured_output_usable']:
            result['relation'].append('original_structure_unusable')
        if not case['before_output']['value'].strip(): result['relation'].append('original_output_empty')
        if item['before_reading']!='correct': result['relation'].append('original_reading_not_correct')
    return result


def alarm_accounting(links, labels, endpoint, method):
    primary={k:c for k,c in links.items() if c['row']['stratum']=='primary'}
    alarms={k:c for k,c in primary.items() if c['row']['checks'][method]['alarm']}
    counts=Counter(labels.get(k,{}).get(endpoint,'UNREVIEWED') for k in alarms)
    faults=counts['CONFIRMED_FAULT']; no_faults=counts['NO_FAULT']
    return dict(total_alarms=len(alarms), labeled_fault_alarms=faults,
                labeled_no_fault_alarms=no_faults, unresolved_alarms=len(alarms)-faults-no_faults,
                status_counts=dict(counts),
                verified_fault_fraction_of_all_alarms=rate(faults,len(alarms)),
                conditional_precision=rate(faults,faults+no_faults))


def analyze(packet, export, links, labels):
    cases={c['case_id']:c for c in packet['cases']}
    items={i['case_id']:i for i in export['items']}
    if len(items)!=len(export['items']) or set(items)!=set(cases) or set(labels)!=set(cases) or set(links)!=set(cases):
        raise ValueError('Diagnostics require the entire sealed selected frame without duplicates')
    if any(labels[k]!=dict(zip(('pointwise','relation'),ifv.labels_for(cases[k],items[k]))) for k in cases):
        raise ValueError('Diagnostics do not accept relabeled observations')
    details=[]
    withheld=deepcopy(labels)
    for key in sorted(cases):
        case,item=cases[key],items[key]
        flags=coherence_flags(case,item)
        reasons=gate_reasons(case,item)
        details.append(dict(case_id=key,contract=case['contract'],
            stratum=links[key]['row']['stratum'],frozen_labels=labels[key],
            coherence_flags=flags,inconclusive_reasons=reasons))
        if flags: withheld[key]=dict(pointwise='INCONCLUSIVE',relation='INCONCLUSIVE')
    primary={k:c for k,c in links.items() if c['row']['stratum']=='primary'}
    original=summarize(links,labels)
    sensitivity=summarize(links,withheld)
    reasons={endpoint:dict(Counter(reason for row in details if row['stratum']=='primary'
                 and row['frozen_labels'][endpoint]=='INCONCLUSIVE'
                 for reason in row['inconclusive_reasons'][endpoint]))
             for endpoint in ('pointwise','relation')}
    flagged=[row for row in details if row['coherence_flags']]
    report=dict(schema='ifv-postreview-analysis/1',scope='one-project-author development pilot, unadjudicated',
        phase1_snapshot=packet['phase1_snapshot'],phase2_packet_id=packet['packet_id'],
        export_snapshot=digest(export),reviewed=len(items),primary_cases=len(primary),
        diagnostic_cases=len(links)-len(primary),actual_reviewers=1,independence_verified=False,
        original_label_coverage={endpoint:rate(sum(labels[k][endpoint] in KNOWN for k in primary),len(primary))
                                 for endpoint in ('pointwise','relation')},
        original=original,all_alarm_accounting={endpoint:{m:alarm_accounting(links,labels,endpoint,m)
            for m in METHODS} for endpoint in ('pointwise','relation')},
        inconclusive_reasons=reasons,
        coherence=dict(flagged_cases=len(flagged),flagged_primary_cases=sum(r['stratum']=='primary' for r in flagged),
            flags=dict(Counter(f for row in flagged for f in row['coherence_flags'])),
            meaning='Literal discrepancies to retain for possible adjudication; no corrections or fault labels inferred.'),
        sensitivity=dict(policy='POST_HOC: withhold both endpoint labels for any literal coherence flag; keep the entire frame.',
            withheld_cases=len(flagged),results=sensitivity),
        method_agreement=dict(A_vs_flat=sum(all(c['row']['checks']['A'][k]==c['row']['checks']['A_flat'][k]
            for k in ('verdict','alarm')) for c in primary.values()),
            compared_primary_cases=len(primary)),
        active_review_minutes=None,inter_rater_agreement=None,population_recall=None,
        software_root_causes_verified=0,human_answers_changed=0,model_calls=0,confirmatory=False)
    return report,details


def from_sealed(path):
    primary=sealed_results(path)
    path=Path(path).resolve();folder=path.parents[2]
    packet=read(folder/'packet.json');export=read(path);labels=read(path.parent/'labels.json')
    links=read(ifv.JOINS/(folder.name+'.json'))
    report,details=analyze(packet,export,links,labels)
    if report['original']!=primary['results']:
        raise ValueError('Post-review primary report differs from the frozen reporter')
    report['sealed_submission_sha256']=sha(path)
    return report,details


def markdown(report):
    lines=['# IFV: hậu kiểm và mẫu số', '',
        f"Một tác giả đã hoàn tất {report['reviewed']}/{report['reviewed']} ca. Đây là pilot development chưa phân xử độc lập.", '',
        'Bảng chính giữ nguyên phiếu, guard và nhãn đã nhập. Không suy thời gian làm từ timestamp.', '',
        '| Endpoint | Có nhãn lỗi/không lỗi | Chưa kết luận |', '|---|---:|---:|']
    for endpoint in ('pointwise','relation'):
        coverage=report['original_label_coverage'][endpoint]
        lines.append(f"| {endpoint} | {coverage['numerator']}/{coverage['denominator']} | {coverage['denominator']-coverage['numerator']} |")
    for endpoint in ('pointwise','relation'):
        lines.extend(['',f'## {endpoint}', '',
            '| Method | TP | FP | FN | TN | Cảnh báo chưa kết luận / toàn bộ cảnh báo |',
            '|---|---:|---:|---:|---:|---:|'])
        for method in METHODS:
            c=report['original'][endpoint]['overall'][method]['confusion']
            a=report['all_alarm_accounting'][endpoint][method]
            lines.append('| '+' | '.join([method,*[str(c[k]) for k in ('TP','FP','FN','TN')],
                f"{a['unresolved_alarms']}/{a['total_alarms']}"])+' |')
    lines.extend(['','## Kiểm tra nhất quán và độ nhạy','',
        f"Có {report['coherence']['flagged_cases']} ca mang cờ đối chiếu chữ/lựa chọn, gồm {report['coherence']['flagged_primary_cases']} ca chính.",
        'Cờ không tự chứng minh người chấm sai; giữ phiếu gốc và báo riêng. Chữ O và số 0 không được nhập làm một.',
        'Phân tích dưới đây là hậu kiểm, tạm giữ bất định cả hai endpoint trên ca có cờ, không thay bảng chính.', '',
        '| Endpoint | A: TP/FP/FN/TN sau withholding | B3: TP/FP/FN/TN sau withholding |',
        '|---|---|---|'])
    for endpoint in ('pointwise','relation'):
        values=['/'.join(str(report['sensitivity']['results'][endpoint]['overall'][m]['confusion'][k])
                         for k in ('TP','FP','FN','TN')) for m in ('A','B3')]
        lines.append('| '+' | '.join([endpoint,*values])+' |')
    lines.extend(['', 'CI/p-value chưa được cấp: chỉ 3 ID primary và một người chấm; không coi field/view/reader là cụm độc lập.',
        'Precision có điều kiện trên ca đã có nhãn khác tỷ lệ lỗi đã ghi nhận trên toàn bộ cảnh báo. Không ngoại suy recall quần thể.',
        'Chi tiết case giữ riêng dưới local; không xuất transcript hoặc ghi chú người chấm vào báo cáo công khai.', ''])
    return '\n'.join(lines)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--submission',type=Path,required=True)
    parser.add_argument('--destination',type=Path,required=True)
    args=parser.parse_args()
    dest=args.destination.resolve()
    if not dest.is_relative_to(EXECUTION.resolve()) or dest==EXECUTION.resolve():
        raise ValueError('Use a new analysis file namespace under master_01')
    report,details=from_sealed(args.submission)
    save_new(dest/'analysis.json',report)
    with (dest/'analysis.md').open('x',encoding='utf-8') as stream:stream.write(markdown(report))
    save_new(PRIVATE/('ifv_analysis_'+report['export_snapshot'][:16]+'.json'),details)
    print(json.dumps(dict(status='DESCRIPTIVE_POSTREVIEW_ANALYSIS',reviewed=report['reviewed'],
        flagged_cases=report['coherence']['flagged_cases'],model_calls=0)))
