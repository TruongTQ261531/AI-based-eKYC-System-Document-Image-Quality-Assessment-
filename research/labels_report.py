"""An outcome-driven report which does not turn automatic labels into human evidence."""
import numpy as np
from research.labels_common import *
from research.labels_study import MODELS
from research.labels_review import status

def report():
    sig=signature();audit=read(OUT/'audit.json');verification=read(OUT/'software_verification.json')
    if any(v['status']!='passed' or v['signature']!=sig for v in (audit,verification)):raise ValueError('Matching audits required')
    corpus=read(OUT/'corpus_release.json');data=read(OUT/'data_audit.json');card=read(OUT/'evaluation_card.json')
    factorial=read(OUT/'factorial_effects.json');statistics=read(OUT/'slices.json');exports=read(OUT/'exports.json');human=status()
    results={m:read(OUT/f'evaluation_{m}.json') for m in MODELS}
    lines=['# Mục 1: nhãn OCR có nguồn gốc và kiểm chứng bố cục/font/ảnh chụp', '',
        'Đã hoàn tất lớp nhãn tác giả, vị trí, xuất dữ liệu, bộ kiểm chứng mới và các kiểm tra tự động. '
        'Phần khả năng đọc do người đánh giá độc lập chưa hoàn tất. Không gọi nhãn hình học hoặc kết quả OCR là nhãn đọc được của người.', '',
        f'Hiện có {human["events"]} sự kiện đề xuất tự khai và {human["independently_verified_field_labels"]} nhãn trường đã được xác nhận độc lập. '
        'Không có bộ ảnh camera mới tự thu thập có sự đồng ý của người tham gia. Kết quả này không tự xác nhận đủ đóng góp CORE B.', '',
        '## Bộ ảnh gốc và từng trường OCR', '',
        f'- {corpus["images"]:,} ảnh, {corpus["fields"]:,} bản ghi vùng chữ, {corpus["physical_document_groups"]} nhóm giấy tờ gốc.',
        f'- Nguồn: {corpus["sources"]}; chất lượng: {corpus["quality_counts"]}.',
        f'- Giữ đủ {corpus["extra_midv2019_references"]} ảnh tham chiếu MIDV-2019 bổ sung thuộc Clean; đây vẫn là cùng 50 giấy tờ, không phải 50 người mới.',
        '- Mỗi trường giữ tên gốc, đáp án tác giả, đa giác, tọa độ ảnh, nguồn annotation/template, chữ viết và trạng thái đánh giá khả năng đọc.',
        '- Tên field01 không bị đoán thành họ tên/CCCD. Trường không có ý nghĩa ngữ nghĩa được tác giả xác định giữ semantic_key rỗng.',
        '- Đáp án tác giả và phần chữ quan sát được là hai mục riêng; Clean/Blur không được dùng thay transcript hoặc độ đọc được.',
        '- Tọa độ của ảnh chụp được chiếu từ template qua góc thẻ tác giả; chưa phải hộp chữ từng frame được người gán độc lập.',
        '- Chia 30/10/10 theo giấy tờ, gom cả MIDV-500, MIDV-2019 và ảnh tham chiếu. Đây là dữ liệu lịch sử đã có exposure, không trở thành test mới cho model cũ.', '',
        '## Kiểm chứng nguồn và tọa độ', '',
        f'Đã băm lại độc lập {data["original_images"]:,} ảnh ({data["original_bytes_rehashed"]:,} byte), '
        f'đối chiếu {data["author_field_records_checked"]:,} trường với annotation gốc. '
        f'Phép tính homography độc lập có sai lệch tối đa {data["independent_projection_max_absolute_error"]:.6g} pixel; '
        f'sai lệch tỷ lệ cắt khung tối đa {data["independent_clipping_max_fraction_error"]:.6g}. '
        'Các kiểm tra này xác nhận phép chiếu và nguồn dữ liệu, không chứng minh mọi hộp khớp hoàn hảo với chữ thực hoặc người đọc được ảnh.', '',
        f'Đã dựng lại {data["synthetic_rasters_rebuilt"]} raster giả lập và {data["photographed_views_rebuilt"]} view ảnh chụp; '
        f'kiểm tra {data["glyph_field_checks"]} vùng glyph. '
        f'Đối chiếu {data["previous_unique_encoded_images_checked"]} ảnh VLM cũ; số trùng pixel mới: {data["new_pixel_overlap"]}.', '',
        '## Bộ kiểm chứng mới', '',
        f'{card["views"]} view, {card["document_instances"]} ID, {card["distinct_decoded_rasters"]} raster khác nhau; vai trò: {card["roles"]}. '
        '32 ID giả lập được dựng theo 2 bố cục × 2 nhóm font × full/che giá trị; '
        '24 ID ảnh chụp MIDV-2020 mới chọn có full/che giá trị. Font Tahoma/Times là font giá trị mới so với fine-tuning cục bộ; '
        'ngôn ngữ/nhãn, nội dung, thứ tự trường và cỡ chữ được kiểm soát theo ID. Không nhận là font chưa có trong pretraining.', '',
        f'Thiết bị ảnh chụp: {card["public_photo_devices"]}. Đây là instance mới từ cùng bộ công khai, không phải quần thể camera mới. '
        'Đọc được vẫn chưa được người đánh giá; tham chiếu là đáp án tác giả/nguồn còn được khai báo. '
        'Benchmark ngữ nghĩa giới hạn 17 khóa hiện có; lớp annotation gốc vẫn giữ mọi trường native.', '',
        '## Kết quả cố định theo nguồn trên test', '',
        '| Reader | Full giả lập F1 | Che giả lập F1 | Full ảnh chụp F1 | Che ảnh chụp F1 |',
        '|---|---:|---:|---:|---:|']
    from research.labels_metrics import summary
    for model in MODELS:
        values=[]
        for source,capture in (('authored','full'),('authored','value_mask'),('midv2020','full'),('midv2020','value_mask')):
            subset=[r for r in results[model]['rows'] if r['role']=='test' and r['source']==source and r['capture']==capture]
            values.append(summary(subset)['f1'])
        lines.append('| '+model+' | '+' | '.join(f'{v:.4f}' for v in values)+' |')
    lines+=['', 'Các F1 là đối chiếu tham chiếu tác giả/nguồn được khai báo, không phải độ chính xác đã lọc bằng nhãn legibility của người.', '',
        '## Tách riêng bố cục và font trên ảnh giả lập full', '',
        '| Reader | Bố cục cũ/font cũ | Bố cục mới/font cũ | Bố cục cũ/font mới | Cả hai mới |',
        '|---|---:|---:|---:|---:|']
    from research.labels_synth import CONDITIONS
    for model in MODELS:
        cells=factorial['models'][model]['full']['conditions']
        lines.append('| '+model+' | '+' | '.join(f'{cells[c]["f1"]:.4f}' for c in CONDITIONS)+' |')
    lines+=['', '| Reader | Hiệu ứng | ΔF1 | CI95% |','|---|---|---:|---|']
    for model in MODELS:
        for name,v in factorial['models'][model]['full']['contrasts'].items():
            lines.append(f'| {model} | {name} | {v["delta"]:+.4f} | [{v["ci95_low"]:+.4f}, {v["ci95_high"]:+.4f}] |')
    lines+=['', 'Bootstrap 10.000 lần theo ID, seed 20261109; giữ bốn điều kiện của cùng ID trong một cụm. '
        'CI mô tả chưa điều chỉnh nhiều phép so sánh, có điều kiện trên model, hai font và hai bố cục cố định. '
        'Ảnh chụp được báo riêng, không gọi chênh lệch nguồn là hiệu ứng nhân quả của camera.', '',
        '## Lượt chạy, phục hồi và kiểm thử', '',
        f'Đã replay {audit["replayed_score_rows"]} hàng điểm từ raw output và {audit["additional_fresh_calls"]} lượt đọc lại trực tiếp từ pixel. '
        f'Có {audit["fresh_output_hash_mismatches"]} hash output đọc lại khác lượt chính. '
        f'Ledger ghi {audit["generation_attempts"]} lần bắt đầu, {audit["completed_text_generation_calls"]} lần hoàn tất, '
        f'{audit["failed_generation_attempts"]} lần lỗi và {audit["interrupted_attempts_without_end"]} lần chưa rõ trạng thái kết thúc. '
        'Cache resume không được đếm thành lượt OCR mới; dựng dữ liệu, băm, phép chiếu và bootstrap không được đếm thành lượt sinh văn bản.', '',
        'Thời gian mỗi ảnh tính từ pixel RGB đã giải mã qua rect2/OCR/parser; thời gian đọc/giải mã file được ghi riêng. '
        'Không gồm tải model. GPU VLM và CPU ONNX không phải đối chứng tốc độ cùng phần cứng. Mọi lỗi JSON, output rỗng và chạm384 token được giữ.', '',
        f'{verification["unique_python_checks"]} kiểm tra Python khác nhau, {verification["subtests_passed"]} subtest và '
        f'{verification["frontend_checks"]} kiểm tra giao diện đã qua; thêm kiểm tra cú pháp JavaScript mới và 48 API tác vụ mù trên dữ liệu thật. '
        f'Có {verification["warnings"]} cảnh báo trong log. Hash {len(verification["tested_working_tree_sources"])} file mã nguồn/môi trường '
        'được giữ nguyên trong suốt lượt kiểm tra. Các fixture đánh giá không được ghi vào dữ liệu người thật.', '',
        'Một lượt chuẩn bị manifest ban đầu thiếu đường dẫn private wheel RapidOCR; đã dùng loader cache SHA-verified hiện có trước mọi dự đoán. '
        'Không cài dependency hoặc tạo venv mới; xem [vấn đề chuẩn bị](results/ocr_labels_v1/preparation_issues.json).', '',
        '## Dùng dữ liệu và trang localhost', '',
        'Mở [trang nhãn OCR](http://127.0.0.1:8005/): lọc ảnh, xem vùng chữ/đáp án tác giả, kéo để đề xuất vùng mới, '
        'hoặc mở chế độ đánh giá độc lập không nhận đáp án/box ký tự/output OCR. '
        'Các đề xuất là append-only, lưu ở SQLite riêng; không sửa nhãn phát hành hoặc test đã công bố.', '',
        f'Bản xuất annotations ở local có {exports["annotations"]["images"]:,} ảnh và {exports["annotations"]["fields"]:,} trường; '
        f'bản xuất chỉ nhãn người đã được xác nhận hiện có {exports["verified"]["fields"]} trường. '
        'Không tự biến đáp án tác giả nằm ngoài ảnh hoặc bị che thành training target quan sát được. '
        'Ảnh, text riêng và weights không đưa lên Git. Hai mã reviewer/tích ô tự khai chưa chứng minh có hai người độc lập.', '',
        'Còn cần hai người thực sự đánh giá và xử lý bất đồng để kết thúc phần legibility độc lập của mục1; '
        'bộ ảnh camera mới có sự đồng ý vẫn chưa có. Không huấn luyện lại hoặc chọn model bằng test đã mở này. '
        'eKYC8000 và web nghiên cứu8003 đã được xác nhận hoạt động, web8003 tiếp tục dùng partial_42.', '',
        'Bằng chứng: [audit dữ liệu](results/ocr_labels_v1/data_audit.json), [audit output](results/ocr_labels_v1/audit.json), '
        '[hiệu ứng bố cục/font](results/ocr_labels_v1/factorial_effects.json), [các lát dữ liệu](results/ocr_labels_v1/slices.json), '
        '[kiểm thử phần mềm](results/ocr_labels_v1/software_verification.json), [protocol](OCR_LABELS_PROTOCOL.md), '
        '[hướng dẫn](OCR_LABELS_RUNBOOK.md). Nguồn: [MIDV-2020](https://arxiv.org/abs/2107.00396); giữ attribution/CC BY-SA2.5.']
    path=ROOT/'research/OCR_LABELS_RESULTS_VI.md';path.write_text('\n'.join(lines)+'\n',encoding='utf-8',newline='\n')
    try:
        import matplotlib
        matplotlib.use('Agg');import matplotlib.pyplot as plt
        fig,ax=plt.subplots(figsize=(10,4.8));x=np.arange(4);width=.24
        for i,model in enumerate(MODELS):
            cells=factorial['models'][model]['full']['conditions'];y=np.array([cells[c]['f1'] for c in CONDITIONS])
            low=y-np.array([cells[c]['ci95_low'] for c in CONDITIONS]);high=np.array([cells[c]['ci95_high'] for c in CONDITIONS])-y
            ax.bar(x+(i-1)*width,y,width,label=model,yerr=[np.maximum(0,low),np.maximum(0,high)],capsize=3)
        ax.set_xticks(x,['Seen layout\nSeen font','New layout\nSeen font','Seen layout\nNew font','New layout\nNew font'])
        ax.set_ylim(0,1);ax.set_ylabel('Author-reference field F1');ax.set_title('Fixed-reader transfer: 24 paired authored test IDs')
        ax.legend();ax.grid(axis='y',alpha=.2);ax.set_axisbelow(True);fig.tight_layout()
        fig.savefig(OUT/'font_layout_f1.png',dpi=300);fig.savefig(OUT/'font_layout_f1.svg');plt.close(fig)
    except ImportError:raise RuntimeError('Existing matplotlib runtime unavailable; do not claim figure generated')
    save(OUT/'report_provenance.json',dict(signature=sig,report_sha256=sha(path),report_code_sha256=sha(__file__),
        audit_sha256=sha(OUT/'audit.json'),software_verification_sha256=sha(OUT/'software_verification.json'),
        figure_sha256=sha(OUT/'font_layout_f1.png'),human_evidence_not_fabricated=True))
    print('LABEL_REPORT_READY',flush=True)

if __name__=='__main__':report()
