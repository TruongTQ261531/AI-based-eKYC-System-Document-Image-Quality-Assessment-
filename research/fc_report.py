"""Readable report from audited fixed-arm comparisons; no success assumption."""
import numpy as np
from research.fc_common import *


def report():
    audit=read(OUT/'audit.json')
    if audit['status']!='passed' or audit['signature']!=signature():raise ValueError('Matching passed audit required')
    # The already-running supervisor predates the explicit software stage.
    # Its report child loads this module freshly; require the same checks there.
    if not (OUT/'software_verification.json').exists():
        if read(CACHE/'workflow.json')['stage']!='report':raise ValueError('Run fc_workflow to complete software verification first')
        from research.fc_workflow import restore_source_web
        from research.fc_verify import verify
        restore_source_web();verify()
    design=read(OUT/'training_design.json');pre=read(OUT/'preflight.json');card=read(OUT/'dataset_card.json')
    stats=read(OUT/'paired_statistics.json');joined=read(OUT/'pixel_cluster_sensitivity.json')
    records={k:read(OUT/f'test_{k}.json') for k in KEYS}
    dev={k:read(OUT/f'development_{k}.json') for k in KEYS}
    proof=design['random_selection_proof']
    primary=[r for r in stats['comparisons'] if r['primary']]
    higher=sum(r['p_holm']<.05 and r['f1']['ci9875_low']>0 for r in primary)
    lower=sum(r['p_holm']<.05 and r['f1']['ci9875_high']<0 for r in primary)
    verdict=(f'Trong bốn so sánh chính, {higher}/4 ủng hộ hard cao hơn và {lower}/4 ủng hộ hard thấp hơn '
        'theo cả p Holm < 0,05 và CI 98,75% đã đăng ký. ')
    if not higher and not lower:
        verdict+='Chưa đủ bằng chứng phân biệt hard với random/repeat trên bộ test này. '
    secondary=[r for r in stats['comparisons'] if not r['primary']]
    verdict+='So với uniform (đối chứng phụ), ΔF1 theo hai seed là '+', '.join(
        f'{r["a"].split("_")[-1]}: {r["f1"]["delta"]:+.5f}' for r in secondary)+'.'
    lines=['# Mục 4: đối chứng khớp ngân sách và test mới', '', verdict, '',
        'Đã hoàn tất vòng đối chứng và audit. Đây là kiểm chứng một giả thuyết về cách chọn/che dữ liệu; '
        'hoàn tất mục4 không đồng nghĩa đã cải thiện model hoặc đạt CORE B. '
        'Các phương án và checkpoint cuối được khóa trước test; không chọn model triển khai bằng kết quả test.', '',
        '## Những gì được so sánh', '',
        'Tám adapter: bốn phương án × hai seed42/31415. Uniform V3 và hard HP là bốn checkpoint lịch sử được giữ nguyên. '
        'Random và repeat là bốn LoRA mới từ cùng Vintern gốc, không warm-start từ một adapter khác. '
        'Mỗi arm có128 ID,640 slot theo cùng thứ tự,320 update,1280 lượt ảnh, accumulation4, rank8/alpha16, '
        'cùng prompt17 khóa tùy chọn, rect2 và ngân sách sinh384 token.', '',
        'Random dùng cùng thuật toán tạo cặp, nhưng chọn ID theo nguồn/bố cục và ngân sách token đã khớp. '
        'Repeat dùng cùng32 ID như hard, lặp một hướng che ở cả hai slot thay vì A/B. '
        'Loss hiện học từng ảnh độc lập; đây là đối chứng độ đa dạng hướng che, không phải bỏ một pair loss.', '',
        f'Đã xét đầy đủ{proof["enumerated_subsets"]} tổ hợp: '
        f'{proof["token_matched_subsets"]} tổ hợp khớp token, '
        f'mức khác biệt tối đa là{proof["maximum_new_ids_after_token_match"]} ID, '
        f'có{proof["maximally_separated_subsets"]} tổ hợp đạt mức này. '
        'Chọn bằng reservoir sampling với seed cố định. Đây là số tổ hợp dữ liệu, không phải số lần chạy model. '
        f'Random trùng{design["random_overlap_hard_ids"]}/32 ID chọn che với hard. '
        'Vì hỗ trợ dữ liệu hạn chế, không diễn giải thành phép thử rộng giữa hai tập32 ID hoàn toàn khác nhau.', '',
        'Ba phương án chính hard/random/repeat khớp tổng token đáp án. Uniform cũ có ít token hơn và là đối chứng phụ '
        'cho toàn bộ can thiệp. Không tuyên bố khớp FLOPs, thời gian hoặc số token trong từng update.', '',
        '| Arm | Token đáp án mỗi seed | Slot đổi pixel | ID đổi pixel | Pixel train khác nhau |',
        '|---|---:|---:|---:|---:|']
    for arm in ARMS:
        value=pre['actual_training_pixel_support'].get(arm,{})
        lines.append(f'| {arm} | {design["answer_loss_tokens_per_seed"][arm]} | '
            f'{value.get("pixel_changed_slots",0)} | {value.get("pixel_changed_ids",0)} | '
            f'{value.get("distinct_training_pixels","xem manifest")} |')
    lines+=['', '640 slot không đồng nghĩa640 ảnh độc lập: repeat cố ý lặp pixel. '
        'Random gán lại64 slot nhưng có một ảnh bằng pixel với ô gốc, nên số đổi pixel được báo riêng. '
        'Bản chuẩn bị đầu và lượt tìm mức6 ID không thành công được giữ trong cache; '
        'điều chỉnh lựa chọn xảy ra trước mọi update mới. '
        'Xem [training design](results/fair_controls_v1/training_design.json), '
        '[exposure](results/fair_controls_v1/exposure_audit.json) và '
        '[nhật ký điều chỉnh chuẩn bị](results/fair_controls_v1/preparation_revision.json).', '',
        '## Tập kiểm chứng và tính độc lập', '',
        f'Test mới192 view trên48 ID giấy tờ mẫu:24 ảnh MIDV từ các member16/17/18 đã chọn bằng metadata và24 mẫu giả lập mới. '
        f'Có{pre["distinct_test_pixels"]} pixel raster khác nhau, '
        f'{pre["cross_id_test_pixel_groups"]} nhóm pixel trùng giữa các ID. '
        f'Có{card["test_pair_fallbacks"]} fallback pair_mask giữ trong kết quả tổng. '
        'Không trùng ID, pixel đã giải mã hoặc fingerprint đáp án đầy đủ với các vai trò cũ được kiểm kê.', '',
        f'EXIF ảnh mới: {card["photo_device_counts"]}. Đây là ảnh mẫu từ nguồn công khai và generator, '
        'không phải ảnh camera tự thu thập mới, người dùng thật hoặc kiểm chứng tách người tự nhiên. '
        'Giữ generator/font/layout cũ, thay nội dung/ID; không nhận đóng góp font/layout mới. '
        'Legibility vẫn là proxy hình học, chưa có đánh giá người độc lập.', '',
        '## Kết quả trên cùng192 view mới', '',
        '| Model | F1 dev | F1 test | Output mất nguồn | Bỏ sót lân cận | Sai lân cận | Recall lân cận | Cặp thành công |',
        '|---|---:|---:|---:|---:|---:|---:|---:|']
    for key in KEYS:
        s=records[key]['summary'];d=dev[key]['summary']
        lines.append(f'| {key} | {d["f1"]:.4f} | {s["f1"]:.4f} | {s["declared_hidden_outputs"]} | '
            f'{s["neighbor_omissions"]} | {s["neighbor_wrong"]} | {s["neighbor_recall"]:.4f} | {s["pair_success"]}/{s["pair_eligible"]} |')
    denominator=records[KEYS[0]]['summary']
    lines+=['', f'Mẫu số chung: {denominator["declared_hidden_reference_keys"]} lượt trường mất nguồn khai báo, '
        f'{denominator["neighbor_reference_keys"]} lượt trường lân cận có nguồn body nguyên vẹn. '
        'Các số là lượt trường trên nhiều view, không phải số người. Nguồn chưa được parser nhận không tự chứng minh hallucination.', '',
        '## Bốn so sánh chính đã đăng ký', '',
        '| So sánh | ΔF1 | CI95% | CI98,75% | p hoán vị | p Holm | Nhận định có điều kiện |',
        '|---|---:|---|---|---:|---:|---|']
    for value in stats['comparisons']:
        if not value['primary']:continue
        v=value['f1'];label='chưa phân biệt rõ'
        if value['p_holm']<.05 and v['ci9875_low']>0:label='ủng hộ hard cao hơn'
        elif value['p_holm']<.05 and v['ci9875_high']<0:label='ủng hộ hard thấp hơn'
        lines.append(f'| {value["a"]} − {value["b"]} | {v["delta"]:+.4f} | '
            f'[{v["ci95_low"]:+.5f}, {v["ci95_high"]:+.5f}] | [{v["ci9875_low"]:+.5f}, {v["ci9875_high"]:+.5f}] | '
            f'{value["p_permutation"]:.5f} | {value["p_holm"]:.5f} | {label} |')
    lines+=['', 'Bootstrap10000 lần phân tầng nguồn, lấy ID làm cụm; CI98,75% Bonferroni cho bốn so sánh chính. '
        'Hoán vị10000 lần đổi nhãn hai model cho toàn bộ view của từng ID, p=(extreme+1)/10001; Holm trên bốn p chính. '
        'Giả định exchangeability và hai seed là giới hạn. Các kiểm định theo ID có điều kiện trên model/template/camera cố định, '
        'không chứng minh ưu thế trên quần thể seed hoặc camera mới. Chỉ số lỗi phụ không được dùng chọn một test subset thuận lợi.', '',
        f'Độ nhạy nối ID có pixel trùng dùng{joined["resampling_clusters"]} cụm, '
        f'từ{joined["document_instances"]} ID. '
        f'Kiểm kê MRZ trước test có{pre["source_coverage_exclusions"]} ID ngoài phần source parser nhận; '
        'phân tích độ nhạy giữ cùng output và chỉ loại các ID đã định trước. Kết quả chính luôn giữ192 view.', '',
        'Xem [thống kê chính và phụ](results/fair_controls_v1/paired_statistics.json), '
        '[cụm pixel](results/fair_controls_v1/pixel_cluster_sensitivity.json), '
        '[độ bao phủ nguồn](results/fair_controls_v1/source_coverage_sensitivity.json), '
        '[các lát nguồn/view/device/layout](results/fair_controls_v1/slices.json).', '',
        '## Định dạng và kiểm tra từ pixel', '',
        '| Model | JSON hợp lệ | Chạm384 token | Fresh khác test | Pixel panel p50/p95 giây |',
        '|---|---:|---:|---:|---|']
    for key in KEYS:
        rows=records[key]['rows'];fresh=read(OUT/f'fresh_{key}.json');times=[r['wall_seconds'] for r in fresh['rows']]
        lines.append(f'| {key} | {sum(bool(r["valid_json"]) for r in rows)}/192 | '
            f'{sum(bool(r["hit_token_limit"]) for r in rows)} | {fresh["mismatches"]}/8 | '
            f'{np.percentile(times,50):.2f}/{np.percentile(times,95):.2f} |')
    lines+=['', 'Fresh dùng bốn input trên hai ID, mỗi model đọc lại hai lần:64 lượt. '
        'Đây là kiểm tra nhất quán và panel thời gian nhỏ, không phải64 ID hoặc benchmark tốc độ CPU/SOTA. '
        'Giữ cả lỗi JSON và chạm ngân sách; không chạy lại với prompt tốt hơn sau khi xem test.', '',
        '## Bằng chứng và giới hạn còn lại', '',
        f'Đã replay{audit["replayed_score_rows"]} hàng điểm: '
        f'{audit["new_cached_generation_calls"]} lượt sinh mới và{audit["reused_development_outputs"]} output development cũ được tái chấm; '
        f'thêm{audit["additional_pixel_level_calls"]} lượt từ pixel và{audit["probe_calls"]} lượt probe development. '
        f'Có{audit["fresh_output_hash_mismatches"]} fresh hash khác test. '
        'Các số lượt sinh văn bản không gộp với lượt chạy encoder ảnh. '
        f'Đã chạy lại encoder trên {read(OUT/"feature_audit.json")["freshly_reextracted_features"]} đầu vào để đối chiếu đặc trưng; '
        f'nguồn đặc trưng tham chiếu: {read(OUT/"feature_audit.json")["reference_feature_origins"]}. '
        f'Có thêm {read(OUT/"feature_audit.json")["additional_reference_encoder_calls"]} lượt encoder để tạo tham chiếu còn thiếu cache. '
        'Rescoring, tổ hợp dữ liệu, bootstrap và hoán vị chỉ là tính toán lại, không sinh thêm output OCR. '
        'Xem [audit encoder và cache](results/fair_controls_v1/feature_audit.json).', '',
        f'Bảo toàn{audit["frozen_V1_files"]} file V1, {audit["frozen_V4_files"]} file V4, '
        f'{audit["frozen_HP_files"]} file HP và hợp đồng R2/V3. '
        f'Khóa trước train: `{audit["pretraining_publication"]}`; trước test: `{audit["pretest_publication"]}`. '
        'Checkpoint cuối của cả tám model đã kiểm tra tensor/optimizer/order/token/hash trước test và xác nhận lại sau test.', '',
        f'Backup update phải tính lại trong vòng mới: {audit["discarded_update_records"]}. '
        'Log/checkpoint gián đoạn nếu có được giữ, không cộng replay vào320 bước hiệu dụng hoặc gọi là run độc lập. '
        'Cấu hình tài nguyên của các run lịch sử khác nhau; số token bằng nhau không chứng minh thời gian/FLOPs bằng nhau.', '',
        'Đối chứng chọn ca chỉ khác tối đa năm ID dưới điều kiện hiện có; power hạn chế. '
        'Đối chứng repeat vẫn thay đổi phân bố trường/token theo từng slot. '
        'Uniform không khớp token và chỉ là đối chứng phụ; V1 không bị biến thành đối chứng nhân quả cùng ngân sách. '
        'Chưa có người gán nhãn legibility, ảnh mới tự thu thập hoặc chứng nhận PAD. '
        'Không tự thay model web hoặc khẳng định đủ đóng góp CORE B. Mục2 sau đây phải chọn cấu hình trên development '
        'và dùng test mới để xác nhận nếu đã dùng kết quả này để điều chỉnh phương pháp.', '',
        'Bằng chứng: [audit](results/fair_controls_v1/audit.json), '
        '[preflight](results/fair_controls_v1/preflight.json), '
        '[inventory checkpoint](results/fair_controls_v1/training_state_inventory.json), '
        '[protocol](FAIR_CONTROLS_PROTOCOL.md), [runbook](FAIR_CONTROLS_RUNBOOK.md).']
    path=ROOT/'research/FAIR_CONTROLS_RESULTS_VI.md'
    verification=read(OUT/'software_verification.json')
    if audit.get('io_recoveries'):
        lines+=['', '## Gián đoạn ghi tiến độ', '',
            'Một stage development dừng vì Windows từ chối atomic replace file progress. '
            'Bốn model đã huấn luyện và56 output đã lưu được giữ nguyên; chúng được kiểm tra hash sau khi tiếp tục. '
            'Đổi reader sang delete-sharing và retry metadata với cùng payload, không sửa dữ liệu/model/phép chấm '
            'hoặc huấn luyện lại.56 output cache không bị tính thành56 lượt OCR mới. '
            'Log lỗi gốc được giữ; xem [ghi chú I/O](FAIR_CONTROLS_IO_NOTE.md) và '
            '[record phục hồi](results/fair_controls_v1/io_recovery.json).']
    if verification['status']!='passed' or verification['signature']!=signature():raise ValueError('Matching software checks required')
    lines+=['', '## Kiểm thử phần mềm và localhost', '',
        f'{verification["combined_unique_python_checks"]} kiểm tra Python, '
        f'{verification["subtests_passed"]} subtest và{verification["frontend_total"]} kiểm tra hành vi giao diện đã qua. '
        f'Bộ chính có{verification["main_skipped_optional"]} bài cần overlay; đã chạy riêng và đều qua. '
        f'Có{verification["warning_count"]} cảnh báo trong log, không cài dependency mới.', '',
        'Đã xác nhận eKYC8000 ready/API3.2.0 và web nghiên cứu8003 ready, vẫn dùngpartial_42. '
        'Health của8003 thuộc nghiên cứu V3 cũ, không dùng để đếm run FC. '
        'Các kiểm thử là mô phỏng/HTTP, không phải kiểm chứng camera người dùng thật. '
        'Xem [bằng chứng/hash log](results/fair_controls_v1/software_verification.json).']
    if verification.get('tested_working_tree_sources'):
        lines+=['', f'Bản kiểm tra cuối lưu hash của {len(verification["tested_working_tree_sources"])} file mã nguồn và môi trường; '
            'đã xác nhận các file này không đổi trong suốt lượt kiểm tra. '
            'Hash từng file mô tả cả thay đổi chưa commit tại thời điểm test, không chỉ tên commit HEAD.']
    if (OUT/'software_reverification.json').exists():
        repeat=read(OUT/'software_reverification.json')
        if repeat.get('status')!='passed':raise ValueError('Software reverification record incomplete')
        lines+=['', 'Đã giữ bằng chứng vòng kiểm tra phần mềm đầu và chạy lại toàn bộ sau khi bổ sung snapshot mã nguồn. '
            '304 là số kiểm tra Python khác nhau, không cộng hai lượt thành608 bài độc lập. '
            'Không chạy lại huấn luyện, test OCR hoặc chọn model trong bước này. '
            'Xem [record hai lượt và nơi giữ log cũ](results/fair_controls_v1/software_reverification.json).']
    path.write_text('\n'.join(lines)+'\n',encoding='utf-8',newline='\n')
    save(OUT/'report_provenance.json',dict(signature=signature(),report_sha256=sha(path),
        report_code_sha256=sha(ROOT/'research/fc_report.py'),audit_sha256=sha(OUT/'audit.json')))
    print('FC_REPORT_READY',flush=True)


if __name__=='__main__':report()
