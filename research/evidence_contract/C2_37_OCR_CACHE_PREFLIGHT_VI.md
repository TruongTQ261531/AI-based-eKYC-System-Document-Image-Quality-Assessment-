# C2-37 · Kiểm tra cache OCR trước phân tích

Ngày 23/11/2026 · Baseline `83f282c8667574eeb1735bbc5020e187ed1cee0a`

Kiểm tra lại ngày 23/11/2026 từ commit báo cáo `8ab565712022f30bc98d8db0d46cfb1dc96e618b`.

**Kết quả trong các nguồn đã kiểm là 0/37 ca, 0/18 giấy tờ có cặp before/after xác minh được cho cùng reader, checkpoint và cấu hình.** Có cache một phía (`CACHE_AVAILABLE_PARTIAL`). Trong 45 ảnh full-frame riêng biệt của panel, 13 ảnh có ít nhất một đầu ra xác minh được. Có 19 ca chỉ có phía after, 2 ca chỉ có phía before và 16 ca thiếu cả hai phía trong các nguồn đã xác minh. Các số này tính hợp qua reader để mô tả độ phủ, còn số cặp được tính trong từng cấu hình.

## Phạm vi và phương pháp chỉ đọc

Aggregate và verification private trùng byte với hai receipt công khai. SHA-256 queue khớp aggregate, đủ 37 candidate và 18 giấy tờ. Đối chiếu ảnh before với acquisition V2. Kiểm theo manifest và receipt của V2 r2, Source Visibility V3, Hard Pairs, Fair Controls, E2E OCR, Recovery V4, OCR Labels và các cache có cấu trúc của TASK5/smoke/stage pilot. Tìm theo SHA-256 byte ảnh, rồi xác minh nội dung đầu ra khớp digest đã ghi, signature, model/checkpoint và cấu hình của từng run tương ứng. Tên tệp hoặc pixel hash chỉ dùng làm đầu mối. Các bản chiếu điểm số, kết quả fusion và đặc trưng thị giác không được đếm thêm như lần đọc độc lập. Phạm vi kiểm là các kho và artifact đã biết trong workspace. [Receipt C2-37](human_gate/receipts/c2_37_20261123/verification.json)

- **Ảnh trước tiền xử lý.** Đọc lại và băm byte của 18 ảnh before và 27 ảnh after trong mỗi workspace, đối chiếu với queue. Hai tập SHA-256 rời nhau. Đối chiếu thêm byte tệp nguồn lịch sử cho các bản ghi được chấp nhận. Riêng E2E lưu physical ID theo quy ước khác. Đã nối qua UID MIDV-2020 trong manifest và kiểm lại byte ảnh. SHA-256 tệp ảnh xác định ảnh nguồn trước decode/preprocess. Profile và raster đầu vào sau biến đổi được xử lý theo provenance riêng của từng pipeline.
- **Reader, phiên bản và checkpoint.** Tính lại bốn signature Vintern từ code và manifest, kiểm hash các lock với receipt công bố. Kiểm trọng số Vintern nền bằng SHA-256 và 13 tệp code/cấu hình/tokenizer đi kèm bằng Git blob ID tại revision đã ghim. Đối chiếu 13 adapter có digest riêng và cấu hình adapter với biên nhận checkpoint. Với E2E, tính lại signature của manifest gồm phiên bản thư viện, code, reader, cấu hình và policy. Sáu tệp nguồn mô hình/cấu hình trong manifest khớp hash byte. Hai phiên bản E2E được xét riêng.
- **Cache đã lưu.** So UID, SHA-256 ảnh, reader/model, signature, profile và digest đầu ra với manifest thích hợp. Với Vintern, digest tính trên text đầu ra đã lưu. Với E2E, digest tính trên biểu diễn chuẩn hóa của text và box, kèm khóa lượt lặp, reader, policy và raster. Quét lại hash full-frame và pixel trong các kho cache JSON/JSONL đã biết. DocAligner có khớp byte ảnh nhưng lưu kết quả định vị. Cache feature Vintern có mục khớp byte và profile ngoài tập có đầu ra OCR đã xác minh. Các mục này không bổ sung cặp OCR.

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

Tổng **172 bản ghi cache đã xác minh** gồm **112 bản ghi Vintern và 60 dòng E2E theo policy**. Trong 112 bản ghi Vintern, 12 bản ghi tái sử dụng có thể nối về bản gốc bằng byte ảnh, digest checkpoint và digest đầu ra. Còn 100 bản ghi nguồn của các chuỗi tái sử dụng đã kiểm. Với E2E, 12 dòng v1 và 48 dòng v2 quy về lần lượt 4 và 16 khóa lịch sử theo UID, lượt lặp, reader và raster vì nhiều policy cùng dùng output trên cùng raster. Chỉ dùng các số này để mô tả cấu trúc cache. Đơn vị phân tích của C2-37 vẫn là candidate ghép cặp trong cụm giấy tờ.

Với RapidOCR, đã đối chiếu byte ảnh after và digest đầu ra hậu xử lý của 22 bản ghi V2 r2 và 66 bản ghi V3. Hai lock khớp hash mã CPU. Bộ cài RapidOCR và recognizer Latin trên máy cũng khớp receipt Recovery V4. Các bản ghi CPU V2 r2/V3 thiếu chứng cứ gắn đúng runtime và trọng số nhận dạng với từng lần đọc lịch sử. Các dòng hậu xử lý của V3 còn dùng chung raw OCR. Vì vậy giữ `UNKNOWN` cho provenance ở mức từng output và `AMBIGUOUS` cho 19 ca tương ứng ở mỗi reader. Recovery V4, OCR Labels và cache dự đoán OCR legacy trong phạm vi rà soát chưa bổ sung cặp có căn cứ.

## Bàn giao qua GitHub

ChatGPT có thể tiếp tục xây logic ghép cặp và xử lý thiếu dữ liệu trên fixture, rà claim-to-evidence và viết phần giới hạn cho bài Research Paper. Để phân tích C2-37 thực tế, cần tìm hoặc tạo hợp lệ đầu ra còn thiếu trên cùng ảnh byte và cùng phiên bản reader, với digest checkpoint/config, cùng chứng cứ truth độc lập và reference được duyệt trước khi tính endpoint dựa trên truth. Dùng mẫu số 37 ca / 18 cụm và báo thiếu dữ liệu theo protocol. [Protocol C2-37](C2_37_ANALYSIS_PROTOCOL_VI.md)

`CAN_RUN_PROSPECTIVE = BLOCKED`. `GO_PREPARATORY_ONLY`, `NO_GO_SUPERIORITY`, P5B `INFEASIBLE`, TASK 6B/7B `BLOCKED`. D10 của C2-37 giữ `REVIEW_ACCESS_PENDING`, `RETENTION_PENDING`, `RELEASE_PENDING`. [Hồ sơ D10](C2_37_D10_VI.md)
