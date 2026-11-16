# Các bước tiếp theo sau IFV cá nhân

Mốc mới: [readiness audit](READINESS_ANALYSIS_20261116.md) đã giải thích A/flat,
tái hiện 2 lỗi parser bằng before/fix/revert trên 118 ca và lập
[evidence map](METHODS_EVIDENCE_MAP_20261116.md). Bước tiếp theo ngoài review là
khóa đóng góp hẹp, kiểm dữ liệu ngoài renderer, thiết kế so sánh sinh test/triage
cùng thông tin và ngân sách, rồi sizing cohort mới. Bản thảo Emerging là phương
án song song với mục tiêu Research; không train thêm để thay kết quả pilot.

Cập nhật 16/11/2026. **DONE: pha 1 86/86 ô, pha 2 46/46 ca; 7A đã nhập,
replay và xuất phân tích mô tả.** Không còn chờ phiếu đối chiếu hiện tại.
[Trạng thái](IFV_REVIEW_STATUS.md) · [Kết quả](IFV_RESULTS_VI.md)

| Thứ tự | Việc triển khai | Đầu vào / tiêu chí kết thúc |
|---|---|---|
| 1 — DONE | Nhập pha 2, khóa export và replay hai endpoint | Giữ nguyên 46 câu trả lời; 26/42 nhãn pointwise, 21/42 nhãn relation; 0 model calls |
| 2 — DONE | Hậu kiểm mẫu số, source guards và nhất quán | 17 cờ literal/15 primary; báo riêng độ nhạy, cảnh báo chưa kết luận và C2. Không sửa bảng chính |
| 3 — DONE quyết định pilot | Rà superiority và claim ledger | Giữ NO-GO 6B/7B; A_flat trùng A, lợi ích FAR không vững qua sensitivity, pointwise sensitivity/coverage của A thấp hơn B3 |
| 4 — DONE ba mốc development | [Biến thể trên pilot cũ](A_DEVELOPMENT_20261116.md), [reference controls](REFERENCE_CONTROLS_20261116.md), [readiness audit](READINESS_ANALYSIS_20261116.md) | Thêm phân tích 255 cấu hình/164 control, 118 ca parser actual trên 5 phiên bản; 2 lỗi lịch sử được cô lập. 260 Python + 6 subtests qua. Không có model fault mới hoặc superiority/GO |
| 5 — READY gói, chưa có phiếu ngoài | Gửi riêng ZIP R02/R03 theo [hướng dẫn](REVIEWER_HANDOFF_VI.md); thu pha 1 của từng người rồi mới cấp pha 2 | Khuyến nghị thêm hai người ngoài. Tool agreement và kiểm logic đã có; 0 reviewer mới thực nhận. Giữ exposure, phiếu gốc và bất đồng trước phân xử; tác giả không cần làm lại toàn phiếu |
| 6 — Dữ liệu/adequacy | Hoàn thiện prep 6A cho phạm vi claim được chọn | Nhãn nguồn, quyền dùng, tách ID/content/pixel/lineage, số cụm và budget theo sizing. Chỉ tạo/khóa confirmatory sau GO mới |
| 7 — DONE build/replay, còn duyệt khoa học | [PDF Emerging 3 trang](paper/output/pdf/emerging_20261116.pdf), [gói replay 22 file](paper/readiness_replay_20261116.zip) | Build và xem đủ trang; extracted replay 596 parser calls qua. Còn novelty/tác giả duyệt, quyền phát hành và supplement ẩn danh. Research là mục tiêu có điều kiện |
| Song song — Ứng dụng | Profiling stage, chuẩn bị audit nhãn định vị và kiểm hồi quy khi có thay đổi | [Luồng độc lập](INDEPENDENT_WORK_STATUS.md). Không thay reader nghiên cứu đã khóa hoặc train lại để thay phân bố lỗi đã đo |
| Mọi mốc hoàn tất — GitHub | Commit/push mã, tài liệu, aggregate và receipt sau kiểm thử | Theo [chính sách](../../PROJECT_SYNC_POLICY.md); nhánh progress được đồng bộ và kiểm HEAD. Raw review, ZIP ảnh và identities giữ local; main chờ duyệt PR |

Báo cáo hiện tại đủ cho mô tả một tác giả trên development, chưa đủ cho gold
độc lập, inter-rater agreement, population recall, cost benefit hoặc
confirmatory superiority. [Quyết định đầy đủ](REVISED_GO_NO_GO.md)
