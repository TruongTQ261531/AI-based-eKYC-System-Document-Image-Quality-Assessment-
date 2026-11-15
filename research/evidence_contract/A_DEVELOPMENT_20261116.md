# Development A sau pilot · 16/11/2026

Đây là thử nghiệm **post-pilot exploratory**, dùng findings cũ để thiết kế
các ứng viên. Không phải confirmatory, không thay A cũ hoặc sửa nhãn người.
Kế hoạch đã được ghi trước lượt chạy này; không phải preregistration trước
pilot. [Plan](execution/master_01/development_20261116/variant_plan.json)

## Ý tưởng và cách triển khai

1. **A_change_union:** bổ sung tín hiệu đổi output B2 vào kênh field của A;
   relation vẫn giữ A. Đây là tín hiệu phụ có thể đánh dấu thêm thay đổi, không
   tự chứng minh lỗi regression hoặc source correctness.
2. **A_dual:** tách hai kênh. Kênh field dùng chính B3, kênh relation giữ A.
   Khi ảnh gốc đã sai, vẫn đưa lỗi field vào danh sách mà không gọi nó là
   transformation regression. Đây là tổ hợp hai bộ kiểm cũ, không phải detector
   mới vượt B3. Baseline nhận cùng thông tin vẫn phải được đối chiếu.
3. **A_reference_gate:** control yêu cầu reference độc lập đã được phê duyệt.
   Hiện chưa có approval nên abstain toàn bộ. Zero alarms/FP ở control này
   không phải cải thiện accuracy.

Không thay parser/weights/input/source graph của SUT. Đã dùng toàn bộ **132
lượt theo lịch** và **120 so sánh khử trùng**, trên ba reader đóng băng. Đây
là cùng cache, không phải thêm 132 ảnh hay 132 inference mới. Giữ toàn bộ 46
ca review, 42 primary và 4 diagnostic; không refill sau kết quả.

## Kết quả mô tả trên nhãn cũ của một tác giả

| Phương án | TP/FP/FN/TN pointwise | Coverage trên ca có nhãn | TP/FP/FN/TN relation |
|---|---|---|---|
| A cũ | 2/0/5/19 | 18/26 | 2/0/0/19 |
| A_change_union | 4/0/3/19 | 20/26 | 2/0/0/19 |
| A_dual | 7/3/0/16 | 26/26 | 2/0/0/19 |
| B3 | 7/3/0/16 | 26/26 | 2/3/0/16 |
| A_flat | 2/0/5/19 | 18/26 | 2/0/0/19 |

Trong panel hậu kiểm giữ bất định các ca có cờ: A cũ TP/FN=2/4,
A_change_union=3/3 và A_dual=6/0. B3 cũng 6/0. Mẫu số pointwise chỉ còn 20;
đây không phải bộ nhãn mới đã phân xử. Chưa có dữ liệu external để kết luận
mức tăng độ tin cậy hoặc xác nhận hiệu quả qua quần thể.

Kênh field của A_dual trùng B3 trên toàn bộ 132 lượt, đúng theo thiết kế;
kênh relation trùng A cũ. Không đổi tên B3 rồi báo một phát hiện mới. A_change
có thể hữu ích như một lựa chọn tín hiệu phụ nhưng vẫn bỏ sót ba operational
field errors và cần kiểm lại trên reference độc lập. Không chọn mặc định ứng
viên chỉ vì kết quả thuận lợi trên panel đã xem.

[Bảng đầy đủ hai panel](execution/master_01/development_20261116/variant_results.md) ·
[Case digest và kết quả](execution/master_01/development_20261116/variant_results.json) ·
[Reader/contract slices](execution/master_01/development_20261116/variant_strata.json)

## Bước tiếp theo có căn cứ

- Thu hai reviewer ngoài dự án theo [gói độc lập](REVIEWER_HANDOFF_VI.md),
  giữ exposure/phiếu gốc và đo agreement trước phân xử. Số reviewer mới hiện
  vẫn là **0**; chuẩn bị hai ZIP không được tính thành hai người đã chấm.
- Chốt reference, semantic key, whole-image availability và backup trước khi
  infer bộ mới. Chưa có căn cứ nguồn C2 thì giữ chưa kết luận; không sửa MRZ
  bằng author reference hoặc prediction.
- Với dữ liệu development mới, đánh giá A_dual/A_change dưới matched budgets,
  cùng endpoint và baseline, giữ cost/unknowns. Chỉ mở cohort confirmatory
  sau reference, adequacy và GO mới. Superiority gate hiện vẫn NO-GO.
- Chưa mở training mới: lỗi đang xử lý là endpoint visibility/reference,
  không có chứng cứ rằng training lại reader sẽ giải quyết các vấn đề đó.

Lượt này: **0 model inference mới, 0 training, 0 nhãn người được sửa/tạo**.

Kiểm thử: **209 Python + 6 subtests và 15 JavaScript qua**. Checkpoint verifier
đã đối chiếu lại hai panel, bảy phân tầng pointwise và hai ZIP; báo cáo sealed
cũ replay trùng hoàn toàn. 328 tài sản được bảo vệ, gồm phiếu và log cũ, giữ hash.
[Receipt kiểm cuối](execution/master_01/development_20261116/final_verification.json).
Đây là kiểm tự động/fixture và nội dung gói; chưa có browser visual QA cho ZIP mới.
