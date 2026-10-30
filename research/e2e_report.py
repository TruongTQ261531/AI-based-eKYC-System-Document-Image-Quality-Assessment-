"""Generate a Vietnamese report from complete audited experiment outputs."""
import json
from pathlib import Path

from research.benchmark import save,digest

ROOT=Path('research/results/e2e_ocr_v2')


def pct(value):return f'{100*value:.2f}' if value is not None else '—'
def number(value):return f'{value:.3f}' if value is not None else '—'


def main():
    manifest=json.loads((ROOT/'manifest.json').read_text());audit=json.loads((ROOT/'audit.json').read_text())
    repeat=json.loads((ROOT/'repeat_audit.json').read_text());init=json.loads((ROOT/'initialization.json').read_text())
    full=[r for r in json.loads((ROOT/'summary.json').read_text()) if r['repeat']==1]
    failures=json.loads((ROOT/'failure_breakdown.json').read_text());alphabet=json.loads((ROOT/'alphabet_coverage.json').read_text())
    paired=json.loads((ROOT/'paired_bootstrap.json').read_text())
    mechanism=json.loads((ROOT/'mechanism_bootstrap.json').read_text())
    matched=json.loads((ROOT/'matched_repeat_means.json').read_text())
    visibility=json.loads((ROOT/'corner_visibility.json').read_text())['ground_truth_visible_corner_counts']
    validation=json.loads((ROOT/'validation.json').read_text())
    execution=json.loads((ROOT/'execution.json').read_text())
    paragraphs=['# Benchmark OCR đầu cuối: kết quả thực nghiệm 30/10/2026','',
        'Đây là nghiên cứu riêng trên nhánh `research/document-recovery-core-b`. Runtime mentor được giữ nguyên. '
        'Kết quả đo OCR từ pixel ảnh và vùng chữ do model tự phát hiện; không dùng tọa độ GT để cắt chữ đưa vào model. '
        'Nhãn chuẩn chỉ dùng chấm sau inference. Đây là **spatial field transcription**, chưa phải semantic KIE '
        'hay tự gán nhãn họ tên/địa chỉ cho mọi loại giấy tờ.','',
        '## Phạm vi và nguồn gốc','',
        '- Lượt đầy đủ: **161 ảnh**, gồm91 ca neural trả về ba góc,50 ca đủ bốn góc chọn bằng hash và20 ảnh MIDV-2020.',
        '- Có1.643 trường Latin nhìn thấy đầy đủ để chấm:910/489/244 theo ba nhóm. '
        '10 trường bị cắt và193 trường ngoài phạm vi/không hợp lệ được đếm riêng; không bỏ ảnh tương ứng khỏi latency/routing.',
        '- Hai lượt tiếp theo chạy inference mới trên cùng **32 ảnh** (24/4/4), với primary IDs khác nhau trong panel. '
        'Tổng225 lượt ảnh, **không phải ba lượt đầy đủ161 ảnh**. Accuracy chính dùng lượt1; SD lặp chỉ dùng cùng panel32.',
        '- Mẫu chọn có chủ đích theo số góc dự đoán, không đại diện ngẫu nhiên mọi ảnh MIDV. '
        'Ba góc model phát hiện không đồng nghĩa GT chỉ có ba góc nhìn thấy.',
        f'- Trong91 ca neural ba góc, GT có1/2/3/4 góc trong khung tương ứng '
        f'{visibility["1"]}/{visibility["2"]}/{visibility["3"]}/{visibility["4"]} ảnh. '
        'Do đó không gọi cả91 ca là giấy tờ thật sự mất đúng một góc ngoài khung.',
        '- Sáu trọng số/config có nguồn và hash; EasyOCR kiểm MD5 registry tác giả, VietOCR/DocAligner kiểm SHA256 đã ghim. '
        'Không train, tạo venv, cài dependency hay tải model mới trong đợt này.',
        '- [Giao thức](E2E_OCR_PROTOCOL.md), [nguồn và giới hạn đo](E2E_OCR_PROVENANCE.md), '
        '[manifest](results/e2e_ocr_v2/manifest.json), [ảnh/target audit](results/e2e_ocr_v2/sample_audit.json).','',
        '## Sáu phương án','',
        '`raw_fullframe` giữ ảnh gốc, không cần localizer. `neural_strict` chỉ đọc khi có quad hợp lệ. '
        '`three_fullframe` thêm nhánh đưa nguyên ảnh ba góc đi tiếp. `three_support` dùng giao hai nửa mặt phẳng '
        'quan sát được, crop bbox và tô trắng ngoài polygon; `three_support_bbox` bỏ bước mask. '
        '`three_parallelogram05` hoàn thành hình bình hành, nới5% rồi warp. Nhánh bốn góc giống nhau giữa các policy neural.','',
        'CRAFT tìm vùng chữ thật trên mỗi ảnh đầu ra. Hai recognizer dùng cùng detector và normalization dòng grayscale; '
        'VietOCR chuyển các patch grayscale sang RGB. Vì vậy đây chưa phải so sánh nguyên trạng với đường color-crop '
        'của mentor. Nhận dạng thử0/180 độ bằng confidence của chính reader; không dùng GT chọn hướng.','']
    paragraphs.extend(['## Kết luận trực tiếp từ lượt đầy đủ','',
        'Đây là so sánh mô tả trên mẫu đã khóa, trước khi suy rộng sang dữ liệu/camera khác. '
        '“Đúng trường” yêu cầu khớp toàn bộ chuỗi đã normalize, không phải chỉ đúng vài ký tự.',''])
    for reader in ('easyocr_en','vietocr'):
        selected={r['policy']:r for r in full if r['engine']==reader and r['stratum']=='three_corners'}
        raw=selected['raw_fullframe'];support=selected['three_support'];bbox=selected['three_support_bbox'];parallel=selected['three_parallelogram05']
        paragraphs.append(f'- **{reader},91 ca ba góc:** raw {pct(raw["field_exact"])}%, '
            f'support {pct(support["field_exact"])}%, bbox {pct(bbox["field_exact"])}%, '
            f'parallelogram+5% {pct(parallel["field_exact"])}%. '
            f'Support − raw: {100*(support["field_exact"]-raw["field_exact"]):+.2f} điểm%; '
            f'support − parallelogram: {100*(support["field_exact"]-parallel["field_exact"]):+.2f} điểm%. '
            f'Wall support/parallelogram: {number(support["mean_wall_seconds"])}/{number(parallel["mean_wall_seconds"])} giây/ảnh.')
    paragraphs.extend(['',
        'Trong kết quả này, support crop có cải thiện so với raw, nhưng baseline hình bình hành nới5% '
        'đọc đúng nhiều trường hơn và nhanh hơn support với cả hai reader trên nhóm ba góc. '
        'Mask không tăng field exact tổng so với crop bbox. Vì vậy chưa có bằng chứng về ưu thế OCR/CPU '
        'riêng của support mask để làm đóng góp thuật toán chính. Không được đổi cách chấm hay bỏ baseline '
        'đang thắng để tạo novelty.','',
        'Mức exact tuyệt đối còn thấp trên tập khó này và chưa đo semantic KIE; kết quả không chứng minh '
        'hệ thống tự điền thông tin hoặc duyệt eKYC đáng tin cậy trên mọi giấy tờ. '
        'Các tỷ lệ routing chỉ nói ảnh được đưa đi đọc, không xác thực danh tính.',''])
    for stratum,title in (('primary','141 ảnh chính: toàn bộ trường mục tiêu'),('three_corners','91 ca ba góc dự đoán'),('external','20 ảnh ngoài')):
        paragraphs.extend(['## '+title,'','Field exact tính cả trường bị bỏ sót/ảnh bị từ chối là sai. CER không bị chặn ở1. '
            'Cột có điều kiện chỉ tính trường trong các ảnh được route. “Có vùng” nghĩa là có ít nhất một vùng text dự đoán được ghép vào field; không phải AP detector chuẩn.','',
            '| Reader | Policy | Field exact (%) | CER micro | Có vùng (%) | Route (%) | Exact trong ca route (%) | Wall TB/P95 (s) | CPU TB (s) |',
            '|---|---|---:|---:|---:|---:|---:|---:|---:|'])
        for r in full:
            if r['stratum']!=stratum:continue
            paragraphs.append(f'| {r["engine"]} | {r["policy"]} | {pct(r["field_exact"])} | {number(r["micro_cer"])} | '
                f'{pct(r["detection_coverage"])} | {pct(r["routed_fraction"])} | {pct(r["conditional_field_exact"])} | '
                f'{number(r["mean_wall_seconds"])}/{number(r["p95_wall_seconds"])} | {number(r["mean_cpu_seconds"])} |')
        paragraphs.append('')
    paragraphs.extend(['## Chạy lặp và audit','',
        f'- Tiến trình benchmark hoàn tất mã0; wall toàn bộ study {execution["elapsed_seconds"]/60:.2f} phút '
        '(không phải latency một ảnh/một reader). Không bỏ ca bất thường.',
        f'- Audit **{audit["image_checkpoints"]} checkpoint**, **{audit["public_rows"]} hàng ảnh-policy-reader**; '
        f'chấm lại từ output private:{audit["score_mismatches"]} sai khác, cộng stage timing:{audit["timing_sum_mismatches"]} sai khác.',
        f'- Toàn bộ hàng công khai khớp projection checkpoint; tính lại **{audit["summary_rows_recomputed"]}** hàng summary '
        'và kiểm hash prediction. Audit phát hiện lỗi lưu/xuất/tổng hợp; evaluator vẫn dùng cùng thuật toán chấm.',
        f'- Panel32 so cùng ảnh-policy-reader trong ba lượt: **{repeat["prediction_mismatches"]}** mismatch canonical prediction hash '
        '(text normalize, box làm tròn6 chữ số, không gồm confidence) và '
        f'**{repeat["field_score_mismatches"]}** mismatch score; không dùng cache OCR giữa các lượt.',
        f'- Có **{repeat["unique_localizer_calls"]}** lần localizer và **{repeat["unique_ocr_executions"]}** raster OCR thực sự khác nhau '
        'trong các đơn vị ảnh/lượt. Một OCR execution ở đây gồm một detector và tối đa hai reader; '
        'không được gọi số hàng kết quả là số inference độc lập.',
        '- Raster giống hệt trong cùng ảnh/lượt được chia sẻ, và cùng chi phí stage được tính cho mỗi policy tương đương. '
        'Các reader chạy nối tiếp, được báo như hai lựa chọn reader riêng; không cộng thời gian hai reader để gọi là latency một reader.',
        f'- Batch VietOCR kiểm trên{init["vietocr_batch_parity"]["synthetic_lines"]} dòng tổng hợp: '
        f'{init["vietocr_batch_parity"]["text_mismatches"]} khác text; confidence lệch tối đa '
        f'{init["vietocr_batch_parity"]["max_confidence_difference"]:.3g}. Đây không phải chứng minh parity cho mọi ảnh.',
        '- [Audit checkpoint](results/e2e_ocr_v2/audit.json), [repeat audit](results/e2e_ocr_v2/repeat_audit.json), '
        '[thống kê cùng panel](results/e2e_ocr_v2/matched_repeat_summary.json).','',
        f'- Kiểm thử cuối: **{validation["commands"][0]["tests"]} Python**, '
        f'**{validation["commands"][1]["passed"]} frontend** đều đạt. '
        'Bỏ riêng tests/test_manifest.py vì worktree không chứa manifest raw; nguồn ảnh benchmark đã được kiểm hash. '
        'Có một cảnh báo deprecation Starlette/httpx từ dependency sẵn có; không cài/thay dependency. '
        '[Validation](results/e2e_ocr_v2/validation.json), [Python log](results/e2e_ocr_v2/python_tests.txt), '
        '[frontend log](results/e2e_ocr_v2/frontend_tests.txt).','',
        '### Biến thiên thời gian trên cùng panel','',
        'Bảng này chỉ dùng28 ảnh chính của panel (24 ba góc +4 control) trong cả ba lượt; '
        'không lấy SD giữa tập161 và tập32. Mean ± SD là giữa ba trung bình lượt, không phải CI hay SD từng ảnh.','',
        '| Reader | Policy | Wall trung bình ± SD lượt (s/ảnh) | P95 trung bình ± SD lượt (s) |',
        '|---|---|---:|---:|'])
    for r in matched:
        if r['stratum']!='primary':continue
        wall=r['mean_wall_seconds'];tail=r['p95_wall_seconds']
        paragraphs.append(f'| {r["engine"]} | {r["policy"]} | {number(wall["mean"])} ± {number(wall["repeat_sd"])} | '
                          f'{number(tail["mean"])} ± {number(tail["repeat_sd"])} |')
    paragraphs.extend(['',
        'Thời gian biến thiên rõ giữa các lượt dù output ổn định. Đây là desktop CPU dùng chung, '
        'model cùng resident và thứ tự policy cố định; chưa đối trọng thứ tự/cache/nhiệt độ. '
        'So sánh thời gian áp dụng cho cấu hình đo này, chưa chứng minh ưu thế throughput hoặc latency ổn định khi triển khai.','',
        '## Sai số và giới hạn ngôn ngữ','',
        '| Reader | Policy | Review hình học (ảnh) | Route nhưng không có text (ảnh) | Field không ghép được vùng | Field có vùng nhưng sai |',
        '|---|---|---:|---:|---:|---:|'])
    for r in failures:
        paragraphs.append(f'| {r["engine"]} | {r["policy"]} | {r["geometry_review_images"]} | {r["routed_no_text_images"]} | '
                          f'{r["missed_target_fields"]} | {r["detected_wrong_fields"]} |')
    paragraphs.extend(['','Đếm vùng OCR không ghép vào target không tương đương false-positive rate: '
        'dataset không gán nhãn mọi tiêu đề/nền. Phép chấm không chứng minh precision cho mọi text xuất ra.',''])
    for a in alphabet:
        paragraphs.append(f'- {a["engine"]}: {a["alphabet_supported_fields"]}/{a["eligible_fields"]} trường có toàn bộ ký tự '
                          'tương thích alphabet sau normalization. Đây là điều kiện khả biểu diễn, không phải tỷ lệ đọc đúng.')
    paragraphs.extend(['','Main target không bị thay sau khi xem kết quả. Subset alphabet chỉ là diagnostic để giải thích giới hạn reader; '
        'không thay bảng chính bằng subset dễ hơn. [Alphabet audit](results/e2e_ocr_v2/alphabet_coverage.json).','',
        '## Độ bất định và tỷ lệ xem xét','',
        'Bootstrap2.000 lần theo physical ID trên test seed13, chỉ lượt đầy đủ đầu tiên. '
        'Trung bình field trong ảnh rồi ảnh trong ID; mỗi ID có trọng số bằng nhau. Vì vậy delta này không nhất thiết '
        'bằng chênh lệch bảng pooled-field phía trên. Năm split ID có chồng lặp và panel lặp không phải thêm mẫu độc lập. '
        'Các CI là thăm dò, không chỉnh nhiều phép so sánh.','',
        '| Reader | Policy so với raw | Delta exact theo ID (điểm %) | CI95% (điểm %) |',
        '|---|---|---:|---:|'])
    for r in paired:
        if r['metric']!='field_exact':continue
        lo,hi=r['ci95'];paragraphs.append(f'| {r["engine"]} | {r["policy"]} | {100*r["mean_paired_delta"]:.2f} | [{100*lo:.2f}; {100*hi:.2f}] |')
    paragraphs.extend(['','### Kiểm tra cơ chế riêng trên nhóm ba góc','',
        'Các đối chiếu bổ sung được ghi trước khi xem accuracy trong [kế hoạch phân tích](E2E_ANALYSIS_PLAN.md). '
        'Đây là test IDs seed13 có ảnh thuộc nhóm ba góc, không phải toàn bộ91 ảnh. Dấu dương là policy lớn hơn control; '
        'với thời gian, số âm nghĩa là nhanh hơn. Không có điều chỉnh nhiều phép so sánh.','',
        '| Reader | Policy − control | Số ID exact/wall | Delta exact (điểm %) [CI95%] | Delta wall (s) [CI95%] |',
        '|---|---|---:|---:|---:|'])
    for r in mechanism:
        if r['metric']!='field_exact':continue
        t=next(t for t in mechanism if t['engine']==r['engine'] and t['policy']==r['policy'] and
               t['reference']==r['reference'] and t['metric']=='total_wall')
        lo,hi=r['ci95'];tlo,thi=t['ci95']
        paragraphs.append(f'| {r["engine"]} | {r["policy"]} − {r["reference"]} | {r["physical_ids"]}/{t["physical_ids"]} | '
            f'{100*r["mean_paired_delta"]:.2f} [{100*lo:.2f}; {100*hi:.2f}] | '
            f'{t["mean_paired_delta"]:.3f} [{tlo:.3f}; {thi:.3f}] |')
    paragraphs.extend(['','Accuracy chỉ có22 ID với target hợp lệ, còn latency giữ cả23 ID có ảnh ba góc thuộc split này; '
        'không loại ảnh không có target khỏi chi phí xử lý. CI VietOCR cho support − parallelogram còn bao gồm0, '
        'nên kết quả mô tả baseline tốt hơn không phải bằng chứng đã xác nhận ưu thế thống kê cho mọi quần thể.','',
        'Đã báo đủ đường cong confidence0/.25/.5/.75/.9/.95. '
        'Confidence là tín hiệu của model, không phải nhãn đúng; chưa chọn ngưỡng sản phẩm từ tập test. '
        '“Review proxy” gồm gate hình học/no-text/confidence thấp, không chứng minh khách hàng chắc chắn cần chụp lại. '
        '[Curves](results/e2e_ocr_v2/confidence_review_curves.json).','',
        '## Diễn giải để tiến tới paper','',
        'Đọc đồng thời field exact, CER, coverage và thời gian. Một policy từ chối nhiều có thể chạy nhanh nhưng '
        'đọc đúng ít thông tin hơn. Không dùng coverage đơn thuần, zero observed errors trên20 ảnh hay confidence cao '
        'để kết luận an toàn/novelty/đủ CORE B. Baseline raw, full-frame ba góc và parallelogram+nới5% đều được giữ.',
        '', 'Lịch sử pretrained training overlap chưa được giải quyết, chỉ20 ID ngoài và hai điều kiện chụp; '
        'đây chưa phải kết quả trên CCCD tiếng Việt thực tế, semantic KIE hay PAD. '
        'Mask/crop không sinh lại ký tự ngoài ảnh và không cấp phép chấp nhận giấy tờ thiếu thông tin bắt buộc trong eKYC.',
        '', 'Mọi số chính nằm trong [summary CSV](results/e2e_ocr_v2/summary.csv) và '
        '[per-image numeric rows](results/e2e_ocr_v2/per_image.jsonl.gz); text dự đoán chỉ ở cache cục bộ.',
        '', 'Biểu đồ: [field exact](results/e2e_ocr_v2/field_accuracy.png), '
        '[accuracy/latency](results/e2e_ocr_v2/accuracy_latency.png).'])
    path=Path('research/E2E_RESULTS_VI.md');path.write_text('\n'.join(paragraphs)+'\n',encoding='utf-8',newline='\n')
    save(ROOT/'report_provenance.json',dict(code_sha256=digest(__file__),report_sha256=digest(path),
         source_summary_sha256=digest(ROOT/'summary.json'),validation_sha256=digest(ROOT/'validation.json'),all_policies_reported=True))
    print('REPORT_WRITTEN',path)


if __name__=='__main__':main()
