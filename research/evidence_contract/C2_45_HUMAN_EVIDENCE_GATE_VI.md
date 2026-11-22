# C2-45 · Bằng chứng con người và quyền truy cập ngày 22/11/2026

**Đã chuẩn bị hồ sơ riêng cho đủ 45 candidate trên 24 giấy tờ. Có 0 candidate được phép gửi, 0 candidate đã có hai đề xuất và 0 reference được phê duyệt.** D1–D3 đã quyết định. Intake Round 1 đóng, agreement hoàn tất, chữ ký đóng vòng và phân xử thực tế đang chờ. Pha chuẩn bị không mở IFV mới. [Bàn giao phân xử và chữ ký](C2_45_ADJUDICATION_READINESS_VI.md)

## Mẫu số và mức hoàn tất

| Trạng thái | Nhóm có hình học phù hợp, candidate / ID | Toàn nhóm ưu tiên, candidate / ID |
|---|---:|---:|
| Tổng số | 45 / 24 | 110 / 40 |
| Đã có gói kiểm tra | 45 / 24 | 45 / 24 |
| Được chia sẻ với assessors | 0 / 0 | 0 / 0 |
| Có một đề xuất, chờ người còn lại | 0 / 0 | 0 / 0 |
| Có đủ hai đề xuất | 0 / 0 | 0 / 0 |
| Đã chuẩn bị, đang chờ cả hai | 45 / 24 | 45 / 24 |
| Chưa có đề xuất nào, kể cả ngoài đợt | 45 / 24 | 110 / 40 |
| Thiếu phê duyệt ngữ nghĩa | 45 / 24 | 110 / 40 |
| Thiếu D10 theo artifact | 45 / 24 | 110 / 40 |
| Đã phân xử C2 / có reference duyệt / đủ tám điều kiện (mỗi chỉ tiêu) | 0 / 0 | 0 / 0 |

65 candidate thuộc 32 ID nằm ngoài đợt chuẩn bị. Trong số này, 42 có biến đổi chạm nguồn chính nhưng thiếu tổ hợp phủ hết nguồn chính và giữ hai vùng MRZ, 23 không có biến đổi đã kiểm nào chạm nguồn chính. Các ID có thể xuất hiện ở cả hai nhóm. Giữ nguyên nhóm 96/35 và 894/325 của inventory 1.100. [Aggregate](human_gate/receipts/human_20261122144027Z/aggregate.json) · [Receipt ma trận từng candidate](human_gate/receipts/human_20261122144027Z/matrix_receipt.json)

## Tám điều kiện sau đối chiếu

| Điều kiện | PASS / FAIL / UNKNOWN trong 45 | PASS / FAIL / UNKNOWN trong 110 |
|---|---:|---:|
| Primary supported before | 0 / 0 / 45 | 0 / 0 / 110 |
| Primary removed after | 0 / 0 / 45 | 0 / 0 / 110 |
| Backup supported before | 0 / 0 / 45 | 0 / 0 / 110 |
| Backup supported after | 0 / 0 / 45 | 0 / 0 / 110 |
| Semantic equality approved | 0 / 0 / 45 | 0 / 0 / 110 |
| Provenance verified | 45 / 0 / 0 | 110 / 0 / 0 |
| Reference approved | 0 / 45 / 0 | 0 / 110 / 0 |
| Distinct sources | 45 / 0 / 0 | 110 / 0 / 0 |

FAIL ở dòng reference phản ánh tình trạng phê duyệt hiện tại. Với mỗi hàng có kết quả đồng nhất, số cụm giấy tờ tương ứng là 24 trong nhóm 45 hoặc 40 trong nhóm 110. Tất cả bốn kết luận đọc được/mất nguồn vẫn UNKNOWN.

## Công cụ đã sẵn sàng

Mỗi workspace ngoại tuyến có 45 phiếu trống, 198 tệp ảnh khác hash, gồm 24 ảnh nguồn, 34 ảnh biến đổi và 140 crop khác nhau. Một crop có thể dùng cho nhiều phiếu. Người chấm khai exposure cho từng ca, xem hai ảnh đầy đủ, quan sát bốn điều kiện nguồn, đánh giá nghĩa và độ chính xác, chọn hash của cả hai thời điểm rồi xuất lý do bằng văn bản. Không có đáp án hay proposal của người khác trong gói. Bản của organizer giữ ID, region, polygon, tọa độ crop, mức tác động, biến đổi, quyền và hash của từng artifact. Hai gói đang lưu riêng trên máy organizer.

Trong 45 trường chính có **11 mã định danh**, **26 ngày có năm bốn chữ số** và **8 ngày có năm hai chữ số**; MRZ ngày giữ YYMMDD. Các format lấy từ literal của annotation nguồn. Không suy ra thế kỷ hay sự tương thích ngữ nghĩa. Căn cứ exposure IFV lịch sử của R03 và R02 vẫn được bảo toàn. Mỗi phiếu C2 đòi khai exposure mới.

Schema và validator kiểm phiên bản ca, người chấm, câu trả lời, trích dẫn hash, lý do và quyền ký khi có journal. Một receipt nội dung chỉ cho biết dữ liệu hợp lệ về cấu trúc. Chỉ nhận đề xuất đã xác thực khi registry production ràng buộc đúng người, candidate, ảnh, trường, digest phiếu và checkpoint. [Schema](human_gate/review.schema.json) · [Quyền theo từng phiên bản](C2_45_D10_RIGHTS_VI.md)

## Kiểm chứng và quyết định tiếp theo

72 test mục tiêu và 657 test toàn Evidence Contract cùng 6 subtest đã qua. Verifier đối chiếu chính xác hai bộ 45 form, các hash ảnh và manifest, 5 nhóm phiên bản quyền, số candidate và ID theo từng trạng thái. Sáu phiếu IFV, ba view, hash payload, hàng đợi gốc và 84 hash P2 được kiểm lại. [Verifier](human_gate/receipts/human_20261122144027Z/verification.json) · [Hướng dẫn tái lập](human_gate/receipts/human_20261122144027Z/REPLAY.md)

Chủ dự án cần cung cấp authority và chữ ký Round 1, xác nhận quyền xem riêng và lưu phản hồi theo năm tập artifact trước khi cấp gói. Sau đó R02 và R03 có thể cung cấp tối đa 90 đề xuất riêng cho 45 ca. Hồ sơ đủ điều kiện mới chuyển người phân xử và owner approver. Sức mạnh thống kê vẫn theo P5B `INFEASIBLE`. Duy trì `GO_PREPARATORY_ONLY`, `NO_GO_SUPERIORITY`, TASK 6B/7B BLOCKED.
