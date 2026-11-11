# EASE 2027 protocol draft — chưa đăng ký, chưa thực nghiệm

Phiên bản tài liệu: TASK1-draft-2026-11-06. Đây là kế hoạch prospective, **không phải execution log hoặc kết quả**. Chỉ chuyển sang implementation nhỏ khi có task tiếp theo; chưa được chạy main tests, training hoặc model sweep từ tài liệu này.

## 1. Mục tiêu và cơ sở

Đánh giá phương pháp kiểm thử source-aware evidence contracts của extraction pipeline, theo ba [Research Questions](RESEARCH_QUESTIONS.md). Một contribution chính C1 và hai hỗ trợ C2/C3 như [GAP_ANALYSIS](GAP_ANALYSIS.md). Legacy OCR/VLM kết quả chỉ dùng hồi cứu/exploratory, không đổi checkpoint/split/scorer để phục vụ EASE.

[CFP Research Papers EASE 2027](https://conf.researchr.org/track/ease-2027/ease-2027-papers) là nguồn scope và quy định nộp bài. Protocol phải tạo bằng chứng về testing/quality/SE for AI và empirical evaluation; thành công OCR hoặc web demo chỉ đóng vai trò context. Không có tiêu chí tự động bảo đảm acceptance.

## 2. Bảo toàn và trạng thái xuất phát

Repository: `D:/laptrinhcuatao/Ekyc/versions/research-document-recovery`; `main`, HEAD `f5d130d93525e7633053edc03e6d9f6edeba7a6f`. TASK 0 và các file untracked có trước được giữ. Dùng [PROJECT_INVENTORY](PROJECT_INVENTORY.md), [REUSE_MAP](REUSE_MAP.md), [PRESERVATION_MANIFEST](PRESERVATION_MANIFEST.json) làm mốc lịch sử; không ghi lại chúng để tạo cảm giác các kết quả cũ thay đổi.

TASK 1 có thêm snapshot trước viết tài liệu tại [preservation_before.json](execution/task1_review/preservation_before.json): 880 tracked/nonignored untracked files, tổng 102.001.420 byte. Đây không phải hash lại toàn bộ dữ liệu/cache ignored. Sau viết tài liệu kiểm HEAD/refs và hash các file này; log sau cùng ghi riêng. Không tải weights, không cài package, không tạo venv, không gọi production API hoặc gửi ảnh lên dịch vụ ngoài.

Môi trường dự kiến cho task thực thi sau: Python sẵn `D:/laptrinhcuatao/Ekyc/.venv/Scripts/python.exe`; dùng model/cache/overlay đã kiểm kê. GPU chạy tuần tự; ghi cấu hình thực đo khi thực nghiệm bắt đầu. TASK 1 không đo latency/RAM/VRAM model mới.

## 3. Objects of study và dữ liệu

### SUT và fault pool

Hai họ reader tối thiểu dự kiến: OCR CPU hiện có và Vintern nhỏ/adapter đã có, đóng băng. RapidOCR v4/Latin-v5 chia sẻ detector/classifier nên không được gọi hai kiến trúc độc lập. Hai adapter/seed cùng backbone cũng không tăng số họ hệ thống. Không retrain để làm tester thắng.

Tách ba tập đối tượng:

1. **Oracle validation controls:** output packs đúng/sai biết theo construction và policy, kèm backup, precision, semantic duplicates, all-source removal, incomplete coverage và invalid transforms. Ghi rõ chúng là constructed outputs; không nhận là output inference.
2. **Seeded faults:** đề xuất khoảng 12 root-cause families cho evaluation trong geometry/coordinate handling, field assignment/parser và normalization/source handling; development dùng families khác, quy mô chốt sau feasibility. Mutation patches áp riêng vào SUT copy/adapter, không vào oracle hoặc production. Ghi alive/equivalent/unactivated/crash/timeout và các loại không đánh giá được. Fault families do một bộ specification/taxonomy tạo trước, không chỉ lấy mỗi contract rồi cài lỗi đối nghịch. Tách fault families development và evaluation để tránh overfit.
3. **Historical faults/version changes:** khai thác read-only commit/diff/reports để lập provenance. Không coi mọi fix trong chat hoặc commit là verified bug. Cần minimal reproduction, intended behavior, v0/v1/patch identity và kết quả patch/revert. Mục tiêu tối thiểu cho claim real-bug utility: ba root causes qua ít nhất hai stage. Chưa kiểm chứng mục tiêu này đạt.

SUT thay weights chưa tự chỉ ra software root cause. Natural model failures có thể cung cấp case studies nhưng nằm ngoài mẫu số confirmed software faults.

RQ2/RQ3 dùng controlled evaluation fault pool làm primary; historical faults là corroborating/descriptive evidence riêng, không cộng vào mutants để tạo p-value chung hoặc nhận effect trên quần thể real bugs. Fault eligibility phải được xác lập trước lock bằng witness/reference độc lập. Fault hợp lệ mà một generator không kích hoạt vẫn là miss; không loại khỏi mẫu số theo kết quả method. Equivalent/unusable exclusions cần lý do và bằng chứng độc lập; giữ số lượng tất cả exclusions/crashes/timeouts.

### Data scope và exposure

Tất cả V1/V2/V3/V4, VLM R2/source V3, hard-pair, fair-controls và OCR labels test đã mở giữ nguyên. Không gọi ảnh đổi tên/hash, view mới của cùng ID hoặc re-render cùng đáp án là test ID độc lập. Old outputs chỉ được dùng nếu image/preprocess/model/parser hash khớp; cache replay/rescoring và inference mới có counters riêng.

Đề xuất resource envelope ban đầu: 12 ID development và 40 ID confirmatory **mới hoặc đủ điều kiện**, tách theo canonical identity/source và ancestry. Đây là mục tiêu thiết kế, chưa tạo/chọn ID hay chứng minh đủ nguồn. Construction-exact SPECIMEN mới là core khả thi; bố cục/font cùng họ generator cũ vẫn là in-family validation. Có thể thêm public specimens đủ license/annotation làm extension, báo riêng. Không có bộ camera mới; không claim cross-camera/camera Việt Nam.

Trước lock cần xuất exposure matrix qua train/dev/test cũ, canonical IDs, hashes và related pixels. Nếu không tìm được pool chưa dùng để điều chỉnh, đổi thành retrospective case study hoặc tạo construction pool mới; không dán nhãn “fresh test” cho tập đã xem. Pretraining contamination của public datasets thường không kiểm soát hết, phải công bố giới hạn.

### Nguồn GT và đánh giá của người

Mỗi field có full/visible reference, semantic key, components/source links, typed precision, readability, coverage scope và provenance. Có cả key không tồn tại, chuỗi trùng khác nghĩa, multiline và MRZ không parse/không hợp lệ. Field optionality theo từng schema. Giữ nguyên labels cũ; adapter có schema version mới.

Construction truth phải được kiểm độc lập bằng kiểm raster/glyph support và fixtures, không dùng chính hàm generator trả `valid=True` làm gold. Chỉ dùng vùng đủ điều kiện rõ ràng; anti-aliasing hoặc context khó xử lý chuyển unknown. Không xem toàn bộ blur nhẹ là unreadable theo ngưỡng hình học.

Hiện chỉ có một reviewer, không có bộ camera mới. Một người đủ cung cấp pilot review/issue; nhiều mã hoặc hai lần chấm của cùng người không tạo agreement độc lập. Snapshot TASK 0 (35/48 phiếu, một người) không được tự nâng thành complete hoặc human-verified GT.

Để nhận claim human-readable/natural-image oracle validity cần hai người độc lập có thể đọc script liên quan, blind với method/model verdict, và xử lý disagreement; bất đồng chưa giải quyết giữ unknown. Natural extension chưa đáp ứng điều kiện này thì giữ ngoài confirmatory claim. Core construction-exact không cần chờ hoàn tất 48 phiếu, nhưng vẫn phải kiểm reference bằng cách độc lập về implementation. Không tự giả lập người chấm hoặc dùng model-as-judge làm gold duy nhất.

## 4. Thiết kế đối chứng

Tách hai experiment axes để không quy nhầm nguyên nhân:

- **RQ1/RQ2, oracle/detector comparison:** cùng fixed cases, source annotations, raw executions, normalization policy và fault pool. Thay checker/gates; không đồng thời đổi generator/model. Gold per-field oracle là upper bound, cũng báo annotation cost.
- **RQ3, generator comparison:** cùng SUT, fault assignment, operators, area/shape/source strata, annotation access và final independent validator/checker. Chỉ thay selection/conditioning. Raw pixel random là diagnostic; primary comparator là validity-filtered box-aware random.

| Nhóm | Baseline bắt buộc | Chống đối chứng yếu |
|---|---|---|
| Oracle | Body-only, frozen V3, V3+gate, V3+precision, full contracts | Cùng annotation; mới hơn body-only chưa đủ |
| Regression detector | Schema, aggregate F1 change, normalized per-field diff/MR, diff+common gate, V3/hard-pair version wrapper | Mọi checker nhận cùng output quad; không so proposed dùng transforms với baseline chỉ có ảnh gốc |
| Generator | Pixel random, box random, validity-filtered box random, frozen hard-pair, conditioned | Cùng operator/area pool, annotations, failure verifier và proposal/call caps |
| Reference | Gold per-field checking; independently validated source graph | Upper bound/validation reference, không giả là deployable method cùng annotation cost |

“V3” ở đây là source-aware graph/scorer theo code hash, không nhầm với hình học V3 hoặc VLM source-training arm. `hp_metrics` là legacy behavior metric; version wrapper phải được kiểm ở task sau, không gọi nó sẵn là regression detector đã có.

R10/R12 là đối chiếu conceptual về MT, R13 về guided testing, R14 về evolution-aware prioritization; mô tả trong [RELATED_WORK](RELATED_WORK.md). Không chép số metric khác task thành bảng thắng/thua. Nếu sau này hiện thực adaptation từ một bài, phải ghi adapted implementation/assumptions, không giả là chạy mã chính thức. GBV-PD cần gradient/loss/aligned parameters nên không ép làm baseline chung cho parser và OCR black box. Source span checking đơn giản theo tinh thần R06 nên có diagnostic comparator khi SUT cung cấp spans; không thay OCR transcript bằng pixel GT để làm nó mạnh giả hoặc yếu giả.

## 5. Budget và lặp — đề xuất để khóa sau pilot

Không chạy factorial toàn bộ models × transformations × faults. Dự kiến cap tổng **4.000 logical SUT calls**, không phải lệnh được phép chạy trong TASK 1.

| Phần | Dự kiến trần logical calls | Ý nghĩa |
|---|---:|---|
| Fixed RQ1/RQ2 execution panel | 40 case–fault blocks × 4 quad outputs × 2 SUT families = 320 | Một block có một version/fault assignment; không cross-product mọi fault với mọi ID |
| RQ3 | 5 generators × 3 selection seeds × 2 SUT families × 96 calls/block = 2.880 | 24 quads tối đa/block; fault assignment cân bằng, frozen trước selection |
| Repeat stability panel | Tối đa 96 | Dự kiến lặp thêm hai lần trên 12 input–version requests/family; chọn panel trước outputs |
| Reserve | Tối đa 704 | Validator/selection inference, retries hoặc diagnostics **đã khóa**; không dùng để thử thêm đến khi có p nhỏ |

Tổng phần định danh = 3.296, reserve = 704, tối đa 4.000. Constructed control outputs không phải neural calls. Logical calls tính cả original/follow-up, v0/v1 và inference phục vụ selection/validator; actual physical calls/cache hits báo riêng. Cache sharing không được dùng để tặng thêm quota cho một method. Common base-cache cost hạch toán cold-start và amortized, không biến reused outputs thành run độc lập mới.

Mỗi generator có cùng thêm caps về proposal attempts, wall/CPU/GPU time và person-minutes. Giá trị các caps này **chưa khóa**: pilot phải đo chi phí dựng graph/triage rồi xác định cap khả thi trước xem confirmatory outputs. Khóa cả upfront annotation budget; báo marginal cost lẫn tổng cold-start cost. Dùng chung annotation pool cho mọi baseline để cô lập selection, sau đó sensitivity theo tổng chi phí để kiểm lợi ích thực dụng.

Ba selection seeds không phải ba model retraining seeds; duplicate pixels/faults vẫn là cùng cluster. Hai backend báo riêng. Repeats đo stability, không tăng số tài liệu độc lập. Inference randomness dùng config cố định và logged seed/decoding; timeout/error/retry nằm trong budget, không lặp tới khi đúng. Nếu cap không đủ cho statistical adequacy, thu hẹp claim hoặc tăng kế hoạch trước lock, không âm thầm tăng giữa test.

## 6. Independent validation và fault triage

Reference team/implementation xác nhận preconditions trước xem alarms. Dùng cùng rubric cho tất cả methods. Kiểm mask đúng coordinate space, actual raster support, retained context/precision và source coverage; blind generator identity khi review được. Có negative controls gồm backup còn nguyên, same-string-different-key, untouched field, incomplete MRZ, corrupted transform và intentionally unsupported key.

Triage tất cả alarms trong bounded panel nếu khả thi; nếu vượt annotation budget, lấy stratified probability sample **cả positives và negatives** với sampling weights đã khóa. Nếu không audit hết, không báo một con số unique confirmed faults toàn population như đã kiểm toàn bộ; báo estimated metrics/uncertainty và known-confirmed lower bound. Rejected/unknown/timeout cases vẫn ở ledger, không refill miễn phí.

Mỗi claimed root cause có evidence bundle: case hashes, valid-precondition evidence, four outputs, stage trace, independent label, version diff/fault patch và patch/revert hoặc activation demonstration. Natural opaque model error không có bundle root cause được gọi behavior anomaly. Fault dedup theo causal patch/family trước biết method rankings; không đếm biến thể regex tương đương thành nhiều lỗi.

## 7. Phân tích, threshold và missingness

Primary endpoints/contrasts và guards theo [RESEARCH_QUESTIONS](RESEARCH_QUESTIONS.md). Ghi counts numerator/denominator, effect size, CI, adjusted p và cost; không chỉ báo best configuration. Thresholds, allowed precision/canonicalization, source completeness và detector alarm thresholds chọn trên dev rồi đóng băng. Không sửa V3 scorer/threshold cũ.

Trước confirmatory lock cần statistical adequacy/MDE analysis bằng simulation hoặc calculation, không chạy model hàng loạt. ID-level clustering cho document claims; root-cause/family cho fault claims; multiway sensitivity cho cases chia sẻ cả ID và fault. Nếu quá ít independent families, chỉ báo finite-pool descriptive results và uncertainty, không suy ra quần thể bugs bằng field-level p-values. Paired randomization phải nêu exchangeability unit; không hoán vị các fields như độc lập.

Không có alarm hoặc FP bằng 0 không chứng minh risk bằng 0. Bootstrap toàn số 0 có thể cho CI suy biến; dùng conservative event bounds ở đơn vị độc lập hợp lệ khi áp dụng, hoặc ghi chưa ước lượng được upper risk với số cluster hiện có. Nếu upper CI vượt 5%, không claim false-alarm population bound 5%, dù observed FAR dưới cap. NI margins 5pp và cap 5% là draft decision rules cần justification trước lock, không phải standard eKYC.

Mẫu có reference Z=? không chấm đúng/sai tự động; báo riêng cùng best/worst-case sensitivity bounds nếu phù hợp. Unknown/inapplicable của method không phải TN hoặc pass mặc định. Known-positive mà tester abstain là miss trong end-to-end sensitivity. Invalid-test alarms và unknown-reference alarms có tỷ lệ riêng, đi vào tổng burden/precision audit. Empty output giảm unsupported fields nhưng tăng omission; không gộp hai mục tiêu thành một safety score thiếu mẫu số.

## 8. Validity threats và giới hạn claim

| Threat | Kiểm soát và giới hạn còn lại |
|---|---|
| Construct: source availability khác legibility/correctness | Typed source/reference, independent rubric; tự nhiên chưa có rater thì không claim human readability |
| Construct: alarm khác software fault | Bốn mức evidence, patch/revert, dedup; mutants và opaque model errors báo riêng |
| Internal: generator/oracle cùng lỗi | Independent implementation/raster fixtures, fault taxonomy giữ riêng, audit cả negatives |
| Internal: annotation advantage | Common-information comparisons và cold-start sensitivity; không miễn phí graph |
| Internal: nondeterminism/caching | Frozen requests/hashes, repeat panel, logical/physical/cache counters |
| Conclusion: small effective N, multiple tests | ID/fault clustering, Holm 3 primary contrasts, pre-lock adequacy; không dùng số field thay sample size |
| External: một app, hai backend, in-family specimens | Claim case study, source/layout/stage stratification; không generalize camera/identity/PAD |
| Exposure/license/privacy | Prospective manifest, source ancestry/exposure audit; chỉ specimen/public permitted; không công bố ảnh/weights/raw PII trái phép |

## 9. Dependency gates và điều kiện dừng

| Gate | Dependency / việc cần làm ở task sau | Nghiệm thu trước bước kế |
|---|---|---|
| G1 Design review | TASK 0 + sáu tài liệu TASK 1 | RQs, verdict/baselines và phản biện rõ; kết luận novelty có điều kiện |
| G2 Minimal prototype | G1; task implementation riêng | Read-only adapters và tiny fixtures OR/AND/precision/unknown/optional fields; old files nguyên hash; chưa main inference |
| G3 Validity/fault feasibility pilot | G2 | Independent reference checks, fault provenance inventory, actual annotation/call cost và statistical adequacy; kết quả pilot exploratory |
| G4 Confirmatory lock | G3 | Case/fault roles, hashes, thresholds, budgets, metrics/CI/multiplicity, reviewer identities và stopping rules khóa **trước** outputs; ghi timestamp/hash local hoặc registry ẩn danh khi được phép |
| G5 Main execution | G4 và task execution riêng | Append-only attempt logs, raw outputs, failures/retries, tất cả baseline; không tuning, không retrain |
| G6 Report/artifact | G5 | Chấm lại từ logs, privacy/license review, anonymized replication package và manuscript claim theo bằng chứng |

Chưa đạt G3/G4 thì chưa main test. Nếu novelty chỉ là đổi tên V3/hard-pair hoặc strong baseline bằng nhau, không tiếp tục thêm models đến khi tìm được kết quả thuận lợi. Thu hẹp thành oracle-validity empirical study; báo cả null/negative results và cân nhắc track phù hợp theo CFP khi viết bài.

## 10. Artifact và audit dự kiến

New namespace giữ contracts/versioned schema, case/fault manifests, immutable raw outputs, scoring config, proposal/call/cost ledgers, reference/adjudication provenance và analysis script. Không lưu production sessions, CCCD thật hoặc biometric. Git public chỉ nhận artifacts đã kiểm quyền/ẩn danh khi được phép; TASK 1 không commit/push.

TASK 1 chỉ kiểm tra UTF-8, liên kết local, cấu trúc sáu tài liệu, số RQs/source records, budget arithmetic và bảo toàn files/HEAD/refs. Những kiểm tra này không thay empirical validation, model test hoặc claim kết quả mới. Execution record của lượt này lưu tại `execution/task1_review/`.
