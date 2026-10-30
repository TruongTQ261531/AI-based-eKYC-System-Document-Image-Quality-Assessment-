# Benchmark OCR đầu cuối: kết quả thực nghiệm 30/10/2026

Đây là nghiên cứu riêng trên nhánh `research/document-recovery-core-b`. Runtime mentor được giữ nguyên. Kết quả đo OCR từ pixel ảnh và vùng chữ do model tự phát hiện; không dùng tọa độ GT để cắt chữ đưa vào model. Nhãn chuẩn chỉ dùng chấm sau inference. Đây là **spatial field transcription**, chưa phải semantic KIE hay tự gán nhãn họ tên/địa chỉ cho mọi loại giấy tờ.

## Phạm vi và nguồn gốc

- Lượt đầy đủ: **161 ảnh**, gồm91 ca neural trả về ba góc,50 ca đủ bốn góc chọn bằng hash và20 ảnh MIDV-2020.
- Có1.643 trường Latin nhìn thấy đầy đủ để chấm:910/489/244 theo ba nhóm. 10 trường bị cắt và193 trường ngoài phạm vi/không hợp lệ được đếm riêng; không bỏ ảnh tương ứng khỏi latency/routing.
- Hai lượt tiếp theo chạy inference mới trên cùng **32 ảnh** (24/4/4), với primary IDs khác nhau trong panel. Tổng225 lượt ảnh, **không phải ba lượt đầy đủ161 ảnh**. Accuracy chính dùng lượt1; SD lặp chỉ dùng cùng panel32.
- Mẫu chọn có chủ đích theo số góc dự đoán, không đại diện ngẫu nhiên mọi ảnh MIDV. Ba góc model phát hiện không đồng nghĩa GT chỉ có ba góc nhìn thấy.
- Trong91 ca neural ba góc, GT có1/2/3/4 góc trong khung tương ứng 1/7/73/10 ảnh. Do đó không gọi cả91 ca là giấy tờ thật sự mất đúng một góc ngoài khung.
- Sáu trọng số/config có nguồn và hash; EasyOCR kiểm MD5 registry tác giả, VietOCR/DocAligner kiểm SHA256 đã ghim. Không train, tạo venv, cài dependency hay tải model mới trong đợt này.
- [Giao thức](E2E_OCR_PROTOCOL.md), [nguồn và giới hạn đo](E2E_OCR_PROVENANCE.md), [manifest](results/e2e_ocr_v2/manifest.json), [ảnh/target audit](results/e2e_ocr_v2/sample_audit.json).

## Sáu phương án

`raw_fullframe` giữ ảnh gốc, không cần localizer. `neural_strict` chỉ đọc khi có quad hợp lệ. `three_fullframe` thêm nhánh đưa nguyên ảnh ba góc đi tiếp. `three_support` dùng giao hai nửa mặt phẳng quan sát được, crop bbox và tô trắng ngoài polygon; `three_support_bbox` bỏ bước mask. `three_parallelogram05` hoàn thành hình bình hành, nới5% rồi warp. Nhánh bốn góc giống nhau giữa các policy neural.

CRAFT tìm vùng chữ thật trên mỗi ảnh đầu ra. Hai recognizer dùng cùng detector và normalization dòng grayscale; VietOCR chuyển các patch grayscale sang RGB. Vì vậy đây chưa phải so sánh nguyên trạng với đường color-crop của mentor. Nhận dạng thử0/180 độ bằng confidence của chính reader; không dùng GT chọn hướng.

## Kết luận trực tiếp từ lượt đầy đủ

Đây là so sánh mô tả trên mẫu đã khóa, trước khi suy rộng sang dữ liệu/camera khác. “Đúng trường” yêu cầu khớp toàn bộ chuỗi đã normalize, không phải chỉ đúng vài ký tự.

- **easyocr_en,91 ca ba góc:** raw 12.53%, support 16.70%, bbox 16.70%, parallelogram+5% 20.33%. Support − raw: +4.18 điểm%; support − parallelogram: -3.63 điểm%. Wall support/parallelogram: 15.341/11.810 giây/ảnh.
- **vietocr,91 ca ba góc:** raw 22.09%, support 27.69%, bbox 27.69%, parallelogram+5% 32.64%. Support − raw: +5.60 điểm%; support − parallelogram: -4.95 điểm%. Wall support/parallelogram: 16.248/12.762 giây/ảnh.

Trong kết quả này, support crop có cải thiện so với raw, nhưng baseline hình bình hành nới5% đọc đúng nhiều trường hơn và nhanh hơn support với cả hai reader trên nhóm ba góc. Mask không tăng field exact tổng so với crop bbox. Vì vậy chưa có bằng chứng về ưu thế OCR/CPU riêng của support mask để làm đóng góp thuật toán chính. Không được đổi cách chấm hay bỏ baseline đang thắng để tạo novelty.

Mức exact tuyệt đối còn thấp trên tập khó này và chưa đo semantic KIE; kết quả không chứng minh hệ thống tự điền thông tin hoặc duyệt eKYC đáng tin cậy trên mọi giấy tờ. Các tỷ lệ routing chỉ nói ảnh được đưa đi đọc, không xác thực danh tính.

## 141 ảnh chính: toàn bộ trường mục tiêu

Field exact tính cả trường bị bỏ sót/ảnh bị từ chối là sai. CER không bị chặn ở1. Cột có điều kiện chỉ tính trường trong các ảnh được route. “Có vùng” nghĩa là có ít nhất một vùng text dự đoán được ghép vào field; không phải AP detector chuẩn.

| Reader | Policy | Field exact (%) | CER micro | Có vùng (%) | Route (%) | Exact trong ca route (%) | Wall TB/P95 (s) | CPU TB (s) |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| easyocr_en | raw_fullframe | 13.30 | 0.691 | 55.68 | 100.00 | 13.30 | 13.030/24.531 | 25.642 |
| vietocr | raw_fullframe | 22.80 | 0.659 | 55.68 | 100.00 | 22.80 | 14.228/27.712 | 28.008 |
| easyocr_en | neural_strict | 8.86 | 0.815 | 28.52 | 35.46 | 25.36 | 4.740/18.657 | 9.373 |
| vietocr | neural_strict | 12.94 | 0.826 | 28.52 | 35.46 | 37.01 | 4.810/18.960 | 9.508 |
| easyocr_en | three_fullframe | 17.01 | 0.621 | 64.40 | 100.00 | 17.01 | 13.421/26.674 | 26.437 |
| vietocr | three_fullframe | 27.31 | 0.619 | 64.40 | 100.00 | 27.31 | 14.321/29.012 | 28.223 |
| easyocr_en | three_support | 19.73 | 0.591 | 69.34 | 100.00 | 19.73 | 14.484/33.357 | 28.529 |
| vietocr | three_support | 30.95 | 0.594 | 69.34 | 100.00 | 30.95 | 15.140/30.893 | 29.811 |
| easyocr_en | three_support_bbox | 19.73 | 0.589 | 69.41 | 100.00 | 19.73 | 14.479/30.840 | 28.533 |
| vietocr | three_support_bbox | 30.95 | 0.592 | 69.41 | 100.00 | 30.95 | 15.106/30.501 | 29.718 |
| easyocr_en | three_parallelogram05 | 22.09 | 0.581 | 72.62 | 100.00 | 22.09 | 12.205/28.946 | 24.081 |
| vietocr | three_parallelogram05 | 34.17 | 0.545 | 72.62 | 100.00 | 34.17 | 12.890/28.717 | 25.416 |

## 91 ca ba góc dự đoán

Field exact tính cả trường bị bỏ sót/ảnh bị từ chối là sai. CER không bị chặn ở1. Cột có điều kiện chỉ tính trường trong các ảnh được route. “Có vùng” nghĩa là có ít nhất một vùng text dự đoán được ghép vào field; không phải AP detector chuẩn.

| Reader | Policy | Field exact (%) | CER micro | Có vùng (%) | Route (%) | Exact trong ca route (%) | Wall TB/P95 (s) | CPU TB (s) |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| easyocr_en | raw_fullframe | 12.53 | 0.702 | 55.16 | 100.00 | 12.53 | 13.491/24.801 | 26.513 |
| vietocr | raw_fullframe | 22.09 | 0.682 | 55.16 | 100.00 | 22.09 | 14.777/28.511 | 29.071 |
| easyocr_en | neural_strict | 0.00 | 1.000 | 0.00 | 0.00 | — | 0.243/0.510 | 0.519 |
| vietocr | neural_strict | 0.00 | 1.000 | 0.00 | 0.00 | — | 0.243/0.510 | 0.519 |
| easyocr_en | three_fullframe | 12.53 | 0.702 | 55.16 | 100.00 | 12.53 | 13.693/25.103 | 26.961 |
| vietocr | three_fullframe | 22.09 | 0.682 | 55.16 | 100.00 | 22.09 | 14.979/28.814 | 29.518 |
| easyocr_en | three_support | 16.70 | 0.656 | 62.75 | 100.00 | 16.70 | 15.341/34.540 | 30.201 |
| vietocr | three_support | 27.69 | 0.644 | 62.75 | 100.00 | 27.69 | 16.248/32.420 | 31.978 |
| easyocr_en | three_support_bbox | 16.70 | 0.653 | 62.86 | 100.00 | 16.70 | 15.333/33.401 | 30.209 |
| vietocr | three_support_bbox | 27.69 | 0.640 | 62.86 | 100.00 | 27.69 | 16.196/32.549 | 31.836 |
| easyocr_en | three_parallelogram05 | 20.33 | 0.640 | 67.80 | 100.00 | 20.33 | 11.810/27.700 | 23.311 |
| vietocr | three_parallelogram05 | 32.64 | 0.568 | 67.80 | 100.00 | 32.64 | 12.762/26.629 | 25.170 |

## 20 ảnh ngoài

Field exact tính cả trường bị bỏ sót/ảnh bị từ chối là sai. CER không bị chặn ở1. Cột có điều kiện chỉ tính trường trong các ảnh được route. “Có vùng” nghĩa là có ít nhất một vùng text dự đoán được ghép vào field; không phải AP detector chuẩn.

| Reader | Policy | Field exact (%) | CER micro | Có vùng (%) | Route (%) | Exact trong ca route (%) | Wall TB/P95 (s) | CPU TB (s) |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| easyocr_en | raw_fullframe | 6.97 | 0.880 | 22.13 | 100.00 | 6.97 | 11.824/19.090 | 23.222 |
| vietocr | raw_fullframe | 7.79 | 0.873 | 22.13 | 100.00 | 7.79 | 13.770/22.465 | 27.048 |
| easyocr_en | neural_strict | 42.62 | 0.371 | 71.31 | 90.00 | 46.64 | 17.338/36.264 | 33.956 |
| vietocr | neural_strict | 42.21 | 0.523 | 71.31 | 90.00 | 46.19 | 20.578/45.266 | 40.347 |
| easyocr_en | three_fullframe | 43.03 | 0.362 | 72.95 | 95.00 | 45.06 | 17.822/36.260 | 34.916 |
| vietocr | three_fullframe | 42.21 | 0.514 | 72.95 | 95.00 | 44.21 | 21.144/45.266 | 41.462 |
| easyocr_en | three_support | 43.03 | 0.371 | 71.72 | 95.00 | 45.06 | 17.989/36.264 | 35.249 |
| vietocr | three_support | 42.62 | 0.523 | 71.72 | 95.00 | 44.64 | 21.321/45.268 | 41.818 |
| easyocr_en | three_support_bbox | 43.03 | 0.371 | 71.72 | 95.00 | 45.06 | 17.982/36.261 | 35.236 |
| vietocr | three_support_bbox | 42.62 | 0.523 | 71.72 | 95.00 | 44.64 | 21.300/45.266 | 41.777 |
| easyocr_en | three_parallelogram05 | 43.03 | 0.365 | 72.54 | 95.00 | 45.06 | 17.642/36.267 | 34.553 |
| vietocr | three_parallelogram05 | 42.21 | 0.517 | 72.54 | 95.00 | 44.21 | 20.992/45.266 | 41.162 |

## Chạy lặp và audit

- Tiến trình benchmark hoàn tất mã0; wall toàn bộ study 224.33 phút (không phải latency một ảnh/một reader). Không bỏ ca bất thường.
- Audit **225 checkpoint**, **2700 hàng ảnh-policy-reader**; chấm lại từ output private:0 sai khác, cộng stage timing:0 sai khác.
- Toàn bộ hàng công khai khớp projection checkpoint; tính lại **144** hàng summary và kiểm hash prediction. Audit phát hiện lỗi lưu/xuất/tổng hợp; evaluator vẫn dùng cùng thuật toán chấm.
- Panel32 so cùng ảnh-policy-reader trong ba lượt: **0** mismatch canonical prediction hash (text normalize, box làm tròn6 chữ số, không gồm confidence) và **0** mismatch score; không dùng cache OCR giữa các lượt.
- Có **225** lần localizer và **731** raster OCR thực sự khác nhau trong các đơn vị ảnh/lượt. Một OCR execution ở đây gồm một detector và tối đa hai reader; không được gọi số hàng kết quả là số inference độc lập.
- Raster giống hệt trong cùng ảnh/lượt được chia sẻ, và cùng chi phí stage được tính cho mỗi policy tương đương. Các reader chạy nối tiếp, được báo như hai lựa chọn reader riêng; không cộng thời gian hai reader để gọi là latency một reader.
- Batch VietOCR kiểm trên8 dòng tổng hợp: 0 khác text; confidence lệch tối đa 4.36e-07. Đây không phải chứng minh parity cho mọi ảnh.
- [Audit checkpoint](results/e2e_ocr_v2/audit.json), [repeat audit](results/e2e_ocr_v2/repeat_audit.json), [thống kê cùng panel](results/e2e_ocr_v2/matched_repeat_summary.json).

- Kiểm thử cuối: **134 Python**, **15 frontend** đều đạt. Bỏ riêng tests/test_manifest.py vì worktree không chứa manifest raw; nguồn ảnh benchmark đã được kiểm hash. Có một cảnh báo deprecation Starlette/httpx từ dependency sẵn có; không cài/thay dependency. [Validation](results/e2e_ocr_v2/validation.json), [Python log](results/e2e_ocr_v2/python_tests.txt), [frontend log](results/e2e_ocr_v2/frontend_tests.txt).

### Biến thiên thời gian trên cùng panel

Bảng này chỉ dùng28 ảnh chính của panel (24 ba góc +4 control) trong cả ba lượt; không lấy SD giữa tập161 và tập32. Mean ± SD là giữa ba trung bình lượt, không phải CI hay SD từng ảnh.

| Reader | Policy | Wall trung bình ± SD lượt (s/ảnh) | P95 trung bình ± SD lượt (s) |
|---|---|---:|---:|
| easyocr_en | raw_fullframe | 10.359 ± 3.207 | 19.340 ± 4.804 |
| easyocr_en | neural_strict | 1.726 ± 0.692 | 7.340 ± 2.967 |
| easyocr_en | three_fullframe | 10.705 ± 3.333 | 22.515 ± 7.475 |
| easyocr_en | three_support | 10.955 ± 3.156 | 23.324 ± 7.327 |
| easyocr_en | three_support_bbox | 11.074 ± 3.409 | 24.118 ± 9.108 |
| easyocr_en | three_parallelogram05 | 8.834 ± 2.687 | 20.040 ± 7.042 |
| vietocr | raw_fullframe | 10.864 ± 3.212 | 19.938 ± 7.354 |
| vietocr | neural_strict | 1.526 ± 0.560 | 6.928 ± 2.443 |
| vietocr | three_fullframe | 11.009 ± 3.242 | 20.730 ± 8.013 |
| vietocr | three_support | 11.568 ± 3.363 | 21.601 ± 7.931 |
| vietocr | three_support_bbox | 11.565 ± 3.406 | 21.444 ± 7.636 |
| vietocr | three_parallelogram05 | 9.328 ± 2.694 | 21.637 ± 8.534 |

Thời gian biến thiên rõ giữa các lượt dù output ổn định. Đây là desktop CPU dùng chung, model cùng resident và thứ tự policy cố định; chưa đối trọng thứ tự/cache/nhiệt độ. So sánh thời gian áp dụng cho cấu hình đo này, chưa chứng minh ưu thế throughput hoặc latency ổn định khi triển khai.

## Sai số và giới hạn ngôn ngữ

| Reader | Policy | Review hình học (ảnh) | Route nhưng không có text (ảnh) | Field không ghép được vùng | Field có vùng nhưng sai |
|---|---|---:|---:|---:|---:|
| easyocr_en | raw_fullframe | 0 | 2 | 810 | 630 |
| easyocr_en | neural_strict | 93 | 0 | 1070 | 345 |
| easyocr_en | three_fullframe | 1 | 2 | 564 | 736 |
| easyocr_en | three_support | 1 | 2 | 498 | 764 |
| easyocr_en | three_support_bbox | 1 | 2 | 497 | 765 |
| easyocr_en | three_parallelogram05 | 1 | 3 | 450 | 779 |
| vietocr | raw_fullframe | 0 | 2 | 810 | 495 |
| vietocr | neural_strict | 93 | 0 | 1070 | 289 |
| vietocr | three_fullframe | 1 | 2 | 564 | 594 |
| vietocr | three_support | 1 | 2 | 498 | 608 |
| vietocr | three_support_bbox | 1 | 2 | 497 | 609 |
| vietocr | three_parallelogram05 | 1 | 3 | 450 | 612 |

Đếm vùng OCR không ghép vào target không tương đương false-positive rate: dataset không gán nhãn mọi tiêu đề/nền. Phép chấm không chứng minh precision cho mọi text xuất ra.

- easyocr_en: 1522/1643 trường có toàn bộ ký tự tương thích alphabet sau normalization. Đây là điều kiện khả biểu diễn, không phải tỷ lệ đọc đúng.
- vietocr: 1542/1643 trường có toàn bộ ký tự tương thích alphabet sau normalization. Đây là điều kiện khả biểu diễn, không phải tỷ lệ đọc đúng.

Main target không bị thay sau khi xem kết quả. Subset alphabet chỉ là diagnostic để giải thích giới hạn reader; không thay bảng chính bằng subset dễ hơn. [Alphabet audit](results/e2e_ocr_v2/alphabet_coverage.json).

## Độ bất định và tỷ lệ xem xét

Bootstrap2.000 lần theo physical ID trên test seed13, chỉ lượt đầy đủ đầu tiên. Trung bình field trong ảnh rồi ảnh trong ID; mỗi ID có trọng số bằng nhau. Vì vậy delta này không nhất thiết bằng chênh lệch bảng pooled-field phía trên. Năm split ID có chồng lặp và panel lặp không phải thêm mẫu độc lập. Các CI là thăm dò, không chỉnh nhiều phép so sánh.

| Reader | Policy so với raw | Delta exact theo ID (điểm %) | CI95% (điểm %) |
|---|---|---:|---:|
| easyocr_en | neural_strict | -1.53 | [-7.87; 5.73] |
| easyocr_en | three_fullframe | 5.75 | [1.36; 11.56] |
| easyocr_en | three_support | 8.02 | [3.35; 13.40] |
| easyocr_en | three_support_bbox | 8.11 | [3.59; 13.69] |
| easyocr_en | three_parallelogram05 | 9.88 | [5.33; 15.27] |
| vietocr | neural_strict | -5.30 | [-11.02; 0.36] |
| vietocr | three_fullframe | 5.81 | [3.10; 9.01] |
| vietocr | three_support | 10.21 | [6.66; 13.76] |
| vietocr | three_support_bbox | 10.21 | [6.90; 13.49] |
| vietocr | three_parallelogram05 | 12.11 | [8.76; 15.79] |

### Kiểm tra cơ chế riêng trên nhóm ba góc

Các đối chiếu bổ sung được ghi trước khi xem accuracy trong [kế hoạch phân tích](E2E_ANALYSIS_PLAN.md). Đây là test IDs seed13 có ảnh thuộc nhóm ba góc, không phải toàn bộ91 ảnh. Dấu dương là policy lớn hơn control; với thời gian, số âm nghĩa là nhanh hơn. Không có điều chỉnh nhiều phép so sánh.

| Reader | Policy − control | Số ID exact/wall | Delta exact (điểm %) [CI95%] | Delta wall (s) [CI95%] |
|---|---|---:|---:|---:|
| easyocr_en | three_support − three_fullframe | 22/23 | 4.26 [1.40; 7.20] | 1.456 [-0.140; 3.242] |
| easyocr_en | three_support_bbox − three_fullframe | 22/23 | 4.39 [2.02; 7.02] | 1.485 [0.539; 2.383] |
| easyocr_en | three_parallelogram05 − three_fullframe | 22/23 | 7.98 [4.73; 11.27] | -1.796 [-3.107; -0.715] |
| easyocr_en | three_support − three_support_bbox | 22/23 | -0.13 [-1.06; 0.93] | -0.029 [-0.967; 1.125] |
| easyocr_en | three_support − three_parallelogram05 | 22/23 | -3.72 [-6.98; -0.49] | 3.252 [1.839; 4.924] |
| vietocr | three_support − three_fullframe | 22/23 | 8.81 [3.97; 14.32] | 1.333 [0.420; 2.261] |
| vietocr | three_support_bbox − three_fullframe | 22/23 | 8.81 [3.96; 14.00] | 1.322 [0.536; 2.069] |
| vietocr | three_parallelogram05 − three_fullframe | 22/23 | 12.62 [7.27; 18.42] | -1.687 [-2.680; -0.695] |
| vietocr | three_support − three_support_bbox | 22/23 | 0.00 [0.00; 0.00] | 0.011 [-0.484; 0.451] |
| vietocr | three_support − three_parallelogram05 | 22/23 | -3.81 [-8.54; 0.98] | 3.019 [2.339; 3.650] |

Accuracy chỉ có22 ID với target hợp lệ, còn latency giữ cả23 ID có ảnh ba góc thuộc split này; không loại ảnh không có target khỏi chi phí xử lý. CI VietOCR cho support − parallelogram còn bao gồm0, nên kết quả mô tả baseline tốt hơn không phải bằng chứng đã xác nhận ưu thế thống kê cho mọi quần thể.

Đã báo đủ đường cong confidence0/.25/.5/.75/.9/.95. Confidence là tín hiệu của model, không phải nhãn đúng; chưa chọn ngưỡng sản phẩm từ tập test. “Review proxy” gồm gate hình học/no-text/confidence thấp, không chứng minh khách hàng chắc chắn cần chụp lại. [Curves](results/e2e_ocr_v2/confidence_review_curves.json).

## Diễn giải để tiến tới paper

Đọc đồng thời field exact, CER, coverage và thời gian. Một policy từ chối nhiều có thể chạy nhanh nhưng đọc đúng ít thông tin hơn. Không dùng coverage đơn thuần, zero observed errors trên20 ảnh hay confidence cao để kết luận an toàn/novelty/đủ CORE B. Baseline raw, full-frame ba góc và parallelogram+nới5% đều được giữ.

Lịch sử pretrained training overlap chưa được giải quyết, chỉ20 ID ngoài và hai điều kiện chụp; đây chưa phải kết quả trên CCCD tiếng Việt thực tế, semantic KIE hay PAD. Mask/crop không sinh lại ký tự ngoài ảnh và không cấp phép chấp nhận giấy tờ thiếu thông tin bắt buộc trong eKYC.

Mọi số chính nằm trong [summary CSV](results/e2e_ocr_v2/summary.csv) và [per-image numeric rows](results/e2e_ocr_v2/per_image.jsonl.gz); text dự đoán chỉ ở cache cục bộ.

Biểu đồ: [field exact](results/e2e_ocr_v2/field_accuracy.png), [accuracy/latency](results/e2e_ocr_v2/accuracy_latency.png).
