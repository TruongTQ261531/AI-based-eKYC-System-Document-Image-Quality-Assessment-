# OCR tiếng Việt và chống giả qua màn hình — API 3.1.0

**Bản hiện tại 3.2.0** đã bổ sung CRAFT phát hiện chữ tổng quát, định vị vùng
thẻ và form động không bắt buộc 5 trường. Mô tả OCR/kiểm thử bên dưới là lịch
sử v3.1; xem [thay đổi và bằng chứng hiện tại](document_recovery_and_fields.md).

Cập nhật ngày 28/10/2026 trên project hiện có. Giữ FastAPI, `.venv`, weights
chất lượng/YuNet/SFace, 4 động tác và thời hạn 180 giây.

## OCR và tự động điền

`ekyc/scanocr.py` dùng detector ONNX từ
[phgrouptechs/scanocr-identity-vi](https://huggingface.co/phgrouptechs/scanocr-identity-vi),
revision `700b8c73e450668780af7b96d65ab88afc288e86`, và VietOCR `vgg_transformer`.
Detector xác định ID_Number, Full_Name, DOB, Gender, Address; VietOCR đọc chữ
có dấu từ các vùng này. Không đọc box bao toàn thẻ như một dòng chữ; không dùng
Hometown để tự điền địa chỉ thường trú.

Ảnh nắn/xoay từ bước chân dung được letterbox 640×640 (RGB 0–1), decode output
1×15×8400, NMS theo lớp; vùng chữ cắt từ ảnh nắn gốc. `module3_ocr.py` ghép dòng
theo vị trí, bỏ nhãn trường, giữ dấu tiếng Việt và số 0 đầu, chuẩn hóa ngày sinh.
Confidence nhận chữ <0,65, dữ liệu thiếu, sai định dạng hoặc mâu thuẫn để trống.
Số CMND/CCCD phải gồm 9/12 chữ số; không sửa O thành 0 hay đoán số thiếu.
Model tập trung giấy tờ Việt Nam, không cam kết OCR mọi loại giấy tờ quốc tế MIDV.

API `/api/document` trả `fields` để frontend tự điền 5 ô ngay khi xử lý xong ảnh
đã xác nhận. Người dùng vẫn sửa/xác nhận được. Không hardcode thông tin khách
hàng; `fields_verified=false`. Thiếu chân dung vẫn xem được form nhưng chưa
được sang đối chiếu selfie. Toàn bộ inference cục bộ, không tải weights hoặc
gửi ảnh qua mạng lúc xử lý. PyTorch nạp checkpoint bằng `weights_only=True`.

## Chống giả trước Module 5

`ekyc/presentation_attack.py` dùng MiniFASNetV2 (crop 2,7×) và MiniFASNetV1SE
(crop 4×) của Silent-Face-Anti-Spoofing, bản ONNX của
[yakhyo](https://github.com/yakhyo/face-anti-spoofing). YuNet hiện có tìm mặt.
Crop giữ bối cảnh quanh mặt, không căn chỉnh như SFace. Đúng contract của
weights này: BGR float32 **0–255**, 80×80; **class 1** là bona fide.
Hai file PAD được kiểm SHA-256 khi nạp.

Chính sách hiện tại, chưa hiệu chỉnh trên camera người dùng:

- Cả hai điểm bona fide ≥0,80: tiếp tục. Một điểm ≤0,20: `spoof_detected`,
  dừng ngay thử thách và xóa mẫu đối chiếu. Còn lại: chưa đủ bằng chứng,
  không cộng động tác hay cấp proof. Điểm model không phải xác suất đã hiệu chỉnh.
- Cuối thử thách cần ít nhất 6 frame liên tiếp qua PAD, cùng các kiểm tra
  cử động, nhiều mặt, mất mặt, đổi người, nonce/thứ tự và thời hạn hiện có.
- Ảnh cuối chạy PAD lại: nghi giả trả HTTP 403; chưa rõ trả HTTP 422.
  Cả hai hủy proof, UI xóa ảnh chờ và yêu cầu thử thách mới.
- Thiếu weights/lỗi model: HTTP 503 và hủy challenge, không gọi Module 5.
  Client không thể khai `pad=live` để bỏ qua kiểm tra.
- Module 5 giữ so khớp giấy tờ, các mẫu thử thách và ảnh cuối, ngưỡng SFace
  0,363. Chỉ được gọi khi cả cử động và PAD đã qua. `identity_verified=false`.

Đây là phát hiện dấu hiệu giả mạo từ RGB, không chứng thực camera vật lý.
Không bảo đảm phát hiện mọi màn hình, cuộc gọi, góc chụp/ánh sáng; camera giả
truyền pixel trực tiếp và deepfake vẫn là khoảng trống. Chưa đo APCER/BPCER
hoặc kiểm định PAD (`pad_certified=false`). Yêu cầu bảo đảm cao cần hệ thống
thu nhận được chứng thực, ví dụ chiều sâu/IR, hoặc PAD SDK được đánh giá trên
loại tấn công mục tiêu; browser RGB hiện tại không cung cấp bảo đảm đó.

## Tái lập môi trường có sẵn

Máy hiện tại đã có weights và 3 gói inference bổ sung. Không cần chạy lại setup.
Khi cần tái lập:

```powershell
.\.venv\Scripts\python.exe -m pip install --no-deps -r requirements-inference.txt
.\.venv\Scripts\python.exe -m scripts.setup_identity_models
```

Chỉ thêm ONNXRuntime 1.24.4, VietOCR 0.3.13, einops 0.2.0. Dùng `build_model`/
`translate`, không import Predictor tải online hoặc chức năng training; không
cài imgaug/albumentations/lmdb/gdown và không hạ Pillow theo training extras.
Torch, Torchvision, NumPy, Pillow, PyYAML và dependency ONNXRuntime đã có.
Nguồn/SHA-256 trong `models/identity_model_sources.json`, digest cố định trong
script setup. VietOCR khoảng 152 MB, ScanOCR 12 MB, hai PAD tổng 3,5 MB.
Model card ScanOCR ghi Apache-2.0, metadata ONNX vẫn ghi AGPL-3.0 của
Ultralytics; giữ thông tin nguồn này để rà soát khi phân phối.

## Bằng chứng kiểm thử

Kết quả cuối: **97 test Python, 13 test frontend qua**. Compileall qua.

- Unit/API: dấu, số 0, ngày sai, địa chỉ nhiều dòng, trường mâu thuẫn,
  confidence, NMS/letterbox; class/normalization PAD, thiếu/không rõ/giả mạo,
  client giả kết quả, lỗi model, kiểm tra lại ảnh cuối trước Module 5.
- Frontend: tự điền 5 trường, sửa/xác nhận, xóa dữ liệu lần quét trước,
  từ chối ở frame/ảnh cuối và không cho đối chiếu khi thiếu proof.
- `outputs/identity_models_smoke.json`: VietOCR thật đọc đúng 5/5 dòng tổng hợp;
  detector thật chạy đúng output và không phát hiện vùng trên ảnh trắng.
  PAD thật nhận `image_T1.jpg` của tác giả là live, `image_F1.jpg`/`image_F2.jpg`
  là spoof. API thật từ chối cả hai mẫu giả ở frame đầu, ảnh cuối bị chặn HTTP
  409. T1 chỉ ở bước căn chỉnh, không được coi là hoàn thành liveness.
  Phiên smoke được tạo giả lập để kiểm tra riêng PAD; không phải lượt đầy đủ
  OCR→CCCD→người thật. Không upload dữ liệu người dùng; chỉ lưu báo cáo/fixture test.

Chưa thử CCCD thật hoặc cuộc gọi Zalo/Messenger trên thiết bị người dùng.
Test cử động thành công dùng observation giả lập. Ba ảnh demo không phải
benchmark độ chính xác chống giả.

Thử thủ công: mở localhost, Ctrl+F5, chụp CCCD, kiểm tra 5 trường tự điền rồi
thử bằng mặt trực tiếp. Tạo lượt khác dùng ảnh/video và cuộc gọi trên điện thoại.
Nếu classifier phát hiện giả, UI phải từ chối ngay, không xuất hiện nút chụp
xác nhận. Ghi nhận cả bỏ sót lẫn từ chối nhầm theo camera/ánh sáng để đánh giá.
