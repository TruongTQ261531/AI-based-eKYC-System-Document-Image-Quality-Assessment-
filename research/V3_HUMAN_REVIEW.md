# Đánh giá của người: đã chuẩn bị công cụ, chưa có nhãn thực tế

Mở [trang đánh giá độc lập](http://127.0.0.1:8003/review). Bộ ảnh gồm 48 ID,
mỗi ID chỉ xuất hiện một lần: 24 ảnh dựng và 24 ảnh chụp giấy tờ mẫu MIDV;
16 ảnh đủ, 16 ảnh cắt nội dung, 16 ảnh che giá trị. Không có đáp án hay kết quả
model trong trang hoặc API của bộ đánh giá. Ảnh giữ nguyên byte của benchmark.

Hai người làm riêng, dùng mã ẩn danh A/B; ghi ngôn ngữ mình đọc được. Không xem
output OCR, không mở mapping riêng hoặc nhãn tác giả, không trao đổi đáp án.
Nếu không giữ được điều kiện đó, không tự xác nhận ô độc lập trên trang.
Ô xác nhận là tự khai của người dùng, không phải chứng minh tự động về danh tính
hoặc tính độc lập của người đánh giá.

Chọn khả năng đọc cho từng trường trong danh sách chung. Danh sách không có
nghĩa giấy tờ phải có mọi trường. Nếu đọc đầy đủ, chép nguyên văn một giá trị
còn thấy; nếu chỉ đọc được một phần, chỉ chép phần đó. Có thể dùng nguồn khác
trong ảnh nếu biết đọc, ví dụ MRZ. Năm hai chữ số giữ nguyên, không suy đoán thế
kỷ. Name/Given names và Surname là hai trường riêng; số giấy tờ khác số cá nhân.
Không mặc định dữ liệu optional của MRZ là số cá nhân.

Nếu không biết ngôn ngữ, ghi lý do trong chú thích; không đồng nhất việc không
biết ngôn ngữ với ảnh mờ. Có thể mở ảnh gốc để phóng lớn. Không dùng ảnh gốc
khác của cùng giấy tờ hoặc công cụ OCR để đoán phần đã mất.

Bấm đánh dấu hoàn tất sau khi kiểm tra mọi trường. Xuất tệp định kỳ; không có
localStorage hoặc lưu câu trả lời lên máy chủ. Có thể xuất phần đang làm và nhập
lại trên cùng bộ ảnh. Mỗi người giữ một tệp riêng. Không đưa các tệp trả lời lên
Git. Khi có tệp, cần kiểm tra schema, hash ảnh, tỷ lệ hoàn tất, ngôn ngữ, mức đồng
thuận và xử lý bất đồng trước khi dùng làm bằng chứng trong paper.

**Hiện có 0 nhãn của người được nhận.** Việc kiểm thử giao diện bằng câu trả lời
giả không được tính là đánh giá của người. Không có công cụ nào ở đây tự tạo
câu trả lời từ GT hoặc output model. Nhãn bổ sung sẽ được báo riêng, không thay
âm thầm tham chiếu chính hoặc dùng chọn model sau khi đã mở test.
