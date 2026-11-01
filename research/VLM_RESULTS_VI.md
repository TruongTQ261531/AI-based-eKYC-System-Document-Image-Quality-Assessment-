# Fine-tune Vintern local: kết quả thực tế

Thử nghiệm LoRA trên SPECIMEN tổng hợp, tách khỏi V4 và bản mentor. Fine-tune mô hình có sẵn không tự tạo novelty hay bảo đảm CORE B.

Chọn **seed_42** trên development, trước test; cổng development đạt: **True**. Không đổi lựa chọn theo test/đối chứng.

## Dữ liệu và khóa trước test

720 ảnh/144 mock physical IDs: train480/96IDs, development80/16, calibration40/8, test120/24. Calibration chưa dùng. Tách theo ID và checksum ảnh; cùng generator, hai bố cục/hai font giữa các tập. GT giữ cặp nhãn–giá trị còn đủ trong raster và bỏ trường che kín. Đây là proxy hình học tổng hợp, không phải nhãn legibility từ người chấm. Chưa có ảnh camera mới hoặc held-out-layout.

Đợt LoRA này không train trên ảnh full_dataset_original. Manifest local có21,050 dòng với nhãn chất lượng; thư mục gốc có21,100 TIF và không có annotation JSON/XML. Nhãn Clean/Blur không thay thế bản chép từng trường cho OCR. Kiểm kê: input_scope.json.

Mọi VLM dùng cùng preprocessing: giữ tỷ lệ, pad896×448 và chia2tile448; không dùng dynamic thumbnail mặc định của tác giả. Đây là cấu hình đầu vào giới hạn của đợt thử, không phải kết luận về toàn bộ năng lực model gốc. OCR CPU giữ cấu hình triển khai sẵn có.

Baseline OCR là RapidOCR/recognizer Latin PP-OCRv5 và spatial KIE của web nghiên cứu V4 ở8001; không phải mọi hệ OCR trên thị trường hoặc model ScanOCR của bản mentor. Giữ cả raw-layout và policy web đã frozen.

Corpus dùng10 nhóm trường canonical trên ba họ giấy tờ giả lập. Đây là adaptation KIE, không phải kiểm chứng OCR toàn văn hoặc mọi nhãn/trường mới ngoài schema. Một phần lợi ích có thể đến từ định dạng, nhãn và bố cục đã gặp trong generator.

Commit khóa trước test: `10268e47bbb25a536f51d2aa7ac71753762f0d8b`. Hai seed chính và một đối chứng:192 optimizer steps,768 presentations/lượt. Đối chứng chỉ full/corner_clip/blur_glare:288ảnh, cùng96IDs; chính480ảnh. Khớp compute và identities, không khớp số raster/epoch. Đối chứng phát sinh từ development, đã khai báo trước test.

## Test chính

| Phương án | Đúng/reference | Precision | Recall | F1 strict | F1 bỏ fence/null | Đúng định dạng | Xuất trường che kín |
|---|---:|---:|---:|---:|---:|---:|---:|
|OCR raw + layout (CPU)|396/483|0.7984|0.8199|0.8090|—|dict sẵn|11|
|OCR web V4 nghiên cứu (CPU)|396/483|0.7984|0.8199|0.8090|—|dict sẵn|11|
|Vintern gốc|113/483|0.3520|0.2340|0.2811|0.5583|0.2750|19|
|LoRA seed42|474/483|0.9713|0.9814|0.9763|0.9773|1.0000|3|
|LoRA seed31415|472/483|0.9752|0.9772|0.9762|0.9762|1.0000|0|
|LoRA đủ nội dung (đối chứng)|452/483|0.8417|0.9358|0.8863|0.9067|0.9167|43|

Đúng theo cặp khóa–giá trị; ngày/giới tính canonicalization giống nhau, vẫn lưu literal exact. Định dạng extraction strict không phải chỉ JSON syntax: null/bool/nested/fence đều bị từ chối. Parser phụ bỏ một fence toàn bộ và null/empty; không sửa giá trị/ánh xạ bằng GT. OCR trả dict sẵn nên không dùng làm đối chứng formatting sinh. Extra keys có thể có giá trị còn thấy nhưng nhãn bị cắt; không tự coi tất cả là hallucination. Trường bị che kín được đếm riêng.

Strict đếm key của trường che kín kể cả khi giá trị là chuỗi rỗng. Parser phụ bỏ null/empty như abstention. Do đó đếm key strict không đồng nghĩa mọi key đều mang giá trị bịa hoặc không rỗng.

| VLM | Object parse được | Fence | Null/empty | Literal đúng | Extra | Missing | Key che kín strict / parser phụ |
|---|---:|---:|---:|---:|---:|---:|---:|
|Vintern gốc|120/120|85|62|112|192|354|19 / 60|
|LoRA seed42|120/120|0|1|474|7|2|3 / 2|
|LoRA seed31415|120/120|0|0|472|4|3|0 / 0|
|LoRA đủ nội dung (đối chứng)|110/120|0|23|452|76|22|43 / 26|

## Từng điều kiện chụp (F1 strict)

| Phương án | full | corner_clip | field_clip | blur_glare | value_mask |
|---|---:|---:|---:|---:|---:|
|OCR raw + layout (CPU)|0.8083|0.8083|0.8571|0.7950|0.7788|
|OCR web V4 nghiên cứu (CPU)|0.8083|0.8083|0.8571|0.7950|0.7788|
|Vintern gốc|0.2604|0.2706|0.3333|0.2809|0.2595|
|LoRA seed42|0.9833|1.0000|0.9595|0.9833|0.9126|
|LoRA seed31415|0.9791|1.0000|0.9595|0.9707|0.9505|
|LoRA đủ nội dung (đối chứng)|0.9617|1.0000|0.8214|0.9617|0.5211|

Mỗi cột có24 ảnh của cùng24 IDs, không phải120 giấy tờ độc lập.

## Khoảng tin cậy và kiểm tra lặp

| So sánh | Chênh lệch F1 | CI95 |
|---|---:|---:|
|LoRA seed42 − Vintern gốc|0.6952|[0.6103, 0.8053]|
|LoRA seed42 − OCR web V4 nghiên cứu (CPU)|0.1673|[0.0740, 0.2597]|
|LoRA seed42 − LoRA đủ nội dung (đối chứng)|0.0900|[0.0558, 0.1292]|
|LoRA seed31415 − Vintern gốc|0.6951|[0.6045, 0.7978]|
|LoRA seed31415 − OCR web V4 nghiên cứu (CPU)|0.1672|[0.0830, 0.2589]|
|LoRA seed31415 − LoRA đủ nội dung (đối chứng)|0.0899|[0.0560, 0.1302]|

Bootstrap ghép cặp2000 lần theo24 physical IDs, giữ5biến thể cùng ID đi chung. Exploratory, chưa điều chỉnh nhiều phép thử. Hai seed không phải hai corpus độc lập.

Replay: 672 hàng VLM chính, 224 đối chứng, 400 OCR; 48 nhóm, mỗi nhóm3 lần suy luận. Rerun là panel12ảnh ×2 sau test120, không phải3 bộ120ảnh. Không sai khác score/hash. Audit số từ output đã lưu, không phải xác nhận độc lập của người.

Phân loại lỗi đọc sai/bỏ sót/định dạng và trường che/cắt/không in được lưu số trong `error_taxonomy.json`; không công bố giá trị cá nhân.

## Thời gian, bộ nhớ

| Phương án | p50/p95 giây (cached vision) | p50/p95 giây (fresh ảnh+vision+sinh) |
|---|---:|---:|
|Vintern gốc|6.25 / 8.03|6.04 / 8.04|
|LoRA seed42|4.54 / 5.08|4.56 / 4.92|
|LoRA seed31415|4.54 / 5.08|4.32 / 5.03|
|LoRA đủ nội dung (đối chứng)|4.70 / 5.31|chưa đo fresh riêng|
|OCR raw + layout (CPU)|—|0.59 / 0.71 CPU, decode ngoài timer|
|OCR web V4 nghiên cứu (CPU)|—|0.66 / 0.75 CPU, decode ngoài timer|

Fresh-online:72 lần (12ảnh ×3mô hình ×2thứ tự), luôn tính mới vision; 0 khác output cache. Gồm hash/decode/preprocess/vision/generation, model resident; loại HTTP/camera/cold-load. CPU OCR và GPU VLM là cấu hình triển khai khác nhau, không phải benchmark cùng backend. Số token sinh khác nhau giữa các phương án; chênh thời gian không chứng minh kernel hay tốc độ mỗi token được cải tiến.

| Train | Step chọn | Dev token loss | Optimizer invocation(s) | Feature setup(s) | Peak allocated VRAM(GiB) | Peak process RSS(GiB) |
|---|---:|---:|---:|---:|---:|---:|
|LoRA seed42|0192|0.010142|554.34|115.43|2.560|5.883|
|LoRA seed31415|0192|0.011925|566.22|0.35|2.560|5.883|
|LoRA đủ nội dung (đối chứng)|0048|0.110094|3320.82|0.35|2.559|6.112|

Lưu ý LoRA đủ nội dung (đối chứng): khoảng không tăng step >120s: `[{"after_step": 140, "before_step": 141, "seconds": 2708.1448808999266}]`. Thời gian invocation giữ nguyên; chưa xác định nguyên nhân khoảng dừng, không diễn giải nó là tốc độ GPU.

Kiểm kê bổ sung sau khóa, không đổi lựa chọn model:

- LoRA seed42: checkpoint đã nhận768 presentations, 480 raster riêng, 96/96 ID của pool. Không gọi các checkpoint là khớp effective training exposure.
- LoRA seed31415: checkpoint đã nhận768 presentations, 480 raster riêng, 96/96 ID của pool. Không gọi các checkpoint là khớp effective training exposure.
- LoRA đủ nội dung (đối chứng): checkpoint đã nhận192 presentations, 192 raster riêng, 91/96 ID của pool. Không gọi các checkpoint là khớp effective training exposure.

RAM16GB, RTX3050 Laptop6GB. Base938,193,024tham số, trainable1,081,344; BF16 LoRA r8/alpha16, không phải QLoRA. Frozen vision/projector/baseLM. Trace lưu cả allocated/reserved VRAM; RSS gồm load, không phải tổng RAM máy. Tải/chuẩn bị nhiềuGB tách thời gian optimizer. Checkpoint được chọn có4×step presentations; đối chứng được giữ sớm hơn theo cùng quy tắc development.

GPU smoke:20 bước +resume10 bước; 192tensor thay đổi; maxabs resume/continuous=0.0. Lỗi logger sau4bước đầu và Host ở fixture TestClient được giữ trong lịch sử, đã sửa/kiểm tra lại.

## Triển khai và giới hạn

Web LoRA opt-in: http://127.0.0.1:8002/ . Camera xử lý trong bộ nhớ, tính mới vision; không tra dataset/GT, không lưu ảnh/text, không gọi API ngoài. Demo lấy ảnh train để thử UI, không là accuracy test. Không phê duyệt danh tính hoặc tuyên bố liveness/PAD qua thí nghiệm OCR.

Adapter xuất riêng khoảng4.35MB, cần full Vintern đúng revision/loader gắn language_model. Weights/checkpoints/corpus/raw output ở ignored cache/data, không đưa Git. Python OCR gốc giữ nguyên, CUDA runtime ở cache riêng.

Kết quả xác nhận adaptation trên corpus tổng hợp nhỏ cùng họ bố cục/font. LoRA và synthetic masking là kỹ thuật có sẵn, chưa đủ kết luận thuật toán mới/CORE B. Cần ảnh chụp vật lý khác thiết bị/bố cục, nhãn legibility từ người chấm, closest-prior comparison và phân tích lỗi độc lập trước claim rộng.
