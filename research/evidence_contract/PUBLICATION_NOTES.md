# Phạm vi đồng bộ GitHub ngày 11/11/2026

Theo yêu cầu của chủ repository, đưa phần nghiên cứu local vào `main` của
[AI-based eKYC System](https://github.com/TruongTQ261531/AI-based-eKYC-System-Document-Image-Quality-Assessment-).
Commit cha khi tiếp nhận là `f5d130d93525e7633053edc03e6d9f6edeba7a6f`.
Đây là đồng bộ lên repository có danh tính của tác giả; chưa phải artifact ẩn danh để nộp hội nghị.

## Nội dung được đưa lên

- Code, protocol, schema và tests của Evidence-Contract Testing; audit TASK 0–5.5;
  phần chuẩn bị TASK 6A/7A, pilot TASK 8 và bản thảo TASK 9.
- Báo cáo, manifest, hash, log thực thi và kết quả development đã có.
  Các lượt thử thất bại được giữ cùng các lượt thành công.
- [Gói replay development](paper/candidate_20261111_02.zip) gồm code dự án và
  output trên giấy tờ giả lập. Gói đã có receipt kiểm 660 quyết định trên 132 ca;
  thao tác đồng bộ Git không chạy thêm OCR/VLM hoặc training.
- Code và báo cáo so sánh tile budget đã có trong `research/priority2_tiles.py`
  và `research/results/priority2_tiles_v1/`.

## Nội dung vẫn chỉ có trên máy

Weights/checkpoint, cache model và inference, dữ liệu gốc, ảnh giấy tờ/ảnh giao diện,
phiếu đánh giá, database và các thư mục test tạm không được đưa vào commit này.
Không xóa những file đó khỏi máy. Manifest cũ có thể dẫn tới các tài sản local
không nằm trong bản clone GitHub; chúng là bằng chứng của lần chạy tại thời điểm
ghi nhận, không phải cam kết mọi tài sản đã được phát hành.

Các receipt cũ, gồm trạng thái `published: false` của ZIP khi đóng gói và HEAD cũ
trong báo cáo phục hồi, được giữ nguyên theo thời điểm tạo. Ghi chú này phân biệt
việc đồng bộ hiện tại với các snapshot lịch sử đó. Quyền phát hành dữ liệu khác
và kiểm ẩn danh cuối cho submission vẫn là công việc riêng.

## Trạng thái khoa học và cách tiếp tục

[MASTER_EXECUTION_STATUS.md](MASTER_EXECUTION_STATUS.md) là điểm resume nghiên cứu.
IFV chưa có phiếu thật; TASK 6B/7B vẫn NO-GO. Không có confirmatory inference mới
và không thay đổi checkpoint hoặc production trong lần đồng bộ.

[REPLICATION_PLAN.md](paper/REPLICATION_PLAN.md) hướng dẫn giải nén gói replay và
kiểm kết quả không gọi model. Gói chỉ tái hiện các quyết định development đã lưu;
không thay cho kiểm chứng ảnh, readability, IFV hoặc thí nghiệm confirmatory.
