# C2-37 · Protocol mô tả trước quan sát, ngày 23/11/2026

**Câu hỏi.** Trên các biến đổi lịch sử đã chọn vì hình học và có đủ quyền đánh giá, khi nào nguồn chính thực sự mất khả năng đọc trong khi nguồn dự phòng vẫn hỗ trợ cùng trường, và khi nào oracle hoãn quyết định? Đích là mô tả độ tin cậy và abstention trên panel hữu hạn này. Số phiếu nhận tại thời điểm khóa bằng 0. [Quyết định phạm vi](C2_37_FIRST_CONTINUATION_VI.md) · [Aggregate khóa thành viên và phiên bản](human_gate/receipts/c2_37_20261123/aggregate.json)

### Chọn mẫu và đơn vị

Giữ nguyên thứ tự queue C2_MASTER_45 đã khóa. Nối physical ID **và** SHA-256 ảnh trước biến đổi với manifest thu nhận v2. Tra cột code với bảng DOCTYPES của MIDV. Loại toàn bộ candidate của code 25, giữ các code 05, 32 và 41. Hai tập rời nhau ở cả candidate và giấy tờ. Không dùng output OCR, exposure, bất đồng hay kết quả tương lai để chọn. Không thay ca vì từ chối, thiếu truth hay ít hiệu ứng. Danh sách loại trừ đầy đủ ở máy organizer, selection digest trong aggregate.

Mẫu số tuyển là 37 candidate, 18 physical ID, lần lượt 12/7 Azerbaijan, 11/4 Latvia, 14/7 Serbia. Mỗi candidate là một cặp trước/sau của trường và nguồn đã khóa. Cùng một ID có thể có nhiều candidate và dùng lại crop. Hai assessor chấm cùng một candidate. Không nhân cỡ mẫu theo số form, crop, lần đọc hay số arm. Không mở rộng sang sáu ID bị giữ trong đợt này.

### Source quality, truth và thiếu dữ liệu

1. Sau D10 và khi có authority, thu riêng bốn quan sát về nguồn chính trước/sau và MRZ trước/sau, semantic, precision, exposure, căn cứ hash và rationale. Giữ PASS/FAIL/UNKNOWN trên từng điều kiện; báo từng phân bố theo cả số ca và số ID. Hai assessor cần ký proposal độc lập; bất đồng hoặc uncertainty chuyển người phân xử và owner duyệt theo registry.
2. Hình học, annotation nhà cung cấp, checksum, literal giống nhau hoặc khớp OCR chỉ chứng minh đặc tính kỹ thuật. Body gồm 11 identifier và 26 ngày có năm bốn chữ số. Với MRZ giữ literal và precision (ngày YYMMDD); trường hợp thiếu căn cứ về thế kỷ, source hoặc sự tương đương giữ UNKNOWN. Ghi nhận exposure và bảng phân tầng template/field; không loại sau quan sát để tăng hiệu ứng.
3. Báo dòng chảy từ 37 ca qua quyền, đủ hai phiếu, phân xử, reference, đủ tám điều kiện. Công bố số thiếu theo lý do, số cụm đóng góp và tỷ lệ trên toàn panel. Truth cho lỗi đầu ra phải có chứng cứ độc lập thích hợp; approved reference của một trường chưa tự xác định lỗi của mỗi đầu ra.

### Endpoints và mẫu số đã khóa

Áp dụng cùng frame **pointwise tier 1 ghép cặp** và cùng policy D4 trong protocol v3. Chỉ tính khi có dữ liệu đúng thẩm quyền và điều kiện khoa học. Mục tiêu chính là báo bảng chuyển trạng thái asserted → checked và phần quyết định bị hoãn. Với từng arm, báo riêng FAULT, NO_FAULT, UNKNOWN, INVALID_TEST. Coverage = số quyết định nhị phân / số ca trong frame ghép cặp đầy đủ. Abstention = số UNKNOWN / cùng mẫu số. Báo INVALID_TEST riêng. Đầu ra thiếu được ghi thiếu và dừng so sánh ghép cặp chưa đầy đủ. Báo cả số ca có frame / 37.

Với F ca truth lỗi, N ca truth không lỗi, tính sensitivity = FAULT trên F / F, FAR = FAULT trên N / N; ΔFAR = FAR asserted − FAR checked trên cùng N. Trên F tách trường hợp bỏ sót do NO_FAULT, UNKNOWN hoặc INVALID_TEST. Báo số cảnh báo rút và số phát hiện đúng mất đi theo truth. Selective risk có mẫu số là quyết định nhị phân có truth. UNKNOWN của oracle khác với thiếu truth. Báo tỷ lệ có truth trên tổng, giữ thiếu truth trong mẫu số coverage; với mẫu số rỗng báo NA. Với truth thiếu báo khoảng cực trị theo v3. [Định nghĩa và frame v3](B_PROTOCOL_V3_20261121.md)

Gộp tử số và mẫu số của các candidate để mô tả panel, kèm bảng số đóng góp theo ID và template. Phép so paired giữ hai arm và hai thời điểm trong một candidate, mọi candidate trong cùng physical ID. Với 18 ID thuộc ba template, chỉ mô tả cụm và độ biến thiên; không tiến hành kiểm định superiority, không diễn giải sai khác theo template như mẫu độc lập. Constructed controls, replay lịch sử và quan sát người thật có bảng riêng. Không đổi threshold, estimand, margin, tập mẫu hay quy tắc abstention theo kết quả. Mọi thay đổi tương lai phải có amendment ghi thời điểm, exposure và lý do. [Giới hạn P5B](P5B_STATISTICAL_CALIBRATION_VI.md)
