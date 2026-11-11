# TASK 6 — Gate review

Trạng thái: **BLOCKED — chưa bắt đầu chuẩn bị hoặc seal confirmatory test.**

Điều kiện của người dùng: chỉ bắt đầu sau khi TASK5 có báo cáo GO hợp lệ. Kiểm tra trực tiếp [GO_NO_GO_REVIEW](GO_NO_GO_REVIEW.md) và [final checks TASK5](execution/task5_pilot/final_checks.json) cho thấy quyết định hiện tại vẫn là **NO-GO cho scaling/confirmatory/superiority claims**. GO giới hạn chỉ cho audit độc lập về oracle validity và fault provenance. Không diễn giải `all_checks_passed=true` của kiểm thử phần mềm thành GO nghiên cứu.

## Bằng chứng và lý do

- TASK5 ghi0 cảnh báo riêng của A so với B3 mạnh; oracle tham chiếu phẳng cho cùng verdict trên toàn bộ panel chính. Đây là kết quả development, không phải bác bỏ thống kê H1–H3.
- Chưa có independent real-model failure labels trong pilot; xác minh readability/semantic validity và fault provenance vẫn là điều kiện còn thiếu.
- Không tìm thấy quyết định GO mới thay thế trong các artifact gate đã kiểm tra. Tất cả4 tài liệu và16 file code được final checks TASK5 ghim hash vẫn khớp.

## Phạm vi lượt này

Chỉ rà điều kiện và ghi bằng chứng vào [gate_check.json](execution/task6_gate/gate_check.json). Không thực hiện exposure audit toàn bộ V1–V4, không sinh SPECIMEN/ảnh chụp, không gắn nhãn người hay xuất bản protocol. Không tạo TEST_MANIFEST/TEST_LOCK, không đọc output confirmatory, không gọi model, train hoặc đổi RQs/checkpoints/production. Không gọi các view192/224 lịch sử là unseen test. Không có test mới được tuyên bố đã chạy.

Bảy deliverable dataset/preregistration/lock của TASK6 được hoãn để tuân thủ precondition, không tạo stub giả như một test đã sẵn sàng. Gate log này không phải EXPOSURE_AUDIT hay LOCK_VERIFICATION.

## Điều kiện mở lại

Hoàn thành audit giới hạn được TASK5 cho phép: xác minh nguồn/GT và positive/negative controls độc lập, đối chiếu V3+common gate/flat checker, xác lập fault provenance và chi phí. Sau đó cần một quyết định GO mới có bằng chứng và phạm vi cho phép chuẩn bị confirmatory. Nếu thay phương pháp hoặc framing, phải ghi nhận cập nhật prospective trước khi khóa; không sửa RQs hay kết quả cũ để hợp thức hóa GO.

HEAD khi rà: `f5d130d93525e7633053edc03e6d9f6edeba7a6f`; branch `main`. Chi tiết SHA256 và kiểm tra bảo toàn trong gate log; không commit/push.
