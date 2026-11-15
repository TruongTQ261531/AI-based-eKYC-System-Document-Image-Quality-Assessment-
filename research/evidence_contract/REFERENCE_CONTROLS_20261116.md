# Phần triển khai không chờ feedback · 16/11/2026

Đã hoàn thành prototype kiểm tham chiếu và ma trận đối chứng theo
[kế hoạch ghi trước lượt chạy](execution/master_01/reference_stress_20261116/plan.json).
Đây là development sau pilot, toàn bộ output được cài sẵn với origin
`oracle_unit_injected`. Không dùng JSON feedback mới, không sửa A/B3 đóng băng,
phiếu cũ hoặc hai ZIP pha 1 đang gửi cho người chấm.

## Vấn đề được làm rõ

- **A_change_union có trade-off bất lợi:** trên đối chứng C2 có backup hợp lệ,
  output đúng vẫn bị tín hiệu nominal-mask của B2 báo động. Với C3/C4, output
  đổi từ sai thành đúng cũng có thể bị union gọi là cảnh báo. Lợi ích 4/7 trên
  pilot cũ không đủ để chọn union làm mặc định.
- **A và B3 có thể cùng sai:** khi cố ý làm sai reference trong graph nhưng
  giữ nguyên ảnh và output đúng, cả hai cùng báo mismatch. Agreement giữa hai
  oracle dùng chung reference không xác minh tính đúng của reference đó.
- **Lỗi đã có từ trước cần một kênh riêng:** stable wrong vẫn là lỗi field;
  điều kiện original-correct không cho phép gọi nó là regression của cặp ảnh.
- **JSON hỏng cần tách endpoint:** không biến parse failure thành omission
  hoặc absence. Lỗi cấu trúc được ghi ở lane riêng; field/relation giữ bất định.

## Code đã triển khai

[reference_policy.py](master/reference_policy.py) nhận reference được niêm phong
theo hash nội dung, gắn với before/after pixel hash, semantic key, mutation và
policy normalization. Mỗi nguồn có trạng thái, giá trị và điều kiện rõ ràng.

1. Không chấp nhận reference đổi nội dung, sai ảnh/trường/mutation, nguồn trùng,
   boolean dạng chuỗi hoặc thiếu provenance. Hash chỉ ràng buộc nội dung, không
   chứng minh người cung cấp đúng hoặc độc lập.
2. Chỉ kết luận absence khi inventory đầy đủ và mọi nguồn khai báo đều có chứng
   cứ xóa cùng semantic linkage. Empty output không tự cấp bằng chứng absence.
   Nguồn xung đột hoặc chưa xác minh tiếp tục UNKNOWN.
3. Policy `conservative-field-values/1` giữ O/0, dấu tiếng Việt và hoa/thường
   của identifier; text dùng NFC/casefold/whitespace. Full date và YYMMDD có
   precision riêng, không đoán thế kỷ. Policy MRZ v1 chỉ chấp nhận nguồn có đủ
   semantic/integrity/format/field/composite flags; trường không có field checksum
   phù hợp tiếp tục chưa được hỗ trợ theo policy này.
4. `A_bound_dual` dùng reference đã qua lớp kiểm cho field và giữ điều kiện
   original-correct cho relation C3/C4. `B3_bound` nhận **cùng reference** và có
   kênh field trùng hoàn toàn. Lợi ích reference có thể dùng cho cả baseline;
   không có claim graph hoặc detector mới vượt baseline cùng thông tin.
5. Reference constructed chỉ dùng cho output injected. Với `actual_model`,
   reference này bị từ chối kể cả khi ID nằm trong allowlist. Reference external
   cần đúng ID đã được phê duyệt ngoài module; allowlist thực hiện vẫn trống.
   Không tự chuyển review cá nhân thành gold hay cấp GO.

## Kết quả đối chứng

Đã chạy **252 lượt = 9 tình huống × 7 kiểu output × 4 seed**. Sau khử trùng còn
**131 so sánh injected khác nhau, 13 cặp pixel**. Các seed, view và output được
cài sẵn không phải các đối tượng độc lập. Trong 131 so sánh, 76 có endpoint
pointwise đủ điều kiện và 55 có endpoint relation đủ điều kiện theo thiết kế.

| Pointwise, sau khử trùng | TP/FP/FN/TN | Decision coverage | Alarm trên ca chưa đủ điều kiện |
|---|---|---|---|
| A đóng băng | 36/4/14/22 | 55/76 | 10 |
| A_change_union | 36/15/14/11 | 62/76 | 0 |
| A_dual / B3 | 50/4/0/22 | 76/76 | 0 |
| A_bound_dual / B3_bound | 50/0/0/26 | 76/76 | 0 |

Các giá trị đúng/sai ở đây là kỳ vọng đối chứng đã khai báo, không phải nhãn
ảnh tự nhiên. Bảng tốt của phương án bound phụ thuộc reference đúng được cấp
cho nó; B3_bound được cùng lợi ích. Pixel checker dùng phép so sánh riêng nhưng
**chia sẻ inventory của renderer nguyên bản**. Nó kiểm xóa/giữ pixel và context,
không tự đọc chữ để xác minh giá trị ngoài fixture hoặc cấp human readability.

Lane cấu trúc bắt **36/36 JSON hỏng được cài sẵn**, 0 cảnh báo trên cấu trúc tốt
trong 252 lượt. Không coi đây là 36 lỗi model được tìm ra hoặc metric tổng thể
của hệ eKYC. Các abstention trên lỗi có nhãn vẫn tính vào FN và báo coverage;
không dùng giảm alarm do từ chối kết luận làm accuracy gain.

[Toàn bộ hai panel và endpoint](execution/master_01/reference_stress_20261116/run_01/results.md) ·
[Results JSON](execution/master_01/reference_stress_20261116/run_01/results.json) ·
[252 case và provenance injected](execution/master_01/reference_stress_20261116/run_01/cases.json)

## Kiểm chứng và trạng thái tiếp theo

- **245 Python + 6 subtests, 15 JavaScript PASS.** Có 36 test mới về binding,
  trust scope, normalization, false alarms, collateral context và chống sửa số.
- [Verifier stdlib riêng](master/reference_stress_verify.py) qua kiểm hash,
  origin, khử trùng và tính lại số đếm. Nó không tái dựng pixel, chạy lại method
  hoặc chứng nhận control truth. Có test từ chối count bị sửa và đổi injected
  thành real-model evidence.
- Ghi [môi trường/font](execution/master_01/reference_stress_20261116/environment.json)
  để phân biệt tái lập pixel chính xác với chạy trên renderer/font khác.
- 0 inference model mới, 0 training, 0 phiếu người được tạo/sửa. Superiority
  confirmatory vẫn NO-GO. P1 có prototype đã kiểm; reference external, dữ liệu
  mới, adequacy và approval thực tiếp tục là việc riêng.

Điểm tiếp tục: giữ union như công cụ chẩn đoán; chuẩn bị tích hợp reference có
provenance và baseline ngang thông tin. Chỉ đánh giá hiệu quả trên model/ảnh
mới theo protocol và reference được phê duyệt. Bạn tiếp tục gửi hai ZIP pha 1;
không cần đợi feedback để hoàn tất mốc kiểm phần mềm này.
