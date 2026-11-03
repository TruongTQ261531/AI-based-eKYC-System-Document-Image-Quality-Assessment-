"""Generate the result report from audited artifacts, including failed gates."""
from research.hp_common import *
from research.hp_metrics import summary


def make():
    audit=read(OUT/'audit.json')
    if audit['status']!='passed' or audit['signature']!=signature():raise ValueError('Matching audit required')
    lock=read(OUT/'test_lock.json');card=read(OUT/'dataset_card.json');pre=read(OUT/'preflight.json')
    records={k:read(OUT/f'test_{k}.json') for k in KEYS};dev={k:read(OUT/f'development_{k}.json') for k in KEYS}
    intervals=read(OUT/'paired_intervals.json');sensitivity=read(OUT/'duplicate_cluster_sensitivity.json');fresh=read(OUT/'fresh_repeats.json')
    coverage=read(OUT/'source_coverage_sensitivity.json')
    decision=('đạt' if lock['promotion_approved'] else 'không đạt')
    lines=['# Kết quả cải thiện hai nhóm lỗi bằng cặp che/giữ', '',
        f'Ứng viên **{lock["selected_hard_candidate"]}** được chọn bằng development và **{decision} cổng thay model**. '
        'Quyết định này đã khóa trước test. Hai seed và mọi kết quả trái chiều đều có trong bảng dưới; '
        'kiểm tra tính toàn vẹn đã vượt qua không đồng nghĩa phương pháp mới có hiệu quả tốt hơn.', '',
        'Thực nghiệm mới sau R2/V3. Hai LoRA mới bắt đầu từ cùng Vintern gốc, đối chiếu hai '
        'checkpoint source-supervised có cùng seed/ngân sách. Không so F1 tuyệt đối giữa hai test khác nhau '
        'để gọi là cải thiện. Test mới và mọi kết quả âm được giữ.', '',
        '## Dữ liệu và can thiệp', '',
        '640 slot train trên128 mẫu giấy tờ; chỉ64 slot của32 ID đã chọn trước được thay bằng cặp ảnh '
        'che tất cả nguồn khai báo của A/giữ B và đảo chiều.29 ID ảnh chụp,3 ID giả lập. '
        'Không đổi ID/slot exposure,320 update,1280 lượt ảnh, prompt, rect2,384 token, rank8/alpha16, '
        'optimizer hoặc checkpoint cuối. Đối chứng là hai adapter uniform-source V3 đã có; '
        'không tính chúng thành hai run huấn luyện mới.', '',
        f'Development96 ca trên24 ID; test192 ca trên48 ID mới (24 ảnh MIDV chưa dùng và24 giấy tờ giả lập mới). '
        f'Test có {pre["distinct_new_test_rasters"]} raster khác nhau theo SHA256; '
        f'{pre["cross_document_exact_raster_groups"]} nhóm raster trùng giữa các ID. '
        'Giữ các raster trùng/fallback, không coi số lượt đọc là số giấy tờ độc lập. '
        f'Có {pre["fallback_counts_by_role"]["development"]} fallback dev và {pre["fallback_counts_by_role"]["test"]} fallback test '
        'vì không có cặp che/giữ nguyên vẹn gần nhau. Chúng dùng value_mask và vẫn nằm trong kết quả tổng.', '',
        f'Camera EXIF test: {card["photo_device_counts"]}. Đây là ảnh giấy tờ mẫu công khai, '
        'không phải bộ camera mới tự thu thập hoặc người dùng thật. Hai font/layout giả lập mới tương quan với nhau; '
        'không quy tác động riêng cho font. Transcript/vị trí lấy từ tác giả/generator; '
        'khả năng đọc được vẫn là proxy hình học, chưa có nhãn người độc lập.', '',
        '## Kết quả trên cùng test mới', '',
        '| Model | F1 dev | F1 test | Key mất nguồn vẫn xuất | Bỏ sót lân cận | Sai lân cận | Recall lân cận | Thành công cặp |',
        '|---|---:|---:|---:|---:|---:|---:|---:|']
    for key in KEYS:
        s=records[key]['summary'];d=dev[key]['summary']
        lines.append(f'| {key} | {d["f1"]:.4f} | {s["f1"]:.4f} | {s["declared_hidden_outputs"]} | {s["neighbor_omissions"]} | {s["neighbor_wrong"]} | {s["neighbor_recall"]:.4f} | {s["pair_success"]}/{s["pair_eligible"]} |')
    denominator=records['uniform_42']['summary']
    lines+=['', f'Cùng mẫu số cho cả bốn model: {denominator["declared_hidden_reference_keys"]} '
        f'trường mất tất cả nguồn khai báo và {denominator["neighbor_reference_keys"]} trường lân cận có nguồn nguyên vẹn. '
        'Các số là lượt trường trên nhiều view của48 giấy tờ, không phải số người. '
        '“Mất nguồn” được tính theo hợp đồng nhãn hình học; nguồn chưa được parser nhận không được coi là bằng chứng chắc chắn về hallucination.']
    lines+=['', '## So sánh ghép cặp theo seed', '',
        '| So sánh | ΔF1 test | CI95% theo ID | CI95% nối ID trùng raster |',
        '|---|---:|---|---|']
    for a,b in zip(intervals['comparisons'],sensitivity['comparisons']):
        v=a['f1'];w=b['f1']
        lines.append(f'| {a["a"]} − {a["b"]} | {v["delta"]:+.4f} | [{v["ci95_low"]:+.6f}, {v["ci95_high"]:+.6f}] | [{w["ci95_low"]:+.6f}, {w["ci95_high"]:+.6f}] |')
    lines+=['', '| So sánh | ΔRecall lân cận | CI95% | ΔSố output mất nguồn | CI95% |',
        '|---|---:|---|---:|---|']
    for value in intervals['comparisons']:
        n=value['neighbor_recall'];h=value['hidden_outputs']
        lines.append(f'| {value["a"]} − {value["b"]} | {n["delta"]:+.4f} | '
            f'[{n["ci95_low"]:+.6f}, {n["ci95_high"]:+.6f}] | {h["delta"]:+.0f} | '
            f'[{h["ci95_low"]:+.2f}, {h["ci95_high"]:+.2f}] |')
    lines+=['', 'Recall lân cận tăng là chiều mong muốn; số output mất nguồn giảm là chiều mong muốn. '
        'CI lấy từ cùng resample ID đã đăng ký, không từ coi từng trường là mẫu độc lập. '
        'CI theo dữ liệu trong từng seed không thay thế đánh giá biến thiên qua nhiều seed.']
    lines+=['', 'Bootstrap10000 lần, seed20261104, phân tầng nguồn. Phân tích chính dùng48 cụm ID; '
        f'phân tích độ nhạy dùng{sensitivity["resampling_clusters"]} cụm nối ID có raster trùng. '
        'Các trường và nhiều view của một giấy tờ không được coi là các ID độc lập. '
        'Trong36 cặp test hợp lệ có24 ảnh chụp và12 ảnh giả lập bố cục hàng.12 ảnh giả lập '
        'bố cục cột thưa dùng fallback; không kết luận hiệu quả cặp riêng trên bố cục/font đó.', '',
        '## Độ nhạy với một nguồn MRZ chưa nhận được', '',
        'Một mẫu ảnh mới có transcript MRZ tác giả dài43/44 ký tự. Parser TD3 không nhận nó; '
        'ngoài hợp đồng không đồng nghĩa thông tin thật sự vắng. Phân tích phụ đã đăng ký trước test '
        'giữ nguyên output và chỉ loại ID này, còn47 ID/188 ca. Kết quả chính vẫn giữ đủ192 ca; '
        'không có lượt model mới hoặc sửa transcript dựa trên dự đoán.', '',
        '| So sánh | ΔF1 trên47 ID | CI95% |','|---|---:|---|']
    for value in coverage['intervals']['comparisons']:
        s=value['f1'];lines.append(f'| {value["a"]} − {value["b"]} | {s["delta"]:+.4f} | [{s["ci95_low"]:+.6f}, {s["ci95_high"]:+.6f}] |')
    lines+=['', 'Xem [ghi chú độ bao phủ](HARD_PAIR_COVERAGE_NOTE.md). Không thay kết luận chính bằng một tập con tốt hơn.', '',
        '## Các nguồn và kiểu ảnh', '', '| Model | Nguồn | View | F1 | Bỏ sót lân cận | Key mất nguồn vẫn xuất |',
        '|---|---|---|---:|---:|---:|']
    for key in KEYS:
        for source in ('authored','midv2020'):
            for view in ('full','field_clip','value_mask','pair_mask'):
                s=summary([r for r in records[key]['rows'] if r['source']==source and r['capture']==view])
                lines.append(f'| {key} | {source} | {view} | {s["f1"]:.4f} | {s["neighbor_omissions"]} | {s["declared_hidden_outputs"]} |')
    lines+=['', '## Định dạng và ngân sách đọc', '',
        '| Model | JSON hợp lệ | Chạm384 token |', '|---|---:|---:|']
    for key in KEYS:
        rows=records[key]['rows']
        lines.append(f'| {key} | {sum(bool(r["valid_json"]) for r in rows)}/{len(rows)} | '
            f'{sum(bool(r["hit_token_limit"]) for r in rows)} |')
    lines+=['', 'Giữ mọi ca lỗi JSON và chạm ngân sách trong kết quả tổng; không bỏ hoặc chạy lại với prompt tốt hơn. '
        'Chạm384 token là bộ đếm sinh, không tự chứng minh đáp án bị cắt. '
        'Chỉ số trường phải được đọc cùng chỉ số định dạng và thành công cặp.']
    lines+=['', '## Ngân sách hiệu dụng và bộ đếm bộ nhớ', '', '| Run | Trạng thái | Update | Lượt ảnh | Token loss | Max allocated/reserved GiB |',
        '|---|---|---:|---:|---:|---|']
    for key in KEYS:
        seed=key.rsplit('_',1)[1];new=key.startswith('hard_')
        r=read(OUT/f'train_hard_{seed}.json') if new else read(OLD_OUT/f'train_source_{seed}.json')
        events=r['events'];status='huấn luyện mới' if new else 'đối chứng đã có'
        lines.append(f'| {key} | {status} | {r["steps"]} | {r["presentations"]} | {r["token_exposure"]["answer_loss_tokens"]} | '
            f'{max(e["peak_allocated_bytes"] for e in events)/2**30:.3f} / {max(e["peak_reserved_bytes"] for e in events)/2**30:.3f} |')
    lines+=['', 'Khớp ID/lượt ảnh và số update không đồng nghĩa khớp số token, thời gian hoặc FLOPs. '
        'Đối chứng là các run lịch sử; chính sách cache/tài nguyên đã thay đổi như ghi chú runtime. '
        'Token và update trong bảng lấy từ log canonical của320 bước hiệu dụng; '
        'các update phải tính lại và chẩn đoán được kê riêng bên dưới. '
        'Cột bộ nhớ là max trên các event giữ lại, không chứng minh ưu thế bộ nhớ hoặc tốc độ huấn luyện.']
    lines+=['', f'Đã replay {audit["replayed_prediction_rows"]} hàng điểm từ output nguyên văn; '
        f'{audit["recorded_new_cached_generation_calls"]} lượt sinh mới từ feature cache và '
        f'{audit["reused_old_development_outputs"]} output development cũ được tái chấm. '
        f'Thêm16 lượt từ pixel trên8 ảnh/4 ID: {fresh["mismatches"]} hash khác với test. '
        f'p50/p95 đầu cuối mẫu lặp: {fresh["p50_fresh_seconds"]:.2f}/{fresh["p95_fresh_seconds"]:.2f}s. '
        'Các timer feature-cache và pixel-level có phạm vi khác nhau; không tuyên bố ưu thế tốc độ. '
        'VRAM allocated/reserved là bộ đếm PyTorch, không phải tổng VRAM vật lý.', '',
        '## Sự cố tài nguyên và kiểm tra resume', '',
        f'Lượt hard42 được dừng có kiểm soát sau khi đã lưu checkpoint80 do cache gây áp lực bộ nhớ. '
        f'Có {audit["recorded_discarded_updates_replayed"]} update sau checkpoint được ghi nhận rồi phát lại; '
        'không cộng chúng vào ngân sách hiệu dụng320 hoặc coi là dữ liệu độc lập. '
        'Hai bước chẩn đoán ngoài primary từ cùng checkpoint80 kiểm tra cache gốc và cache thu hồi: '
        'mọi192 tensor LoRA, optimizer và RNG khớp, sai khác tối đa0. '
        'Cấu hình cache đã được công bố trước resume; không đổi input/loss/seed/ngân sách. '
        'Parity một bước không chứng minh mọi chuỗi cập nhật tương đương. '
        f'Đối chiếu thêm {audit["scalar_replayed_updates_exact"]} event scalar được phát lại cũng khớp; '
        'đây không phải so mọi tensor sau từng bước. '
        'Peak/timer trước thay đổi vẫn giữ nguyên. Xem [ghi chú runtime](HARD_PAIR_RUNTIME_NOTE.md).', '',
        '## Quyết định và giới hạn', '',
        f'Ứng viên hard chọn bằng development: **{lock["selected_hard_candidate"]}**; '
        f'cổng promotion: **{lock["promotion_approved"]}**. Quyết định được công bố trước test. '
        'Web cũ được khôi phục sau thực nghiệm; không đổi model dựa trên test. '
        'Muốn đưa ứng viên mới vào web phải giữ quyết định development và hoàn tất kiểm thử phục vụ riêng.', '',
        'Can thiệp này đồng thời thay crop bằng đầy đủ ngữ cảnh và thay chính sách mask ở64 slot; '
        'không tách riêng lợi ích hard selection, cặp đối nghịch hoặc số token đáp án. '
        'Chỉ một backbone nhỏ, hai seed; điều kiện sáng/che là giả lập trên giấy tờ mẫu. '
        'Chưa có nhãn legibility độc lập, kiểm thử camera người dùng hoặc chứng nhận chống giả. '
        'Không kết luận đạt CORE B, SOTA hoặc xác minh danh tính từ các kết quả này.', '',
        f'Khóa trước huấn luyện: `{audit["pretraining_publication"]}`. '
        f'Khóa trước test: `{audit["test_seal_publication"]}`. '
        'Bảo toàn101 file V1,63 file V4 và hợp đồng R2/V3. '
        'Ảnh, nhãn riêng, output OCR nguyên văn và weights mới không đưa lên Git.', '',
        'Bằng chứng: [audit](results/hard_pairs_v1/audit.json), '
        '[CI](results/hard_pairs_v1/paired_intervals.json), '
        '[protocol](HARD_PAIR_PROTOCOL.md), [runbook](HARD_PAIR_RUNBOOK.md), '
        '[đối chiếu nghiên cứu và giới hạn novelty](HARD_PAIR_RELATED_WORK.md).']
    path=ROOT/'research/HARD_PAIR_RESULTS_VI.md';path.write_text('\n'.join(lines)+'\n',encoding='utf-8',newline='\n')
    save(OUT/'report_provenance.json',dict(signature=signature(),report_sha256=sha(path),audit_sha256=sha(OUT/'audit.json'),
        report_code_sha256=sha(Path(__file__))))
    print('HP_REPORT_READY',flush=True)


if __name__=='__main__':make()
