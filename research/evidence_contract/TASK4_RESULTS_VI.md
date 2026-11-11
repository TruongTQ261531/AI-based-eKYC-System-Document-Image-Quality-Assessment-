# Kết quả TASK 4

06/11/2026. Đã hoàn thành prototype và smoke theo yêu cầu. **Chưa chạy benchmark chính, chưa kiểm định H1–H3, chưa chứng minh hiệu quả oracle trên lỗi thực tế.**

## Đã triển khai

| File mới | Chức năng |
|---|---|
| `runner.py` | Chỉ nhận ảnh; kiểm hash/policy; cache model/input/config/code/runtime; khóa OS; ghi nguyên tử không ghi đè; event log nối tiếp; hồi phục gián đoạn; replay không nạp model |
| `reader_adapters.py` | Tái sử dụng RapidOCR v4, Latin recognizer v5 và Vintern partial_42 step0320; cùng pixels và cấu hình cũ; không đưa GT/key mục tiêu/polygon vào predictor |
| `normalized_output.py`, `normalized_output.schema.json` | Dự đoán, raw/JSON validity, hash, latency/runtime, confidence native; không tạo confidence giả; missing fields chỉ nối tham chiếu sau inference |
| `oracle.py` | Năm verdict; phân biệt sai giá trị, thiếu trường, unsupported theo nguồn khai báo, absence được xác minh, false alarm do GT/source và không thể kết luận; certificate/nhãn độc lập ràng buộc đúng ảnh/output/model/normalizer/policy |
| `evaluator.py` | Mẫu số/unit rõ; dedup ảnh/field/call; metric theo contract/source/model/readability/document; tách failure và root-cause defect |
| `smoke_task4.py`, `verify_task4.py` | Fixture, worker tuần tự, chấm lại và kiểm tra bảo toàn |
| `tests/test_runner_oracle.py` | 50 unit tests mới với output/certificate/lỗi cố ý chèn, tách khỏi kết quả model thật |
| `.gitignore` | Ignore vùng `local/` chứa raw text/images/cache/runtime mới |

Đặc tả: [ORACLE_VALIDITY](ORACLE_VALIDITY.md), [EVALUATION_METRICS](EVALUATION_METRICS.md). Không thay Research Questions, API eKYC, UI mentor hoặc kết quả V1–V4/hard-pair/fair-controls.

## Kiểm thử đã chạy

Lượt cuối: **146 tests +6 subtests PASS**, skipped0. JUnit ghi152 testcase vì cộng subtests. Gồm50 test mới và96 test unit/adapter cũ liên quan; không phải chạy lại thí nghiệm model đã công bố. Log command, exit code và code hashes tại [pytest_run_06.execution.json](execution/task4_runner/pytest_run_06.execution.json), [stdout](execution/task4_runner/pytest_run_06.log), [JUnit](execution/task4_runner/pytest_run_06.xml).

Bao phủ: JSON lỗi/trùng khóa/nonfinite; không tạo confidence giả; MRZ còn đúng và checksum lỗi/unknown source; sai/bỏ/thêm trường; C3/C4 preconditions; version quad; nhãn/certificate sai binding; root-cause proof; false-alarm denominators; cache hỏng; hai runner cùng key; lỗi/gián đoạn và crash sau raw commit. Lỗi chèn nhân tạo chỉ kiểm oracle; không cộng vào lỗi model thực tế.

Các lượt trước được giữ nguyên, không che lỗi:

| Log | Kết quả và xử lý |
|---|---|
| `unit_run_01.log` | 38 tests,6 lỗi tạo hard link cache trong thư mục tạm Windows |
| `unit_run_02.log` | 38 tests,6 lỗi; rename cũng bị chặn trong thư mục tạm Windows chuyển hướng |
| `unit_run_03.log` | 38/38 PASS sau khi vùng tạm test nằm trong workspace được phép ghi |
| `pytest_run_04.log` | 144 tests +5 subtests PASS |
| `pytest_run_05.log` | 145 tests +5 subtests PASS; có hash thực thi |
| `pytest_run_06.log` | 146 tests +6 subtests PASS, code giao cuối; có hash thực thi |
| `smoke_01/*process.json` | Ba worker dừng preflight vì đường dẫn RapidOCR có sẵn chưa được thêm trước khi đọc package metadata; **0 image-reader inference**. Đã sửa thứ tự nạp đường dẫn, không cài/đổi package |
| `final_checks.log` | Lần gọi audit bằng đường dẫn file thiếu package path; dừng import trước kiểm tra/inference. Gọi lại đúng dạng Python module, không đổi reader/model |

Full JSON Schema Draft2020-12 validation chưa chạy vì không có `jsonschema`; đã kiểm schema JSON/required fields và runtime validators. Không chạy toàn bộ production/UI suite vì không sửa production/UI. Không chạy locked test, retrain hoặc chọn cấu hình theo smoke.

## Smoke với model thực

Run `smoke_02`:1 giấy tờ giả lập,4 ảnh,4 cặp C1–C4, seed42. C1 và C3 dùng chung all-source mask. Ba reader ×4 ảnh = **12 image-reader invocations thực tế**, completed12, failed0, ambiguous0. Raw outputs lấy từ predictor thực, không thay bằng đáp án fixture.

| Reader | PASS | Candidate | Inconclusive | Verified failure |
|---|---:|---:|---:|---:|
| RapidOCR v4 | 1 | 1 | 2 | 0 |
| RapidOCR Latin v5 | 2 | 1 | 1 | 0 |
| Vintern partial_42 | 2 | 1 | 1 | 0 |
| Tổng | **5** | **3** | **4** | **0** |

Ba candidate đều là lỗi đọc trường còn nguồn hỗ trợ ở C2; chưa gọi là hallucination/lỗi đã xác nhận. Inconclusive C3/C4 có giá trị gốc đã đọc sai, chưa đủ điều kiện kết luận regression do biến đổi. Valid mutation pairs4/4. Chưa có independent failure/readability gold: alarm precision/recall/FAR **NA**, không phải0%. Không xác nhận root-cause software defect.

Có21 supported reference fields,3 removed fields,24 field-reader views,12 image-reader views,4 unique pixel images và1 physical ID. Literal exact-match: v4=0/7, Latin v5=4/7, partial_42=5/7. Đây là fixture nhỏ, không dùng xếp hạng model. CER/F1/runtime có mẫu số tại [evaluation_final.json](execution/task4_runner/smoke_02/evaluation_final.json).

Chi phí:31.351s invocation wrapper;63.007s loading;94.359s cold-inclusive;113.146s tổng fresh workers gồm startup/preflight. Chi phí toàn phương pháp gồm generation/annotation/review chưa đo đầy đủ; chưa claim hiệu suất nghiên cứu.

## Resume, replay và bảo toàn

- Resume:12 cache hits, **0 inference mới,0 model load**; giữ call ID/raw/model/config/input hash.
- Replay:12 raw outputs, **0 inference mới,0 model load**; event log không đổi.
- Hai lần chấm bằng code cuối tạo [evaluation_final](execution/task4_runner/smoke_02/evaluation_final.json) và [evaluation_replayed](execution/task4_runner/smoke_02/evaluation_replayed.json) giống nhau. `budget.image_reader_invocations=12` là chi phí lượt gốc; `new_image_reader_invocations=0` cho thao tác chấm. Các score trước được giữ riêng.
- [final_checks.json](execution/task4_runner/final_checks.json) kiểm cache/call IDs, code hashes, số lượt, event log và replay. [actual_events.json](execution/task4_runner/smoke_02/actual_events.json) chỉ có hash/status/timing, không chứa OCR text/GT values.

HEAD `f5d130d93525e7633053edc03e6d9f6edeba7a6f`, branch `main`; không commit/push/rebase. Tracked/staged diff rỗng; các mục untracked khác có sẵn được giữ nguyên. Đối chiếu SHA2562.523 file có trước TASK4,179.019.262 bytes: [preservation_final.json](execution/task4_runner/preservation_final.json). Ignored model assets được kiểm read-only theo manifest trước fresh/resume; không tuyên bố recursively hash mọi ignored cache/dataset.

Không sửa checkpoint, dataset/split, prior model selection hay `research/results/` cũ. Raw inference/images/runtime mới ở ignored `local/`; public report không chứa CCCD thật, embedding hoặc thông tin định danh khách hàng.

## Chưa được chứng minh

Trước confirmatory evaluation cần corpus/GT/source-coverage/readability độc lập, oracle/fault adjudication pool, protocol/budget/baseline locks theo RQ cũ. TASK2 artifacts chưa tìm thấy từ TASK3. Chưa có precision/recall trên lỗi thật, validated root-cause defect set, kiểm chứng fresh-inference nondeterminism nhiều lần hoặc lợi ích generation ở cùng annotation budget. Không thay các việc đó bằng50 unit tests hay12 lượt smoke này.
