# Source-Aware Evidence-Contract Testing — method draft

TASK 1, 06/11/2026. **Đặc tả để cài và thử ở task sau; chưa có framework mới.** Đóng góp ứng viên C1 được giới hạn trong [GAP_ANALYSIS](GAP_ANALYSIS.md). Khái niệm MR, source grounding, tri-state uncertainty và differential regression đều có prior art; không claim phát minh riêng.

## 1. Ranh giới hệ thống và luồng dữ liệu

SUT `P_v` là extraction pipeline có version: image preprocessing/Module 2 → OCR/VLM/Module 3 → parser/normalizer → fields. Có thể dùng Module 1 admission như metadata/stage quan sát nếu contract nghiệp vụ xác định rõ. Không sửa production API, UI mentor, checkpoints hoặc cơ chế Module 4–5. Không suy từ OCR sang tính thật của giấy tờ hoặc con người.

Hai đường riêng:

1. Predictor chỉ nhận pixels và instruction/schema **nghiệp vụ** đã khóa. Không nhận đáp án, source graph, target key bị che hoặc mask coordinates từ test oracle. Request stateless, không lấy transcript của ảnh gốc từ session/cache làm câu trả lời ảnh che.
2. Tester nhận provenance/annotation, biến đổi, output và trace; áp contract rồi phát cảnh báo có witness. GT dùng xác minh nằm riêng, không dùng để chọn ca trên confirmatory set.

Nếu đang kiểm quality-gated end-to-end pipeline, một yêu cầu chụp lại hợp lệ theo policy không mặc định là OCR bug. Chỉ áp completeness/non-interference khi extraction contract áp dụng; nếu test làm hỏng điều kiện admission hoặc không rõ policy, ghi invalid/unknown/inapplicable.

## 2. Dữ liệu khái niệm tối thiểu

| Record | Nội dung bắt buộc |
|---|---|
| Case | Case/parent ID; image hash; source/license; role; schema/version; ancestry và pixel-duplicate component |
| Field | Semantic key theo schema của tài liệu, optionality; full reference tách visible reference; typed precision; language; GT provenance |
| Realization | Source ID/type (body, duplicate, TD3...), key semantics; components; raw span/geometry/coordinate space; semantic mapping; confidence/verification provenance |
| Coverage | Declared source universe; nguồn đã kiểm/không hỗ trợ; complete-by-construction hoặc limited/unknown; conflicts và parser/checksum status |
| Transformation | Parent/follow-up hashes; operator/seed/version; actual raster mask; target/retained fields; intended preconditions; observed collateral damage |
| Execution | SUT/model/preprocessor/parser/config hash; request/response raw; decoded/normalized fields; timing/memory/error/cache provenance; per-stage trace nếu có |
| Verdict/witness | Contract ID/version; eligibility; reason; expected relation; observed discrepancy; evidence support/precision; uncertainty; verified failure/fault status tách nhau |

Full reference cho biết nội dung ban đầu, **không** chứng minh nội dung còn đọc được sau biến đổi. Clean/Blur, bbox in-frame hoặc checksum chỉ là tín hiệu riêng. Model confidence không thay nhãn đọc được.

## 3. Source support và precision

Với field k, các realization là các cách đọc cùng ý nghĩa k. **OR** giữa nguồn thay thế; **AND** giữa components của một realization. Cấu trúc này tái sử dụng V3, không phải phần mới. Component của địa chỉ nhiều dòng có thể cần nhiều đoạn; label/context chỉ bắt buộc khi cần xác định đúng key, không mặc định label luôn là một ký tự của value.

Biểu diễn hỗ trợ của từng component bằng `supported/removed/unknown`. Realization supported khi mọi component cần thiết đều supported; removed khi đã có component thiết yếu bị xóa chắc chắn; còn lại unknown. Field có ít nhất một realization supported thì có hỗ trợ ở precision tương ứng. Chỉ kết luận all-sources-removed khi mọi realization trong **universe đã chứng minh đủ** đều removed. Thiếu coverage ⇒ unknown, kể cả mọi box đã biết đều bị che.

Giá trị là typed claim. Ví dụ MRZ `YYMMDD` hỗ trợ ngày/tháng/năm modulo 100; không tự chứng minh thế kỷ trong `YYYY-MM-DD`. Mapping/transliteration/normalization phải có rule đã khóa, không thêm tri thức từ đáp án. Nếu chỉ còn nguồn precision thấp, không áp contract giữ nguyên output precision cao. Khi các nguồn xung đột hoặc MRZ sai độ dài/checksum chưa có chính sách giải thích, chuyển unknown cho assertion liên quan; không chọn nguồn thuận lợi dựa vào prediction.

TD3 parser cũ có thể trả spans cùng `checksum_valid=False`; adapter phải giữ cờ, không biến parse success thành chữ đã đọc đúng hoặc giấy tờ hợp lệ. Chỉ support các source types đã khai báo. QR/barcode/TD1/TD2 chưa được kiểm thì không gọi nguồn của chúng là vắng. Chuỗi trùng ở hai key khác nghĩa không tự thành backup source.

Đây là bằng chứng **khả dụng theo policy quan sát đã xác minh**, không phải lời giải thích model thật sự chú ý/đọc từ vùng nào. Model có thể đoán trúng; kết quả đúng nhưng thiếu visual support vẫn là policy violation nếu extraction policy cấm completion, không chứng minh cơ chế nhận thức hallucination.

## 4. Admissibility trước verdict

Gate có bốn kết quả:

- `valid`: source/key mapping, precision, readable reference, transformation và retained context đạt precondition cụ thể.
- `invalid`: có bằng chứng biến đổi không đạt ý định, sai tọa độ, che lấn B hoặc đổi ngữ nghĩa cần giữ.
- `unknown`: chưa đủ nhãn legibility/coverage/semantics để kết luận.
- `inapplicable`: contract không áp dụng, ví dụ không có backup source cần thử.

Gate không tham khảo output của SUT đang được đánh giá để “xác nhận” test. Candidate generator và reference validator không dùng chung một lời khẳng định làm proof. Với specimens, lấy text/glyph support từ renderer và kiểm raster riêng; với ảnh tự nhiên cần review độc lập ở mức nguồn/key. Pixel diff chỉ kiểm vùng thay đổi, không tự chứng minh readability hoặc semantic non-interference.

Tester trả `pass/fail` khi assertion có đủ căn cứ; nếu thiếu thì `unknown/inapplicable` với reason. **Pass chỉ là contract này chưa bị vi phạm**, không phải toàn bộ document đúng. Invalid/unknown không biến thành thành công refusal và không bị xóa khỏi attempt ledger.

## 5. Contract families cần prototype

| Contract | Precondition | Expected relation | Không được kết luận khi |
|---|---|---|---|
| C-BACKUP | Che một realization của A; còn backup xác minh đọc được, cùng semantic key, đủ precision; context/admission giữ | Thông tin A còn được hỗ trợ. Không phát unsupported-output alarm chỉ vì body mất; correctness/completeness áp theo extraction policy | Backup precision thấp hơn claim, source conflict, chưa biết legibility |
| C-REMOVE | Xóa mọi nguồn của A trong universe đủ coverage; B/nhãn/context cần thiết còn nguyên | Theo policy pixel-faithful, A phải absent/null/empty; B có yêu cầu đọc riêng | Chỉ che các nguồn đã biết trong ảnh coverage limited; vẫn có encoded source chưa kiểm |
| C-NI | A thay đổi/che; nguồn và semantic context cần thiết của B giữ, B được xác minh readable, v0/source case đọc đúng | B phải giữ thông tin đúng ở common supported precision | Pixel B giữ nhưng nhãn liên kết/ý nghĩa B mất; task cho phép global reject hợp lệ |
| C-PRECISION | Universe cho phép xác định giới hạn precision; transformation loại một nguồn precision cao | Output không khẳng định phần precision không còn bằng chứng; projection về common precision nhất quán | Schema chỉ cho full dates mà chưa quy định abstention; parser tự thêm century |
| C-PARSE | Có fixed raw reader outputs với semantic reference và format variants được phép | Parser/normalizer giữ giá trị được hỗ trợ; raw format errors và semantic loss báo riêng | Thay đổi có chủ đích của API/schema chưa được đặc tả |

C-REMOVE và C-NI đánh giá hai field độc lập; `{}` không thể thành “pass toàn ca” chỉ vì không xuất A. Không ép một trường thực sự không tồn tại phải có output. Core prototype nên bắt đầu C-BACKUP, C-NI, C-PRECISION; C-REMOVE chỉ trên coverage-exact cases. Không mở rộng diffusion/editing nặng trước khi core oracle hợp lệ.

## 6. Regression witness và phân loại lỗi

Cho x, follow-up Tx, baseline v0 và candidate v1, lưu bốn execution:

`Q = {P_v0(x), P_v0(Tx), P_v1(x), P_v1(Tx)}`.

Witness mạnh cho B: ba output đầu đúng ở precision đã khóa, output cuối sai/mất B; Tx valid cho C-NI. Đây là tiêu chuẩn cố ý chặt để tách interaction của transformation và version. Cũng ghi các pattern khác: lỗi có sẵn ở v0, ordinary version regression trên x, improvement, cùng sai, stochastic disagreement, chưa đủ GT. Không loại chúng khỏi tổng số để làm tỷ lệ đẹp.

Các mức bằng chứng phải tách:

1. **Contract alarm:** tester phát fail.
2. **Verified behavior failure:** reference độc lập xác nhận violation và valid input relation.
3. **Verified regression:** behavior failure mới qua version; đã loại intended change và nondeterminism theo protocol.
4. **Confirmed software fault:** historical bug có commit/patch/revert reproduction hoặc seeded fault có patch identity/activation và reference specification. Một anomaly của neural reader tự nó không có root-cause identity.

Ghi output tại geometry, OCR/raw text, parser và normalized fields để tìm earliest observable divergence. Chỉ attribution khi controlled replay hoặc patch/revert hỗ trợ; nếu không, ghi localization candidate. Cache replay raw text kiểm parser không được nhận là inference pixel mới.

## 7. Evidence-conditioned generation — procedure đề xuất

Đầu vào: annotation graph đã khóa, case/fault pool không chứa output confirmatory, operator set và budget. Xây feasible source-removal/retention pairs theo key semantics, precision và vùng ảnh. Chọn theo vòng phân tầng deterministic giữa backup/neighbor/precision families rồi seed-shuffle trong stratum; ưu tiên coverage mới của contract/source/stage, **không** chọn theo lỗi trên test đang chạy. Đây là heuristic thiết kế, chưa có bằng chứng hiệu quả.

Sinh biến đổi → independent admissibility check → nếu valid thì chạy quad → áp cùng contracts → blind failure/fault verification → ghi attempt và cost. Proposal bị loại vẫn ghi lý do/chi phí; không refill vô hạn miễn phí. Các random baselines nhận cùng candidate domains, annotations, operators, area strata và validator; khác biệt primary là source-structure conditioning/prioritization. Nếu khác cả operator hoặc oracle thì phải là ablation riêng, không quy tác động cho selection.

## 8. Tái sử dụng và tránh làm sai kết quả cũ

Giữ V3/hard-pair/scorers như legacy có hash. Viết adapter mới cho source coverage, semantic precision, human review snapshot và stage/version trace. `hp_data.build/write_capture`, training entry points và helper tạo manifest không được gọi vào namespace cũ. `fc_statistics.analyze` cố định design cũ nên không thể dùng nguyên hàm để suy luận theo software faults; chỉ tái sử dụng phép Holm và nguyên tắc clustering sau kiểm tra.

Mọi new artifact thuộc `research/evidence_contract/`, không ghi `research/results/` cũ. Không đưa CCCD thật hoặc biometric vào corpus/log. TASK 1 chỉ có tài liệu và log bảo toàn/kiểm tài liệu; không implement các records/operators nêu trên.
