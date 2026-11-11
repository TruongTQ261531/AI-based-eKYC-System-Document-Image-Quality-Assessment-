# Đối chứng có cùng bằng chứng và ngân sách

| Phương pháp | Vai trò | Quan sát trên development |
|---|---|---|
| B0 full-reference | Đếm sai trường cả khi phần chữ bị che chủ đích | 91 cảnh báo. Không có cảnh báo A riêng ngoài B0, nhưng hai endpoint khác nhau |
| B1 validity-filtered random | Bộ chọn ca, dùng cùng checker A và miền ứng viên | A-conditioned 8/60 và random 9/60 cảnh báo. Theo yêu cầu reader duy nhất là 48 và 51. Kết quả chưa có lỗi xác minh để so yield |
| B2 source-agnostic | Quan hệ hình học hoặc che dựa trên ý định, cùng gate | 9 cảnh báo chính, 6 giao với A, 3 riêng B2. Control đúng backup bị báo và control bỏ backup có thể thoát |
| B3 / gated V3 | Đối chiếu tham chiếu khả kiến và nguồn thay thế, cùng validity report | B3 có 58 cảnh báo chính. Gated V3 trùng B3 120/120. Gated V3 cũng xử lý các diagnostic invalid/bất định giống A trên output đã lưu |
| A | Điều kiện nguồn, relation trước–sau và lý do abstain | 17 cảnh báo chính, 0 riêng A. A có thể dùng lịch sử phiên bản trong schema, nhưng các run hiện tại chưa có version quad của lỗi lịch sử |
| A_flat | Phẳng hóa tại biên oracle, giữ cùng metadata và eligibility | Trùng A 120/120. Chưa có bằng chứng lợi ích riêng từ biểu diễn graph khi input thông tin đã ngang nhau |

Chi phí inference giữa A và B3 bằng nhau trên cùng pack vì chia sẻ output. Timing audit trước trên 132 pack cho median A 11,49–14,21 ms và B3 0,070–0,075 ms. A thực hiện thêm provenance/hash/trace. Thiếu ablation tracing ngang nhau và chưa đo phút công người. So sánh budget fair-controls phải tính các proposal thất bại, cache, trùng ảnh và người xác minh. Chưa có cơ sở nói A rẻ hơn. [Audit lịch sử](A_VS_B3_DIAGNOSIS.md)

M1–M7 cho **A, B3 và A_flat cùng 5/5** lỗi có cấu trúc được kích hoạt. Nếu tính cả lỗi JSON và attribution, mỗi phương pháp chính có 5/7. Checker schema và membership bắt hai lỗi giao diện tương ứng. Đây là điểm kiểm soát đối chứng mạnh, không cộng vào hiệu quả natural model. [Fault injection](AUTOMATED_FAULT_INJECTION_REPORT.md)
