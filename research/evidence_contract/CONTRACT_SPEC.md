# TASK 3 — Source-aware evidence contracts

Ngày triển khai: 06/11/2026. Namespace: `research/evidence_contract/`. Đây là implementation nghiên cứu, không thay production eKYC, checkpoint hoặc kết quả cũ. [METHOD_SPEC](METHOD_SPEC.md) và [RESEARCH_QUESTIONS](RESEARCH_QUESTIONS.md) được giữ nguyên byte.

Trong workspace chỉ tìm thấy artifacts TASK 0–1; chưa tìm thấy schema/adapter hoặc báo cáo TASK 2. Không coi TASK 2 đã hoàn tất. Implementation này cung cấp interface độc lập có adapter read-only, để có thể đối chiếu/integrate foundation TASK 2 sau mà không đổi RQs.

## Mapping với method đã chốt

| ID TASK 3 | Method trước đó | Phạm vi implementation |
|---|---|---|
| C1 Complete Evidence Removal | C-REMOVE | Physical removal + exhaustive declared source scope; không suy absence từ che body đơn |
| C2 Alternative Source Preservation | C-BACKUP | Body mất nhưng backup còn hợp lệ; correctness, omission và precision chấm riêng với unsupported assertion |
| C3 Neighbor Field Non-Interference | C-NI | Quan hệ A/B được khai báo; giữ value lẫn semantic context của B; witness qua version khi có đủ thông tin |
| C4 Evidence-Preserving Geometry | Evidence-preserving preconditions của method | Identity, integer translation có padding và quarter-turn có policy; không mặc định arbitrary warp invariant |

Typed precision được áp xuyên suốt C2–C4; chưa triển khai riêng C-PARSE, fault-injection framework, model benchmark hoặc các primary contrasts của RQ1–3. C1–C4 ở đây là **contract IDs**, không phải đánh số các đóng góp nghiên cứu C1/C2/C3 trong GAP_ANALYSIS.

## Interface và module

| File | Trách nhiệm |
|---|---|
| [source_graph.py](source_graph.py) | Immutable typed graph, OR/AND, source conditions, scope và precision; adapter V3, HP, OCR labels; JSON round-trip |
| [validity.py](validity.py) | Mutation/review records và validation trên raster thực; không đọc prediction của SUT |
| [generator.py](generator.py) | Deterministic plans/pairs, seed/hashes, original protection, write vào new run directory |
| [contracts.py](contracts.py) | C1–C4, structured-output checks, reading diagnostics, bound four-execution regression witness |
| [fixtures.py](fixtures.py) | Fictional known-answer fixtures và renderer development hiện có, chỉ gọi hàm in-memory |
| [pilot.py](pilot.py) | Pilot có giới hạn, attempt ledger, synthetic control outputs và kiểm file đã lưu |
| [tests/test_contracts.py](tests/test_contracts.py) | Positive/negative/invalid/inconclusive tests, role/privacy/binding/preservation guards |

Import package không chạy study. Không API network, database mới, setup/download hoặc training entry point. `hp_data` có import runtime torch ở dependency cũ; không khởi tạo VLM, tải weights, chạy forward hoặc optimizer.

## Evidence graph

`EvidenceGraph` giữ document ID, physical ID, source ID, role, input dimensions, pixel SHA256 và optional original-file SHA256. `Field` có semantic key/reference/typed precision/optionality và nguồn realization. Mỗi `Realization` có provenance, điều kiện hợp lệ và components. Component phân biệt **value** với **semantic_context**, required với optional, availability với readability, construction support với human verification.

OR giữa alternative realizations; AND giữa required components trong một realization. Nguồn được hỗ trợ chỉ khi conditions đủ và mọi required component có evidence thích hợp. Nguồn nhiều dòng thiếu một phần không được coi là đọc đầy đủ. Giá trị giống nhau nhưng key khác nghĩa không tự tạo liên kết. Conflict giữa nguồn supported và reference làm state UNKNOWN; không chọn nguồn thuận với prediction.

MRZ cần explicit semantic link, strict format và composite checksum. Các trường numeric/date/personal cần field checksum khi áp dụng; checksum policy thiếu không mặc định hợp lệ. Adapter giữ nguyên checksum sai/thiếu. Điều này là policy bảo thủ của research oracle, không xác thực giấy tờ thật. Ngày `YYMMDD` không cho phép suy century; `date_full` và `date_yymmdd` có assessment riêng. Calendar invalid và format chưa hỗ trợ không được tự sửa.

Các native fields không có `semantic_key` được ghi trong `unmapped_fields`, không suy key theo index/vị trí. Adapter OCR-label hạ source coverage của các fields còn lại khi có nguồn unmapped. V3/HP mặc định limited scope và geometry-only, không tự nhận human-readable. Source không có role giữ `unassigned`; không được đổi role test thành development. Data policy chưa biết giữ unknown; không tự gán public/fictional cho ảnh bất kỳ.

`complete` coverage chỉ có ý nghĩa trong source universe có provenance đủ, ví dụ toàn bộ source inventory của renderer fixture. Geometry không phát hiện được mọi nguồn QR/barcode, bản ngữ hoặc duplicate chưa annotate. Với những trường hợp này phải giữ limited/unknown.

## Trạng thái kết quả

| Contract status | Ý nghĩa |
|---|---|
| PASS | Assertion cụ thể này phù hợp evidence và policy; không có nghĩa toàn document hoặc eKYC đúng |
| VIOLATION | Assertion thất bại sau khi preconditions hợp lệ; loại lỗi nằm trong diagnostics |
| INVALID_TEST | Có bằng chứng mask/geometry/binding làm sai precondition, che lấn hoặc mất vùng cần giữ |
| INCONCLUSIVE | Chưa đủ coverage/readability/precision/policy hoặc contract không áp dụng; không tính là pass |

Validator có `VALID`, `INVALID_TEST`, `INCONCLUSIVE`. `VALID` chỉ nói input relation đủ điều kiện theo phạm vi chứng nhận; không phải kết quả của model. Contract có thể INCONCLUSIVE trên pair VALID, ví dụ rotation không được SUT policy cam kết invariant. Trường hợp không có backup hoặc contract không áp dụng được ánh xạ INCONCLUSIVE với reason riêng, vì interface yêu cầu bốn trạng thái trên.

## C1 — Complete Evidence Removal

**Preconditions:** graph và ảnh đúng hash, mask opaque thực tế, xóa hết vùng value/glyph của tất cả declared candidate sources của A, không phá nguồn/context khác, và universe đủ coverage. Không bỏ qua một MRZ khả nghi rồi coi A vắng chỉ vì checksum của nó sai; generator vẫn mask mọi nguồn đã khai báo cho all-source cases.

**Expected relation:** A absent/null/empty. Nonempty A là VIOLATION `assertion_after_complete_removal`, kể cả đoán trúng full reference. Đây là unsupported-assertion theo policy pixel-faithful; không kết luận model đã dùng cơ chế hallucination nào.

**Exceptions:** limited universe, glyph extent chưa xác minh, unknown encoded source → INCONCLUSIVE. Mask sót ký tự, bbox loại mất glyph đã annotate, che lấn B → INVALID_TEST. Malformed JSON không được chuyển thành `{}` để nhận PASS; báo format error và INCONCLUSIVE.

## C2 — Alternative Source Preservation

**Preconditions:** body source của A thực sự bị mask; một backup cùng key còn nguyên, có source conditions hợp lệ và evidence đủ precision. Backup có thể là duplicated body, MRZ hoặc source type khác được khai báo.

**Expected relation:** đọc từ backup là hợp lệ, không báo thiếu visual evidence chỉ vì body mất. `unsupported_assertion=False` trong C2. `reading_status` tách `correct`, `wrong`, `omitted`, `precision_overreach`, `precision_loss` và `unverified_reference`.

**Policy:** mặc định extraction yêu cầu các fields đã được xác minh supported: đọc sai/bỏ sót là VIOLATION về reading, không gán là absence hallucination. Nếu policy cho phép bỏ field supported, omission có thể PASS nhưng vẫn có diagnostic omission. Không ép các trường không tồn tại trong schema/tài liệu phải xuất hiện.

**Exceptions:** backup checksum/semantic link/legibility chưa xác minh → INCONCLUSIVE. Không có alternative source → INCONCLUSIVE/inapplicable; không tự sinh MRZ. Source conflicts cũng không được giải quyết bằng chọn giá trị khớp prediction.

## C3 — Field non-interference

**Preconditions:** target A được mask đúng intended declared sources; value và semantic context của B giữ; B supported ở precision áp dụng; extraction requirement không đổi. Không yêu cầu A phải human-readable để kiểm B nếu A có geometry/ink extent đủ. Không dùng trạng thái nguồn A mất để suy nguồn B mất.

**Expected relation:** trước biến đổi đọc B đúng thì sau biến đổi vẫn đúng. Nếu trước đã sai/chưa biết → INCONCLUSIVE về regression, đồng thời giữ reading diagnostics. Che A làm mất label/context cần để hiểu B → INVALID_TEST dù toàn bộ pixel value B không đổi.

Một cặp x/Tx chỉ xác lập conditional metamorphic behavior failure. `behavior_regression_verified=True` còn đòi witness `v0(x), v0(Tx), v1(x)` đúng, `v1(Tx)` sai; distinct version hashes; binding cả hai ảnh; stability và unchanged-requirement provenance. `software_fault_confirmed` vẫn false: patch/revert hoặc seeded-fault causal validation thuộc bước sau. Không biến model anomaly thành lỗi phần mềm đã định danh.

Những cặp A/B được chỉ định theo semantic keys có sẵn, không suy nghĩa từ geometry. Core C3 không gán mặc định mọi cặp đều gần; khoảng cách near/far cần báo riêng khi dùng claim neighbor-specific. Pilot hiện là kiểm logic A/B, không kiểm chứng lợi thế hard-pair selection theo khoảng cách.

## C4 — Evidence-preserving geometry

**Preconditions:** matrix/size/binding hợp lệ, source và context nằm trong frame, text preservation được chứng nhận và operation có trong SUT policy. Trước biến đổi đọc sai thì không suy thành regression mới.

Integer `translate_pad` dùng OpenCV nearest-neighbor; validator đối chiếu toàn ảnh bằng NumPy placement độc lập. `rotate90` được kiểm bằng correspondence pixel riêng, nhưng mặc định policy chỉ cho identity và translate-pad. Quarter-turn có pixel preservation mà chưa có orientation guarantee vẫn INCONCLUSIVE. Không coi mọi khác biệt OCR sau xoay/rescale/warp là lỗi.

Warp nội suy không có chứng nhận tự động sẽ giữ INCONCLUSIVE; chỉ nguồn có paired human attestation đủ scope mới có thể được nâng evidence state. SUT policy còn phải cho phép operation tương ứng. Crop làm mất nguồn, matrix sai hoặc pixel-correspondence sai của operation được cam kết → INVALID_TEST.

## Mutation validity và human review

Generator dùng OpenCV; validator rasterize annotation bằng Pillow và kiểm pixel bằng NumPy. Kiểm union mask opaque, không đổi pixel ngoài mask, target regions/glyph support bị xóa hết, các nguồn và context còn lại không bị chạm. Ký tự đã annotate nằm ngoài bbox là lỗi annotation/precondition; không cho mask nhỏ nhận PASS.

Annotation geometry có thể thiếu glyph hoặc thiếu nguồn mà pixel checks không phát hiện hết. Không suy human readability từ Clean/Blur/bbox/foreground. C1 không có glyph extent đủ proof yêu cầu independent removal review; các uncertainty được giữ trong `review_required`/reason codes.

`ReviewEvidence` gắn trước/sau pixel hashes, source-level observed text, provenance, canonical person IDs và upstream `independent_verified` attestation. Hai code của cùng person không được tính thành hai người. Library không xác thực con người hoặc tự adjudicate reviewer registry; adapter dữ liệu đáng tin phải xác minh attestation trước khi truyền vào. Vì chưa có TASK 2 foundation/đánh giá độc lập, pilot không đưa actual human attestation nào. Review trong unit tests là dữ liệu mô phỏng và ghi rõ là mô phỏng.

Human review không override pixel corruption, source loss, checksum policy hoặc source-coverage thiếu bằng cách đơn giản đặt `valid=True`. Trường hợp cần xem lại giữ INCONCLUSIVE; không xóa row hoặc refill miễn phí.

## Generator và provenance

Families: original/full control; single-source mask; all-sources mask; paired A/B masks hai chiều; padded translation; quarter-turn diagnostic. Dùng `hp_data.regions_for` cho declared-source masks, `nodes_for/rect_quad` cho adapters; `v3_sources` cho strict TD3/span projection; `labels_synth.ink_patch/render/specification` cho in-memory fixture/development. Không gọi `build`, `write_capture`, `save`, `progress` hoặc preserve helpers ghi dữ liệu cũ.

Mỗi pair lưu original/follow-up PNG và case JSON: encoded-file SHA256, decoded-pixel SHA256, graph hash, document/physical/source ID, role, seed, contract ID, targeted source IDs, mask polygons, homography, size/fill/operator và expected/observed source states. **Expected state là ý định generator, không phải oracle proof.** Mask padding/geometry do seed cố định; không đọc model outputs để chọn ca.

Original được copy và giữ read-only trong `Pair`; output directory phải là child mới của evidence_contract, không overwrite run cũ. Export chỉ nhận fictional/public-specimen policies. Train/test/confirmatory/calibration bị gate chặn trước transform; role không rõ cũng bị chặn. Không tạo database chứa hồ sơ/biometric.

## Chạy lại an toàn

Từ repository `D:/laptrinhcuatao/Ekyc/versions/research-document-recovery`, dùng Python venv đã có. Dry-run không tạo data:

```powershell
& 'D:\laptrinhcuatao\Ekyc\.venv\Scripts\python.exe' -m research.evidence_contract.pilot
```

Pilot cần output **chưa tồn tại**; không dùng lại tên run đã hoàn tất:

```powershell
& 'D:\laptrinhcuatao\Ekyc\.venv\Scripts\python.exe' -m research.evidence_contract.pilot --run --output research/evidence_contract/execution/task3_manual_new
```

Unit tests có output tạm mới theo timestamp; không đặt basetemp trùng run cũ vì pytest có thể dọn thư mục basetemp:

```powershell
$testRun = 'research/evidence_contract/execution/manual-tests-' + (Get-Date -Format 'yyyyMMdd-HHmmss-fff')
& 'D:\laptrinhcuatao\Ekyc\.venv\Scripts\python.exe' -m pytest research/evidence_contract/tests -q -p no:cacheprovider --basetemp $testRun
```

Kết quả thực tế, denominator/coverage và giới hạn được ghi trong [GENERATOR_AUDIT](GENERATOR_AUDIT.md). Không dùng fixture control outputs làm số đo OCR/VLM, H1–H3 superiority hoặc paper acceptance.
