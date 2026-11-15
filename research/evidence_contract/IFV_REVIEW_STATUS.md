# Trạng thái IFV

**COMPLETE_SINGLE_REVIEW_UNADJUDICATED**, cập nhật 16/11/2026, Asia/Bangkok.
Phần đánh giá cá nhân của bạn đã hoàn tất cả hai pha: **86/86 ô quan sát và
46/46 ca đối chiếu output**. Không còn ca chưa nộp trong sample này.
[Báo cáo chính](execution/master_01/ifv_descriptive_ece01b67a2f6af39.md) ·
[Hậu kiểm](execution/master_01/ifv_20261115/analysis.md) ·
[Bước tiếp theo](NEXT_ACTIONS.md)

Đã chuẩn bị gói chấm offline R02/R03 và công cụ agreement theo
[handoff](REVIEWER_HANDOFF_VI.md). Số reviewer ngoài thực nhận vẫn **0**;
hai gói chưa phải hai người đã chấm. Phiếu cá nhân và các bảng dưới giữ nguyên.

| Mục | Trạng thái đã kiểm |
|---|---|
| Pha 1 | 31 ảnh, 86 ô đủ schema; snapshot đã khóa ngày 14/11 |
| Pha 2 | Nhập nguyên trạng 46 ca: 42 primary trên 3 ID và 4 diagnostic |
| Người đánh giá | 1 tác giả dự án tự khai, chưa phân xử hoặc xác minh độc lập; 2 phiên bản pha 1 và 1 export pha 2 |
| Ca chưa chấm | 0; INCONCLUSIVE là chưa đủ căn cứ kết luận theo guard, không phải thiếu phiếu |
| Pointwise primary | 7 operational CONFIRMED_FAULT, 19 NO_FAULT, 16 INCONCLUSIVE; mẫu số có nhãn 26/42 |
| Relation primary | 2 operational CONFIRMED_FAULT, 19 NO_FAULT, 21 INCONCLUSIVE; mẫu số có nhãn 21/42 |
| Diagnostic | 4/4 INCONCLUSIVE; không gộp vào primary |
| Thống kê | Chỉ mô tả subset; CI/p-value, recall quần thể, agreement và phút công: NA |
| Gate | NO-GO cho confirmatory superiority; tiếp tục characterization và chuẩn bị protocol mới |

Nhãn CONFIRMED_FAULT ở đây là trạng thái vận hành do quy tắc đã chốt gán cho
phiếu một tác giả; không phải gold label độc lập hoặc software root cause.

## Kết quả chính, giữ nguyên phiếu và guard

| Endpoint | A: TP/FP/FN/TN | B3: TP/FP/FN/TN | A_flat |
|---|---|---|---|
| Pointwise | 2/0/5/19 | 7/3/0/16 | Trùng A |
| Relation | 2/0/0/19 | 2/3/0/16 | Trùng A |

A có 14 cảnh báo primary: 12 chưa kết luận ở cả hai endpoint. Precision 2/2
chỉ tính trên cảnh báo đã có nhãn, không phải toàn bộ 14 cảnh báo. Pointwise
sensitivity của A là 2/7, B3 là 7/7. Decision coverage trên 26 ca có nhãn:
A 18/26, B3 26/26. Không dùng FAR thấp hơn để bỏ qua các khác biệt này.

## Hậu kiểm và độ nhạy

Có 17 ca mang cờ đối chiếu chữ/lựa chọn, gồm 15 primary: ví dụ output có chữ
nhưng được đánh dấu bỏ sót, hoặc chọn đúng dù khác transcript pha 1 ở chữ O
và số 0. Các cờ là kiểm tra literal, không tự chứng minh người chấm sai hoặc
sửa đáp án. Mọi câu trả lời và ghi chú gốc được giữ dưới `local/`.

Phân tích hậu kiểm tạm giữ bất định cả hai endpoint trên ca có cờ, giữ toàn
bộ frame: pointwise còn 20 ca có nhãn (6 lỗi, 14 không lỗi), relation còn 16
(2 lỗi, 14 không lỗi). B3 không còn 3 FP trong panel độ nhạy; A vẫn bỏ sót 4/6
lỗi pointwise, B3 ghi nhận 6/6. Đây không phải bảng chính hoặc adjudication.
Không chốt lợi ích FAR của A từ phiếu chưa phân xử.

Cả 10 ca C2 (9 primary + 1 diagnostic) giữ INCONCLUSIVE theo bằng chứng đã
khóa. Pha 2 đã hoàn tất nhưng không bổ sung được nguồn backup đủ điều kiện.
Không nới guard hay thay mẫu sau khi xem kết quả.

## Ràng buộc dữ liệu

Pha 1: `00ff0a49d4df5a84c2d78511bcf2d9ed36e19945747a93c08d6788e3b9a9da79`.
Pha 2: `812605bbab3940be838ac9da07ed903c0098717ace789f703f080869dde3267d`.
SHA256 export pha 2 gốc:
`6e43cc68e6cf4f4ca0d91a4a1b6f70a7fa74faff6060d1162f8a7ed9c989559b`.
[Tiếp nhận](execution/master_01/ifv_20261115/intake.json)

Lượt phân tích này có 0 inference/training mới, 0 câu trả lời bị sửa và 0
human annotations được tạo tự động. Phiếu cũ và receipt chờ review vẫn là
lịch sử; trạng thái hiện tại dùng báo cáo 15/11 phía trên.
