"""Generate reviewable reports only from complete audited experiments."""
import json
import gzip
import statistics
from pathlib import Path

from research.benchmark import save,digest
from research.recovery_study import OUT


def read(name):return json.loads((OUT/name).read_text(encoding='utf-8'))
def pct(x):return '—' if x is None else f'{100*x:.2f}'
def num(x):return '—' if x is None else f'{x:.3f}'


def field_summary(rows):
    fields=[f for r in rows for f in r['score']['fields']]
    n=len(fields);chars=sum(f['truth_length'] for f in fields)
    if not n:return 0,None,None
    return n,sum(f['exact'] for f in fields)/max(n,1),sum(f['edit_distance'] for f in fields)/max(chars,1)


def main():
    audit=read('independent_audit.json');summary=read('summary.json');models=read('selector_models.json')
    repeat=read('repeat_audit.json');data=read('dataset_card.json');online=read('online_traces.json')
    legacy=read('legacy_panel.json');paired=read('paired_bootstrap.json');schema=read('canonical_semantic_summary.json')
    visible=read('visible_transcription_summary.json');truncation=read('truncation_diagnostics.json')
    execution=read('execution.json');validation=read('validation.json')
    external=read('up_external.json');stress=read('layout_stress.json');alphabet=read('alphabet_coverage.json')
    target_coverage=read('target_coverage.json')
    environment=read('environment.json')
    panel_ids=set(read('manifest.json')['panel_uids'])
    with gzip.open(OUT/'per_image.jsonl.gz','rt') as stream:
        native_panel=[r for r in map(json.loads,stream) if r['repeat']==1 and r['uid'] in panel_ids and r['policy']=='completion']
    test=[r for r in summary if r['role']=='test'];latin='rapid_latin_v5'
    primary=models['selectors'][latin]['primary_method']
    lines=['# Nghiên cứu V4: phục hồi giấy tờ, benchmark và web localhost','',
        '**Kết quả thực nghiệm; không phải xác nhận bài đã được CORE B chấp nhận.** '
        'Bản mentor và các kết quả cũ được giữ nguyên. Tất cả phương án, kể cả phương án thua baseline, đều được công bố.','',
        '## Phạm vi mới','',
        f'- **{data["images"]} ảnh / {data["identities"]} document ID**, gồm 360 ảnh SPECIMEN mới từ 90 ID '
        'và 180 biến thể của 60 ID MIDV chọn thêm. SPECIMEN không phải CCCD thật hoặc 90 người thật.',
        '- Tách **40 ID development, 30 calibration, 80 test**. Không có ID hoặc ảnh byte-identical đi qua nhiều role. '
        '30 ID SPECIMEN test thuộc hai cấu hình font/thứ tự trường chưa dùng ở development. '
        'Sáu mã cấu hình gốc chỉ tạo bốn nhóm ngôn ngữ/font/thứ tự; 0/2 và 1/3 dùng chung vị trí. '
        'Không diễn giải chúng thành sáu layout không gian độc lập.',
        '- Một lượt đủ 540 ca và hai lượt mới trên cùng 24 ca khác ID: **588 lượt inference**, không phải ba lượt đủ 540 ảnh. '
        'Các lần lặp không tạo thêm ID độc lập.',
        f'- Thời gian toàn đợt inference: **{execution["elapsed_seconds"]/60:.2f} phút**. '
        'Đây là tổng chi phí thử tất cả view/reader, không phải thời gian một yêu cầu camera.',
        '- FastViT-SA24 và LCNet100; RapidOCR chính thức với PP-OCRv4 và reader Latin PP-OCRv5. '
        'Pipeline Latin dùng detector PP-OCRv4, không gọi nó là nguyên hệ thống PP-OCRv5 mới nhất. '
        'Không tạo venv/cài dependency vào môi trường hiện tại.',
        '- Baseline thêm: raw, strict, completion +5%, bbox, contour, text deskew; selector confidence, ridge, boosted stumps '
        'và cascade có tối đa một fallback. Hyperparameter/cấu trúc chọn bằng grouped CV trên development.',
        '- MIDV xuất hiện trong dữ liệu/ảnh minh họa huấn luyện của tác giả; không tuyên bố các ảnh MIDV chọn thêm là unseen-pretraining. '
        'Nguồn SPECIMEN được tạo mới, nhưng chưa có bộ camera thực mới độc lập.',
        '- [Dataset card](DATASET_CARD_V4.md), [giao thức](RESEARCH_V4_PROTOCOL.md), '
        '[bổ sung chấm trước test](RECOVERY_EVALUATION_ADDENDUM.md), [prior art/baseline](RESEARCH_V4_RELATED_WORK.md).','',
        f'Máy đo: **{environment["cpu"]}**, {environment["logical_processors"]} logical processors, '
        f'{environment["ram_bytes"]/1024**3:.2f} GiB RAM, Windows / Python {environment["python"]}. '
        'ONNX CPU, 2 thread/session; máy desktop không dành riêng CPU. '
        '[Phiên bản thư viện và máy](results/recovery_v4/environment.json).','',
        '## Kết quả chính trên ID test','',
        f'Cascade chính cho Latin là **{primary}**, chọn từ development trước khi chấm test. '
        'Field exact dưới đây yêu cầu đúng toàn bộ trường còn nhìn thấy đầy đủ; trường bị bỏ sót/ảnh bị từ chối tính sai. '
        'Không dùng GT để cắt chữ đưa vào OCR. GT chỉ ghép/chấm sau inference.','',
        '| Nguồn | Phương án | Field exact (%) | CER micro | Wall TB (s) | Giữ lại (%) |',
        '|---|---|---:|---:|---:|---:|']
    for source in ('authored_specimen','midv2020_derived'):
        for method in ('raw','completion','bbox','lcnet','max_confidence','allviews_ridge','allviews_stumps','cascade_ridge','cascade_stumps'):
            r=next(r for r in test if r['source']==source and r['reader']==latin and r['method']==method)
            lines.append(f'| {source} | {method} | {pct(r["field_exact"])} | {num(r["micro_cer"])} | {num(r["mean_wall_seconds"])} | {pct(r["retention"])} |')
    lines.extend(['','Wall của các selector được **tái dựng từ stage đã đo**, dùng cache raster trùng trong cùng ca và bỏ qua overhead selector. '
        'Đó không phải thời gian request online. Bảng online thật ở dưới. Native retention là gate hình học; selector retention '
        'có thêm ngưỡng confidence lấy từ calibration với mục tiêu 80%. Mục tiêu này không bảo đảm 80% hoặc độ an toàn ở test.','',
        '### Đối chiếu với completion theo physical ID','',
        'Bootstrap 2.000 lần theo document ID; trung bình field trong ảnh rồi ảnh trong ID. '
        'Vì vậy delta không nhất thiết bằng chênh lệch pooled-field ở bảng trên. CI thăm dò, không điều chỉnh nhiều phép so sánh.','',
        '| Reader | Nguồn | Cascade đã khóa | Số ID | Delta exact (điểm %) | CI95% |',
        '|---|---|---|---:|---:|---:|'])
    decisions=[]
    for reader,setting in models['selectors'].items():
        for source in ('authored_specimen','midv2020_derived'):
            r=next(r for r in paired if r['reader']==reader and r['source']==source and r['method']==setting['primary_method'] and r['metric']=='exact')
            lo,hi=r['ci95'];lines.append(f'| {reader} | {source} | {r["method"]} | {r["physical_ids"]} | {100*r["mean_delta"]:+.2f} | [{100*lo:.2f}; {100*hi:.2f}] |')
            decisions.append(r)
    positive=[r for r in decisions if r['mean_delta']>0 and r['ci95'][0]>0]
    identical_accuracy=all(r['mean_delta']==0 for r in decisions)
    lines.extend(['',f'Có **{len(positive)}/{len(decisions)}** đối chiếu cascade chính cho CI exact hoàn toàn trên 0. '
        'Không suy từ một tập/reader thắng sang ưu thế phổ quát. Các cấu trúc còn lại và mọi số liệu native nằm trong '
        '[summary CSV](results/recovery_v4/summary.csv) và [bootstrap](results/recovery_v4/paired_bootstrap.json).','',
        '## Pipeline online chạy thật','',
        'Cùng 24 ảnh panel, 3 lượt fresh, so cascade Latin với completion; thứ tự hai phương án được đối trọng. '
        '144 yêu cầu pipeline, không dùng lại OCR giữa yêu cầu. Các role trong panel gồm development/calibration/test; '
        'đây là kiểm chứng triển khai/timing, không phải thêm 24 test ID mới. Model cùng resident, desktop CPU không độc quyền.','',
        '| Nguồn | Phương án | Mean ± SD giữa 3 lượt (s/ảnh) | OCR TB / yêu cầu | Giữ lại thực tế (%) |',
        '|---|---|---:|---:|---:|'])
    for source in ('authored_specimen','midv2020_derived'):
        for method in ('fixed_completion','primary_cascade'):
            chosen=[r for r in online['rows'] if r['source']==source and r['method']==method]
            means=[statistics.mean(r['actual_wall'] for r in chosen if r['repeat']==i) for i in (1,2,3)]
            lines.append(f'| {source} | {method} | {statistics.mean(means):.3f} ± {statistics.stdev(means):.3f} | '
                f'{statistics.mean(r["ocr_executions"] for r in chosen):.2f} | {pct(statistics.mean(not r["review_recommended"] for r in chosen))} |')
    lines.extend(['',f'Output online so với lựa chọn từ exhaustive candidates: **{online["output_mismatches"]} mismatch**; '
        f'tối đa **{online["maximum_ocr_executions"]} OCR execution/yêu cầu**. '
        f'Gate review online khác gate exhaustive ở **{online["review_gate_differences"]}** yêu cầu: '
        'online bổ sung cờ review khi output rỗng, kể cả khi threshold bằng0. '
        'Wall này đo phần dự đoán, chưa gồm HTTP transfer/decode. Web còn báo thời gian xử lý request có decode/encode/cold load. '
        '[Actual traces](results/recovery_v4/online_traces.json).','',
        '## OCR reader đối chứng trên cùng panel','',
        'Legacy chỉ chạy 24 ảnh, không phải toàn bộ 540. EasyOCR/VietOCR dùng chung CRAFT; '
        'VietOCR màu lấy crop màu từ vùng do detector dự đoán, chọn 0/180 bằng confidence. Không dùng crop GT.','',
        '| Nguồn | Reader / pipeline cùng panel | Field exact (%) | CER micro | Wall TB (s) |',
        '|---|---|---:|---:|---:|'])
    for source in ('authored_specimen','midv2020_derived'):
        for reader in ('rapid_v4','rapid_latin_v5','easyocr_en','vietocr','vietocr_color'):
            if reader.startswith('rapid'):
                selected=[dict(r,wall=r['total_wall']) for r in native_panel if r['source']==source and r['engine']==reader]
            else:selected=[r for r in legacy['rows'] if r['source']==source and r['reader']==reader]
            fields=[f for r in selected for f in r['score']['fields']];chars=sum(f['truth_length'] for f in fields)
            exact=sum(f['exact'] for f in fields)/max(len(fields),1);cer=sum(f['edit_distance'] for f in fields)/max(chars,1)
            lines.append(f'| {source} | {reader} | {pct(exact)} | {num(cer)} | {statistics.mean(r["wall"] for r in selected):.3f} |')
    lines.extend(['','Không đối chiếu số legacy panel trực tiếp với bảng toàn bộ test để tuyên bố reader nào thắng. '
        'Dùng bảng panel ghép cùng ảnh trong artifact khi so reader; các reader không độc lập hoàn toàn vì chia sẻ detector.','',
        '## KIE có schema và chữ bị cắt','',
        'Phép chấm này chỉ áp dụng SPECIMEN có nhãn trường ngữ nghĩa, không dùng GT box để gán key khi suy luận. '
        'Extractor đổi ngày thành ISO và gender thành Nam/Nữ. Vì vậy báo cả literal string và canonical schema '
        'đã công bố trước khi xem test; đây không phải cải thiện OCR bằng sửa chuỗi theo GT.','',
        '| Reader | Phương án | KIE literal (%) | KIE canonical (%) | OCR đúng nhưng sai gán trường |',
        '|---|---|---:|---:|---:|'])
    for r in schema:
        if r['role']=='test' and r['method'] in ('raw','completion','bbox',models['selectors'][r['reader']]['primary_method']):
            lines.append(f'| {r["reader"]} | {r["method"]} | {pct(r["literal_exact"])} | {pct(r["canonical_exact"])} | {r["transcription_correct_semantic_wrong"]} |')
    lines.extend(['','Ảnh field-clip có thể không còn trường nguyên vẹn để chấm primary. Chúng vẫn được giữ trong chi phí/review. '
        'Secondary dưới đây so với substring gồm ký tự có ≥99,5% diện tích support rectangle nằm trong khung. '
        'Đây là proxy hình học từ font, không phải nhãn đọc được do con người xác nhận.','',
        '| Latin, chỉ field bị cắt | Số trường | Visible-reference exact (%) | Visible CER |',
        '|---|---:|---:|---:|'])
    for r in visible:
        if r['reader']==latin and r['scope']=='partially_captured_fields' and r['method'] in ('raw','completion','bbox',primary):
            lines.append(f'| {r["method"]} | {r["fields"]} | {pct(r["exact"])} | {num(r["micro_cer"])} |')
    lines.extend(['','### Mẫu không có target nguyên vẹn','',
        '| Nguồn / capture, chỉ test | Ảnh | Ảnh không có trường đủ điều kiện | Trường đủ điều kiện |',
        '|---|---:|---:|---:|'])
    for r in target_coverage:
        lines.append(f'| {r["source"]} / {r["capture"]} | {r["images"]} | {r["zero_eligible_target_images"]} | {r["eligible_fields"]} |')
    lines.extend(['','Các ảnh không có target không đóng góp mẫu số primary OCR; vẫn nằm trong mẫu số latency/review. '
        'Đây là giới hạn cần đọc cùng secondary visible metric, không phải ảnh được OCR chính xác 100%.','',
        '### Review đối với ảnh bị cắt trường','',
        '| Nguồn / Latin | Phương án | Ảnh giữ lại có field bị cắt (%) | Recall cờ review cho ảnh bị cắt (%) |',
        '|---|---|---:|---:|'])
    for r in truncation:
        if r['reader']==latin and r['method'] in ('fixed_completion',primary):
            lines.append(f'| {r["source"]} | {r["method"]} | {pct(r["retained_partial_fraction"])} | {pct(r["truncation_review_recall"])} |')
    lines.extend(['','Không diễn giải visible-field exact cao hoặc confidence cao là giấy tờ đầy đủ/hợp lệ. '
        'Ảnh/text còn có thể sai hoặc bị thiếu; người dùng phải kiểm tra. Web không duyệt eKYC hoặc xác thực chân dung.','',
        '## Kiểm chứng chuyển miền, không fit lại','',
        '**MIDV-UP:** 24 ảnh tác giả chụp thực, 24 ID, bốn loại giấy tờ bổ sung và hai nhóm điện thoại; '
        'hai lượt fresh, ba phương án = 144 yêu cầu. Mẫu nhỏ chọn hash cố định và không chứng minh unseen-pretraining. '
        'Latin reader chưa hỗ trợ toàn bộ tiếng Urdu/Persian. Bảng tính lượt 1, lượt 2 chỉ kiểm độ lặp lại.','',
        '| Tập / phương án | Số trường đủ điều kiện | Field exact (%) | CER micro | Wall thật TB (s) | Giữ lại (%) |',
        '|---|---:|---:|---:|---:|---:|'])
    for dataset,label in ((external,'MIDV-UP'),(stress,'Spatial stress')):
        for method in ('raw','fixed_completion','primary_cascade'):
            selected=[r for r in dataset['rows'] if r['repeat']==1 and r['method']==method]
            n,exact,cer=field_summary(selected)
            lines.append(f'| {label} / {method} | {n} | {pct(exact)} | {num(cer)} | '
                f'{statistics.mean(r["actual_wall"] for r in selected):.3f} | '
                f'{pct(statistics.mean(not r["review_recommended"] for r in selected))} |')
    lines.extend(['',
        '**Spatial stress:** 80 ảnh SPECIMEN từ 20 ID mới với hai cấu trúc hai cột/thẻ dọc. '
        'Một lượt đủ 80 ảnh và hai lượt mới trên cùng 8 ảnh panel: 288 yêu cầu cho ba phương án. '
        'Chỉ stress test mô hình đã khóa; không dùng để thay thế tập test gốc hoặc chọn lại threshold. '
        'Không phải 80 ảnh chụp camera thực. KIE của raw không chấm trong supplement này.','',
        '| Spatial layout | Phương án | Trường | Field exact (%) | CER |',
        '|---|---|---:|---:|---:|'])
    for layout in ('two_column','portrait'):
        for method in ('raw','fixed_completion','primary_cascade'):
            selected=[r for r in stress['rows'] if r['repeat']==1 and r['layout']==layout and r['method']==method]
            n,exact,cer=field_summary(selected)
            lines.append(f'| {layout} | {method} | {n} | {pct(exact)} | {num(cer)} |')
    lines.extend(['','| Spatial stress | Canonical KIE (%) | Ảnh giữ lại có field bị cắt (%) |',
        '|---|---:|---:|'])
    for method in ('fixed_completion','primary_cascade'):
        selected=[r for r in stress['rows'] if r['repeat']==1 and r['method']==method]
        n=sum(r['semantic_score']['eligible_fields'] for r in selected)
        exact=sum(r['semantic_score']['canonical_exact'] for r in selected)/max(n,1)
        kept=[r for r in selected if not r['review_recommended']]
        fraction=sum(r['geometrically_partial'] for r in kept)/max(len(kept),1)
        lines.append(f'| {method} | {pct(exact)} | {pct(fraction)} |')
    coverage=external['coverage']
    lines.extend(['',f'MIDV-UP có **{sum(r["unsupported_alphabet_fields"] for r in coverage)} / '
        f'{sum(r["eligible_fields"] for r in coverage)}** trường đủ predicate gốc nhưng chứa ký tự ngoài alphabet reader. '
        'Không âm thầm loại các trường khó sau khi xem kết quả. Số tương ứng theo nguồn/reader chính:','',
        '| Reader / nguồn test | Trường hỗ trợ toàn bộ alphabet / tổng |','|---|---:|'])
    for r in alphabet:lines.append(f'| {r["reader"]} / {r["source"]} | {r["fully_supported_fields"]} / {r["fields"]} |')
    lines.extend(['','[MIDV-UP traces](results/recovery_v4/up_external.json), '
        '[spatial stress traces](results/recovery_v4/layout_stress.json). Tỷ lệ giữ của raw chỉ loại trường hợp không có chữ, '
        'không được xem là cùng gate calibration với cascade/completion.','',
        '## Audit, kiểm thử và lịch sử','',
        f'- **{audit["native_rows_rescored"]} native rows chấm lại**, **{audit["selector_decisions_replayed"]} quyết định selector replay**, '
        f'**{audit["public_rows"]} hàng công khai**. Sai khác score/publication/wall/CPU: 0.',
        f'- Các kiểm chứng online/legacy/ngoài miền được chấm lại: {audit["additional_validation"]}.',
        f'- Audit lặp supplement: `{audit["supplement_repeats"]}`. Không đếm ảnh lặp thành ID mới.',
        f'- Panel inference 24 ảnh: {repeat["prediction_mismatches"]} canonical prediction mismatch, '
        f'{repeat["score_mismatches"]} field-score mismatch qua 3 lượt. Không gọi số hàng là số inference độc lập.',
        f'- Test cuối: **{validation["python_tests"]} Python**, **{validation["frontend_tests"]} frontend** đạt. '
        'Test manifest raw của mentor được loại riêng trong worktree; dữ liệu nghiên cứu được audit hash. '
        'Log và XML được lưu, không cài package để che cảnh báo dependency.',
        '- Adapter mới thực thi đúng các hàm số học tác giả đã ghim; parity 8 ảnh development và case tied peaks được kiểm. '
        'Chưa kiểm toàn bộ package/các backend/center-crop. Adapter cũ và kết quả V2 được giữ nguyên, không sửa số lịch sử.',
        '- [Independent audit](results/recovery_v4/independent_audit.json), [model lock](results/recovery_v4/selector_lock.json), '
        '[validation](results/recovery_v4/validation.json), [nguồn dataset](results/recovery_v4/dataset_source_documents.json).','',
        '## Kết luận về đóng góp paper','',
        'Đã bổ sung dataset/giao thức, nhiều baseline/cấu trúc, chấm KIE và visible references, '
        'đo online thực tế, audit và web chạy thật. Đây là các artifact có thể kiểm tra được; '
        'không đồng nghĩa một regressor/cascade quen thuộc trở thành thuật toán mới.','',
        f'Trong bốn đối chiếu nguồn–reader của cascade chính, {len(positive)} có CI accuracy hoàn toàn dương. '
        +('Cascade cho độ chính xác bằng completion trong cả bốn đối chiếu. Kết quả này không hỗ trợ claim thuật toán mới vượt baseline. '
          if identical_accuracy else 'Mức cải thiện phải được giới hạn đúng từng nguồn/reader và CI được công bố. ')+
        'Đọc thời gian thực tế và review/truncation để đánh giá ứng dụng. Hướng paper phù hợp để xem xét tiếp là '
        'đánh giá/benchmark có phạm vi rõ; số lượng test và một website chạy được không tự tạo ra novelty.',
        '', 'Các hạn chế chưa thể xóa bằng unit test: ít layout/font/camera, nguồn tổng hợp có khoảng cách thực tế, '
        'MIDV có thể đã thấy trong pretraining, chưa có annotation legibility độc lập và chưa chạy mọi neural rectifier/market API. '
        'Cần dữ liệu camera mới có quyền sử dụng và đối chiếu closest-prior chặt trước quyết định nộp CORE B. '
        'Không có phép kiểm nào bảo đảm quyết định chấp nhận của phản biện.','',
        '## Chạy web','',
        'Từ worktree nghiên cứu chạy `powershell -NoProfile -ExecutionPolicy Bypass -File .\\research\\start-research.ps1`, '
        'mở **http://127.0.0.1:8001/** trong Chrome/Edge. Camera live → preview → xác nhận → OCR → form có thể sửa. '
        'Ảnh giữ nguyên độ phân giải gốc khi gửi; không ghi ảnh/text camera ra file hoặc gửi tới API ngoài. '
        'Đây là nghiên cứu document processing, tách khỏi mentor8000.','',
        'Biểu đồ: [test accuracy](results/recovery_v4/test_accuracy.png), [trace costs](results/recovery_v4/trace_cost.png).'])
    report=Path('research/RECOVERY_RESULTS_VI.md');report.write_text('\n'.join(lines)+'\n',encoding='utf-8',newline='\n')
    manuscript=['# Partial Identity-Document Capture: Visibility, Budgeted OCR Views and Auditable Evaluation','',
        'Working manuscript. Venue decision pending; no claim of accepted CORE B status.','',
        '## Abstract','',
        'Mobile document systems can lose text when four-corner localization fails, yet forwarding or completing the card '
        'can be stronger than complex recovery. We investigate visibility-aware evaluation and bounded OCR view selection '
        'on540 captures from150 document IDs:90 newly authored bilingual specimen identities and60 additional MIDV identities. '
        'Development, calibration and test IDs are disjoint, with an additional font/field-order shift. Six original '
        'configuration IDs represent four style groups, not six independent spatial designs. We compare seven geometric '
        'views, two CPU OCR alternatives, naive confidence selection, linear/stump predictors and bounded cascades. '
        'We distinguish fully visible-field transcription, conservative visible-substring transcription, semantic schema '
        'extraction and review behaviour, and verify deployment using fresh online traces. All outcomes, code/model/input '
        'hashes, negative results and numeric rows are released. The study does not establish document authenticity or PAD.','',
        '## 1. Research question and contribution boundary','',
        'When does completion or rereading preserve more useful text, and when is additional computation justified? '
        'The contribution under evaluation is the task/dataset/evaluation contract and an auditable implementation. '
        'Half-plane geometry, ridge regression, boosted stumps and cascades are established techniques. '
        'Algorithmic superiority must be supported by the held-out comparisons below, not presumed from a method name.','',
        '## 2. Related work','',
        '[DocAttentionRect](https://bmvc2025.bmva.org/proceedings/39/) and '
        '[ArbDR](https://github.com/chaoyunwang/ArbDR) already consider difficult document geometry; '
        '[DocRes](https://openaccess.thecvf.com/content/CVPR2024/html/Zhang_DocRes_A_Generalist_Model_Toward_Unifying_Document_Image_Restoration_Tasks_CVPR_2024_paper.html) '
        'studies general restoration. Missing boundaries alone are therefore not a new task. '
        '[MIDV-2020](https://arxiv.org/abs/2107.00396), '
        '[SIDTD](https://www.nature.com/articles/s41597-024-04160-9) and '
        '[DocXPand](https://github.com/quicksign/docxpand) also precede our generated specimen artifact.','',
        '[Kim, Han and Yang (IJDAR2026)](https://link.springer.com/article/10.1007/s10032-026-00620-7) '
        'separate visible/intended transcripts and study confidence-based OCR/VLM routing. We do not claim either '
        'idea as new. Our narrower setting concerns partial ID capture, spatially matched field transcription, '
        'semantic extraction, non-generative geometric rereading and measured CPU/review behaviour. Geometric '
        'character support differs materially from their human-legibility reference; neither label should be substituted '
        'for the other. The companion prior-work table distinguishes measured baselines from papers cited only as context.','',
        '## 3. Dataset and protocol','',
        'See DATASET_CARD_V4.md and RESEARCH_V4_PROTOCOL.md.540 cases;40/30/80 document IDs by role; '
        'two additional fresh24-case passes. Character support is a typography-derived geometric proxy, not human legibility. '
        'Synthetic examples and new-to-study MIDV images must remain separately labelled. Source training overlap is disclosed.','',
        'Separate frozen-model supplements comprise24 MIDV-UP physical photographs from four templates/two phones '
        'and80 authored captures from20 additional IDs with two-column/portrait layouts. They do not alter the primary '
        'fit, calibration or test results. Their sample size and language limitations are reported explicitly.','',
        '## 4. Methods','',
        'Pin two corner-localizer backbones and official CPU OCR code/weights. Generate seven prediction-only views. '
        'Fit competing view-quality and fallback-gain models with grouped development folds. Calibration selects confidence '
        'thresholds for80% target retention without a distribution-free safety claim. The primary cascade starts with '
        'padded completion and executes at most one alternative OCR view. No GT/template value lookup enters prediction.','',
        '### 4.1 Prediction and budget','',
        'Let x be the captured raster, v0 the completion view and Yv the OCR predictions for a candidate view. '
        'A regressor predicts the field-exact gain of a fallback v from features of Yv0 plus a one-hot view code. '
        'At inference it has no ground-truth transcript, document-type ID or annotated field locations. '
        'Features comprise raster size/aspect, observed corner count, text/confidence/edge statistics and view indicators.','',
        '`v* = argmax_v [ predicted_gain(features(Yv0), v) - 0.002 * development_mean_cost(v) ]`','',
        'Only if this quantity exceeds0.02 is v* executed; otherwise the completion output is returned. '
        'An identical raster skips duplicate OCR, while view construction can still incur overhead. The selected fallback is returned directly, without a third '
        'OCR pass or GT-based reranking. Ridge strengths0.1/1/10 and8/24 boosted-stump rounds are compared '
        'in four physical-ID-grouped development folds. The primary is the better development-CV cascade family. '
        'All-view ridge/stump and maximum-confidence alternatives are separate, costlier comparators.','',
        '### 4.2 Metrics and inference boundary','',
        'Primary field targets have valid Latin/alphanumeric text and at least99.5% geometric visibility. '
        'OCR always receives prediction-derived images, never reference field crops. Only the evaluator maps '
        'predicted boxes into source coordinates and assigns them to a reference field when prediction coverage '
        'is at least0.5 and IoU at least0.01. Reading order is evaluated in the reference field coordinate frame. '
        'Strings use NFC, uppercase and collapsed whitespace. CER micro is summed Levenshtein distance divided '
        'by summed reference length; it is not clipped or a per-image macro mean. Missing output counts as errors.','',
        'Semantic KIE instead compares predicted field keys and values without oracle box-to-key assignment. '
        'Dates/gender receive the documented canonical schema; raw literal results are retained. A secondary '
        'authored-data score evaluates surviving character-reference substrings. No-target images remain in '
        'the latency/review denominator. Confidence review is distinct from OCR output availability and from '
        'geometric truncation; it does not certify document completeness. Exploratory intervals use2000 '
        'physical-ID bootstrap resamples without multiplicity correction.','',
        '## 5. Results','',
        'The following primary choices were locked on development before test scoring. Values are pooled test-field exact; '
        'trace costs and actual online timings are distinct.','',
        '| Source | Latin method | Field exact | Trace wall seconds | Retention |','|---|---|---:|---:|---:|']
    for r in test:
        if r['reader']==latin and r['method'] in ('completion',primary):
            manuscript.append(f'| {r["source"]} | {r["method"]} | {pct(r["field_exact"])}% | {num(r["mean_wall_seconds"])} | {pct(r["retention"])}% |')
    manuscript.extend(['','All methods, paired ID intervals, semantic/visibility diagnostics and fresh online timings are '
        'reported in RECOVERY_RESULTS_VI.md and machine-readable artifacts. Do not replace these by best-test-only tables.','',
        ('The locked primary cascades match completion accuracy in all four source/reader comparisons; algorithmic '
         'superiority is not supported. The learned routing result is retained as a negative experiment.'
         if identical_accuracy else 'Interpret each source/reader comparison with its paired interval; do not generalize one positive result.'),'',
        '## 6. Limitations and submission decision','',
        'The dataset contains few layouts/fonts and no newly collected real camera population. MIDV pretraining exposure '
        'is not excluded. Synthetic visibility differs from human legibility. The legacy reader check is panel-only and '
        'commercial systems are not tested. Classifier-based review does not verify full identity-document validity. '
        'A submission requires a convincing closest-prior distinction and adequate results across the declared trade-offs. '
        'Positive exploratory intervals alone cannot guarantee novelty, practical safety or conference acceptance.','',
        '## Reproducibility and ethical scope','',
        'Report exact code/model/data signatures, all ID roles, inference/repetition counts, source licences, processing '
        'settings and measured-versus-reconstructed times. Keep personal camera content local and memory-only. '
        'Publish only numerical results and clearly marked authored specimen examples. Mentor eKYC runtime is unchanged.'])
    draft=Path('research/MANUSCRIPT_DRAFT.md');draft.write_text('\n'.join(manuscript)+'\n',encoding='utf-8',newline='\n')
    save(OUT/'report_provenance.json',dict(code_sha256=digest(__file__),report_sha256=digest(report),draft_sha256=digest(draft),
        summary_sha256=digest(OUT/'summary.json'),model_sha256=digest(OUT/'selector_models.json'),all_methods_retained=True))
    print('RECOVERY_REPORTS_WRITTEN',report,draft,flush=True)


if __name__=='__main__':main()
