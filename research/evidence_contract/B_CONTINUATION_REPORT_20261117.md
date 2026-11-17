# Tiếp tục B Oracle Reliability — 17/11/2026

**Đã hoàn tất mốc chuẩn bị P0–P4 theo handoff: `GO_PREPARATORY_ONLY`.**
Scientific gate vẫn **`NO_GO_SUPERIORITY`**. Chưa mở TASK6B/7B, chưa có cohort,
inference/training, reference approval hoặc đánh giá người mới. Không coi kiểm
thử synthetic là bằng chứng cải thiện model. [Các quyết định D1–D12](B_OWNER_DECISIONS_20261117.md)
đã cụ thể hóa phần cần chủ dự án/người có thẩm quyền.

## Mốc đã làm và kết quả

| Phần | Đã hoàn tất / kết quả kiểm được |
|---|---|
| P0 — intake | Đọc đủ 1.231 dòng deep-research report, đối chiếu tài liệu repo và giữ manifest bảo toàn 2.741 file |
| P1 — intake người chấm | [Validator/quarantine mới](reviewer_tools/README.md): strict JSON/schema, binding ZIP/reviewer/pha, raw bytes bất biến, chặn nhập trùng; cả 3 ZIP đã phát và R02 86/86 qua kiểm read-only |
| P1 — semantic/exposure | Registry lexical có trạng thái chưa duyệt; quét 22.861 JSON có sẵn; 192/1.000 instance MIDV-2020 có exposure xác nhận, 808 chưa rõ, cả 10 loại đã dùng |
| P2 — reference/adjudication | [Workflow chữ ký và journal](oracle_reliability/REFERENCE_WORKFLOW.md), version/binding/revocation/checkpoint; production authority và approved reference đều 0; dry-run hai người/ba ca đều SYNTHETIC |
| P2 — C2 | 1.100 cặp nguồn tiềm năng trên 400 instance, **0 cặp đủ điều kiện**; thiếu chứng cứ support sau mutation và phê duyệt semantic/provenance/reference |
| P3 — design | [Protocol v2](B_PROSPECTIVE_PROTOCOL_DRAFT_v2_20261117.md) có arm/guard matrix cùng thông tin, endpoint/panel đề xuất, missingness, clustering, ngân sách/stop rules; asserted arm mới là đặc tả |
| P3 — metrics/sizing | Tái tính đúng 492 nhóm/823 cells, thêm UNKNOWN/INVALID/structure/unresolved và giữ NA; [384 scenario sizing](B_SIZING_AND_POWER_DRAFT_20261117.md) là minh họa, chưa khóa N/margin/floor/seed/budget |
| P4 — paper/readiness | [Ledger 12 claim](paper/B_CLAIM_TO_EVIDENCE_20261117.md), [outline B](paper/B_ORACLE_RELIABILITY_OUTLINE_20261117.md), [readiness matrix](paper/B_EASE_READINESS_20261117.md); chưa có PDF B hoặc submission |

Chi tiết kỹ thuật và các lần chạy ở
[tooling milestone](execution/master_01/oracle_reliability_20261116/continuation_20261116_2347/TOOLING_MILESTONE.md).
Thư mục bắt đầu ngày 16/11 được giữ nguyên tên khi công việc sang ngày 17/11.

## Kiểm thử và bảo toàn

**411 tests + 6 subtests PASS** trong bộ Evidence Contract, tăng 75 test so với
baseline 336 + 6. Targeted: 52 intake/registry/semantic tests và 23 accounting/
sizing tests. [Full receipt](execution/master_01/oracle_reliability_20261116/continuation_20261116_2347/full_tests_01.json)
ghi exact command, thời gian, môi trường và hash raw log. Không cộng số lượt chạy
lặp thành mẫu nghiên cứu hoặc số người chấm.

Hai lần lỗi development được giữ nguyên log: chạy script compatibility sai cách
gây import error (đã đổi sang module invocation); endpoint Wilson p=0 có sai số
floating-point 2,78e-17 (đã xử lý đúng biên 0/1). Các lượt sau và full suite đều qua.
Audit C2 lần 2 sau hardening source ID cho cùng inventory/counts. Không sửa hay
che log lỗi. Dependency mới duy nhất: `cryptography==50.0.2` cho kiểm chữ ký.

Verifier độc lập tái tính đủ 492 nhóm từ 823 cells; không xác minh human truth.
**2.741 file được bảo vệ không đổi**, gồm frozen code, phiếu/ZIP, nhãn, log cũ,
protocol và ledger cũ. Final release check được lưu trong thư mục continuation.
Raw reviews, ghi chú, joins, lineage từng ID và inventory candidate giữ local;
GitHub chỉ nhận mã, tài liệu, aggregate và receipts.

## Kết luận khoa học còn giữ nguyên

58 controls là logic do dựng, không phải ảnh/model faults mới. Tier 2 có risk
pointwise 1/7 so với 2/25 tier 1 và mất 14/19 fault; hai nguồn cùng sai vẫn FP.
Flat/B cùng guard vẫn parity trong miền kiểm. Pilot actual có 46 so sánh, 42
primary/3 ID; B chưa được duyệt reference nên abstain field/relation, risk **NA**.
Chưa có bằng chứng natural-fault superiority, cost benefit hoặc population recall.

Author đã hoàn tất cả hai pha. R02 phase 1 có 86/86, role correction được giữ
riêng; R02 phase 2 và R03 còn chờ. Round 1 **OPEN**, không cutoff hoặc phân xử
thực tế. Production reference candidates/approved: **0/0**; 1.100 C2 pairs chỉ là
inventory feasibility, không phải 1.100 approved references. Một candidate trong
demo synthetic được approve rồi revoke; không đi vào production.

Exposure audit nâng lower bound cũ 148 lên 192, không chứng nhận 808 ID còn lại
là unseen. Metadata của cả 1.000 instance đã được truy cập. Pixel/near-duplicate,
cross-corpus lineage và pretraining overlap còn thiếu. 1.097 cặp literal/precision
khác nhau không phải 1.097 annotation sai; ba cặp còn lại có MRZ ngoài phạm vi.
Chưa xác minh C2 backup còn hỗ trợ sau mutation. Huấn luyện thêm không tự giải
quyết các thiếu hụt reference và thiết kế này.

## Gate và bước tiếp theo

| Gate | Trạng thái thực tế | Điều kiện đi tiếp |
|---|---|---|
| Reviewer evidence | BLOCKED_HUMAN_REVIEW | Nhận phiếu thật hoặc cutoff được ghi rõ; agreement trước phân xử |
| Reference approval | BLOCKED_REFERENCE_APPROVAL | D2/D3: authority/quy trình và reference được duyệt theo phiên bản |
| Corpus/release rights | BLOCKED_RIGHTS | D10: quyết định quyền cho artifact/version/cohort cụ thể |
| Protocol/sizing | BLOCKED_PROTOCOL_APPROVAL | D4–D9/D11: contrast, endpoint, floor/margin, design/budget/exposure; triển khai/kiểm asserted arm |
| Cohort/scientific GO | NOT_OPENED | Các gate trên, lineage và lock đầy đủ rồi mới có owner scientific GO |
| EASE Research | NOT_SUBMISSION_READY | Bằng chứng phù hợp claim, novelty và manuscript/anonymous artifact đầy đủ |
| Emerging / RENE | PLANNING_ONLY | Chỉ thu hẹp claim/đổi track bằng amendment có căn cứ; không đổi tên một kết quả thiếu lực kiểm định thành thành công |

Phần chuẩn bị tiếp còn có thể phát triển: audit pixel/near-duplicate trên assets
được phép, comparator đã đặc tả, phân tích novelty và đo chi phí reviewer. Phạm vi
cohort/estimand cần chốt trước để tránh tiếp tục thêm code hoặc chọn dữ liệu theo
kết quả thuận lợi. Bảng D1–D12 là lựa chọn để duyệt, không yêu cầu làm lại phiếu.

## Git và truy vết

HEAD đầu lượt và mốc so sánh: `0f40f5e014b1065d86c10ad453ed23e2db17ac34`.
P0 đã push tại `0d47988274cde4060c6e3b727f80c1197eb5ecd2`.
Mốc tooling/tests/aggregate đã push tại
`ace4628cc3c8b909b7a327a0eda48ff0410b4db8`; `git ls-remote --heads origin` xác
nhận đúng hash và chỉ có `main`. [Receipt](execution/master_01/oracle_reliability_20261116/continuation_20261116_2347/tooling_sync.json).
Delta từ `0f40f5e` gồm các module mới, tests, audit/sizing/accounting và tài liệu
chuẩn bị; frozen scientific evidence không đổi.

Báo cáo này và tài liệu P3/P4 thuộc commit tiếp theo. Final HEAD và remote HEAD
được ghi sau push vào `local/master_01/oracle_reliability_20261116/continuation_20261116_2347/final_sync_receipt.json`
và câu trả lời giao việc, tránh ghi một SHA tự tham chiếu không thể tồn tại trong
chính commit chứa báo cáo. Dùng `git log -1 -- B_CONTINUATION_REPORT_20261117.md`
từ thư mục Evidence Contract để xác định commit nội dung báo cáo. Không force-push,
không tạo branch mới và không coi local commit đơn thuần là đã đồng bộ.
