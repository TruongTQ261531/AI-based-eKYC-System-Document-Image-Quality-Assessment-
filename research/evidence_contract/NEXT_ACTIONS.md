# Các bước tiếp theo sau IFV cá nhân

Ưu tiên hiện tại sau [B v2 ngày 16/11](B_ORACLE_RELIABILITY_20261116.md):
P0/P1/P2 đã hoàn tất, không cần chạy lại pilot hoặc huấn luyện để bù reference
còn thiếu. Theo [protocol mới](B_PROSPECTIVE_PROTOCOL_DRAFT.md), tiếp tục hoàn thiện
lineage/exposure corpus, semantic mapping và panel C2 có backup được xác minh;
chốt contrast, sizing/budget trước cohort mới. Reference approval và scientific
GO cần chủ dự án/người có thẩm quyền. Round 1 vẫn OPEN; nhận R02 pha 2/R03 khi có,
giữ phiếu/ZIP cũ và báo agreement trước phân xử. Chưa có B PDF hoặc submission.

Mốc tiếp nhận R02 16/11: **pha 1 86/86 đã nhập**, đã tính agreement trước phân
xử và tạo [ZIP pha 2 riêng 46 ca](R02_REVIEW_INTAKE_20261116.md). Gửi cho đúng R02,
nhận JSON pha 2; tiếp tục thu pha 1 R03 rồi mới cấp gói riêng. Có 19 bất đồng
semantic key/86 mục (κ=0,0239), cần kiểm hướng dẫn và phân xử sau khi khóa các
đánh giá độc lập. Không gửi bảng bất đồng hoặc đáp án tác giả cùng ZIP.

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
| 5 — R02 pha 1 DONE, pha 2 READY | Gửi ZIP pha 2 riêng R02 theo [hướng dẫn](REVIEWER_HANDOFF_VI.md); thu pha 1 R03 trước khi cấp pha 2 của R03 | Đã nhận 1 người ngoài ở pha 1; pha 2 ngoài dự án còn 0. Agreement pha 1 đã tính, chưa phân xử. Giữ raw export, role correction, exposure và bất đồng; tác giả không cần làm lại toàn phiếu |
| 6 — Dữ liệu/adequacy | Hoàn thiện prep 6A cho phạm vi claim được chọn | Nhãn nguồn, quyền dùng, tách ID/content/pixel/lineage, số cụm và budget theo sizing. Chỉ tạo/khóa confirmatory sau GO mới |
| 7 — DONE build/replay, còn duyệt khoa học | [PDF Emerging 3 trang](paper/output/pdf/emerging_20261116.pdf), [gói replay 22 file](paper/readiness_replay_20261116.zip) | Build và xem đủ trang; extracted replay 596 parser calls qua. Còn novelty/tác giả duyệt, quyền phát hành và supplement ẩn danh. Research là mục tiêu có điều kiện |
| Song song — Ứng dụng | Profiling stage, chuẩn bị audit nhãn định vị và kiểm hồi quy khi có thay đổi | [Luồng độc lập](INDEPENDENT_WORK_STATUS.md). Không thay reader nghiên cứu đã khóa hoặc train lại để thay phân bố lỗi đã đo |
| Mọi mốc hoàn tất — GitHub | Commit/push mã, tài liệu, aggregate và receipt sau kiểm thử | Theo [chính sách](../../PROJECT_SYNC_POLICY.md), main là branch duy nhất; fetch, push thường và kiểm HEAD remote. Raw review, ZIP ảnh và identities giữ local |

Báo cáo pha 2 hiện tại vẫn mô tả một tác giả trên development. Đã có agreement
pha 1 tác giả/R02, chưa có agreement pha 2, gold độc lập, population recall,
cost benefit hoặc confirmatory superiority. [Quyết định đầy đủ](REVISED_GO_NO_GO.md)
