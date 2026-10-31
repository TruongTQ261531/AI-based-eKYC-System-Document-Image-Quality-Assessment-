# Nghiên cứu V4: phục hồi giấy tờ, benchmark và web localhost

**Kết quả thực nghiệm; không phải xác nhận bài đã được CORE B chấp nhận.** Bản mentor và các kết quả cũ được giữ nguyên. Tất cả phương án, kể cả phương án thua baseline, đều được công bố.

## Phạm vi mới

- **540 ảnh / 150 document ID**, gồm 360 ảnh SPECIMEN mới từ 90 ID và 180 biến thể của 60 ID MIDV chọn thêm. SPECIMEN không phải CCCD thật hoặc 90 người thật.
- Tách **40 ID development, 30 calibration, 80 test**. Không có ID hoặc ảnh byte-identical đi qua nhiều role. 30 ID SPECIMEN test thuộc hai cấu hình font/thứ tự trường chưa dùng ở development. Sáu mã cấu hình gốc chỉ tạo bốn nhóm ngôn ngữ/font/thứ tự; 0/2 và 1/3 dùng chung vị trí. Không diễn giải chúng thành sáu layout không gian độc lập.
- Một lượt đủ 540 ca và hai lượt mới trên cùng 24 ca khác ID: **588 lượt inference**, không phải ba lượt đủ 540 ảnh. Các lần lặp không tạo thêm ID độc lập.
- Thời gian toàn đợt inference: **107.68 phút**. Đây là tổng chi phí thử tất cả view/reader, không phải thời gian một yêu cầu camera.
- FastViT-SA24 và LCNet100; RapidOCR chính thức với PP-OCRv4 và reader Latin PP-OCRv5. Pipeline Latin dùng detector PP-OCRv4, không gọi nó là nguyên hệ thống PP-OCRv5 mới nhất. Không tạo venv/cài dependency vào môi trường hiện tại.
- Baseline thêm: raw, strict, completion +5%, bbox, contour, text deskew; selector confidence, ridge, boosted stumps và cascade có tối đa một fallback. Hyperparameter/cấu trúc chọn bằng grouped CV trên development.
- MIDV xuất hiện trong dữ liệu/ảnh minh họa huấn luyện của tác giả; không tuyên bố các ảnh MIDV chọn thêm là unseen-pretraining. Nguồn SPECIMEN được tạo mới, nhưng chưa có bộ camera thực mới độc lập.
- [Dataset card](DATASET_CARD_V4.md), [giao thức](RESEARCH_V4_PROTOCOL.md), [bổ sung chấm trước test](RECOVERY_EVALUATION_ADDENDUM.md), [prior art/baseline](RESEARCH_V4_RELATED_WORK.md).

Máy đo: **AMD Ryzen 5 7235HS**, 8 logical processors, 15.69 GiB RAM, Windows / Python 3.11.4. ONNX CPU, 2 thread/session; máy desktop không dành riêng CPU. [Phiên bản thư viện và máy](results/recovery_v4/environment.json).

## Kết quả chính trên ID test

Cascade chính cho Latin là **cascade_stumps**, chọn từ development trước khi chấm test. Field exact dưới đây yêu cầu đúng toàn bộ trường còn nhìn thấy đầy đủ; trường bị bỏ sót/ảnh bị từ chối tính sai. Không dùng GT để cắt chữ đưa vào OCR. GT chỉ ghép/chấm sau inference.

| Nguồn | Phương án | Field exact (%) | CER micro | Wall TB (s) | Giữ lại (%) |
|---|---|---:|---:|---:|---:|
| authored_specimen | raw | 79.73 | 0.048 | 0.996 | 100.00 |
| authored_specimen | completion | 80.00 | 0.048 | 1.148 | 100.00 |
| authored_specimen | bbox | 79.87 | 0.048 | 1.146 | 100.00 |
| authored_specimen | lcnet | 79.20 | 0.048 | 1.063 | 100.00 |
| authored_specimen | max_confidence | 79.60 | 0.048 | 3.497 | 95.00 |
| authored_specimen | allviews_ridge | 79.33 | 0.048 | 3.497 | 98.50 |
| authored_specimen | allviews_stumps | 79.73 | 0.048 | 3.497 | 97.50 |
| authored_specimen | cascade_ridge | 80.00 | 0.048 | 1.159 | 98.00 |
| authored_specimen | cascade_stumps | 80.00 | 0.048 | 1.148 | 98.00 |
| midv2020_derived | raw | 42.82 | 0.336 | 1.735 | 100.00 |
| midv2020_derived | completion | 57.29 | 0.206 | 2.325 | 100.00 |
| midv2020_derived | bbox | 54.98 | 0.231 | 2.446 | 100.00 |
| midv2020_derived | lcnet | 50.69 | 0.270 | 2.103 | 100.00 |
| midv2020_derived | max_confidence | 48.03 | 0.278 | 7.521 | 24.44 |
| midv2020_derived | allviews_ridge | 55.90 | 0.202 | 7.521 | 28.89 |
| midv2020_derived | allviews_stumps | 56.37 | 0.202 | 7.521 | 23.33 |
| midv2020_derived | cascade_ridge | 57.52 | 0.204 | 2.436 | 28.89 |
| midv2020_derived | cascade_stumps | 57.29 | 0.206 | 2.325 | 28.89 |

Wall của các selector được **tái dựng từ stage đã đo**, dùng cache raster trùng trong cùng ca và bỏ qua overhead selector. Đó không phải thời gian request online. Bảng online thật ở dưới. Native retention là gate hình học; selector retention có thêm ngưỡng confidence lấy từ calibration với mục tiêu 80%. Mục tiêu này không bảo đảm 80% hoặc độ an toàn ở test.

### Đối chiếu với completion theo physical ID

Bootstrap 2.000 lần theo document ID; trung bình field trong ảnh rồi ảnh trong ID. Vì vậy delta không nhất thiết bằng chênh lệch pooled-field ở bảng trên. CI thăm dò, không điều chỉnh nhiều phép so sánh.

| Reader | Nguồn | Cascade đã khóa | Số ID | Delta exact (điểm %) | CI95% |
|---|---|---|---:|---:|---:|
| rapid_v4 | authored_specimen | cascade_stumps | 50 | +0.00 | [0.00; 0.00] |
| rapid_v4 | midv2020_derived | cascade_stumps | 30 | +0.00 | [0.00; 0.00] |
| rapid_latin_v5 | authored_specimen | cascade_stumps | 50 | +0.00 | [0.00; 0.00] |
| rapid_latin_v5 | midv2020_derived | cascade_stumps | 30 | +0.00 | [0.00; 0.00] |

Có **0/4** đối chiếu cascade chính cho CI exact hoàn toàn trên 0. Không suy từ một tập/reader thắng sang ưu thế phổ quát. Các cấu trúc còn lại và mọi số liệu native nằm trong [summary CSV](results/recovery_v4/summary.csv) và [bootstrap](results/recovery_v4/paired_bootstrap.json).

## Pipeline online chạy thật

Cùng 24 ảnh panel, 3 lượt fresh, so cascade Latin với completion; thứ tự hai phương án được đối trọng. 144 yêu cầu pipeline, không dùng lại OCR giữa yêu cầu. Các role trong panel gồm development/calibration/test; đây là kiểm chứng triển khai/timing, không phải thêm 24 test ID mới. Model cùng resident, desktop CPU không độc quyền.

| Nguồn | Phương án | Mean ± SD giữa 3 lượt (s/ảnh) | OCR TB / yêu cầu | Giữ lại thực tế (%) |
|---|---|---:|---:|---:|
| authored_specimen | fixed_completion | 1.079 ± 0.118 | 1.00 | 100.00 |
| authored_specimen | primary_cascade | 1.054 ± 0.081 | 1.00 | 100.00 |
| midv2020_derived | fixed_completion | 2.413 ± 0.327 | 1.00 | 41.67 |
| midv2020_derived | primary_cascade | 2.380 ± 0.330 | 1.00 | 41.67 |

Output online so với lựa chọn từ exhaustive candidates: **0 mismatch**; tối đa **1 OCR execution/yêu cầu**. Gate review online khác gate exhaustive ở **0** yêu cầu: online bổ sung cờ review khi output rỗng, kể cả khi threshold bằng0. Wall này đo phần dự đoán, chưa gồm HTTP transfer/decode. Web còn báo thời gian xử lý request có decode/encode/cold load. [Actual traces](results/recovery_v4/online_traces.json).

## OCR reader đối chứng trên cùng panel

Legacy chỉ chạy 24 ảnh, không phải toàn bộ 540. EasyOCR/VietOCR dùng chung CRAFT; VietOCR màu lấy crop màu từ vùng do detector dự đoán, chọn 0/180 bằng confidence. Không dùng crop GT.

| Nguồn | Reader / pipeline cùng panel | Field exact (%) | CER micro | Wall TB (s) |
|---|---|---:|---:|---:|
| authored_specimen | rapid_v4 | 62.22 | 0.091 | 1.262 |
| authored_specimen | rapid_latin_v5 | 82.22 | 0.045 | 1.118 |
| authored_specimen | easyocr_en | 40.00 | 0.469 | 8.597 |
| authored_specimen | vietocr | 51.11 | 0.337 | 11.704 |
| authored_specimen | vietocr_color | 53.33 | 0.331 | 11.628 |
| midv2020_derived | rapid_v4 | 53.57 | 0.194 | 3.495 |
| midv2020_derived | rapid_latin_v5 | 57.86 | 0.184 | 2.741 |
| midv2020_derived | easyocr_en | 35.71 | 0.413 | 19.858 |
| midv2020_derived | vietocr | 35.71 | 0.539 | 23.344 |
| midv2020_derived | vietocr_color | 33.57 | 0.512 | 22.642 |

Không đối chiếu số legacy panel trực tiếp với bảng toàn bộ test để tuyên bố reader nào thắng. Dùng bảng panel ghép cùng ảnh trong artifact khi so reader; các reader không độc lập hoàn toàn vì chia sẻ detector.

## KIE có schema và chữ bị cắt

Phép chấm này chỉ áp dụng SPECIMEN có nhãn trường ngữ nghĩa, không dùng GT box để gán key khi suy luận. Extractor đổi ngày thành ISO và gender thành Nam/Nữ. Vì vậy báo cả literal string và canonical schema đã công bố trước khi xem test; đây không phải cải thiện OCR bằng sửa chuỗi theo GT.

| Reader | Phương án | KIE literal (%) | KIE canonical (%) | OCR đúng nhưng sai gán trường |
|---|---|---:|---:|---:|
| rapid_v4 | raw | 29.20 | 55.60 | 90 |
| rapid_v4 | completion | 27.73 | 51.87 | 118 |
| rapid_v4 | bbox | 27.87 | 52.40 | 115 |
| rapid_v4 | cascade_stumps | 27.73 | 51.87 | 118 |
| rapid_latin_v5 | raw | 38.67 | 67.60 | 112 |
| rapid_latin_v5 | completion | 37.73 | 66.67 | 121 |
| rapid_latin_v5 | bbox | 37.87 | 66.80 | 119 |
| rapid_latin_v5 | cascade_stumps | 37.73 | 66.67 | 121 |

Ảnh field-clip có thể không còn trường nguyên vẹn để chấm primary. Chúng vẫn được giữ trong chi phí/review. Secondary dưới đây so với substring gồm ký tự có ≥99,5% diện tích support rectangle nằm trong khung. Đây là proxy hình học từ font, không phải nhãn đọc được do con người xác nhận.

| Latin, chỉ field bị cắt | Số trường | Visible-reference exact (%) | Visible CER |
|---|---:|---:|---:|
| raw | 224 | 34.82 | 0.153 |
| completion | 224 | 34.82 | 0.153 |
| bbox | 224 | 34.82 | 0.153 |
| cascade_stumps | 224 | 34.82 | 0.153 |

### Mẫu không có target nguyên vẹn

| Nguồn / capture, chỉ test | Ảnh | Ảnh không có trường đủ điều kiện | Trường đủ điều kiện |
|---|---:|---:|---:|
| authored_specimen / blur_glare | 50 | 0 | 250 |
| authored_specimen / corner_clip | 50 | 0 | 250 |
| authored_specimen / field_clip | 50 | 50 | 0 |
| authored_specimen / full | 50 | 0 | 250 |
| midv2020_derived / corner_clip | 30 | 0 | 365 |
| midv2020_derived / field_clip | 30 | 0 | 131 |
| midv2020_derived / full | 30 | 0 | 368 |

Các ảnh không có target không đóng góp mẫu số primary OCR; vẫn nằm trong mẫu số latency/review. Đây là giới hạn cần đọc cùng secondary visible metric, không phải ảnh được OCR chính xác 100%.

### Review đối với ảnh bị cắt trường

| Nguồn / Latin | Phương án | Ảnh giữ lại có field bị cắt (%) | Recall cờ review cho ảnh bị cắt (%) |
|---|---|---:|---:|
| authored_specimen | fixed_completion | 23.47 | 8.00 |
| authored_specimen | cascade_stumps | 23.47 | 8.00 |
| midv2020_derived | fixed_completion | 42.31 | 65.62 |
| midv2020_derived | cascade_stumps | 42.31 | 65.62 |

Không diễn giải visible-field exact cao hoặc confidence cao là giấy tờ đầy đủ/hợp lệ. Ảnh/text còn có thể sai hoặc bị thiếu; người dùng phải kiểm tra. Web không duyệt eKYC hoặc xác thực chân dung.

## Kiểm chứng chuyển miền, không fit lại

**MIDV-UP:** 24 ảnh tác giả chụp thực, 24 ID, bốn loại giấy tờ bổ sung và hai nhóm điện thoại; hai lượt fresh, ba phương án = 144 yêu cầu. Mẫu nhỏ chọn hash cố định và không chứng minh unseen-pretraining. Latin reader chưa hỗ trợ toàn bộ tiếng Urdu/Persian. Bảng tính lượt 1, lượt 2 chỉ kiểm độ lặp lại.

| Tập / phương án | Số trường đủ điều kiện | Field exact (%) | CER micro | Wall thật TB (s) | Giữ lại (%) |
|---|---:|---:|---:|---:|---:|
| MIDV-UP / raw | 137 | 18.98 | 0.734 | 2.092 | 91.67 |
| MIDV-UP / fixed_completion | 137 | 17.52 | 0.722 | 2.112 | 8.33 |
| MIDV-UP / primary_cascade | 137 | 17.52 | 0.725 | 1.997 | 8.33 |
| Spatial stress / raw | 320 | 87.81 | 0.018 | 1.086 | 100.00 |
| Spatial stress / fixed_completion | 320 | 80.94 | 0.065 | 0.991 | 83.75 |
| Spatial stress / primary_cascade | 320 | 80.94 | 0.065 | 1.008 | 83.75 |

**Spatial stress:** 80 ảnh SPECIMEN từ 20 ID mới với hai cấu trúc hai cột/thẻ dọc. Một lượt đủ 80 ảnh và hai lượt mới trên cùng 8 ảnh panel: 288 yêu cầu cho ba phương án. Chỉ stress test mô hình đã khóa; không dùng để thay thế tập test gốc hoặc chọn lại threshold. Không phải 80 ảnh chụp camera thực. KIE của raw không chấm trong supplement này.

| Spatial layout | Phương án | Trường | Field exact (%) | CER |
|---|---|---:|---:|---:|
| two_column | raw | 170 | 100.00 | 0.000 |
| two_column | fixed_completion | 170 | 100.00 | 0.000 |
| two_column | primary_cascade | 170 | 100.00 | 0.000 |
| portrait | raw | 150 | 74.00 | 0.043 |
| portrait | fixed_completion | 150 | 59.33 | 0.160 |
| portrait | primary_cascade | 150 | 59.33 | 0.160 |

| Spatial stress | Canonical KIE (%) | Ảnh giữ lại có field bị cắt (%) |
|---|---:|---:|
| fixed_completion | 42.19 | 14.93 |
| primary_cascade | 42.19 | 14.93 |

MIDV-UP có **83 / 137** trường đủ predicate gốc nhưng chứa ký tự ngoài alphabet reader. Không âm thầm loại các trường khó sau khi xem kết quả. Số tương ứng theo nguồn/reader chính:

| Reader / nguồn test | Trường hỗ trợ toàn bộ alphabet / tổng |
|---|---:|
| rapid_v4 / authored_specimen | 621 / 750 |
| rapid_v4 / midv2020_derived | 810 / 864 |
| rapid_latin_v5 / authored_specimen | 633 / 750 |
| rapid_latin_v5 / midv2020_derived | 813 / 864 |

[MIDV-UP traces](results/recovery_v4/up_external.json), [spatial stress traces](results/recovery_v4/layout_stress.json). Tỷ lệ giữ của raw chỉ loại trường hợp không có chữ, không được xem là cùng gate calibration với cascade/completion. Trên spatial stress, raw đạt 87.81% còn completion 80.94%; MIDV-UP tương ứng 18.98% và 17.52%. Vì vậy kết quả không hỗ trợ ép mọi ảnh qua nắn hình hoặc claim phục hồi vượt raw ở mọi miền.

## Sửa gán thông tin vào form: ablation bổ sung

Giữ nguyên OCR Latin completion, thêm ghép nhãn–giá trị theo hình học phải/dưới và assignment một giá trị/một nhãn. Tái dùng alias/kiểm tra ngày, giới tính, số giấy tờ hiện có; hỗ trợ nhãn lạ có dấu hai chấm. Không dùng GT box, ID hoặc giá trị mong đợi khi ghép. Đây là kỹ thuật quen thuộc được kiểm cho ứng dụng, không tuyên bố Hungarian assignment hoặc parser nhãn–giá trị là thuật toán mới.

So 360 ảnh authored chính và 80 ảnh stress, 440 ca, chỉ lượt 1. Dùng lại output OCR đã lưu: **0 lượt OCR bổ sung**. Hai lần chạy parser trên cùng output kiểm tra tính xác định, không phải hai lượt camera. Phương án được khóa sau kiểm tra development. Kết quả chính V4 đã được xem tổng hợp trước khi thiết kế parser, nên so sánh trên V4 dưới đây là **post hoc**; ghi rõ trong [giao thức](LAYOUT_KIE_PROTOCOL.md).

| Nguồn / role | Bộ gán | Trường | Canonical key–value exact (%) |
|---|---|---:|---:|
| authored_specimen / development | baseline | 300 | 58.33 |
| authored_specimen / development | layout_assignment | 300 | 67.67 |
| authored_specimen / calibration | baseline | 300 | 60.00 |
| authored_specimen / calibration | layout_assignment | 300 | 71.33 |
| authored_specimen / test | baseline | 750 | 66.67 |
| authored_specimen / test | layout_assignment | 750 | 76.27 |
| authored_layout_stress / external_layout | baseline | 320 | 42.19 |
| authored_layout_stress / external_layout | layout_assignment | 320 | 79.69 |

Bootstrap 2.000 lần theo document ID, thăm dò và không điều chỉnh nhiều phép so sánh:

| Nguồn | ID | Delta semantic exact (điểm %) | CI95% |
|---|---:|---:|---:|
| authored_specimen | 50 | +9.60 | [7.20; 12.00] |
| authored_layout_stress | 20 | +37.25 | [19.75; 54.42] |

Canonical exact ở trên tính theo trường GT đủ điều kiện, có tính chất recall; không gọi nó là precision. Bảng sau chỉ lấy ảnh mà mọi trường annotated còn nguyên hình học; tất cả key dự đoán nằm trong mẫu số precision. Không áp cách phạt full-value này cho substring của field bị cắt.

| Nguồn test / phương án | Ảnh | Exact precision (%) | Recall (%) | F1 (%) | Key ngoài schema authored |
|---|---:|---:|---:|---:|---:|
| authored_specimen / baseline | 150 | 78.62 | 66.67 | 72.15 | 0 |
| authored_specimen / layout_assignment | 150 | 78.68 | 76.27 | 77.45 | 80 |
| authored_layout_stress / baseline | 60 | 67.50 | 45.00 | 54.00 | 0 |
| authored_layout_stress / layout_assignment | 60 | 87.04 | 78.33 | 82.46 | 13 |

Chi phí parser TB **2.78 ms/ảnh**; chi phí tái dựng tọa độ từ cache được lưu riêng, không trộn vào thời gian OCR. Bật bộ gán mới trên web theo quyết định development: **True**. Nếu không cải thiện trên test thì vẫn công bố và giữ đúng quyết định development. [Lock](results/recovery_v4/layout_kie_lock.json), [từng ca](results/recovery_v4/layout_kie.json).

## Audit, kiểm thử và lịch sử

- **8232 native rows chấm lại**, **7056 quyết định selector replay**, **15288 hàng công khai**. Sai khác score/publication/wall/CPU: 0.
- Các kiểm chứng online/legacy/ngoài miền được chấm lại: {'online_rescored': 144, 'legacy_rescored': 72, 'external_up_rescored': 144, 'external_layout_rescored': 288, 'kie_cases_replayed_and_rescored': 440}.
- Audit lặp supplement: `{'midv_up': {'repeated_image_method_groups': 72, 'canonical_prediction_mismatches': 0, 'score_mismatches': 0, 'repeated_images_are_not_additional_independent_documents': True}, 'spatial_layout': {'repeated_image_method_groups': 24, 'canonical_prediction_mismatches': 0, 'score_mismatches': 0, 'repeated_images_are_not_additional_independent_documents': True}}`. Không đếm ảnh lặp thành ID mới.
- Panel inference 24 ảnh: 0 canonical prediction mismatch, 0 field-score mismatch qua 3 lượt. Không gọi số hàng là số inference độc lập.
- Test cuối: **162 Python**, **21 frontend** đạt. Test manifest raw của mentor được loại riêng trong worktree; dữ liệu nghiên cứu được audit hash. Log và XML được lưu, không cài package để che cảnh báo dependency.
- Adapter mới thực thi đúng các hàm số học tác giả đã ghim; parity 8 ảnh development và case tied peaks được kiểm. Chưa kiểm toàn bộ package/các backend/center-crop. Adapter cũ và kết quả V2 được giữ nguyên, không sửa số lịch sử.
- [Independent audit](results/recovery_v4/independent_audit.json), [model lock](results/recovery_v4/selector_lock.json), [validation](results/recovery_v4/validation.json), [nguồn dataset](results/recovery_v4/dataset_source_documents.json).

## Kết luận về đóng góp paper

Đã bổ sung dataset/giao thức, nhiều baseline/cấu trúc, chấm KIE và visible references, đo online thực tế, audit và web chạy thật. Đây là các artifact có thể kiểm tra được; không đồng nghĩa một regressor/cascade quen thuộc trở thành thuật toán mới.

Trong bốn đối chiếu nguồn–reader của cascade chính, 0 có CI accuracy hoàn toàn dương. Cascade cho độ chính xác bằng completion trong cả bốn đối chiếu. Kết quả này không hỗ trợ claim thuật toán mới vượt baseline. Đọc thời gian thực tế và review/truncation để đánh giá ứng dụng. Hướng paper phù hợp để xem xét tiếp là đánh giá/benchmark có phạm vi rõ; số lượng test và một website chạy được không tự tạo ra novelty.

Các hạn chế chưa thể xóa bằng unit test: ít layout/font/camera, nguồn tổng hợp có khoảng cách thực tế, MIDV có thể đã thấy trong pretraining, chưa có annotation legibility độc lập và chưa chạy mọi neural rectifier/market API. Cần dữ liệu camera mới có quyền sử dụng và đối chiếu closest-prior chặt trước quyết định nộp CORE B. Không có phép kiểm nào bảo đảm quyết định chấp nhận của phản biện.

## Chạy web

Từ worktree nghiên cứu chạy `powershell -NoProfile -ExecutionPolicy Bypass -File .\research\start-research.ps1`, mở **http://127.0.0.1:8001/** trong Chrome/Edge. Camera live → preview → xác nhận → OCR → form có thể sửa. Ảnh giữ nguyên độ phân giải gốc khi gửi; không ghi ảnh/text camera ra file hoặc gửi tới API ngoài. Đây là nghiên cứu document processing, tách khỏi mentor8000.

Đường suy luận kiểm tra seal mã/model, không mở annotation huấn luyện/benchmark hoặc tra database định danh. Seal được xuất offline bởi recovery_deploy.py từ bản khóa development.

Kiểm thử browser với OCR thật: thẻ hai cột và mẫu đủ khung điền đúng5 trường; mẫu giấy phép thiếu họ tên do nhãn OCR sai; mẫu sinh viên có lỗi ghép Trường thành giá trị Khóa. Giữ cả lỗi này trong [browser validation](results/recovery_v4/browser_validation.json). UI có cảnh báo/chỉnh sửa/xóa; mọi cảnh báo hình học đều hiện Cần kiểm tra, kể cả gate confidence không bật. Đây là trợ giúp hiển thị, không thay đổi các metric V4. Sửa sau xác nhận yêu cầu xác nhận lại. Chưa kiểm thử chụp camera vật lý.

Ảnh minh chứng: [form hai cột](results/recovery_v4/web_validation.jpg), [cảnh báo cắt chữ](results/recovery_v4/web_warning.jpg).

Biểu đồ: [test accuracy](results/recovery_v4/test_accuracy.png), [trace costs](results/recovery_v4/trace_cost.png).
