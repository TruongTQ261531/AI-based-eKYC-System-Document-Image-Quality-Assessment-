# Kiểm kê dự án cho TASK 0

Ngày kiểm kê 05/11/2026, múi giờ Asia/Bangkok. Phạm vi của lượt này là audit, bảo toàn và lập kế hoạch Source-Aware Evidence-Contract Testing cho EASE 2027 Research Track. `execution/` giữ log thực thi của audit. Framework chưa được xây dựng.

## Workspace và Git

| Mục | Giá trị tại lúc bắt đầu |
|---|---|
| Workspace người dùng mở | `D:/laptrinhcuatao/Ekyc` |
| Repository được kiểm kê | `D:/laptrinhcuatao/Ekyc/versions/research-document-recovery` |
| Branch | `main` |
| HEAD | `f5d130d93525e7633053edc03e6d9f6edeba7a6f` |
| Upstream theo ref local | `origin/main`, ahead 0, behind 0. Không fetch trong TASK 0 |
| File tracked | 842 file, tổng kích thước logic 92.020.619 byte |
| Thay đổi tracked/staged lúc bắt đầu | Không có |
| Thay đổi chưa commit | 12 file untracked, liệt kê bên dưới |
| Worktree mentor | `D:/laptrinhcuatao/Ekyc/versions/mentor-ekyc-v3.2.0`, detached HEAD `4110f22b94699d30950cd1c0b23532ee9ccaaa59` |
| AGENTS.md | Không tìm thấy trong các cấp cha đã kiểm tra và cây nguồn đã tìm, có loại venv/cache/dataset khỏi tìm kiếm |

`PRESERVATION_MANIFEST.json` lưu toàn bộ status, refs, worktrees và SHA256 từng file được bảo vệ. Không tạo branch, commit, fetch, push hoặc sửa lịch sử trong lượt này.

Các file untracked có trước TASK 0 được giữ tại chỗ.

```text
research/priority2_tiles.py
research/results/priority2_tiles_v1/plan.json
research/results/priority2_tiles_v1/comparison.json
research/results/source_visibility_v3/ui/audit-gate.jpg
research/results/source_visibility_v3/ui/field-clip.jpg
research/results/source_visibility_v3/ui/manual-provenance.jpg
research/results/source_visibility_v3/ui/new-specimen-ocr.jpg
research/results/source_visibility_v3/ui/new_specimen.png
research/results/source_visibility_v3/ui/preparation.jpg
research/results/source_visibility_v3/ui/review-ready.jpg
research/results/source_visibility_v3/ui/value-mask.jpg
research/results/vlm_lora_v2/ui/preparation-manual-demo.jpg
```

## Phân cách các hệ thống

| Hệ thống | Nguồn và vai trò |
|---|---|
| Mentor eKYC 3.2.0 | `ekyc/`, `web/index.html`, `web/app.js`, `scripts/`, launcher ở root. Module 1–3 xử lý giấy tờ, challenge camera và Module 5 xử lý đối chiếu. Cổng được cấu hình 8000 |
| Bản workspace gốc | Nguồn dưới `D:/laptrinhcuatao/Ekyc`, được giữ cùng worktree mentor, không chép đè từ nghiên cứu |
| Web nghiên cứu OCR V3 | `research/v3_web.py`, API nghiên cứu tại cổng được cấu hình 8003. Lựa chọn đã ghi nhận là `partial_42`, gate triển khai nghiên cứu chưa đạt |
| Trang nhãn | `research/labels_web.py`, `labels_review.py`, `labels_issues.py`, `web/labels_review.*`, cổng được cấu hình 8005 |
| Vùng nghiên cứu EASE mới | `research/evidence_contract/`. TASK 0 chỉ tạo tài liệu, manifest và log kiểm tra |

Cổng trong bảng là cấu hình tìm thấy trong mã. TASK 0 không khởi động, dừng hoặc gửi phiếu lên các dịch vụ thật. Các test HTTP dùng TestClient cùng database giả trong thư mục thực thi riêng.

## Dữ liệu, weights và môi trường sẵn có

Các đường dẫn dưới đây tính từ repository, trừ khi ghi đường dẫn tuyệt đối. Một số asset dùng junction hoặc hardlink tới workspace gốc. Ghi qua liên kết có thể sửa cùng một file vật lý ở nhiều nơi.

| Thành phần | Đường dẫn và bằng chứng |
|---|---|
| MIDV gốc | `full_dataset_original/` phân giải tới `D:/laptrinhcuatao/Ekyc/full_dataset_original`; có `midv500_dataset/`, `midv2019_dataset/`. `data/manifest.csv` và corpus release mô tả 21.050 ảnh, gồm 50 ảnh tham chiếu MIDV-2019 thêm vào Clean |
| Bản resize cũ | `D:/laptrinhcuatao/Ekyc/dataset_224/` tồn tại ở workspace gốc. Repository nghiên cứu không có thư mục `dataset_224` trực tiếp |
| Annotation gốc | `research/data/ocr_labels_v1/annotations.sqlite3`, 356.790.272 byte tại lúc kiểm kê; đáp án tác giả, vị trí và provenance. Đây là corpus giấy tờ mẫu hiện có |
| Dữ liệu R2/V3 | `research/data/vlm_lora_v2_r2/samples.json`, `sources.json`; `research/data/source_visibility_v3/samples.json` |
| Dữ liệu HP/FC | `research/data/hard_pairs_v1/{samples,base_graphs,sources}.json`; `research/data/fair_controls_v1/{train,evaluation,base_graphs,selection,sources}.json` |
| Bộ nhãn mới | `research/data/ocr_labels_v1/{evaluation,authored,render_specs,sources}.json`; 304 view, 56 ID, 80 view development và 224 view test |
| MIDV-2020 và kiểm chứng phụ | `research/data/midv2020/`, `midv_up/`, `layout_stress/`, `recovery_v4/` |
| Phiếu đang được người dùng chấm | `research/cache/ocr_labels_v1/reviews.sqlite3`; registry tại `research/data/ocr_labels_v1/reviewer_registry.json`. Chỉ đọc số tổng hợp khi kiểm kê, không đưa transcript, ghi chú hoặc ánh xạ người tham gia vào tài liệu này |
| Vintern gốc | `research/cache/vlm_lora_v1/model/`, model ID đã ghim `5CD-AI/Vintern-1B-v3_5`, revision `b98f263eab246eb5269ade64edbdca8a887dc44d`. Manifest tại `research/results/vlm_lora_v1/assets.json` |
| Adapter đang được lựa chọn | `research/cache/vlm_lora_v2_r2/training/partial_42/step_0320/adapter_model.safetensors`, SHA256 `98835d5922f968ce29681e2ec9a2b85f26e87d7ea9538fbfb701cc37cc8a6b27` theo manifest đã công bố |
| Adapter còn lại | Các thư mục `training/` dưới cache VLM V1, R2, source V3, hard-pair và fair-controls. Checkpoint trung gian, optimizer state và log được giữ |
| Localizer/OCR CPU | `research/cache/docaligner/fastvit_sa24.onnx`; `research/cache/upstream/rapid144/rapidocr_onnxruntime/models/`; `latin_PP-OCRv5_rec_mobile.onnx`, `lcnet100.onnx` dưới `cache/upstream/` |
| Weights mentor | `models/` và các liên kết tới `D:/laptrinhcuatao/Ekyc/models/`, gồm quality, ScanOCR/VietOCR, EasyOCR, PAD, YuNet, SFace, MediaPipe. Provenance ở các file `*sources.json` |
| Python hiện có | `D:/laptrinhcuatao/Ekyc/.venv/Scripts/python.exe`, Python 3.11.4. `.venv` của worktree phân giải về môi trường này |
| Môi trường CPU tại audit | pytest 9.1.1, torch 2.14.1, numpy 2.4.6, opencv-python-headless 5.0.0.93, Pillow 13.0.0, FastAPI 0.162.0, Starlette 1.9.0, httpx 0.28.1 |
| Overlay CUDA có sẵn | `research/cache/vlm_lora_v1/site/`, torch 2.7.1+cu126, transformers 4.46.3, peft 0.14.0, accelerate 1.2.1. Chỉ kiểm kê metadata, chưa nạp model trong TASK 0 |
| JavaScript | Node v24.22.1, dùng bộ test giao diện giả lập sẵn có |

Lần dò metadata đầu dùng tên `opencv-python` không thấy distribution đó. Dò lại xác nhận đã cài `opencv-python-headless` và test hình học chạy được. Không cài hoặc nâng package.

## Nghiên cứu đã hoàn thành và phần còn thiếu

Các con số dưới đây lấy từ báo cáo/artifact lịch sử, không phải lượt thực nghiệm mới của TASK 0.

| Vùng kết quả | Trạng thái tìm thấy | Phạm vi còn thiếu |
|---|---|---|
| `feasibility_v1`, `risk_policy_v2`, `partial_support_v3` | Các vòng hình học/coverage/CRC đã có kết quả; các kết quả âm được giữ | Lợi ích riêng của support/CRC chưa được chứng minh rộng; chữ V1/V2/V3 tại đây khác tên VLM R2/V3 |
| `e2e_ocr_v2` | 161 ảnh chính, 225 lượt ảnh gồm panel lặp, 2.700 hàng spatial transcription | Chỉ số khác semantic KIE; các ảnh đã được xem kết quả |
| `recovery_v4` | 540 ảnh, 150 ID, 588 lượt inference chính, 15.288 hàng. Cascade không vượt completion trên chỉ số chính | Camera tự thu thập và legibility độc lập vẫn thiếu |
| `vlm_lora_v1` | LoRA V1, đối chứng và audit đã có; artifact index bảo toàn 101 file lịch sử | Một backbone nhỏ, task/split/ngân sách khác các vòng sau |
| `vlm_lora_v2` | Pilot bị dừng sau lỗi ánh xạ nhãn, được giữ riêng | Không gọi pilot này là một run hoàn thành hoặc dùng adapter của nó thay R2 |
| `vlm_lora_v2_r2` | Bốn run complete/partial hai seed đã hoàn tất, 320 update và 1.280 lượt ảnh/run | So kết quả theo đúng hợp đồng nhãn từng vòng |
| `source_visibility_v3` | Hai run source-supervised và nhiều đối chứng; OR/AND bằng chứng đã triển khai. F1 source so partial có CI chứa 0 ở cả hai seed | Nguồn ngoài contract và khả năng đọc của người chưa được bao phủ đầy đủ |
| `hard_pairs_v1` | Hai run hard, test 48 ID/192 view. Giảm một số omission nhưng tăng output mất nguồn, gate promotion không đạt | Chưa giảm đồng thời hai nhóm lỗi; MRZ 43/44 ký tự có coverage note riêng |
| `fair_controls_v1` | Bốn run random/repeat bổ sung và bốn adapter lịch sử. Bốn so sánh chính chưa phân biệt được hard với random/repeat, p Holm bằng 1 | Power hạn chế, chỉ hai seed, khác camera quần thể chưa kiểm chứng |
| `ocr_labels_v1` | 21.050 ảnh/229.866 vùng; 912 lượt chính và 24 lượt đọc lặp, audit passed. Snapshot báo cáo có 6/48 mẫu chấm đơn | Snapshot live phải đọc riêng. Nhãn hình học không tự trở thành nhãn legibility, còn thiếu dữ liệu camera mới có phép |
| `priority2_tiles_v1` | 32 lượt đo trên 16 view development/8 ID, rect2 F1 0,5615 và rect4 0,5404; CI chênh lệch chứa 0 | Toàn bộ mã và hai JSON kết quả còn untracked, phạm vi development. Không chạy lại trong TASK 0 |

`research/STATUS.md` là snapshot V4 ngày 31/10; `PRIORITY_PROGRESS_VI.md` ghi rõ là snapshot trước hard-pair. Các câu “chưa chạy đối chứng/ca khó” ở đó đã được báo cáo HP/FC mới hơn thay thế về mặt tiến độ. Các file lịch sử được giữ nguyên.

Snapshot đọc riêng trong TASK 0 có **35/48 mẫu pilot**, **269 lượt trường đánh giá đơn**, 81 event và một mã reviewer tự khai. Có 65 lượt trường được đánh dấu tự khai độc lập với đáp án; 0 nhãn trường đạt đối chiếu độc lập. Các mẫu trong chế độ xem tác giả hoặc phiếu không khai độc lập cần được phân biệt với mẫu blind khi đánh giá oracle. Số liệu và thời điểm đọc ở `execution/inventory_snapshot.json`. Đây là snapshot, các phiếu người dùng gửi tiếp có thể tăng số live.

## Tài liệu và mã đã đọc

Đã đọc README, `BRANCH_INTEGRATION_REVIEW.md`, `MENTOR_BASELINE.md` ở root, ba cặp protocol/results OCR Labels, Hard Pair, Fair Controls, `VLM_PRIOR_ART_VI.md`, `STATUS.md`, `PRIORITY_PROGRESS_VI.md`. Đã đối chiếu các mục thiết kế/kết quả/giới hạn của REPORT, E2E, Recovery V4, VLM V1, V2 và V3; cùng coverage note, related work, submission gates và trạng thái V3. Tài liệu được đọc theo phạm vi này, không nhận đã tái thẩm định mọi bài báo được chúng dẫn.

Đã đọc toàn bộ bảy file trọng tâm được yêu cầu là `v3_sources.py`, `hp_data.py`, `hp_metrics.py`, `labels_schema.py`, `labels_review.py`, `labels_metrics.py`, `fc_statistics.py` và kiểm tra thêm phần chấm ngày/parse tại `v3_metrics.py`. `labels_common.py`, runtime/setup và test fixture liên quan cũng đã được kiểm tra.

## Kiểm tra an toàn trong TASK 0

- 60 test Python hiện có đã qua, 1 cảnh báo Starlette/httpx deprecation, không có test thất bại. Log và JUnit tại `execution/python_safe_tests.log` và `.xml`.
- 6 test JavaScript về lưu phiếu, lỗi form, retry và chống bấm lặp đã qua. Log tại `execution/javascript_review_tests.log`.
- `execution/checks.json` ghi command, môi trường override, thời điểm, thời lượng và exit code. SQLite fixture và ảnh giả nằm dưới `execution/pytest_tmp/`.
- Đã chọn riêng `test_hp_statistics.py::ClusterIntervals`. Hai test promotion còn lại có code tạo thư mục trong cache HP lịch sử, nên chưa chạy ở TASK 0.
- Chưa chạy full suite 344 test, camera thật, API eKYC production, inference OCR/VLM, training, feature extraction hoặc benchmark đã hoàn thành. Bộ test hiện tại chỉ xác nhận regression bằng fixture.
- Kết quả kiểm tra băm sau cùng, bao gồm phạm vi chưa băm lại, nằm trong `PRESERVATION_MANIFEST.json` và log thực thi bảo toàn.

Kết quả đối chiếu sau cùng là **23.897 file có hash khớp**, tổng kích thước logic 6.384.486.149 byte, gồm 23.738 file trong repository nghiên cứu, 85 file của workspace gốc và 74 file của worktree mentor. Các file có hardlink hoặc được tham chiếu nhiều nơi có thể được đếm lại; tổng byte này không phải dung lượng vật lý duy nhất.

Bốn index đã đối chiếu khớp gồm VLM V1 101 file, Recovery V4 63 file, `fair_controls_v1/previous_artifacts.json` 53 file và `ocr_labels_v1/previous_artifacts.json` 74 file. HEAD, branch, refs và worktree giữ nguyên, tracked/staged diff rỗng. Chỉ có thư mục `research/evidence_contract/` được thêm vào Git status so với trước.

Còn 10.010 file được kê metadata thay vì băm nội dung, chủ yếu ảnh cache, tensor feature và dữ liệu phụ. Dữ liệu ảnh gốc khoảng 116 GB được tham chiếu bằng corpus release và data audit cũ, chưa được băm lại trong TASK 0. Môi trường site-packages cũng chưa được kiểm tra hash từng file. Các giới hạn này được ghi trong manifest; kết quả bảo toàn không mở rộng tới những byte chưa đọc.

## Rủi ro cần chuyển sang kế hoạch EASE

1. Trùng tên V1/V2/V3 giữa hình học, VLM và API mentor dễ dẫn tới đọc nhầm kết quả hoặc chạy nhầm runner.
2. `source_graph` chỉ mô tả các nguồn đã biết. MRZ không parse được, barcode/QR hoặc nguồn encoded chưa khai báo phải được ghi là coverage chưa đủ.
3. `visible_realizations` dùng quy tắc hình học, ngưỡng giao mask và điều kiện nguyên vẹn. Nó chưa đo blur/glare/khả năng đọc của người.
4. Cùng một hàm vừa tạo nhãn vừa kiểm tra nhãn có thể tạo một oracle khép kín tự xác nhận. Cần validator và tham chiếu kiểm tra độc lập ở các mốc sau.
5. Tests cũ đã được xem điểm; mọi cải thiện trên chúng là hồi cứu. Bộ xác nhận mới phải được khóa sau khi chốt thiết kế.
6. Cache/raw outputs là dữ liệu riêng. Manifest TASK 0 có đường dẫn máy và hash nội bộ, cần gói artifact ẩn danh riêng nếu nộp bài.
