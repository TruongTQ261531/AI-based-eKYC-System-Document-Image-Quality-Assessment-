# Kết quả IFV cá nhân · 15/11/2026

Đã hoàn tất **31 ảnh/86 ô pha 1 và 46/46 ca pha 2**. Export gốc được giữ
nguyên, ràng buộc đúng packet và snapshot. Phân tích không gọi lại model.
Đây là pilot một tác giả đánh giá, chưa có phân xử độc lập.

## Kết quả chính

42 ca primary thuộc 3 ID; 4 diagnostic báo riêng. Các nhãn vận hành sau guard:

| Endpoint | Lỗi theo phiếu + guard | Không lỗi | Chưa kết luận | Chưa chấm |
|---|---:|---:|---:|---:|
| Pointwise: giá trị trên ảnh biến đổi | 7 | 19 | 16 | 0 |
| Relation: lỗi quan hệ đủ tiền điều kiện | 2 | 19 | 21 | 0 |

CONFIRMED_FAULT là mã nhãn vận hành, chưa phải gold độc lập hoặc root cause.
Trong các ca đã có nhãn, kết quả pointwise như sau:

| Method | TP | FP | FN | TN | Sensitivity subset | FAR subset | Decision coverage subset |
|---|---:|---:|---:|---:|---:|---:|---:|
| A | 2 | 0 | 5 | 19 | 2/7 | 0/19 | 18/26 |
| A_flat | 2 | 0 | 5 | 19 | 2/7 | 0/19 | 18/26 |
| B3 / gated V3 | 7 | 3 | 0 | 16 | 7/7 | 3/19 | 26/26 |
| B0 | 7 | 9 | 0 | 10 | 7/7 | 9/19 | 26/26 |
| B2 | 4 | 0 | 3 | 19 | 4/7 | 0/19 | 24/26 |

Endpoint relation có A TP/FP/FN/TN = **2/0/0/19**, B3 = **2/3/0/16**.
Năm lỗi field chưa đạt tiền điều kiện relation không được biến thành
NO_FAULT. Việc thu hẹp endpoint giải thích một phần chênh lệch cảnh báo,
không tự chứng minh kỹ thuật mới phát hiện lỗi tốt hơn.

A có **14 cảnh báo primary**, trong đó **12 chưa kết luận** ở cả hai endpoint.
Vì vậy precision 2/2 trên cảnh báo có nhãn không phải 100% của toàn bộ cảnh
báo. Tỷ lệ lỗi đã được ghi nhận trên toàn bộ cảnh báo là 2/14; đây cũng không
phải precision đã phân xử hay recall quần thể. B3 có 26 cảnh báo, 16 chưa
kết luận ở pointwise và 21 ở relation.

## Độ phủ và tính nhất quán

| Contract | Primary | Pointwise có nhãn | Relation có nhãn |
|---|---:|---:|---:|
| C1: che mọi nguồn | 9 | 7 | 7 |
| C2: giữ nguồn thay thế | 9 | 0 | 0 |
| C3: giữ trường lân cận | 12 | 8 | 7 |
| C4: biến đổi hình học | 12 | 11 | 7 |

Cả 10 ca C2, gồm 1 diagnostic, vẫn INCONCLUSIVE. Guard nguồn/readability
không đổi. Những mã này phản ánh mức đủ bằng chứng, không làm mất việc người
chấm đã hoàn thành các mục trong phiếu.

Kiểm chéo literal phát hiện **17 ca có cờ**, gồm **15 primary**: chọn bỏ sót
khi output không trống, hoặc chọn đúng trong khi chuỗi khác transcript pha 1.
So sánh giữ chữ O và số 0 khác nhau; bỏ khác biệt hoa/thường, whitespace và
Unicode composition. Đây là cờ để giữ lại cho phân xử, không tự gán lại đáp án.
12 cờ before-correct, 4 cờ after-correct, 4 cờ before-omission và 2 cờ
after-omission có thể chồng nhau trên cùng ca.

Phân tích độ nhạy **hậu kiểm**, tạm giữ bất định cả hai endpoint trên mọi ca
có cờ và giữ nguyên frame 42 ca:

| Endpoint | Có nhãn còn lại | A: TP/FP/FN/TN | B3: TP/FP/FN/TN |
|---|---:|---|---|
| Pointwise | 20 | 2/0/4/14 | 6/0/0/14 |
| Relation | 16 | 2/0/0/14 | 2/0/0/14 |

Ba FP của B3 không còn trong panel này. Do đó lợi ích FAR chưa đủ vững để
chốt; bảng độ nhạy không thay bảng chính. Không loại ca theo việc baseline
thắng hay thua, không sửa phiếu đã khóa và không gọi withholding là adjudication.

## Ý nghĩa cho tiến độ

Phần review cá nhân và báo cáo 7A đã xong. A_flat trùng A ở **42/42** ca
primary đã chấm, phù hợp quan sát development trước đó. Chưa có bằng chứng
giá trị riêng của graph, sensitivity/coverage tốt hơn hoặc cost benefit.
CI/p-value không được cấp vì ít cụm; agreement và phút công vẫn NA.

Quyết định tiếp tục là **mô tả điều kiện áp dụng, chất lượng reference và
trade-off coverage**, đồng thời chuẩn bị protocol/reference mới. TASK 6B/7B
cho claim superiority vẫn NO-GO. Một pilot nhỏ thiếu power cũng chưa là
negative result đủ căn cứ để đổi track tự động.

[Báo cáo chính có thể replay](execution/master_01/ifv_descriptive_ece01b67a2f6af39.md) ·
[Hậu kiểm JSON/Markdown](execution/master_01/ifv_20261115/analysis.md) ·
[Quyết định](REVISED_GO_NO_GO.md) · [Protocol tiếp theo](POST_IFV_PROTOCOL_DRAFT.md)
