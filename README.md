# eKYC cục bộ: camera → giấy tờ → xác nhận thông tin → selfie

API **3.2.0** cải thiện chọn toàn vùng thẻ/góc bo tròn và đọc thông tin theo nội dung từng giấy tờ. Form chỉ hiện các mục đã đọc, có cả mã/lớp học sinh hoặc hạng bằng lái, cùng phần văn bản chưa phân loại. [Cách sửa và kiểm thử](docs/document_recovery_and_fields.md). Giữ FastAPI, `.venv`, 4 động tác/180 giây và PAD MiniFASNet; hệ thống không tự phê duyệt eKYC.

## Chạy

Để mở server trong cửa sổ PowerShell:

```powershell
.\start.ps1
```

Hoặc chạy `open-ekyc.ps1` để khởi động server ẩn ở localhost nếu cần rồi mở trình duyệt mặc định.

Mở http://127.0.0.1:8000 trên máy này. `start.ps1` dùng `.venv` sẵn có và kiểm tra cổng 8000; nếu eKYC đã chạy, script báo phiên bản và weights thay vì mở một server thứ hai. Nếu cổng đó bị ứng dụng khác dùng, dừng đúng ứng dụng đó hoặc đổi cổng. Không chạy `setup.ps1` cho thay đổi workflow này.

Nếu PowerShell báo không được phép chạy file `.ps1`, chỉ mở quyền trong cửa sổ hiện tại rồi chạy lại:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\start.ps1
```

Lệnh chạy trực tiếp không qua script:

```powershell
Set-Location D:\laptrinhcuatao\Ekyc
.\.venv\Scripts\python.exe -m uvicorn ekyc.api:app --host 127.0.0.1 --port 8000
```

1. Mở camera (ưu tiên camera sau), căn toàn bộ thẻ vào khung.
2. Chụp, xem lại và xác nhận. Có thể chụp lại trước khi gửi.
3. Module 1 kiểm tra chất lượng → Module 2 nắn phối cảnh → Module 3 OCR và lấy chân dung. Thất bại sẽ hiện nguyên nhân và hướng dẫn điều chỉnh.
4. Kiểm tra các mục đã đọc và phần toàn bộ văn bản OCR. Không ép mọi loại thẻ có cùng trường CCCD; các mục xuất hiện có thể sửa. Dữ liệu sửa được đánh dấu `user_confirmed`, không phải đã xác minh.
5. Mở camera trước và bấm **Bắt đầu kiểm tra cử động**. Làm 4 động tác theo thứ tự ngẫu nhiên trong tối đa 180 giây, nhìn thẳng lại sau mỗi động tác. Không có hạn riêng cho từng động tác. Trang hiển thị góc đầu, trạng thái hai mắt, ánh nhìn và chất lượng vùng mặt. Đạt thử thách thì chụp ảnh chân dung gốc, xem lại và xác nhận trong 45 giây. Module 5 so cả các mẫu thử thách và ảnh cuối với giấy tờ. Kết quả có `liveness_checked=true`, `liveness_passed=true`, `presentation_attack_detection=not_certified`; `identity_verified=false`.

`ImageCapture.takePhoto()` được ưu tiên để lấy ảnh độ phân giải cảm biến; fallback canvas dùng đúng `videoWidth × videoHeight`, không lấy kích thước CSS và không cắt theo khung hướng dẫn. Camera yêu cầu độ phân giải ưu tiên 2560×1440; độ phân giải thực tế tùy thiết bị. Giới hạn đầu vào: 30 MB và 32 megapixel.

Camera tắt khi chuyển bước/rời trang. UI xử lý từ chối quyền, thiếu camera, camera bận, cấu hình không hỗ trợ, môi trường không an toàn, mất kết nối và phiên hết hạn.

## Module 1: giảm loại nhầm và giải thích lỗi

Trong lần audit nền trước khi fine-tune, quy tắc quality cũ yêu cầu argmax = Clean và confidence Clean ≥ 0,60. Cả 50 ảnh tham chiếu bổ sung vào Clean bị quy tắc đó loại (45 Cropped, 5 Blur). Chỉ hạ ngưỡng Clean không sửa được vấn đề dự đoán sai lớp. Việc fine-tune và weights đang dùng được ghi ở phần training bên dưới.

Quy tắc mới `corroborated_defects_v2`:

Từ API 3.2, đây là đánh giá riêng từng ảnh; pipeline web vẫn thử cứu vùng thẻ trước khi từ chối vì Blur/Dark của toàn cảnh. Xem [quy tắc khôi phục và điều kiện còn phải chụp lại](docs/document_recovery_and_fields.md).

- Chặn sớm ảnh quá nhỏ, gần như không có chi tiết, quá tối; hoặc dự đoán Blur/Dark mạnh có phép đo ảnh xác nhận.
- Blur: confidence Blur ≥ 0,80 và phương sai Laplacian < 75 sau khi chuẩn hóa cạnh dài về tối đa 960 px.
- Dark: độ sáng trung bình < 25 và percentile 90 < 60; hoặc confidence Dark ≥ 0,80, trung bình < 55 và percentile 90 < 110.
- Ảnh gần đồng màu: độ lệch chuẩn grayscale < 3. Cạnh ngắn < 160 px không đủ đầu vào.
- Cropped/Distorted hoặc Clean confidence thấp không còn tự động chặn. Chúng được ghi là **nghi ngờ**, cần kiểm tra biên thẻ/OCR ở các bước tiếp theo.
- Ngưỡng 0,60 hiện dùng để đánh dấu độ chắc chắn của Clean, không còn là veto cho mọi ảnh.
- Không đọc được dòng OCR đáng tin cậy nào hoặc không tìm đủ biên thì yêu cầu chụp lại. Nếu OCR đọc được nhưng chưa tách được chân dung, vẫn hiện form và yêu cầu chụp lại trước khi sang bước selfie.

Các ngưỡng đo ảnh là heuristic, chưa hiệu chỉnh trên camera thực tế của khách hàng. Việc vượt Module 1 chỉ cho phép xử lý tiếp, không có nghĩa ảnh đạt chuẩn cuối cùng. Báo cáo `outputs/quality_audit.json` ghi so sánh trên 150 ảnh: 100 ảnh validation (20 mỗi lớp) và 50 tham chiếu. Đây là mẫu chẩn đoán, không phải benchmark độc lập vì nguồn training của checkpoint cũ chưa rõ.

`ekyc/feedback.py` cung cấp mã lỗi, mô tả, mức độ chắc chắn và hướng dẫn cụ thể. Ví dụ mờ → lau ống kính/giữ máy/chờ lấy nét; tối → tăng ánh sáng đều; chưa tìm biên → lùi máy/giữ cả bốn góc/nền tương phản; không đọc được OCR → chữ lớn hơn/tránh lóa. Không kết luận “bị cắt góc” chỉ vì contour không tìm được biên; không khẳng định có lóa khi chưa đo được.

## API và quyền riêng tư

| Endpoint | Chức năng |
|---|---|
| POST /api/document | Nhận ảnh camera qua trường multipart `card`; trả yêu cầu chụp lại hoặc form OCR và mã phiên |
| POST /api/verify | Alias giữ URL cũ, nay chỉ xử lý giấy tờ; không xử lý video |
| POST /api/confirm | Xác nhận form JSON, yêu cầu header `X-Session-Token` |
| POST /api/liveness/start | Khởi tạo thử thách ngẫu nhiên, cần form đã xác nhận |
| POST /api/liveness/frame | Khung hình camera qua trường `image`, nonce/thứ tự do server kiểm tra |
| DELETE /api/liveness | Hủy thử thách, giữ bước giấy tờ để thử lại |
| POST /api/selfie | Ảnh gốc qua trường `image`; cần form đã xác nhận và thử thách đạt chưa quá 45 giây |
| DELETE /api/session | Hủy phiên bằng mã phiên |
| GET /api/health | Trạng thái assets, API version và phương thức liveness; cần `face_landmarker.task` |
| GET /api/results/... | Đã đóng; luôn 404, không phục vụ PII cũ |

- Luồng camera không ghi ảnh, text OCR, thông tin đã sửa hay embedding thành tệp. Multipart được giới hạn và giữ trên RAM, không spool ảnh ra đĩa.
- Phiên chứa embedding và form trên RAM, hạn tối đa 10 phút; dọn nền mỗi 15 giây, kiểm tra expiry ngay khi truy cập. So khớp xong (kể cả không khớp) tiêu thụ phiên. Chụp lỗi selfie vẫn cho thử lại trong cùng phiên.
- Frame được gửi sau khi bấm bắt đầu thử thách, không ghi video/ảnh ra tệp. Thử thách tối đa 180 giây, 3 lần/phiên. Trình duyệt không tự gửi kết quả góc đầu/đã chớp mắt/đã đạt để server tin theo.
- Token chỉ nằm trong RAM của trang, không đưa vào URL/localStorage/cookie. Reset gửi yêu cầu xóa phiên. Khi rời trang, xóa là best-effort; TTL phía server vẫn áp dụng.
- Trả `Cache-Control: no-store`, CSP, no-referrer; chặn cross-origin và Host không được cấu hình. Lỗi validation không phản chiếu dữ liệu cá nhân; lỗi xử lý không trả đường dẫn nội bộ.
- Chạy một worker vì phiên/model ở RAM của tiến trình. Chưa triển khai đăng nhập hoặc khả năng vận hành công khai.
- Các artifact CLI cũ trong `outputs/` không bị xóa; API web không phục vụ chúng. Bộ nhớ RAM được giải phóng khi hết phiên, không cam kết xóa vật lý swap/crash dump của hệ điều hành.

## Điện thoại và HTTPS

`getUserMedia()` cần secure context. HTTP localhost dùng được trên chính máy đó; HTTP IP LAN của máy tính không phải secure context cho điện thoại.

Để chạy từ điện thoại, quản trị viên phải cấu hình hostname trong `EKYC_ALLOWED_HOSTS`, chứng chỉ HTTPS được thiết bị tin cậy, và reverse proxy/TLS phù hợp. Không bỏ qua cảnh báo chứng chỉ. Chỉ tin `X-Forwarded-Proto` từ reverse proxy đã kiểm soát. Mặc định `start.ps1` bind 127.0.0.1, không công khai mạng LAN.

Tài liệu: [getUserMedia](https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia), [ImageCapture.takePhoto](https://developer.mozilla.org/en-US/docs/Web/API/ImageCapture/takePhoto).

## Cấu trúc

- `web/index.html`, `web/app.js`, `web/style.css`: giao diện camera, review, form và selfie.
- `ekyc/api.py`: API, phiên, giới hạn upload và bảo vệ dữ liệu.
- `ekyc/pipeline.py`: tái sử dụng Module 1–3 và Module 5 cho camera.
- `ekyc/module1_quality.py`, `module2_homography.py`, `module3_ocr.py`, `module5_matching.py`, `faces.py`: xử lý model hiện có.
- `ekyc/module4_liveness.py`: giữ cho CLI nghiên cứu cũ, **không gọi trong luồng web mới**.
- `ekyc/face_observation.py`, `ekyc/live_challenge.py`: đo khuôn mặt bằng MediaPipe và quản lý thử thách chủ động cho web v3.
- `ekyc/feedback.py`: chẩn đoán và hướng dẫn khách hàng.
- `ekyc/document_portrait.py`: tìm chân dung theo hướng xoay/kích thước, không tra cứu dataset. Nếu thiếu chân dung nhưng OCR đọc được, vẫn hiển thị form; cần chụp lại giấy tờ trước khi selfie. [Chi tiết và giới hạn](docs/portrait_and_training.md).
- Các file `Module1.py`, `Module2*.py`, `Module3.py` cũ không bị ghi đè.

OCR dùng `ekyc/scanocr.py`: ScanOCR phát hiện vùng chuyên dụng, CRAFT có sẵn tìm chữ tổng quát, VietOCR đọc tiếng Việt. `ekyc/document_fields.py` trích thông tin để dựng form động; không dùng nhận dạng English của EasyOCR. `ekyc/presentation_attack.py` kiểm tra chống giả ở mỗi frame có mặt và ảnh cuối; thiếu kết quả không được chuyển sang Module 5. Xem [workflow giấy tờ](docs/document_recovery_and_fields.md) và [PAD](docs/ocr_and_pad.md).

## Dataset và training

Manifest `data/manifest.csv` gồm **21.050 TIFF gốc**: 9.050 Clean, 3.000 cho mỗi nhóm Blur/Cropped/Dark/Distorted. `data/midv2019_extra_clean.csv` là 50 tham chiếu MIDV2019 được bổ sung theo yêu cầu; 50 tham chiếu MIDV500 khác không đưa vào manifest. Không di chuyển hoặc nhân bản TIFF.

20.770 liên kết JPEG→TIFF khớp duy nhất theo thumbnail; 230 liên kết thuộc nhóm frame gần giống và cùng nhãn (`visual_equivalent_label`), không coi tên JPEG tương ứng là bằng chứng tuyệt đối. Báo cáo nằm trong `data/dataset_report.json`.

Tách theo 50 giấy tờ vật lý xuyên hai dataset: train 14.314, val 3.368, test 3.368. Ảnh tham chiếu cùng giấy tờ luôn cùng split. Gán nhãn Clean vào manifest không tự thay đổi weights.

```powershell
.\.venv\Scripts\python.exe -m ekyc.train_quality --epochs 15 --batch-size 32
```

Đã chạy `python -m ekyc.train_quality_transfer` trên TIFF gốc, fine-tune **classifier của MobileNet**, giữ backbone từ checkpoint có sẵn. 7 epoch; weights được chọn bằng validation và đã kích hoạt tại `models/quality_original_transfer.pth`. Đây không phải huấn luyện bộ định vị thẻ/khuôn mặt; nhãn hiện có chỉ phục vụ đánh giá chất lượng. Script `train_quality` ở trên là lựa chọn huấn luyện toàn mạng riêng, chưa chạy trong lần này.

Validation macro-F1: 0,9638 → 0,9662; 8 tham chiếu Clean validation: 0/8 → 8/8. Test mới macro-F1 0,9833, tham chiếu Clean 8/8. Checkpoint khởi tạo có lịch sử training chưa rõ nên **không coi đây là kết quả tổng quát hóa độc lập**, cũng không phải độ chính xác eKYC. Báo cáo: `outputs/training_original_transfer/training_report.json`; bản sao cạnh weights: `models/quality_original_transfer.report.json`. Dataset/manifest/cache không được tải khi xử lý camera.

CLI nghiên cứu cũ vẫn dùng được, nhưng `ekyc.cli`/`EKYCPipeline.run()` lưu ảnh/JSON ra outputs và có nhánh video/liveness heuristic riêng; không dùng chúng thay API camera.

## Kiểm thử

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
node --test tests/camera_frontend.test.cjs
.\.venv\Scripts\python.exe -m scripts.audit_quality
.\.venv\Scripts\python.exe -m scripts.smoke_identity_models
```

Frontend test dùng DOM/media/network giả lập; test chuỗi đạt dùng observation giả lập. Smoke mới dùng dòng chữ tổng hợp và 3 ảnh demo của tác giả PAD ở `outputs/pad_samples`; báo cáo `outputs/identity_models_smoke.json`. Chưa thử CCCD thật hoặc cuộc gọi Zalo/Messenger. Các script/report `smoke_camera_workflow` và `smoke_active_liveness` cũ dùng MIDV và OCR tiếng Anh, là kiểm thử phiên bản trước. [Giới hạn và bằng chứng hiện tại](docs/ocr_and_pad.md).

Ngưỡng SFace 0,363 là tham chiếu LFW, cần hiệu chỉnh cho ID/selfie. Nguồn: [OpenCV YuNet/SFace](https://docs.opencv.org/4.x/d0/dd4/tutorial_dnn_face.html), [EasyOCR](https://github.com/JaidedAI/EasyOCR).

## Module 2: cải thiện và đánh giá riêng

Luồng đang chạy dùng `ekyc/module2_homography.py`: thêm ứng viên biên/vùng, bằng chứng từng cạnh, tinh chỉnh góc và giảm chọn khung nhỏ bên trong giấy tờ. Ảnh nắn lấy pixel gốc; không tự làm sáng hoặc ép mọi loại giấy tờ về tỷ lệ CCCD. Bản mới vẫn có thể chọn sai vùng trên nền phức tạp và chạy chậm hơn bản cũ.

- [Phương pháp, luồng xử lý và cách chạy](docs/module2_method.md)
- [Kết quả trước–sau và lỗi còn tồn tại](docs/module2_results.md)
- `scripts/rectify_document.py`: chạy một ảnh riêng qua Module 2.
- `scripts/evaluate_module2.py`: so sánh baseline/current trên mẫu cố định, có chế độ đưa góc chuẩn để tách lỗi định vị khỏi lỗi nắn.

Các script chẩn đoán ghi ảnh ra thư mục output do người chạy chọn; khác với luồng web xử lý trên RAM.
