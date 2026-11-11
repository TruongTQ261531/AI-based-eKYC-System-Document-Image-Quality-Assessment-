# TASK 3 — Generator, contracts và verification audit

Ngày chốt: **06/11/2026, Asia/Bangkok**. Kết quả dưới đây lấy từ execution logs/artifacts thực tế. Đây là **fixture/development pilot**, không phải OCR/VLM benchmark, phép thử chính của RQ1–3 hoặc xác nhận novelty/EASE acceptance. Không fine-tune và không chạy neural inference trong TASK này.

## Phạm vi, trạng thái xuất phát và bảo toàn

Repo: `D:/laptrinhcuatao/Ekyc/versions/research-document-recovery`; branch `main`; HEAD `f5d130d93525e7633053edc03e6d9f6edeba7a6f`. Không tìm thấy artifact TASK 2 trong workspace đã rà; chỉ thấy TASK 0–1. Không giả lập kết quả TASK 2 và không đổi METHOD_SPEC/RQs để khớp code.

Đã kiểm lại **889 file có trước**, **102.254.867 byte**, không có mismatch. HEAD/refs, tracked diff và staged diff không đổi. Code hiện tại khớp code hash của lần test cuối và pilot cuối. [Manifest trước](execution/task3_generator/preservation_before.json), [kiểm tra cuối](execution/task3_generator/preservation_final.json). Phạm vi hash gồm tracked và pre-existing nonignored untracked; không tuyên bố đã hash lại mọi ảnh/cache/checkpoint ignored.

Không sửa production API/UI mentor, files legacy, checkpoint, splits, model selection, kết quả nghiên cứu cũ hoặc các tài liệu TASK 0–1. Không gọi completed dataset builders, preserve helpers có side effect, download/setup, Git commit/push hoặc xóa dữ liệu/log. Venv/package hiện có được tái sử dụng.

## Files thực sự tạo

Module mới: `__init__.py`, [source_graph.py](source_graph.py), [validity.py](validity.py), [contracts.py](contracts.py), [generator.py](generator.py), [fixtures.py](fixtures.py), [pilot.py](pilot.py).

Tài liệu và tests: [CONTRACT_SPEC.md](CONTRACT_SPEC.md), file audit này, [tests/test_contracts.py](tests/test_contracts.py). Logs, JUnit, code snapshots, paired PNG/JSON và audits nằm riêng tại `execution/task3_generator/`. Không tạo database.

## Unit/regression verification đã chạy

| Lần thực thi | Kết quả thực tế | Log |
|---|---:|---|
| tests_run_01, implementation ban đầu | 59 passed | [execution.log](execution/task3_generator/tests_run_01/execution.log) |
| tests_run_02, thêm glyph/extent checks và legacy fixtures | 93 passed | [execution.log](execution/task3_generator/tests_run_02/execution.log) |
| tests_run_03, role/privacy hardening | 95 passed | [execution.log](execution/task3_generator/tests_run_03/execution.log) |
| **tests_run_04, implementation hiện tại** | **96 passed; 0 failed/error/skipped**, 15,25 s theo pytest | [execution.log](execution/task3_generator/tests_run_04/execution.log), [JUnit](execution/task3_generator/tests_run_04/junit.xml), [command/hash/timestamps](execution/task3_generator/tests_run_04/execution.json) |

Lần cuối có **69 tests mới** và **27 legacy fixture tests** từ `test_v3_sources.py`, `test_hp_masks.py`, `test_labels_schema.py`. Không cộng các lượt lặp thành số tests độc lập mới. Không chạy lại các thí nghiệm đã hoàn tất hoặc full production/browser suite vì không sửa production.

Coverage hành vi đã kiểm: OR backup/AND multiline; checksum sai/thiếu policy; key unmapped; source conflict; century overreach; C1 positive/negative/inconclusive và malformed JSON; C2 reading/omission riêng; C3 pre-existing error, context loss và bound four-output regression witness; C4 exact transform, crop/pixel corruption, orientation policy; mask sót một pixel, bbox bỏ glyph, no-glyph extent và human-review binding. Có cả role/privacy/export/path/no-overwrite guards. Human review trong tests là **mô phỏng**, không phải phiếu người thật.

## Pilot đã thực thi

Ba run được giữ: [run 01](execution/task3_generator/pilot_run_01/report.json), [run 02](execution/task3_generator/pilot_run_02/report.json) và [run 03 hiện tại](execution/task3_generator/pilot_run_03/report.json). Mỗi run dùng seeds **42, 31415, 20261106**, 8 graph instances × 7 families × 3 seeds = **168 attempts**. Dữ liệu gồm 5 fixture graph instances và 3 existing-renderer development instances (specifications 0–2). Limited-annotation variant giữ cùng physical ID và raster với backup fixture gốc: thực tế chỉ **7 physical IDs / 7 original rasters**.

Families: original/full; single-source mask; all-sources mask; paired A/B hai chiều; integer padded translation; quarter-turn diagnostic. Không mở confirmatory inputs; chỉ renderer in-memory/development đã khóa phạm vi. Không sửa ảnh/data gốc.

| Chỉ số, run 03 | Tử số / mẫu số | Kết quả |
|---|---:|---:|
| Sinh/lưu pair thành công | 168/168 | 100% |
| **Precondition-valid generation yield** | **138/168** | **82,14%** |
| **Invalid-test rate** | **9/168** | **5,36%** |
| Inconclusive validity | 21/168 | 12,50% |
| Contract có quyết định PASS/VIOLATION trên constructed correct-output controls | 114/168 | 67,86% |
| Validity yield khi bỏ 24 identity/full controls khỏi cả tử và mẫu số | 114/144 | 79,17% |
| Generation errors | 0/168 | 0 |
| Ảnh artifact kiểm lại hash/decoded pixels | 336 | 0 mismatch |

Tất cả 9 invalid và 21 inconclusive vẫn được lưu ảnh, metadata và reason trong manifest/attempt ledger. Không refill để đạt tỷ lệ cao hơn. [Attempt ledger](execution/task3_generator/pilot_run_03/attempts.json), [kiểm artifact](execution/task3_generator/pilot_run_03/artifact_audit.json), [lệnh và exit code](execution/task3_generator/pilot_run_03.execution.json).

## Coverage từng contract

| Contract | Attempts | Valid preconditions | Invalid test | Inconclusive validity | Contract decision coverage |
|---|---:|---:|---:|---:|---:|
| C1 — all evidence removal | 24 | 18 | 3 | 3 | 18/24 = 75,00% |
| C2 — backup preservation | 24 | 3 | 3 | 18 | 3/24 = 12,50% |
| C3 — A/B non-interference | 48 | 45 | 3 | 0 | 45/48 = 93,75% |
| C4 — evidence-preserving geometry | 72 | 72 | 0 | 0 | 48/72 = 66,67% |

C4 có thêm **24 contract-INCONCLUSIVE** vì quarter-turn giữ pixel nhưng default SUT policy chưa cam kết orientation invariance. Chúng có mutation validity VALID; không được đổi thành PASS chỉ để tăng coverage. Đây là lý do validity yield khác contract decision coverage.

C2 thấp vì nhiều fixtures chỉ có một body source, một fixture deliberately limited annotation và một fixture MRZ checksum sai. Không thể dùng review để tự tạo backup không có. Corpus hiện chỉ có một valid redundant-source fixture lặp ba seeds; không suy coverage tổng quát từ 3 ca này. Cần thêm verified backup-source development cases trước thí nghiệm paper, giữ tất cả ca không áp dụng trong denominator/report.

## Vì sao mẫu bị giữ lại dưới INVALID/INCONCLUSIVE?

- **9 invalid:** shared-semantic-context fixture có A value đồng thời cần để hiểu key B. Ba loại mask × ba seeds làm mất context B; value pixels B vẫn nguyên. Validator phát hiện đúng loại precondition loss mà value-only bbox check có thể bỏ qua.
- **3 C1 inconclusive:** body bị che nhưng source universe deliberately incomplete. [Ảnh minh họa](execution/task3_generator/pilot_run_02/seed_42/1051c24b33a2190d7d654a7781189849592ca9fc2e5bfa9d06de6973b7184e81/followup.png) vẫn còn duplicate/MRZ ngoài graph; không kết luận A không có evidence.
- **18 C2 inconclusive:** 15 attempts không có declared backup trong scope, 3 có MRZ không đủ checksum policy. Không nhận chúng thành hallucination/reading failure của model.
- **24 C4 policy inconclusive:** pixel correspondence đủ, orientation guarantee chưa được khai báo.

Đã xem trực quan hai ảnh fixture: [complete-removal sample](execution/task3_generator/pilot_run_02/seed_42/ea06eea13e678ad30560b7716a83bca7f2b0e1025374f45dca4924cdb9b0c827/followup.png) và limited-annotation sample trên. Đây là visual sanity check của người triển khai, **không phải independent human readability annotation**.

Review queue của validity có 6 attempts: incomplete-source scope hoặc unverified backup cần thêm provenance/review. Các ca không có backup là inapplicable, không được che giấu bằng cách đề nghị reviewer xác nhận một nguồn không tồn tại.

## C3 near/far và tránh phóng đại sample size

Audit mô tả theo ngưỡng legacy body-gap 0,08 đường chéo: **36 near, 12 far** trên 48 C3 attempts, giữ cả invalid cases. Không lọc theo output hoặc biến far pairs thành near. [pair_distance_audit.json](execution/task3_generator/pair_distance_audit.json) gắn khoảng cách với từng case. Kết quả hiện xác minh field non-interference logic; không chứng minh lợi thế chọn neighbor/hard-pair hoặc H3.

Ba seeds không tạo thêm danh tính hay real bugs. Metadata ablation có cùng pixel giữ cùng physical ID. Không lấy 168 rows/336 PNG làm số giấy tờ độc lập hoặc đóng góp dataset camera mới.

## Constructed control outputs và mức bằng chứng

[constructed_controls.json](execution/task3_generator/pilot_run_03/constructed_controls.json) chứa output packs đúng/sai **do code chủ động tạo từ fixture references** để exercise contracts. Trên ca đủ điều kiện, correct packs nhận PASS và incorrect packs nhận VIOLATION; invalid/unknown/policy-inapplicable giữ nguyên. Không báo đây là OCR accuracy, oracle false-positive rate được xác minh độc lập, fault recall hoặc model hallucination rate.

Single pair chỉ báo behavior violation. Unit tests có simulated version quad để kiểm `behavior_regression_verified`; không historical bug/patch/revert hay seeded-fault corpus nào đã được chạy trong TASK 3. `software_fault_confirmed` không tự bật. H1'–H3' vẫn là giả thuyết; main study chưa chạy.

## Reproducibility và lỗi quan sát được

Ba pilot chạy trên **ba implementation revisions**: run 02 thêm adapter role/privacy hardening và code snapshots tự động; run 03 chặn việc opt-out field checksum bắt buộc của numeric/date MRZ. Không đổi fixture transformations. Đối chiếu **168 cặp tương ứng** run 01–02 và run 02–03: encoded/pixel hashes, masks, case IDs, source states và validity đều khớp, **0 mismatch**. [đối chiếu 01–02](execution/task3_generator/replication_comparison.json), [đối chiếu cuối 02–03](execution/task3_generator/final_pilot_comparison.json). Đây là non-regression/serialization check, không phải ba thí nghiệm model độc lập.

Mỗi run có snapshot đúng hash của **10 source files** (sáu module pilot/core và bốn helper legacy) để tái dựng revision. [snapshot audit cuối](execution/task3_generator/snapshot_audit_final.json): 0 mismatch. Run 03 xác nhận source files không đổi trong execution và original input pixel arrays giữ nguyên.

Một auxiliary distance-audit script ban đầu lỗi `TypeError` vì giả định mọi INVALID_TEST có `after_graph`; validator chủ ý cho phép `None` khi test hỏng. Đã giữ [failure record](execution/task3_generator/postprocess_attempt01.json), sửa postprocessing dùng original/full graph gắn cùng input hash và hoàn thành audit, không đổi core code, labels, pilot hoặc loại row. Đây không phải thất bại của unit tests/pilot, cũng không bị ẩn khỏi audit.

## Chưa xử lý / giới hạn và bước kế tiếp

1. **Natural human legibility/source completeness:** chưa có independent labels hoặc Task 2 attestation adapter được xác minh. Clean/Blur/bbox và construction glyph support không thay được chúng. Một người chấm chỉ đủ pilot feedback; chưa thu review mới.
2. **Encoded/unsupported sources:** QR/barcode, TD1/TD2, malformed MRZ ngoài parser, bản ngữ/semantic mappings chưa khai báo giữ unknown/limited; không tự sửa ký tự/checksum hoặc đoán key từ vị trí.
3. **Geometry tổng quát:** arbitrary perspective, blur/resampling, glare và crop-loss không có blanket invariance. Quarter-turn chỉ kết luận khi SUT policy cho phép và preconditions đủ. Chưa có mục tiêu cải thiện Module 2/OCR trong TASK này.
4. **Selection và external coverage:** explicit semantic A/B pair selection; chưa chạy random/validity-filtered random baselines, fault budget experiment hoặc near-only superiority. C2 cần thêm valid-source diversity.
5. **Regression/fault proof:** interface witness đã có, chưa có actual historical-fault reproduction hoặc independently curated fault pool. Chưa kết luận lỗi thực được tìm thấy hay đạt novelty EASE.
6. **Runtime integration:** code mới là research library/CLI; chưa nối vào API/web production, chưa thực nghiệm camera/biometric, không đánh giá liveness/PAD.

Kết luận TASK 3: bốn contracts, adapters, paired generator, raster validator và verification fixtures đã chạy được trong phạm vi fixture/development. **0 neural model calls, 0 optimizer steps, 0 confirmatory inputs opened, 0 new human reviews** trong runner này. Bước sau cần foundation/annotation/fault feasibility và khóa protocol trước main experiments; không tự tiếp tục training hoặc test chính.
