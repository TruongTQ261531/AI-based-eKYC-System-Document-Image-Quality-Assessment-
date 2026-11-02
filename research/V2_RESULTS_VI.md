# V2: kết quả đo thực tế và giới hạn

Đã hoàn thành bốn lượt LoRA (hai phương án × hai seed), benchmark mới, đối chứng CPU, lặp suy luận ảnh mới và phát lại kết quả từ output gốc. V1 và V4 được giữ nguyên.

## Thiết kế và dữ liệu

- Train 128 ID: 96 SPECIMEN mới + 32 ảnh MIDV đã dùng ở vòng trước, nay chỉ dùng train. Mỗi phương án 640 ảnh/slot, 320 bước × 4 tích lũy = 1280 lượt ảnh, đúng hai epoch.
- Development 24 ID/72 ảnh; test 48 ID/144 ảnh (24 ảnh dựng + 24 giấy tờ mẫu chụp bằng điện thoại, mỗi ID ba biến thể). Toàn bộ ID ảnh chụp dùng dev/test chưa thuộc 80 ID nghiên cứu trước.
- Test có 14 nguồn Samsung không dùng trong train V2, 10 nguồn iPhone. Hai loại fin_id/lva_passport (8 ID) không có trong train; ảnh dựng test dùng bố cục và font khác.
- Đây là tác vụ KIE trên 17 khóa tùy chọn, không phải đánh giá mọi văn bản trên mọi giấy tờ. Các biến thể bản ngữ/phiên âm và nhóm dòng đã ánh xạ được giữ trong tham chiếu. R2 chưa dùng MRZ hoặc các trường chưa ánh xạ làm nguồn hỗ trợ bổ sung; phép so sánh nguồn được báo riêng ở V3.
- Mỗi phương án nhận đúng cùng chuỗi ID/slot và cùng ngân sách optimizer. Số token câu trả lời và thời gian thực tế có thể khác; đã lưu riêng trong train_*.json.
- MIDV là ảnh chụp giấy tờ GIẢ LẬP có transcript của tác giả, không phải một bộ CCCD thật mới tự thu thập. Nhãn sau cắt/che dựa trên hình học vùng giá trị; chưa có người đánh giá độc lập độ đọc được.

Pilot R1 dừng sau event286 (báo tiến độ định kỳ284) vì ánh xạ nhãn bỏ sót trường nhiều dòng/song ngữ, trước khi đánh giá model đã fine-tune trên development hoặc test. Toàn bộ pilot được giữ riêng; bốn lượt R2 khởi tạo lại từ model gốc, không dùng adapter pilot. R2 chấp nhận mọi biến thể tác giả còn hiển thị đầy đủ và ghép các dòng do tác giả đặt tên chung. Prediction model gốc chỉ được tái dùng khi hash ảnh, prompt và xử lý ảnh trùng hoàn toàn; đã chấm lại trên nhãn R2.

## Lựa chọn xử lý ảnh, chỉ dựa trên development

| Đầu vào | F1 trên panel | Trường ngoài nhãn, không rỗng | Giây/ảnh mới trung bình |
|---|---:|---:|---:|
| raw2 | 0.1633 | 172 | 17.04 |
| raw4 | 0.1951 | 169 | 17.90 |
| rect2 | 0.2176 | 168 | 16.85 |
| rect4 | 0.1801 | 166 | 17.57 |

Chọn **rect2** trước train/test. Nắn ảnh chỉ dùng góc dự đoán từ pixel và raw fallback; không dùng góc chuẩn. Không xóa trường khỏi GT nếu chính thuật toán nắn làm mất trường đó.

## Test đã khóa trước khi chấm

Lock được công bố ở [447e15b](https://github.com/TruongTQ261531/AI-based-eKYC-System-Document-Image-Quality-Assessment-/commit/447e15b9a3a8d8fd3e9677356bf6b70a2427dc03). Mọi model dùng cùng prompt, parser, nhãn và profile V2. V1 ở đây là chuyển sang tác vụ mới, không thay số đo V1 đã công bố.

| Phương án | F1 chung | F1 ảnh dựng | F1 ảnh chụp MIDV | Thiếu trường nhìn thấy | Sai giá trị nhìn thấy | Ngoài nhãn, không rỗng |
|---|---:|---:|---:|---:|---:|---:|
| Vintern gốc (prompt V2) | 0.1696 | 0.1772 | 0.1626 | 37 | 322 | 1670 |
| LoRA V1 chuyển sang tác vụ V2 | 0.3685 | 0.7073 | 0.1944 | 363 | 58 | 131 |
| V2 control /42 | 0.3737 | 0.4521 | 0.3296 | 79 | 233 | 417 |
| V2 partial /42 | 0.3949 | 0.5000 | 0.3325 | 150 | 188 | 274 |
| V2 control /31415 | 0.3753 | 0.4404 | 0.3379 | 92 | 227 | 386 |
| V2 partial /31415 | 0.4044 | 0.5276 | 0.3349 | 129 | 196 | 286 |
| rapid_v4 + ghép nhãn/vị trí | 0.2161 | 0.4860 | 0.0000 | 477 | 44 | 1 |
| rapid_latin_v5 + ghép nhãn/vị trí | 0.2143 | 0.5000 | 0.0000 | 499 | 25 | 1 |

“Ngoài nhãn, không rỗng” là key không có trong target quan sát được; có thể bao gồm chuỗi từ chối như N/A. Không đồng nhất toàn bộ số này với việc bịa thông tin danh tính. Parser phụ chỉ bỏ JSON fence trọn vẹn và giá trị null/rỗng; không sửa nội dung dựa trên đáp án. Giữ nguyên output gốc trong cache riêng.

So sánh V1→V2 thay cả dữ liệu, schema, ngân sách và tiền xử lý, nên không tách riêng được tác dụng của việc thêm ảnh chụp. Phép so sánh nhân quả chính là control↔partial cùng seed, ngân sách và ID. Hai baseline CPU dùng ghép nhãn/vị trí đơn giản và không đại diện mọi hệ thống OCR/KIE hiện đại. Latin PP-OCRv5 không phải model dành cho mọi hệ chữ; xem riêng slices theo layout, nhất là rus_internalpassport/grc_passport. [Tài liệu tác giả PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR/blob/main/docs/version3.x/module_usage/text_recognition.en.md).

## Chênh lệch có khoảng tin cậy

| So sánh | ΔF1 | CI95% theo ID |
|---|---:|---:|
| partial_42 − control_42 | +0.0212 | [-0.0039, +0.0477] |
| partial_31415 − control_31415 | +0.0291 | [-0.0048, +0.0645] |
| partial_42 − v1 | +0.0263 | [-0.0244, +0.0803] |
| partial_42 − original | +0.2253 | [+0.1844, +0.2681] |

Bootstrap ghép cặp 10000 lần, giữ nguyên cụm ID và phân tầng nguồn. Chỉ 48 ID test và hai seed; không suy rộng thành độ chính xác eKYC ngoài đời hoặc đảm bảo chống giả.

## Kiểm chứng và localhost

- Audit phát lại 1728 hàng output; 101 file V1 và 63 file V4 không đổi.
- Đã trích xuất lại vision từ pixel của toàn bộ 1112 ảnh tham chiếu duy nhất; cache khác biệt: 0. Kiểm tra này không thay thế nhãn legibility của con người.
- Model web được chọn từ development: **partial_42**. Cổng khuyến nghị triển khai: **False**. Nếu không đạt, trang chỉ mở model khi người dùng chủ động chọn chế độ nghiên cứu.
- 16 lần đọc ảnh mới thêm trên 8 ảnh/4 ID; sai khác so với output đã chấm: 0. p50=10.32s, p95=16.40s. Đây là suy luận có xử lý ảnh + vision + sinh văn bản, khác thời gian đọc feature cache.
- 23 kiểm tra Python và 8 kiểm tra frontend đã chạy. Predictor/camera giả chỉ dùng cho test hành vi HTTP/UI; không dùng chúng làm kết quả OCR. Việc bấm thử SPECIMEN qua web cũng không thay benchmark test.
- Chưa xác nhận khả năng đọc trên camera thật của người dùng. Không có dịch vụ LLM bên ngoài, không ghi ảnh camera ra đĩa, không kiểm tra liveness hay tự duyệt danh tính tại trang nghiên cứu OCR.

## Ý nghĩa đối với paper

V2 bổ sung phép đo chuyển từ ảnh dựng sang ảnh chụp, chống rò rỉ ID, tách bố cục/camera, đối chứng đồng ngân sách và ghi riêng bỏ sót/đọc sai/trường không được hỗ trợ. Đây là bằng chứng phương pháp và dữ liệu tốt hơn V1, chưa phải xác nhận novelty đủ CORE B hoặc bảo đảm được nhận bài.
[KIE-HVQA](https://arxiv.org/abs/2506.20168) đã nghiên cứu hallucination OCR và SFT/GRPO. Nguồn dữ liệu: [MIDV-2020](https://arxiv.org/abs/2107.00396). V2 không nhận ý tưởng fine-tune chống bịa là phát minh đầu tiên.
Thiếu sót còn lại: chưa có bộ ảnh Việt Nam mới tự thu thập có phép; chưa có nhãn legibility độc lập; chỉ một backbone nhỏ, hai seed và ít ID/type. Font test Arial phụ thuộc font Windows đúng checksum trong manifest. Cần căn cứ riêng kết quả ảnh chụp và CI khi quyết định có mở rộng thí nghiệm hoặc viết claim.


## Gián đoạn nguồn điện và độ nhạy thời gian

Windows ghi nhận sleep do pin lúc 09:25:46 UTC và thức lại 14:45:48 UTC ngày 2026-11-02. Một lượt V1 đang sinh văn bản bị tính cả thời gian ngủ. Output, hash, số đo thời gian gốc và mọi hàng độ chính xác được giữ nguyên. Bảng sau là phân tích thời gian bổ sung sau khi phát hiện sự cố, chỉ bỏ đúng lượt có nhật ký sleep khỏi thống kê độ trễ; không bỏ các lượt OCR khó hoặc sai. Nguồn điện/chế độ GPU không được kiểm soát xuyên suốt; các con số này không thiết lập ưu thế tốc độ.

| Model | Số lượt | Lượt sleep | p50/p95 gốc (s) | p50/p95 bỏ lượt sleep (s) |
|---|---:|---:|---:|---:|
| Vintern gốc (prompt V2) | 144 | 0 | 21.53/30.46 | 21.53/30.46 |
| LoRA V1 chuyển sang tác vụ V2 | 144 | 1 | 5.23/17.70 | 5.21/17.09 |
| V2 control /42 | 144 | 0 | 14.03/30.20 | 14.03/30.20 |
| V2 partial /42 | 144 | 0 | 13.75/27.20 | 13.75/27.20 |
| V2 control /31415 | 144 | 0 | 14.79/30.39 | 14.79/30.39 |
| V2 partial /31415 | 144 | 0 | 13.36/20.00 | 13.36/20.00 |
| rapid_v4 + ghép nhãn/vị trí | 144 | 0 | 2.25/5.65 | 2.25/5.65 |
| rapid_latin_v5 + ghép nhãn/vị trí | 144 | 0 | 1.78/4.24 | 1.78/4.24 |

Kiểm tra bổ sung: gọi lại 1 lượt bị gián đoạn với cùng model/ảnh/profile, từ feature cache; số output khác hash: 0. Đây là kiểm tra sau sự cố, tách riêng với 16 phép lặp ảnh mới và không thay kết quả gốc.