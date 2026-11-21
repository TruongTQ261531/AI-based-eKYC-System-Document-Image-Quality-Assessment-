# P6.2 · Khi nào D4 rút lại kết luận?

**Trên 72 ca dựng sẵn, ở mỗi tier, checked rút 6 cảnh báo FAULT và 2 kết luận NO_FAULT của asserted tại endpoint pointwise.** Cả 8 đều chuyển thành UNKNOWN. Ở relation, các số tương ứng là 4 và 1. Hai tier đánh giá lại cùng bộ 72 ca. Không có mẫu số independent truth cho lỗi OCR thực, nên số lỗi thật bị bỏ sót và real fault sensitivity đều là **NA**. [Bảng đầy đủ 83 tổ hợp với lý do, literal, nguồn, guard và reference](execution/master_01/p6_integrity_20261121/D4_STRATA.md)

| Tier, endpoint | FAULT → FAULT | NO_FAULT → NO_FAULT | UNKNOWN → UNKNOWN | INVALID_TEST → INVALID_TEST | FAULT → UNKNOWN | NO_FAULT → UNKNOWN |
|---|---:|---:|---:|---:|---:|---:|
| 1, pointwise | 23 | 5 | 31 | 5 | 6 | 2 |
| 2, pointwise | 8 | 2 | 49 | 5 | 6 | 2 |
| 1, relation | 12 | 3 | 47 | 5 | 4 | 1 |
| 2, relation | 5 | 1 | 56 | 5 | 4 | 1 |

Chiều chuyển là **asserted → checked**. Mỗi dòng có 72 ca. Ở tier 1, checked đưa ra 28 quyết định pointwise và 15 quyết định relation. Ở tier 2, các số là 10 và 6. Đếm quyết định rút theo từng endpoint tránh cộng lặp một ca khi cả hai endpoint cùng đổi.

## Literal và guard đã làm gì?

- Trường gồm 67 ca số giấy tờ, 3 ngày sinh, 1 ngày hết hạn và 1 họ tên. Metadata sau biến đổi có 44 ca chỉ có body, 22 ca có body và MRZ, 3 ca body và duplicated body, 2 ca thiếu danh sách nguồn dùng được, 1 ca có source sai cấu trúc. Các đầu vào lỗi được giữ trong mẫu số.
- Mỗi tier có 52 ca đi tới resolver. 13 ca bị từ chối reference, 4 ca dừng ở output binding, 2 ở mutation gate và 1 vì output không có cấu trúc dùng được. Có 55 reference dựng sẵn được policy chấp nhận, vì một số guard còn chạy sau bước tiếp nhận reference.
- Trong 55/72 ca, bộ đếm của checked ghi không gọi trình kiểm literal ở cả cặp. Trong 17 ca còn lại, xét nguồn MRZ đủ điều kiện ở **ảnh sau** có 6 ca literal hợp lệ, 3 lệch giá trị khai báo, 2 sai checksum, 2 sai field/precision, 1 thiếu literal, 1 sai ngày, 1 sai format và 1 không có literal sau đủ điều kiện. Bảng chi tiết giữ riêng kết quả kiểm literal và lý do cuối của mỗi arm. Một guard relation có thể chi phối quyết định dù literal đã được kiểm.
- Một ca có `value_kind` sai kiểu, một ca có phần tử source sai cấu trúc. Audit giữ hai trường hợp này với mã riêng. Không suy từ dữ liệu bị từ chối rằng literal đã được kiểm.

## Năm phạm vi bằng chứng

| Phạm vi | Quan sát hoặc kết luận |
|---|---|
| Observed on constructed controls | 72 ca, 144 cặp theo tier, 8 ca có divergence. Các nhãn trong fixture là nhãn do tác giả dựng. |
| Historical replay without approved reference | 46 cặp, 42 ca primary trên 3 physical ID. Hai arm cho UNKNOWN ở cả 46 pointwise và 46 relation. Parser ghi NO_FAULT cho structure ở 46 ca. Số reference được duyệt và nhãn truth đã dùng đều bằng 0. |
| Proven code-level constraints | Ở pointwise, khi checked đưa quyết định nhị phân, asserted phải ra cùng quyết định trên cùng đầu vào và tier. Chứng minh nằm ở điều kiện resolver và guard chung. Không dùng bảng tần suất làm chứng minh. |
| Actual-model results with independent truth | Replay có 93 output đã cache. Số ca có truth độc lập đủ dùng cho đối chiếu D4 trong các artifact này là 0. Số lỗi thật bị bỏ sót, FAR thật và sensitivity thật đều chưa ước tính được. |
| Unavailable evidence | Thiếu production reference được duyệt, truth độc lập, tỷ lệ lỗi literal/nguồn thực, phân bố field và template đại diện. |

Ba phản ví dụ `shared_wrong_reference`, `corroborated_shared_wrong_reference` và `correlated_wrong_body_and_valid_MRZ` vẫn tồn tại: nhiều nguồn có thể tự nhất quán mà cùng sai. Việc bỏ một cảnh báo trong controls không chứng minh đã ngăn false alarm trong triển khai. [Cơ chế và giới hạn toán học](D4_MECHANISM_BOUNDS_VI.md) · [Replay lịch sử](execution/master_01/d4_development_20261117/historical_01/summary.json) · [Claim ledger P6](P6_CLAIM_TO_EVIDENCE_MATRIX.md)
