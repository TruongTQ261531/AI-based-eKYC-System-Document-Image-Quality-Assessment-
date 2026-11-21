# Các bước tiếp theo sau IFV cá nhân

## Sau P5B · 21/11/2026

Ưu tiên mô tả các chuyển tiếp mà D4 cho phép, số cảnh báo rút và số lỗi có nhãn bị hoãn theo loại nguồn. Giữ GO_PREPARATORY_ONLY và NO_GO_SUPERIORITY. Quyền dữ liệu, reference, truth và tỷ lệ can thiệp thực sự chạm nguồn vẫn đang mở. [Quyết định P5B](P5B_STATISTICAL_CALIBRATION_VI.md)

## Sau mô phỏng P5 · 21/11/2026

Dừng trước prospective. Ưu tiên so sánh một phương án hiệu chỉnh suy luận cho sensitivity và trường hợp coverage hằng trong bản amendment riêng, rồi kiểm hiệu chuẩn trên seed giữ riêng. Quyết định này cần đọc cùng phần quyền, truth, ngân sách và nhật ký quyết định v3. [Mô phỏng P5 và quy tắc dừng](P5_STATISTICAL_FEASIBILITY_VI.md)

## Sau checklist P0–P4 ngày 21/11/2026

Protocol v3 đã có quyết định thiết kế và trần ngân sách. Việc còn mở là ghi nhận quyết định D1–D3, hoàn thiện quyền và exposure cho đúng phiên bản dữ liệu, kiểm khả năng đạt độ chính xác trong các trần, rồi trình quyết định có mở prospective hay không. Chủ dự án đã yêu cầu chưa chạy. [Checklist và bằng chứng](CHECKLIST_P0_P4_20261121.md)

## Sau audit P2 · 21/11/2026

1. Chốt phạm vi Round 1, người có quyền phân xử và quy tắc xử lý bất đồng. Tiêu chí đạt là D1–D3 có quyết định được ghi nhận, ràng buộc đúng các snapshot đã nhận.
2. Xác minh nguồn trên những giấy tờ đã liên kết được ảnh. Mỗi cặp muốn đưa vào C2 cần có hồ sơ ảnh trước/sau, định danh hai vùng, khả năng đọc, precision, quyền sử dụng và quyết định về reference. Báo số cặp đủ cả tám điều kiện và lý do cho các cặp còn lại.
3. Chốt thiết kế prospective sau khi biết số cụm có quyền và có truth. Tiêu chí đạt là D4–D12 có quyết định về contrast, endpoint, floors, margin, cỡ mẫu, ngân sách, xử lý exposure và giới hạn claim. [Kết quả và blocker P2](P2_AUDIT_VI.md)

## Mốc khảo sát và kế hoạch trước P2 · 20/11/2026

Khảo sát đã thu đủ hai pha của tác giả, R02 và R03. Danh sách bất đồng đã được lập để chờ chủ dự án chốt vòng, người phân xử và quy tắc phân xử theo D1–D3. Trong 22 ca chính mà R02 và R03 cùng có kết luận lỗi hoặc không lỗi về giá trị OCR, một ca có kết luận đối nghịch. [Kết quả khảo sát](R03_PHASE2_REVIEW_INTAKE_20261120.md)

Đọc [bản bàn giao tổng thể](../../PROJECT_HANDOFF_20261120_VI.md) trước khi
tiếp nhận. D4 P1 đã được triển khai và full Evidence Contract suite đạt 579
tests + 6 subtests. Kết quả chỉ là constructed development và replay lịch sử;
NO_GO_SUPERIORITY vẫn còn.

Việc tiếp theo không phụ thuộc phiếu mới: (1) review adapter và counterexamples
D4; (2) hoàn thiện pixel/near-duplicate/lineage audit trên assets được phép;
(3) làm rõ PASS/FAIL/UNKNOWN cho C2; (4) cập nhật novelty matrix bằng nguồn sơ
cấp; (5) hoàn thiện threats, reproducibility và release-rights checklist.
Không chọn prospective cohort, tạo approved reference hay kết luận superiority
trước khi các điều kiện protocol/authority/rights được ghi nhận. R03 và các mục
human gate tiếp tục theo trạng thái thực nhận, không thay bằng test kỹ thuật.

Danh sách phụ thuộc và thứ tự rộng hơn nằm trong bản bàn giao tổng thể. Các mốc
cũ bên dưới được giữ nguyên như nhật ký lịch sử.

Ưu tiên sau **[intake R02 pha 2 ngày 17/11](R02_PHASE2_REVIEW_INTAKE_20261117.md)**:

1. R02 đã hoàn tất 86/86 pha 1 và 46/46 pha 2; không gửi lại ZIP hay yêu cầu
   làm lại toàn phiếu. Raw, role correction và báo cáo tác giả giữ nguyên.
2. Tiếp tục nhận pha 1 R03, khóa snapshot rồi cấp pha 2 riêng. Không gửi bảng
   bất đồng/đáp án/báo cáo R02 cho người đang chấm độc lập. Pha 2 hiện có
   tác giả + 1 external; chưa có đối chiếu giữa hai external.
3. Round 1 OPEN: chỉ đóng khi thành phần/cutoff và authority được quyết định
   rõ. Giữ 1 bất đồng binary pointwise và các khác biệt validity/uncertainty
   để phân xử sau khóa vòng; không tự đổi đáp án hoặc lấy đa số làm gold.
4. Theo [D1–D12](B_OWNER_DECISIONS_20261117.md), tiếp tục reference/lineage/
   rights, contrast/comparator và prospective design/sizing. R02 không tự
   giải quyết C2 (0/9 binary), 3 ID primary hoặc superiority: A còn FN=5/9
   theo riêng panel R02. Không mở TASK 6B/7B hoặc chạy lại model để tăng n.

Mốc này **432 tests + 6 subtests PASS**, 3.645 tệp cũ không đổi; code, aggregate
và receipt được đồng bộ main. Các kế hoạch/bảng bên dưới là lịch sử trước
lần nhận R02 pha 2; trạng thái chờ R02 trong đó đã được thay bằng DONE ở trên.

Ưu tiên hiện tại **17/11**, sau [mốc continuation](B_CONTINUATION_REPORT_20261117.md):
tooling chuẩn bị đã qua **411 tests + 6 subtests**. Không cần làm lại phiếu cá
nhân, rebuild ZIP cũ hoặc chạy lại pilot để tạo số mẫu mới. Tiếp tục theo
[protocol v2](B_PROSPECTIVE_PROTOCOL_DRAFT_v2_20261117.md) và
[bảng quyết định D1–D12](B_OWNER_DECISIONS_20261117.md): nhận JSON thật/cutoff rõ,
chỉ định authority/phân xử; chốt contrast/endpoint/floors/margin, design/budget,
rights và exposure trước cohort. Comparator asserted mới có đặc tả; lineage
pixel/near-duplicate và novelty vẫn cần hoàn thiện theo claim đã chọn.
R02 pha 2/R03 còn chờ; Round 1 OPEN. 384 sizing scenarios không phải final N;
0 production approvals, 0/1.100 C2 candidates eligible. Scientific NO-GO giữ nguyên.
Các đoạn/bảng cũ dưới đây là tiến độ tại thời điểm được ghi.

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
