# Mục 1: nhãn OCR có nguồn gốc và kiểm chứng bố cục/font/ảnh chụp

Đã hoàn tất lớp nhãn tác giả, vị trí, xuất dữ liệu, bộ kiểm chứng mới và các kiểm tra tự động. Đánh giá khả năng đọc chuyển sang pilot một người theo nguồn lực người dùng xác nhận. Không gọi nhãn hình học hoặc kết quả OCR là nhãn đọc được của người; không tính hai lượt của cùng người thành hai reviewer.

Theo snapshot xuất lúc 2026-11-04T02:26:14.245322+00:00: 6/48 mẫu pilot đã nhận đánh giá, 30 lượt trường đánh giá đơn và 0 nhãn trường đạt đối chiếu độc lập. Không có bộ ảnh camera mới tự thu thập có sự đồng ý của người tham gia. Kết quả này không tự xác nhận đủ đóng góp CORE B.

## Bộ ảnh gốc và từng trường OCR

- 21,050 ảnh, 229,866 bản ghi vùng chữ, 50 nhóm giấy tờ gốc.
- Nguồn: {'midv2019': 6050, 'midv500': 15000}; chất lượng: {'Blur': 3000, 'Clean': 9050, 'Cropped': 3000, 'Dark': 3000, 'Distorted': 3000}.
- Giữ đủ 50 ảnh tham chiếu MIDV-2019 bổ sung thuộc Clean; đây vẫn là cùng 50 giấy tờ, không phải 50 người mới.
- Mỗi trường giữ tên gốc, đáp án tác giả, đa giác, tọa độ ảnh, nguồn annotation/template, chữ viết và trạng thái đánh giá khả năng đọc.
- Tên field01 không bị đoán thành họ tên/CCCD. Trường không có ý nghĩa ngữ nghĩa được tác giả xác định giữ semantic_key rỗng.
- Đáp án tác giả và phần chữ quan sát được là hai mục riêng; Clean/Blur không được dùng thay transcript hoặc độ đọc được.
- Tọa độ của ảnh chụp được chiếu từ template qua góc thẻ tác giả; chưa phải hộp chữ từng frame được người gán độc lập.
- Chia 30/10/10 theo giấy tờ, gom cả MIDV-500, MIDV-2019 và ảnh tham chiếu. Đây là dữ liệu lịch sử đã có exposure, không trở thành test mới cho model cũ.

## Kiểm chứng nguồn và tọa độ

Đã băm lại độc lập 21,050 ảnh (116,173,241,398 byte), đối chiếu 229,866 trường với annotation gốc. Phép tính homography độc lập có sai lệch tối đa 0.000122069 pixel; sai lệch tỷ lệ cắt khung tối đa 2.54592e-06. Các kiểm tra này xác nhận phép chiếu và nguồn dữ liệu, không chứng minh mọi hộp khớp hoàn hảo với chữ thực hoặc người đọc được ảnh.

Đã dựng lại 256 raster giả lập và 48 view ảnh chụp; kiểm tra 1280 vùng glyph. Đối chiếu 2373 ảnh VLM cũ; số trùng pixel mới: 0.

## Bộ kiểm chứng mới

304 view, 56 ID, 304 raster khác nhau; vai trò: {'development': 80, 'test': 224}. 32 ID giả lập được dựng theo 2 bố cục × 2 nhóm font × full/che giá trị; 24 ID ảnh chụp MIDV-2020 mới chọn có full/che giá trị. Font Tahoma/Times là font giá trị mới so với fine-tuning cục bộ; ngôn ngữ/nhãn, nội dung, thứ tự trường và cỡ chữ được kiểm soát theo ID. Không nhận là font chưa có trong pretraining.

Thiết bị ảnh chụp: {'SM-G973F': 10, 'iPhone XS Max': 14}. Đây là instance mới từ cùng bộ công khai, không phải quần thể camera mới. Đọc được vẫn chưa được người đánh giá; tham chiếu là đáp án tác giả/nguồn còn được khai báo. Benchmark ngữ nghĩa giới hạn 17 khóa hiện có; lớp annotation gốc vẫn giữ mọi trường native.

## Kết quả cố định theo nguồn trên test

| Reader | Full giả lập F1 | Che giả lập F1 | Full ảnh chụp F1 | Che ảnh chụp F1 |
|---|---:|---:|---:|---:|
| rapid_v4 | 0.5841 | 0.5809 | 0.2471 | 0.1905 |
| rapid_latin_v5 | 0.6354 | 0.6069 | 0.0649 | 0.0725 |
| partial_42 | 0.8833 | 0.8301 | 0.6061 | 0.6077 |

Các F1 là đối chiếu tham chiếu tác giả/nguồn được khai báo, không phải độ chính xác đã lọc bằng nhãn legibility của người.

## Các đầu ra không đạt trên toàn bộ 224 view test

| Reader | JSON không hợp lệ | Không trích được trường | Chạm384 token | Giá trị ngoài nguồn tham chiếu |
|---|---:|---:|---:|---:|
| rapid_v4 | 0/224 | 26/224 | không áp dụng | 21 |
| rapid_latin_v5 | 0/224 | 29/224 | không áp dụng | 26 |
| partial_42 | 3/224 | 3/224 | 1 | 69 |

Các cột có thể trùng cùng một ảnh, không cộng lại thành số ca lỗi. Không có trường trích được là proxy yêu cầu chụp lại, chưa phải tỷ lệ khách hàng thực sự phải chụp lại. Giá trị ngoài nguồn tham chiếu là lỗi theo hợp đồng chấm hiện tại, không tự chứng minh nguyên nhân hallucination hoặc khả năng đọc của người.

## Tách riêng bố cục và font trên ảnh giả lập full

| Reader | Bố cục cũ/font cũ | Bố cục mới/font cũ | Bố cục cũ/font mới | Cả hai mới |
|---|---:|---:|---:|---:|
| rapid_v4 | 0.5856 | 0.5556 | 0.6106 | 0.5833 |
| rapid_latin_v5 | 0.6354 | 0.6354 | 0.6354 | 0.6354 |
| partial_42 | 0.8833 | 0.8814 | 0.8619 | 0.9068 |

| Reader | Hiệu ứng | ΔF1 | CI95% |
|---|---|---:|---|
| rapid_v4 | combined_shift | -0.0023 | [-0.0444, +0.0378] |
| rapid_v4 | font_at_seen_layout | +0.0250 | [-0.0063, +0.0584] |
| rapid_v4 | layout_at_seen_font | -0.0300 | [-0.0788, +0.0175] |
| rapid_v4 | layout_font_interaction | +0.0027 | [-0.0428, +0.0501] |
| rapid_latin_v5 | combined_shift | +0.0000 | [+0.0000, +0.0000] |
| rapid_latin_v5 | font_at_seen_layout | +0.0000 | [+0.0000, +0.0000] |
| rapid_latin_v5 | layout_at_seen_font | +0.0000 | [+0.0000, +0.0000] |
| rapid_latin_v5 | layout_font_interaction | +0.0000 | [+0.0000, +0.0000] |
| partial_42 | combined_shift | +0.0234 | [-0.0319, +0.0806] |
| partial_42 | font_at_seen_layout | -0.0214 | [-0.0793, +0.0379] |
| partial_42 | layout_at_seen_font | -0.0020 | [-0.0743, +0.0739] |
| partial_42 | layout_font_interaction | +0.0468 | [-0.0251, +0.1199] |

Bootstrap 10.000 lần theo ID, seed 20261109; giữ bốn điều kiện của cùng ID trong một cụm. CI mô tả chưa điều chỉnh nhiều phép so sánh, có điều kiện trên model, hai font và hai bố cục cố định. Ảnh chụp được báo riêng, không gọi chênh lệch nguồn là hiệu ứng nhân quả của camera.

## Thời gian đo trực tiếp trên test full

| Reader | Nguồn | View | Pixel→OCR p50 giây | p95 giây | Kiểm hash/đọc/giải mã file p50 giây |
|---|---|---:|---:|---:|---:|
| rapid_v4 | authored | 96 | 1.228 | 1.822 | 0.008 |
| rapid_v4 | midv2020 | 16 | 3.070 | 6.863 | 0.128 |
| rapid_latin_v5 | authored | 96 | 1.378 | 1.807 | 0.008 |
| rapid_latin_v5 | midv2020 | 16 | 2.392 | 4.342 | 0.130 |
| partial_42 | authored | 96 | 13.261 | 17.511 | 0.010 |
| partial_42 | midv2020 | 16 | 17.821 | 39.698 | 0.137 |

## Lượt chạy, phục hồi và kiểm thử

Đã replay 912 hàng điểm từ raw output và 24 lượt đọc lại trực tiếp từ pixel. Có 0 hash output đọc lại khác lượt chính. Ledger ghi 936 lần bắt đầu, 936 lần hoàn tất, 0 lần lỗi và 0 lần chưa rõ trạng thái kết thúc. Cache resume không được đếm thành lượt OCR mới; dựng dữ liệu, băm, phép chiếu và bootstrap không được đếm thành lượt sinh văn bản.

Thời gian mỗi ảnh tính từ pixel RGB đã giải mã qua rect2/OCR/parser; thời gian đọc/giải mã file được ghi riêng. Không gồm tải model. GPU VLM và CPU ONNX không phải đối chứng tốc độ cùng phần cứng. Mọi lỗi JSON, output rỗng và chạm384 token được giữ.

344 kiểm tra Python khác nhau, 1496 subtest và 54 kiểm tra giao diện đã qua; thêm kiểm tra cú pháp JavaScript mới và 48 API tác vụ mù trên dữ liệu thật. Có 1 cảnh báo trong log. Hash 279 file mã nguồn/môi trường được giữ nguyên trong suốt lượt kiểm tra. Các fixture đánh giá không được ghi vào dữ liệu người thật.

Một lượt chuẩn bị manifest ban đầu thiếu đường dẫn private wheel RapidOCR; đã dùng loader cache SHA-verified hiện có trước mọi dự đoán. Không cài dependency hoặc tạo venv mới; xem [vấn đề chuẩn bị](results/ocr_labels_v1/preparation_issues.json).

## Dùng dữ liệu và trang localhost

Mở [trang nhãn OCR](http://127.0.0.1:8005/): lọc ảnh, xem vùng chữ/đáp án tác giả, kéo để đề xuất vùng mới, hoặc mở chế độ đánh giá độc lập không nhận đáp án/box ký tự/output OCR. Các đề xuất là append-only, lưu ở SQLite riêng; không sửa nhãn phát hành hoặc test đã công bố.

Trạng thái trong snapshot đánh giá đơn: {'not_present': 3, 'partial': 17, 'readable': 4, 'uncertain': 1, 'unreadable': 5}. Phiếu gửi sau thời điểm snapshot vẫn được giữ trong database live, không tự sửa báo cáo đã phát hành. Không biết ngôn ngữ hoặc chưa chắc chắn không bị coi thành nhãn âm “không đọc được”.

Có 0 mẫu được đề nghị kiểm tra/sửa/loại trong snapshot riêng. Các đề nghị không xóa ảnh hoặc loại case khỏi benchmark đã khóa, không tạo nhãn đọc được và không được cộng thành mẫu đã gán nhãn xong. Lý do riêng và lịch sử rút đề nghị được giữ ở local; nếu tạo tập đã chỉnh sửa phải phát hành phiên bản mới và báo quy tắc loại.

Bản xuất annotations ở local có 21,050 ảnh và 229,866 trường; bản xuất đánh giá đơn có 30 lượt trường; bản xuất đối chiếu nhiều người hiện có 0 trường. Không tự biến đáp án tác giả nằm ngoài ảnh hoặc bị che thành training target quan sát được. Ảnh, text riêng và weights không đưa lên Git. Hai mã reviewer/tích ô tự khai chưa chứng minh có hai người độc lập.

Một người có thể hoàn thành pilot, kiểm thử web và cung cấp nhãn người sơ bộ. Độ hoàn thành phải dựa vào phiếu thực tế; cần thêm người độc lập và xử lý bất đồng nếu muốn báo cáo độ đồng thuận giữa người gán nhãn. bộ ảnh camera mới có sự đồng ý vẫn chưa có. Không huấn luyện lại hoặc chọn model bằng test đã mở này. eKYC8000 và web nghiên cứu8003 đã được xác nhận hoạt động, web8003 tiếp tục dùng partial_42.

Bằng chứng: [audit dữ liệu](results/ocr_labels_v1/data_audit.json), [audit output](results/ocr_labels_v1/audit.json), [hiệu ứng bố cục/font](results/ocr_labels_v1/factorial_effects.json), [các lát dữ liệu](results/ocr_labels_v1/slices.json), [kiểm thử phần mềm](results/ocr_labels_v1/software_verification.json), [protocol](OCR_LABELS_PROTOCOL.md), [hướng dẫn](OCR_LABELS_RUNBOOK.md), [pilot một người](OCR_LABELS_SINGLE_REVIEW.md). Nguồn: [MIDV-2020](https://arxiv.org/abs/2107.00396); giữ attribution/CC BY-SA2.5.
