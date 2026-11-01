"""Generate a measured report only after complete replay and fresh-repeat audit."""
import time
from research.v2_common import *

def report():
    audit=read(OUT/'audit.json')
    if audit['status']!='passed' or audit['signature']!=signature():raise ValueError('Complete V2 audit required')
    lock=read(OUT/'test_lock.json');pub=read(OUT/'lock_publication.json');fresh=read(OUT/'fresh_repeats.json')
    choice=read(OUT/'input_choice.json');ci=read(OUT/'paired_intervals.json');cpu=read(OUT/'test_cpu.json')
    keys=('original','v1','control_42','partial_42','control_31415','partial_31415')
    records={k:read(OUT/f'test_{k}.json') for k in keys};names=dict(original='Vintern gốc (prompt V2)',v1='LoRA V1 chuyển sang tác vụ V2',
        control_42='V2 control /42',partial_42='V2 partial /42',control_31415='V2 control /31415',partial_31415='V2 partial /31415')
    from research.v2_runtime import summary
    allrows={k:r['rows'] for k,r in records.items()}
    for k in ('rapid_v4','rapid_latin_v5'):
        allrows[k]=[r for r in cpu['rows'] if r['model']==k];names[k]=k+' + ghép nhãn/vị trí'
    text=['# V2: kết quả đo thực tế và giới hạn', '',
        'Đã hoàn thành bốn lượt LoRA (hai phương án × hai seed), benchmark mới, đối chứng CPU, '
        'lặp suy luận ảnh mới và phát lại kết quả từ output gốc. V1 và V4 được giữ nguyên.', '',
        '## Thiết kế và dữ liệu', '',
        '- Train 128 ID: 96 SPECIMEN mới + 32 ảnh MIDV đã dùng ở vòng trước, nay chỉ dùng train. '
        'Mỗi phương án 640 ảnh/slot, 320 bước × 4 tích lũy = 1280 lượt ảnh, đúng hai epoch.',
        '- Development 24 ID/72 ảnh; test 48 ID/144 ảnh (24 ảnh dựng + 24 giấy tờ mẫu chụp bằng điện thoại, mỗi ID ba biến thể). '
        'Toàn bộ ID ảnh chụp dùng dev/test chưa thuộc 80 ID nghiên cứu trước.',
        '- Test có 14 nguồn Samsung không dùng trong train V2, 10 nguồn iPhone. '
        'Hai loại fin_id/lva_passport (8 ID) không có trong train; ảnh dựng test dùng bố cục và font khác.',
        '- Đây là tác vụ KIE trên 17 khóa tùy chọn, không phải đánh giá mọi văn bản trên mọi giấy tờ. '
        'Các biến thể bản ngữ/phiên âm và nhóm dòng đã ánh xạ được giữ trong tham chiếu. '
        'R2 chưa dùng MRZ hoặc các trường chưa ánh xạ làm nguồn hỗ trợ bổ sung; phép so sánh nguồn được báo riêng ở V3.',
        '- Mỗi phương án nhận đúng cùng chuỗi ID/slot và cùng ngân sách optimizer. '
        'Số token câu trả lời và thời gian thực tế có thể khác; đã lưu riêng trong train_*.json.',
        '- MIDV là ảnh chụp giấy tờ GIẢ LẬP có transcript của tác giả, không phải một bộ CCCD thật mới tự thu thập. '
        'Nhãn sau cắt/che dựa trên hình học vùng giá trị; chưa có người đánh giá độc lập độ đọc được.', '',
        'Pilot R1 dừng sau event286 (báo tiến độ định kỳ284) vì ánh xạ nhãn bỏ sót trường nhiều dòng/song ngữ, '
        'trước khi đánh giá model đã fine-tune trên development hoặc test. Toàn bộ pilot được giữ riêng; '
        'bốn lượt R2 khởi tạo lại từ model gốc, không dùng adapter pilot. R2 chấp nhận mọi biến thể tác giả còn '
        'hiển thị đầy đủ và ghép các dòng do tác giả đặt tên chung. Prediction model gốc chỉ được tái dùng '
        'khi hash ảnh, prompt và xử lý ảnh trùng hoàn toàn; đã chấm lại trên nhãn R2.', '',
        '## Lựa chọn xử lý ảnh, chỉ dựa trên development', '',
        '| Đầu vào | F1 trên panel | Trường ngoài nhãn, không rỗng | Giây/ảnh mới trung bình |',
        '|---|---:|---:|---:|']
    for r in choice['comparisons']:
        s=r['summary'];text.append(f"| {r['profile']} | {s['f1']:.4f} | {s['unsupported_nonempty']} | {r['mean_fresh_seconds']:.2f} |")
    text+=['',f"Chọn **{choice['profile']}** trước train/test. Nắn ảnh chỉ dùng góc dự đoán từ pixel và raw fallback; không dùng góc chuẩn. "
           'Không xóa trường khỏi GT nếu chính thuật toán nắn làm mất trường đó.', '',
           '## Test đã khóa trước khi chấm', '',
           f"Lock được công bố ở [{pub['commit'][:7]}](https://github.com/TruongTQ261531/AI-based-eKYC-System-Document-Image-Quality-Assessment-/commit/{pub['commit']}). "
           'Mọi model dùng cùng prompt, parser, nhãn và profile V2. V1 ở đây là chuyển sang tác vụ mới, không thay số đo V1 đã công bố.', '',
           '| Phương án | F1 chung | F1 ảnh dựng | F1 ảnh chụp MIDV | Thiếu trường nhìn thấy | Sai giá trị nhìn thấy | Ngoài nhãn, không rỗng |',
           '|---|---:|---:|---:|---:|---:|---:|']
    for k,rows in allrows.items():
        s=summary(rows);a=summary([r for r in rows if r['source']=='authored']);p=summary([r for r in rows if r['source']=='midv2020'])
        text.append(f"| {names[k]} | {s['f1']:.4f} | {a['f1']:.4f} | {p['f1']:.4f} | {s['visible_omissions']} | {s['wrong_visible_values']} | {s['unsupported_nonempty']} |")
    text+=['', '“Ngoài nhãn, không rỗng” là key không có trong target quan sát được; có thể bao gồm chuỗi từ chối như N/A. '
           'Không đồng nhất toàn bộ số này với việc bịa thông tin danh tính. Parser phụ chỉ bỏ JSON fence trọn vẹn và giá trị null/rỗng; '
           'không sửa nội dung dựa trên đáp án. Giữ nguyên output gốc trong cache riêng.', '',
           'So sánh V1→V2 thay cả dữ liệu, schema, ngân sách và tiền xử lý, nên không tách riêng được tác dụng '
           'của việc thêm ảnh chụp. Phép so sánh nhân quả chính là control↔partial cùng seed, ngân sách và ID. '
           'Hai baseline CPU dùng ghép nhãn/vị trí đơn giản và không đại diện mọi hệ thống OCR/KIE hiện đại. '
           'Latin PP-OCRv5 không phải model dành cho mọi hệ chữ; xem riêng slices theo layout, nhất là '
           'rus_internalpassport/grc_passport. [Tài liệu tác giả PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR/blob/main/docs/version3.x/module_usage/text_recognition.en.md).', '',
           '## Chênh lệch có khoảng tin cậy', '',
           '| So sánh | ΔF1 | CI95% theo ID |', '|---|---:|---:|']
    for r in ci['comparisons']:text.append(f"| {r['a']} − {r['b']} | {r['delta_f1']:+.4f} | [{r['ci95_low']:+.4f}, {r['ci95_high']:+.4f}] |")
    text+=['', 'Bootstrap ghép cặp 10000 lần, giữ nguyên cụm ID và phân tầng nguồn. Chỉ 48 ID test và hai seed; '
           'không suy rộng thành độ chính xác eKYC ngoài đời hoặc đảm bảo chống giả.', '',
           '## Kiểm chứng và localhost', '',
           f"- Audit phát lại {audit['raw_output_rows_replayed']} hàng output; {audit['frozen_v1_files_unchanged']} file V1 "
           f"và {audit['frozen_v4_files_unchanged']} file V4 không đổi.",
           f"- Đã trích xuất lại vision từ pixel của toàn bộ {audit['all_visual_caches_replayed']} ảnh tham chiếu duy nhất; "
           f"cache khác biệt: {audit['visual_cache_mismatches']}. Kiểm tra này không thay thế nhãn legibility của con người.",
           f"- Model web được chọn từ development: **{lock['selected_model']}**. Cổng khuyến nghị triển khai: **{lock['deployment_approved']}**. "
           'Nếu không đạt, trang chỉ mở model khi người dùng chủ động chọn chế độ nghiên cứu.',
           f"- {fresh['additional_fresh_calls']} lần đọc ảnh mới thêm trên 8 ảnh/4 ID; sai khác so với output đã chấm: "
           f"{fresh['mismatch_count']}. p50={fresh['fresh_seconds_p50']:.2f}s, p95={fresh['fresh_seconds_p95']:.2f}s. "
           'Đây là suy luận có xử lý ảnh + vision + sinh văn bản, khác thời gian đọc feature cache.',
           '- 23 kiểm tra Python và 8 kiểm tra frontend đã chạy. Predictor/camera giả chỉ dùng cho test hành vi HTTP/UI; '
           'không dùng chúng làm kết quả OCR. Việc bấm thử SPECIMEN qua web cũng không thay benchmark test.',
           '- Chưa xác nhận khả năng đọc trên camera thật của người dùng. Không có dịch vụ LLM bên ngoài, không ghi ảnh camera ra đĩa, '
           'không kiểm tra liveness hay tự duyệt danh tính tại trang nghiên cứu OCR.', '',
           '## Ý nghĩa đối với paper', '',
           'V2 bổ sung phép đo chuyển từ ảnh dựng sang ảnh chụp, chống rò rỉ ID, tách bố cục/camera, đối chứng đồng ngân sách '
           'và ghi riêng bỏ sót/đọc sai/trường không được hỗ trợ. Đây là bằng chứng phương pháp và dữ liệu tốt hơn V1, '
           'chưa phải xác nhận novelty đủ CORE B hoặc bảo đảm được nhận bài.',
           '[KIE-HVQA](https://arxiv.org/abs/2506.20168) đã nghiên cứu hallucination OCR và SFT/GRPO. '
           'Nguồn dữ liệu: [MIDV-2020](https://arxiv.org/abs/2107.00396). V2 không nhận ý tưởng fine-tune chống bịa là phát minh đầu tiên.',
           'Thiếu sót còn lại: chưa có bộ ảnh Việt Nam mới tự thu thập có phép; chưa có nhãn legibility độc lập; '
           'chỉ một backbone nhỏ, hai seed và ít ID/type. Font test Arial phụ thuộc font Windows đúng checksum trong manifest. '
           'Cần căn cứ riêng kết quả ảnh chụp và CI khi quyết định có mở rộng thí nghiệm hoặc viết claim.', '']
    path=ROOT/'research/V2_RESULTS_VI.md';path.write_text('\n'.join(text),encoding='utf-8',newline='\n')
    save(OUT/'report_provenance.json',dict(signature=signature(),report_sha256=sha(path),audit_sha256=sha(OUT/'audit.json'),
        lock_sha256=sha(OUT/'test_lock.json'),generated_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())))
    (ROOT/'research/V2_STATUS.md').write_text('# V2 completed\n\nFour matched-budget LoRA runs, six VLM models, two CPU readers, new sealed test and fresh-repeat audit completed.\n'
        'See V2_RESULTS_VI.md and results/vlm_lora_v2_r2/audit.json for measured results and limits.\n'
        'Browser SPECIMEN checks and actual-user camera validation are separate from benchmark completion.\n',encoding='utf-8',newline='\n')
    from research.v2_export import export
    export()
    from research.v2_figures import make
    make()
    print('V2_REPORT_READY',flush=True)

if __name__=='__main__':report()
