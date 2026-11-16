# Quyết định sau khi hoàn tất IFV cá nhân

Mốc readiness 16/11 giữ **NO_GO_SUPERIORITY**. Phân tích quyết định giải thích
A/flat trong miền có điều kiện, đồng thời lưu 11 counterexample ở boundary.
Hai lỗi parser nay có chứng cứ historical fix/revert trên mã chạy thực; đây là
known-fault development, không phải A phát hiện lỗi mới. Bản thảo Emerging riêng
thu hẹp claim, chưa được xác nhận đủ novelty hoặc sẵn sàng nộp.
[Chi tiết gap, kết quả và tiêu chí đóng](READINESS_ANALYSIS_20261116.md).

Mốc reference controls 16/11 không thay GO: counterexample của union và shared
reference đã được tái hiện trên injected fixtures. Bound prototype cần reference
đúng và không hơn baseline cùng reference ở kênh field. Chưa có external approval,
fault provenance tự nhiên hoặc adequacy mới. [Kết quả](REFERENCE_CONTROLS_20261116.md).

Kiểm lại 16/11: **NO-GO superiority không đổi**. [Ứng viên A mới](A_DEVELOPMENT_20261116.md)
dùng lại pilot và không thay frozen A; A_dual field trùng B3. [Hai gói reviewer](REVIEWER_HANDOFF_VI.md)
đã chuẩn bị nhưng chưa có phiếu ngoài, chưa có reference độc lập được duyệt,
adequacy hoặc lock mới. Hoàn thiện tooling không cấp scientific GO.

Ngày 15/11/2026, Asia/Bangkok. **IFV cá nhân COMPLETE: 86 ô pha 1 và 46 ca pha
2 đã nhập nguyên trạng.** Đã replay báo cáo hai endpoint, phân tích ca chưa
kết luận, kiểm tra nhất quán và độ nhạy. Một tác giả đánh giá, chưa adjudicate.
[Báo cáo chính](execution/master_01/ifv_descriptive_ece01b67a2f6af39.md) ·
[Hậu kiểm](execution/master_01/ifv_20261115/analysis.md)

**NO-GO cho TASK 6B/7B với claim A phát hiện lỗi tốt hơn baseline mạnh.**
Tiếp tục được phần development characterization, chuẩn bị reference/protocol
và viết kết quả mô tả. Đây không phải scientific GO để mở confirmatory.

| Điều kiện | Kết quả sau IFV | Quyết định |
|---|---|---|
| Hoàn tất review cá nhân | 46/46 ca: 42 primary và 4 diagnostic; không có UNREVIEWED | DONE; không tiếp tục chờ phiếu này |
| Có endpoint đủ điều kiện | Pointwise 26/42 có nhãn: 7 lỗi, 19 không lỗi. Relation 21/42: 2 lỗi, 19 không lỗi | Mô tả subset, giữ 16/21 ca còn lại bất định |
| Sensitivity và coverage trước baseline | Pointwise A TP/FN=2/5, B3=7/0. Coverage A 18/26, B3 26/26 | Chưa ủng hộ superiority; không chỉ dựa FAR 0/19 so với 3/19 |
| Robustness của nhãn | 17 ca có cờ literal, 15 primary. Khi giữ bất định ca có cờ, 3 FP B3 biến mất; A vẫn FN=4 trong 6 lỗi pointwise | Hiệu ứng FAR chưa vững; không tự sửa label hoặc chọn panel thuận lợi |
| Giá trị riêng của graph | A_flat trùng A trên 42/42 ca primary được review; lịch sử 120/120 verdict theo lịch cũng trùng | Chưa có lợi ích phân biệt được trước flat cùng thông tin |
| C2 alternative sources | 0/10 ca có nhãn binary, gồm 9 primary | Chưa kiểm được claim alternative-source reliability từ sample này |
| Tính độc lập và thống kê | 1 tác giả, 3 ID primary, chưa có chuẩn độc lập; CI không được cấp | Chưa đủ cho inference quần thể, agreement hoặc confirmatory |
| Fault provenance và chi phí | 7 field-error clusters vận hành không phải 7 root causes; chưa đo phút công | RQ2 real-bug utility và cost benefit tiếp tục chưa có bằng chứng |

Hai endpoint không dùng thay thế cho nhau. Năm lỗi pointwise không trở thành
lỗi relation vì điều kiện original-correct chưa đạt; kết quả relation 2/2
sensitivity không giải quyết được việc bỏ sót lỗi field đã tồn tại. Không
đổi RQ hoặc guard sau khi xem kết quả để tuyên bố một endpoint thắng.

## Hướng tiếp tục

Giữ nguyên RQ1–3 và các kết quả cũ như lịch sử. Nhánh tiếp theo được đề xuất
là nghiên cứu thực nghiệm về **độ tin cậy tham chiếu, điều kiện áp dụng và
trade-off giữa coverage với phát hiện lỗi**. Cần protocol prospective riêng;
không đổi framing của pilot thành một phép kiểm confirmatory.
[Protocol chuẩn bị](POST_IFV_PROTOCOL_DRAFT.md)

Trước quyết định GO mới cần reference phù hợp endpoint và kiểm độc lập,
định nghĩa pointwise/relation tách biệt, panel C2 có backup được xác minh,
adequacy theo ID/family, dữ liệu có quyền dùng và exposure audit. Giữ strong
flat/gated baselines cùng annotation. Nếu chỉ làm được nghiên cứu nhỏ thì
báo findings đúng mức maturity, không gọi thiếu power là negative result.

Không yêu cầu làm lại toàn bộ 46 ca. Danh sách cờ cụ thể đã lưu riêng để dùng
nếu cần phân xử có provenance; cùng tác giả sau khi thấy output không trở
thành reviewer mù/độc lập. Các lần bổ sung tương lai phải là amendment mới,
không ghi đè phiếu đã khóa.

[Tiến độ mới](EASE2027_ROADMAP_VI.md) · [Bước tiếp theo](NEXT_ACTIONS.md) ·
[Gate lịch sử](TASK6_GATE_REVIEW.md)
