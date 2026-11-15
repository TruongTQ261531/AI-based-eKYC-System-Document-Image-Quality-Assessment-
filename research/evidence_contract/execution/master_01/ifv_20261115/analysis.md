# IFV: hậu kiểm và mẫu số

Một tác giả đã hoàn tất 46/46 ca. Đây là pilot development chưa phân xử độc lập.

Bảng chính giữ nguyên phiếu, guard và nhãn đã nhập. Không suy thời gian làm từ timestamp.

| Endpoint | Có nhãn lỗi/không lỗi | Chưa kết luận |
|---|---:|---:|
| pointwise | 26/42 | 16 |
| relation | 21/42 | 21 |

## pointwise

| Method | TP | FP | FN | TN | Cảnh báo chưa kết luận / toàn bộ cảnh báo |
|---|---:|---:|---:|---:|---:|
| A | 2 | 0 | 5 | 19 | 12/14 |
| B3 | 7 | 3 | 0 | 16 | 16/26 |
| B3_V3_gate | 7 | 3 | 0 | 16 | 16/26 |
| A_flat | 2 | 0 | 5 | 19 | 12/14 |
| B0 | 7 | 9 | 0 | 10 | 16/32 |
| B2 | 4 | 0 | 3 | 19 | 4/8 |

## relation

| Method | TP | FP | FN | TN | Cảnh báo chưa kết luận / toàn bộ cảnh báo |
|---|---:|---:|---:|---:|---:|
| A | 2 | 0 | 0 | 19 | 12/14 |
| B3 | 2 | 3 | 0 | 16 | 21/26 |
| B3_V3_gate | 2 | 3 | 0 | 16 | 21/26 |
| A_flat | 2 | 0 | 0 | 19 | 12/14 |
| B0 | 2 | 9 | 0 | 10 | 21/32 |
| B2 | 2 | 0 | 0 | 19 | 6/8 |

## Kiểm tra nhất quán và độ nhạy

Có 17 ca mang cờ đối chiếu chữ/lựa chọn, gồm 15 ca chính.
Cờ không tự chứng minh người chấm sai; giữ phiếu gốc và báo riêng. Chữ O và số 0 không được nhập làm một.
Phân tích dưới đây là hậu kiểm, tạm giữ bất định cả hai endpoint trên ca có cờ, không thay bảng chính.

| Endpoint | A: TP/FP/FN/TN sau withholding | B3: TP/FP/FN/TN sau withholding |
|---|---|---|
| pointwise | 2/0/4/14 | 6/0/0/14 |
| relation | 2/0/0/14 | 2/0/0/14 |

CI/p-value chưa được cấp: chỉ 3 ID primary và một người chấm; không coi field/view/reader là cụm độc lập.
Precision có điều kiện trên ca đã có nhãn khác tỷ lệ lỗi đã ghi nhận trên toàn bộ cảnh báo. Không ngoại suy recall quần thể.
Chi tiết case giữ riêng dưới local; không xuất transcript hoặc ghi chú người chấm vào báo cáo công khai.
