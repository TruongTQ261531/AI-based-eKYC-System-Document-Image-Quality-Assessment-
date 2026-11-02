"""Measured source-reference findings; acceptance/novelty are not fabricated."""
import time
import numpy as np
from research.v3_common import *

def report():
    audit=read(OUT/'audit.json')
    if audit['status']!='passed' or audit['signature']!=signature():raise ValueError('Source audit required')
    comp=read(OUT/'test_comparison.json');cpu=read(OUT/'test_cpu.json');lock=read(OUT/'test_lock.json')
    pub=read(OUT/'lock_publication.json');card=read(OUT/'dataset_card.json');ci=read(OUT/'paired_intervals.json');fresh=read(OUT/'fresh_repeats.json')
    from research.v3_fusion import MODELS,fusion_signature
    fusion_audit=read(OUT/'fusion_audit.json');fusion_lock=read(OUT/'fusion_lock.json')
    if fusion_audit['status']!='passed' or fusion_audit['signature']!=fusion_signature():raise ValueError('Secondary audit required')
    from research.v3_metrics import summary
    records={k:read(OUT/f'test_{k}.json') for k in MODELS};rows={k:r['rows'] for k,r in records.items()}
    from research.v3_diagnostics import run
    diagnostics=run()
    names=dict(original='Vintern gốc',v1='V1 chuyển tác vụ',control_42='R2 complete42',partial_42='R2 body-partial42',
        control_31415='R2 complete31415',partial_31415='R2 body-partial31415',source_42='V3 source-partial42',source_31415='V3 source-partial31415')
    for key in cpu['summaries']:rows[key]=[r for r in cpu['rows'] if r['model']==key];names[key]=key
    text=['# V3: kết quả xét nguồn thông tin còn nhìn thấy','',
        'Đã hoàn thành hai lượt LoRA bổ sung với cùng pixel và ngân sách R2, benchmark tám model VLM và sáu cấu hình hậu xử lý OCR CPU. '
        'Kết quả là thực nghiệm trên giấy tờ mẫu, không phải chứng nhận eKYC hoặc bảo đảm được nhận CORE B.','',
        '## Vấn đề và can thiệp có kiểm soát','',
        'Một giá trị trên hộ chiếu có thể xuất hiện ở ô thân thẻ, bản phiên âm và MRZ. Che một ô không đồng nghĩa mất thông tin. '
        'V3 tạo nhãn theo OR giữa các nguồn, AND giữa các dòng thành phần; ngày tháng chỉ dùng độ đầy đủ thực sự được in. '
        'MRZ chỉ có YYMMDD không cho phép tự bịa thêm thế kỷ. Các vùng và văn bản gốc do tác giả MIDV cung cấp; '
        'đây vẫn là proxy hình học, chưa có nhãn legibility độc lập của người đọc.','',
        f"- Giữ nguyên toàn bộ 1496 dòng ảnh R2, cùng hash và thứ tự. Train128 ID/640 slot ở nhánh partial,320 bước ×4 tích lũy =1280 lượt ảnh, hai seed42/31415.",
        '- Hai model source-aware được khởi tạo lại từ Vintern gốc, không tiếp tục adapter R2. So với R2 partial cùng seed, chỉ target giám sát thay đổi.',
        f"- Thay đổi {card['target_changes']['train/changed_targets']} target trong toàn bộ bảng train hai nhánh; "
        f"{card['target_changes']['test/changed_targets']} trường hợp test có target khác; "
        f"bổ sung {card['target_changes']['test/new_supported_keys']} key còn có nguồn hỗ trợ trong ảnh test.",
        '- Test48 ID/144 ảnh:24 SPECIMEN mới và24 giấy tờ mẫu chụp bằng điện thoại;14 nguồn Samsung không có trong train, '
        '8 ID của hai loại fin_id/lva_passport giữ riêng khỏi train. Các giới hạn camera/ID và pretraining như R2 vẫn còn.',
        f"- Cả hai khóa được kiểm tra remote tại [{pub['commit'][:7]}](https://github.com/TruongTQ261531/AI-based-eKYC-System-Document-Image-Quality-Assessment-/commit/{pub['commit']}) trước test.",
        '- Sáu output R2 được chấm lại trên cùng pixel, không gọi đó là sáu thí nghiệm suy luận độc lập mới. Báo cáo R2 theo hợp đồng cũ vẫn được giữ nguyên.','',
        '## Test dưới hợp đồng nguồn V3','',
        '| Phương án | F1 mọi nguồn | F1 đủ độ chính xác ngày | F1 ảnh dựng | F1 ảnh chụp | Bỏ sót | Sai giá trị | Key ngoài nhãn |',
        '|---|---:|---:|---:|---:|---:|---:|---:|']
    for key,value in rows.items():
        s=summary(value);a=summary([r for r in value if r['source']=='authored']);p=summary([r for r in value if r['source']=='midv2020'])
        text.append(f"| {names[key]} | {s['f1']:.4f} | {s['max_precision_f1']:.4f} | {a['f1']:.4f} | {p['f1']:.4f} | {s['visible_omissions']} | {s['wrong_visible_values']} | {s['unsupported_nonempty']} |")
    text+=['','Cột độ chính xác ngày chỉ chấp nhận mức năm đầy đủ nhất còn được thể hiện trong các nguồn khai báo. '
        'Ngày hai chữ số năm vẫn là một quan sát hợp lệ, nhưng không được đánh đồng với ngày có năm bốn chữ số. '
        '“Ngoài nhãn” luôn tương đối với tập nguồn khai báo, không chứng minh mọi giá trị là bịa hoặc mọi nguồn ngoài hợp đồng đều không tồn tại.',
        '','## Ngân sách và chi phí huấn luyện','',
        '| Nhánh | Seed | Bước | Lượt ảnh | Token tính loss | Token đầu vào + đáp án | Giây vòng tối ưu | GPU allocated tối đa (GiB) |',
        '|---|---:|---:|---:|---:|---:|---:|---:|']
    for seed0 in CONFIG['seeds']:
        for arm in ('control','partial','source'):
            folder=OUT if arm=='source' else R2OUT;r=read(folder/f'train_{arm}_{seed0}.json');events=r['events'];tokens=r['token_exposure']
            text.append(f"| {arm} | {seed0} | {r['steps']} | {r['presentations']} | {tokens['answer_loss_tokens']} | {tokens['input_and_answer_tokens']} | {events[-1]['wall_seconds']:.1f} | {max(e['peak_allocated_bytes'] for e in events)/2**30:.3f} |")
    text+=['','Ngân sách được khớp theo bước và lượt ảnh; số token giám sát thay đổi theo target và được công khai ở trên. '
        'Thời gian vòng tối ưu không bao gồm mọi bước nạp model/chuẩn bị dữ liệu. GPU allocated là bộ đếm PyTorch, '
        'không phải toàn bộ VRAM của hệ thống. Bộ đếm reserved trên Windows/WDDM không được gọi là lượng VRAM vật lý đã dùng.']
    text+=['','## Thời gian và proxy yêu cầu chụp lại','',
        '| Phương án | Đường đo | p50 (s) | p95 (s) | Output rỗng hoặc JSON lỗi |',
        '|---|---|---:|---:|---:|']
    for key,value in rows.items():
        times=[r['wall_seconds'] for r in value];s=summary(value)
        mode='VLM GPU, đọc feature cache' if key in MODELS else 'OCR CPU, xử lý ảnh + hậu xử lý'
        text.append(f"| {names[key]} | {mode} | {np.percentile(times,50):.2f} | {np.percentile(times,95):.2f} | {s['retake_proxy_rate']:.1%} |")
    text+=['','Các dòng GPU dùng cache chưa phải độ trễ camera đầu cuối. Phép lặp ảnh mới của model được chọn được báo bên dưới; '
        'nạp model nguội được đo riêng với thời gian suy luận khi chạy web. CPU và GPU không phải đối chiếu tốc độ trên phần cứng tương đương. '
        'Một số lượt CPU chạy song song công việc GPU; không dùng bảng này để tuyên bố thắng tuyệt đối về tốc độ. '
        'Output rỗng/JSON lỗi chỉ là proxy, không phải tỷ lệ khách hàng chụp lại được quan sát, cũng không phải quyết định eKYC.']
    text+=['','## So sánh đúng cặp và khoảng tin cậy','',
        '| So sánh | ΔF1 | CI95% theo ID |','|---|---:|---:|']
    for p in ci['comparisons']:text.append(f"| {p['a']} − {p['b']} | {p['delta']:+.4f} | [{p['ci95_low']:+.6f}, {p['ci95_high']:+.6f}] |")
    text+=['','Bootstrap10000 lần theo48 cụm ID, phân tầng24+24 nguồn; hai seed được báo riêng. '
        'Đây không phải CI bao phủ mọi biến động training hay camera ngoài mẫu.','',
        '## Phân tích mô tả ảnh hưởng của hợp đồng nhãn','',
        'Phân tích sau thực nghiệm, không dùng chọn model. Giữ nguyên từng output để chấm theo hai hợp đồng; không phát sinh suy luận mới.',
        f"Tổng trường tham chiếu test: thân thẻ {diagnostics['body_test_reference_fields']}, nhiều nguồn {diagnostics['source_test_reference_fields']}. "
        f"Nguồn hỗ trợ cho key bổ sung: {diagnostics['added_reference_origins']}.",'',
        '| Model | F1 thân thẻ | F1 nhiều nguồn | Ngoài nhãn cũ → đúng theo nguồn | Mới được tính nhưng model bỏ sót |',
        '|---|---:|---:|---:|---:|']
    for key,d in diagnostics['models'].items():
        text.append(f"| {names[key]} | {d['body_contract_f1']:.4f} | {d['source_contract_f1']:.4f} | {d['formerly_outside_now_correct']} | {d['newly_supported_but_omitted']} |")
    text+=['',
        '## Kiểm chứng và ứng dụng local','',
        f"- Phát lại {audit['replayed_prediction_rows']} hàng kết quả nguồn từ output nguyên văn. "
        'Số hàng chấm lại và ba hậu xử lý dùng chung OCR không được tính thành số lần suy luận độc lập.',
        '- Audit R2 đã đối chiếu mọi feature vision dùng trong nghiên cứu với trích xuất mới từ pixel, cùng các file/weights/checkpoint và budget. V3 dùng đúng các pixel/feature này.',
        f"- Hai lượt OCR CPU độc lập khớp nguyên văn ở {audit['independently_repeated_CPU_outputs_verified']} cặp output. Mỗi nhóm ba hậu xử lý V3 vẫn dùng chung một lần OCR, được đếm riêng với số cấu hình chấm điểm.",
        f"- Model được chọn từ development: **{lock['selected_model']}**; cổng khuyến nghị: **{lock['deployment_approved']}**. "
        'Nếu model source-aware không tốt hơn, không gọi nó là model thắng chỉ vì là phiên bản mới.',
        f"- Lặp thêm16 lần suy luận ảnh mới trên8 ảnh/4 ID: sai khác {fresh['mismatches']}; "
        f"p50={fresh['p50_fresh_seconds']:.2f}s, p95={fresh['p95_fresh_seconds']:.2f}s. Thời gian này có xử lý ảnh/vision, khác đọc feature cache.",
        '- Không tự gán thế kỷ; chữ số kiểm tra MRZ không chứng minh giấy tờ thật. Không phê duyệt danh tính, không đánh giá liveness ở trang OCR nghiên cứu.',
        '- Camera thật của người dùng chưa được dùng làm benchmark. Nhãn sửa bằng tay trên web được phân biệt với kết quả OCR và chỉ tồn tại trên trình duyệt.','',
        'Đã chuẩn bị [trang đánh giá độc lập](http://127.0.0.1:8003/review) với 48 ảnh, mỗi ID một view. '
        'Hiện chưa nhận được nhãn của người; kiểm thử giao diện bằng câu trả lời giả không tính là annotation. '
        'Xem V3_HUMAN_REVIEW.md; phần bổ sung không đổi tham chiếu chính đã khóa.','',
        '## Đóng góp có thể viết và giới hạn','',
        'Có thể viết về sai lệch đánh giá khi dùng một ô làm toàn bộ bằng chứng, nhãn theo nhiều nguồn/thành phần và độ chính xác ngày, '
        'và phép thử LoRA ít tham số được kiểm soát pixel/ngân sách. Chỉ kết quả thực nghiệm mới quyết định can thiệp có hiệu quả.',
        'Không nhận OR/AND, MRZ fusion hoặc LoRA là phát minh đầu tiên. Cần đối chiếu với '
        '[KIE-HVQA](https://arxiv.org/abs/2506.20168), '
        '[nghiên cứu redundancy trong OCR](https://arxiv.org/abs/2508.14557), '
        '[BoundingDocs](https://flore.unifi.it/retrieve/271bfa4d-4b12-4bd3-8ec1-a5f64ce8ca0b/s10032-025-00563-5.pdf) '
        'và [ICAO Doc9303 Part4](https://www.icao.int/sites/default/files/publications/DocSeries/9303_p4_cons_en.pdf).',
        'CORE B chưa thể khẳng định chỉ nhờ fine-tune/đổi nhãn. Còn thiếu tập ảnh Việt Nam mới tự chụp có phép, '
        'nhãn legibility độc lập, nhiều camera/ID và backbone hơn. Hợp đồng nguồn chỉ gồm các vùng tác giả và TD3 đã khai báo, '
        'không bao phủ mọi thông tin suy ra từ mã quốc gia/QR/đặc điểm khuôn mặt. Chưa có kiểm chứng người thật hoặc chống giả.','']
    fused=read(OUT/'test_fusion.json')['models']
    text+=['','## Baseline bổ sung: điền trường thiếu từ MRZ hợp lệ','',
        'Đăng ký sau khi xem development, trước mọi suy luận test. Tám phép ghép dùng output VLM đã có và cùng OCR CPU rapid_v4; '
        'không phải tám model mới hay tám lượt suy luận VLM độc lập. Không ghi đè giá trị, sửa ký tự hoặc suy đoán thế kỷ. '
        'Checksum không chứng minh giấy tờ thật. Thời gian ghép cache là tổng bộ đếm thành phần, chưa phải độ trễ một request đầu cuối.','',
        '| VLM thành phần | F1 gốc | F1 ghép | Bỏ sót gốc → ghép | Ngoài nhãn gốc → ghép |',
        '|---|---:|---:|---:|---:|']
    for key in MODELS:
        a=summary(rows[key]);b=fused[key]['summary']
        text.append(f"| {names[key]} | {a['f1']:.4f} | {b['f1']:.4f} | {a['visible_omissions']} → {b['visible_omissions']} | {a['unsupported_nonempty']} → {b['unsupported_nonempty']} |")
    text+=['',f"Chọn thành phần từ development: {fusion_lock['component']}; bật ghép trên web: **{fusion_lock['use_fusion_on_development']}**. "
        'Chỉ bật khi F1 development tăng và số key ngoài nhãn không tăng; không dùng test để đổi quyết định. '
        f"Đã phát lại {fusion_audit['rows_replayed']} phép ghép; thêm {fusion_audit['fresh_calls']} lần gọi ảnh mới cho hybrid. "
        'Nếu development không có lợi ích, web giữ VLM đơn và không chạy thêm hybrid chỉ để tăng số lần kiểm thử.','']
    text+=['','## Chẩn đoán riêng các trường có thêm nguồn hỗ trợ','',
        'Đây là phân tích mô tả bổ sung, không dùng chọn model hoặc thay kết quả tổng thể. '
        'Chỉ xét key vắng trong hợp đồng thân thẻ nhưng có nguồn khai báo còn hiện trong V3. '
        'Các key/ảnh cùng giấy tờ không phải các mẫu độc lập; không coi số trường là số người hoặc ID.','',
        '| Model | Trường bổ sung | Đúng | Sai giá trị | Bỏ sót | Recall tập con |',
        '|---|---:|---:|---:|---:|---:|']
    for key,d in diagnostics['models'].items():
        text.append(f"| {names[key]} | {d['newly_supported_reference_fields']} | {d['formerly_outside_now_correct']} | {d['newly_supported_wrong_values']} | {d['newly_supported_but_omitted']} | {d['newly_supported_recall']:.4f} |")
    text+=['','Can thiệp target chỉ thay đổi 22/640 slot train của nhánh partial; '
        'phải xem cả hiệu quả ở trường bổ sung lẫn đánh đổi trên các trường khác. '
        'Kết quả tốt ở tập con không tự chứng minh model tốt hơn trên toàn bộ test.']
    text+=['','## Ngân sách sinh văn bản','',
        'Tất cả model VLM dùng cùng giới hạn 384 token mới. Cờ chạm giới hạn cho biết đã dùng hết ngân sách; '
        'không tự chứng minh model bịa thông tin hoặc biết nguyên nhân output sai. Không đổi giới hạn sau khi mở test.','',
        '| Model | Lượt test | Chạm giới hạn | Trung vị token sinh |','|---|---:|---:|---:|']
    for key,d in diagnostics['models'].items():
        text.append(f"| {names[key]} | {d['test_generations']} | {d['token_limit_hits']} | {d['median_generated_tokens']} |")
    text+=['','## Tương tác giữa hợp đồng nhãn và mức cải thiện được đo','',
        'Phân tích thăm dò bổ sung trên đúng output đã có: so chênh lệch F1 partial − control '
        'dưới hai hợp đồng. Giá trị thay đổi = chênh lệch theo nguồn − chênh lệch theo thân thẻ. '
        'Không dùng kết quả này để chọn model hay thay giả thuyết chính. Bootstrap ghép cặp 10000 lần '
        'theo 48 cụm giấy tờ, phân tầng nguồn, seed 20261103; CI thăm dò chưa chỉnh đa so sánh. '
        'Đây là khác biệt hợp đồng tác vụ, không phải chứng minh mọi bộ nhãn trước đó sai.','',
        '| Seed | Gain theo thân thẻ | Gain theo nguồn | Thay đổi gain | CI95% thay đổi |',
        '|---|---:|---:|---:|---:|']
    for d in diagnostics['training_gain_contract_interactions']['rows']:
        text.append(f"| {d['seed']} | {d['body_contract_gain']:+.4f} | {d['source_contract_gain']:+.4f} | {d['gain_change']:+.4f} | [{d['ci95_low']:+.6f}, {d['ci95_high']:+.6f}] |")
    text+=['','Hai pipeline CPU body-only đạt F1=0 ở tập con ảnh chụp. Đây là phép đo cả OCR '
        'và bộ ghép nhãn có alias tiếng Anh/Việt hạn chế, không phải độ chính xác nhận chữ độc lập. '
        'Không dùng kết quả này để tuyên bố VLM vượt mọi OCR hiện đại hoặc bộ trích xuất chuyên cho từng ngôn ngữ/giấy tờ.']
    if (OUT/'cpu_label_supplement_test.json').exists():
        extra=read(OUT/'cpu_label_supplement_test.json');dev_extra=read(OUT/'cpu_label_supplement_development.json')
        extra_audit=read(OUT/'cpu_label_supplement_audit.json');choice_extra=read(OUT/'cpu_label_supplement_choice.json')
        from research.v3_cpu_supplement import supplement_signature
        if extra_audit['status']!='passed' or extra_audit['signature']!=supplement_signature():raise ValueError('CPU label supplement audit required')
        text+=['','## Kiểm tra hậu nghiệm vị trí nhãn trong pipeline CPU','',
            'Thiết kế sau khi đã thấy kết quả test gốc, không phải test xác nhận độc lập. Hai cách chuẩn hóa '
            'tiền tố/song ngữ dùng cùng alias và ghép hình học, mỗi cách có/không fallback MRZ, cho hai reader. '
            'Tái dùng output OCR đã có, không phát sinh lượt OCR hay VLM mới. Giữ đủ tám cấu hình và kết quả gốc. '
            'Thời gian chỉ là tổng timer OCR cũ với timer parsing mới; không phải đo đầu cuối mới.','',
            '| Cấu hình bổ sung | F1 dev | F1 test | F1 test ảnh chụp | Key ngoài nhãn |',
            '|---|---:|---:|---:|---:|']
        for key,value in extra['models'].items():
            s=value['summary'];photo=summary([r for r in value['rows'] if r['source']=='midv2020'])
            text.append(f"| {key} | {dev_extra['models'][key]['summary']['f1']:.4f} | {s['f1']:.4f} | {photo['f1']:.4f} | {s['unsupported_nonempty']} |")
        text+=['',f"Chọn trong phần bổ sung bằng dev: {choice_extra['selected']}. "
            f"Đã phát lại {extra_audit['derived_rows_replayed']} hàng chấm; số suy luận neural thêm: 0. "
            'Đây là chẩn đoán độ nhạy của một bộ ghép nhãn đơn giản, không phải baseline SOTA hoặc căn cứ đổi model web. '
            'Benchmark và cổng triển khai chính không thay đổi.']
    from research.v2_interruptions import appendix
    text+=appendix(rows,names,OUT)
    path=ROOT/'research/V3_RESULTS_VI.md';path.write_text('\n'.join(text),encoding='utf-8',newline='\n')
    from research.v3_artifacts import make
    make()
    save(OUT/'report_provenance.json',dict(signature=signature(),report_sha256=sha(path),audit_sha256=sha(OUT/'audit.json'),lock_sha256=sha(OUT/'test_lock.json')))
    (ROOT/'research/V3_STATUS.md').write_text('# V3 completed\n\nJoint locks published before test, eight VLM comparators and six CPU configurations scored, raw outputs replayed.\n'
        'See V3_RESULTS_VI.md. Actual-user camera and independent human legibility evaluation remain unperformed.\n',encoding='utf-8',newline='\n')
    print('SOURCE_REPORT_READY',flush=True)

if __name__=='__main__':report()
