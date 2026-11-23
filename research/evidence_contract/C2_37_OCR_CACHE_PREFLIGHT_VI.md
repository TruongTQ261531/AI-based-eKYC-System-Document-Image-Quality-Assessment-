# C2-37 · Kiểm tra cache OCR trước phân tích

Ngày 23/11/2026 · Baseline `83f282c8667574eeb1735bbc5020e187ed1cee0a`

**Kết quả trong các nguồn đã kiểm là 0/37 ca, 0/18 giấy tờ có cặp before/after xác minh được cho cùng reader, checkpoint và cấu hình.** Có cache một phía (`CACHE_AVAILABLE_PARTIAL`). Trong 45 ảnh full-frame riêng biệt của panel, 13 ảnh có ít nhất một đầu ra xác minh được. Có 19 ca chỉ có phía after, 2 ca chỉ có phía before và 16 ca thiếu cả hai phía trong các nguồn đã xác minh. Các số này tính hợp qua reader để mô tả độ phủ, còn số cặp được tính trong từng cấu hình.

## Phạm vi và phương pháp chỉ đọc

Aggregate và verification private trùng byte với hai receipt công khai. SHA-256 queue khớp aggregate, đủ 37 candidate và 18 giấy tờ. Đối chiếu ảnh before với acquisition V2. Kiểm theo manifest và receipt của V2 r2, Source Visibility V3, Hard Pairs, Fair Controls, E2E OCR, Recovery V4, OCR Labels và các cache có cấu trúc của TASK5/smoke/stage pilot. Tìm theo SHA-256 byte ảnh, rồi xác minh nội dung đầu ra khớp digest đã ghi, signature, model/checkpoint và cấu hình của từng run tương ứng. Tên tệp hoặc pixel hash chỉ dùng làm đầu mối. Các bản chiếu điểm số, kết quả fusion và đặc trưng thị giác không được đếm thêm như lần đọc độc lập. Phạm vi kiểm là các kho và artifact đã biết trong workspace. [Receipt C2-37](human_gate/receipts/c2_37_20261123/verification.json)

## Kết quả theo cấu hình

Các hàng gộp dưới đây có cùng số đếm **cho từng reader/checkpoint hoặc policy được nêu**, mỗi cấu hình có mẫu số 37. “Đầu ra xác minh” đếm bản ghi trong mỗi cấu hình, gồm lượt lặp đã lưu. Nhiều candidate có thể dùng chung một ảnh.

| Reader và cấu hình lịch sử | BOTH_BOUND | BEFORE_ONLY | AFTER_ONLY | NEITHER | AMBIGUOUS | Ảnh riêng xác minh / đầu ra xác minh mỗi cấu hình |
|---|---:|---:|---:|---:|---:|---:|
| Vintern V2 r2 · original, v1, control và partial (mỗi seed riêng) | 0 | 0 | 19 | 18 | 0 | 11 / 11 |
| Vintern Source Visibility V3 · source, từng seed | 0 | 0 | 19 | 18 | 0 | 11 / 11 |
| Vintern Hard Pairs · uniform và hard, từng seed | 0 | 0 | 3 | 34 | 0 | 2 / 2 |
| Vintern Fair Controls · uniform, hard, random và repeat, từng seed | 0 | 0 | 3 | 34 | 0 | 2 / 2 |
| EasyOCR EN và VietOCR · E2E OCR v1, từng reader và policy | 0 | 1 | 0 | 36 | 0 | 1 / 1 |
| EasyOCR EN và VietOCR · E2E OCR v2, từng reader và policy | 0 | 2 | 0 | 35 | 0 | 2 / 4 |
| RapidOCR v4 · V2 r2 và Source Visibility V3, xét riêng từng run | 0 | 0 | 0 | 18 | 19 | 0 / 0 |
| RapidOCR Latin v5 · V2 r2 và Source Visibility V3, xét riêng từng run | 0 | 0 | 0 | 18 | 19 | 0 / 0 |
| RapidOCR v4, RapidOCR Latin v5 và Vintern partial_42 · cache raw có spec của TASK5, smoke và stage pilot, tại các kho có reader tương ứng | 0 | 0 | 0 | 37 | 0 | 0 / 0 |

Tổng **172 bản ghi đã xác minh** trong các cấu hình một phía ở bảng trên. Vintern khớp input, digest đầu ra, model SHA, signature và lock cấu hình. E2E khớp hash input trong manifest, signature có trọng số/cấu hình và digest đầu ra theo từng policy và lượt lặp. Với RapidOCR V2 r2/V3, xác nhận được byte ảnh after và đầu ra đã lưu. Tổ hợp artifact đã kiểm chưa ràng buộc được checkpoint/runtime chính xác với từng output theo tiêu chí này, nên provenance là `UNKNOWN`. Các postprocessor V3 cùng dùng một đầu ra OCR nên không nhân số lần đọc. Recovery V4, OCR Labels và cache dự đoán OCR legacy được rà trong phạm vi trên chưa bổ sung cặp có căn cứ.

## Bàn giao qua GitHub

ChatGPT có thể tiếp tục xây logic ghép cặp và xử lý thiếu dữ liệu trên fixture, rà claim-to-evidence và viết phần giới hạn cho bài Research Paper. Để phân tích C2-37 thực tế, cần tìm hoặc tạo hợp lệ đầu ra còn thiếu trên cùng ảnh byte và cùng phiên bản reader, với digest checkpoint/config, cùng chứng cứ truth độc lập và reference được duyệt trước khi tính endpoint dựa trên truth. Dùng mẫu số 37 ca / 18 cụm và báo thiếu dữ liệu theo protocol. [Protocol C2-37](C2_37_ANALYSIS_PROTOCOL_VI.md)

`CAN_RUN_PROSPECTIVE = BLOCKED`. `GO_PREPARATORY_ONLY`, `NO_GO_SUPERIORITY`, P5B `INFEASIBLE`, TASK 6B/7B `BLOCKED`. D10 của C2-37 giữ `REVIEW_ACCESS_PENDING`, `RETENTION_PENDING`, `RELEASE_PENDING`. [Hồ sơ D10](C2_37_D10_VI.md)
