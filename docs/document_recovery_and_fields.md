# Khôi phục vùng thẻ và thông tin theo nội dung — API 3.2.0

Thay đổi trực tiếp frontend/backend ngày 28/10/2026. Không thêm dependency,
weights hay môi trường cho đợt này.

## Lỗi tái hiện từ screenshot

Vùng camera trong screenshot được người dùng cung cấp đã qua Module 1.
Module 2 cũ chọn tứ giác phía trong, cắt hụt phần trên/phải của thẻ; ScanOCR
chuyên vùng chỉ trả 2 trường đáng tin cậy. Screenshot không chứa thông báo lỗi,
nên đây là lỗi định vị đã tái hiện, chưa chứng minh nguyên nhân duy nhất của
lần từ chối trên ảnh cảm biến gốc (1280×720).

## Cách sửa

- Dùng class bao toàn thẻ trong ScanOCR làm gợi ý vùng, không dùng nó làm
  dữ liệu định danh. Candidate biên phải phủ gần trọn vùng này; không chọn
  khung chữ/chân dung mạnh hơn nhưng nhỏ hơn ở bên trong.
- Thêm candidate hình chữ nhật bao contour có độ chữ nhật cao để xử lý góc
  bo tròn. Vẫn cần bằng chứng bốn cạnh; test thiếu cạnh/tràn khung giữ nguyên.
- Khi chưa đủ bằng chứng bốn góc nhưng model định vị được thẻ: giữ crop có
  lề thay vì loại ngay hoặc giả nhận đã nắn đúng phối cảnh. Metadata ghi
  `detected_region_crop` và `perspective_not_verified_region_preserved`.
- Quality trên toàn khung cảnh không còn chặn sớm ảnh Blur/Dark có thể cứu.
  Trừ ảnh gần đồng màu/đen hoặc quá nhỏ, thử định vị/nắn, kiểm tra vùng thẻ và
  OCR trước. Nếu đọc được, trả review; nếu OCR vẫn thất bại, dùng quality của
  vùng thẻ để giải thích lỗi. Không cam kết khôi phục chữ đã mất hoặc lóa trắng.
- Khi không định vị được: thử đọc chữ toàn ảnh để người dùng xem/sửa, nhưng
  **không trích mặt ngoài thẻ làm chân dung giấy tờ**. Nhánh này không đủ điều
  kiện so selfie dù OCR có đọc được chữ.

## OCR và form nhiều loại giấy tờ

VietOCR vẫn là bộ đọc tiếng Việt. Ngoài vùng chuyên dụng của ScanOCR, dùng
CRAFT có sẵn để tìm dòng chữ tổng quát (EasyOCR chỉ phát hiện chữ, không dùng
bộ nhận dạng tiếng Anh). Không tải weights khi xử lý yêu cầu.

`ekyc/document_fields.py` đọc nhãn/giá trị, hỗ trợ nhãn Việt/Anh, nhiều dòng,
số có số 0 đầu và số chữ kết hợp. Các mục có thể gồm họ tên, số giấy tờ, ngày
sinh, quốc tịch, quê quán, địa chỉ, ngày cấp/hết hạn, mã học sinh, lớp, niên khóa,
trường, hạng bằng lái. Nhãn khác dạng `Nhãn: giá trị` được giữ thành mục bổ sung;
dòng chưa phân loại vẫn xuất hiện trong phần toàn bộ văn bản OCR.

Không có danh sách trường bắt buộc theo mẫu CCCD. Thẻ học sinh không bị yêu
cầu có số CCCD, giới tính hay địa chỉ. Kiểu giấy tờ chỉ là gợi ý theo nội dung
OCR, không phải xác minh mẫu/độ thật của giấy tờ. Kết quả OCR vẫn có thể sai.

API trả `document_fields`, `document_type`, `additional_fields`, `ocr_text`.
Năm key cũ trong `fields` còn để tương thích API; UI chỉ hiện mục có giá trị.
Các mục bổ sung cũng được sửa/xác nhận. Server chỉ nhận sửa các key đã đọc
trong phiên, giới hạn số lượng/độ dài; không để client tự khai kết quả xác minh.
Không có ảnh chân dung thì vẫn xem được OCR nhưng cần giấy tờ có ảnh để so mặt.

## Kết quả thực tế

Kiểm tra cuối: **110 test Python và 15 test frontend qua**, compileall qua.

`outputs/document_regression.json` chứa tên key, độ dài và số lượng; không chứa
ảnh hay giá trị OCR cá nhân. Chạy weights thật:

| Ca | Định vị | OCR trả review | Thông tin xuất hiện |
|---|---|---|---|
| Vùng camera từ screenshot người dùng, xử lý trực tiếp | Contour có gợi ý vùng | Có, có chân dung | 7 mục: tên, số giấy tờ, ngày sinh, giới tính, địa chỉ, quốc tịch, quê quán |
| Cùng vùng ảnh, mã hóa JPEG 95 rồi gửi localhost thật | Contour có gợi ý vùng | HTTP 200, confirm HTTP 200 | 6 mục: 5 mục chính và quốc tịch; quê quán chưa được gán sau nén JPEG |
| Thẻ học sinh tổng hợp | Contour | Có | Tên, mã học sinh, lớp, niên khóa |
| Bằng lái tổng hợp | Contour | Có | Tên, số giấy tờ chữ/số, hạng, ngày cấp, hạn dùng |

Thời gian trên lần đo này: lượt đầu có nạp model khoảng 22 giây; bằng lái
khoảng 12 giây; screenshot khoảng 9 giây. Không phải benchmark tải.
Hai thẻ tổng hợp không có ảnh chân dung, không dùng để kết luận độ chính xác
trên giấy tờ thật. Có 6/7 mục không có nghĩa mọi ký tự đều đúng; số mục khác
nhau sau nén cho thấy OCR vẫn nhạy với chất lượng ảnh. Cần người dùng rà nội
dung trên ảnh cảm biến gốc. Lượt HTTP xác nhận vẫn yêu cầu liveness, đã xóa
phiên kiểm thử và không lưu giá trị OCR/ảnh. Server đang phục vụ API 3.2.0.

```powershell
.\.venv\Scripts\python.exe -m pytest -q
node --test tests/camera_frontend.test.cjs
.\.venv\Scripts\python.exe -m scripts.regression_document_workflow
```

Script regression chỉ tạo thẻ tổng hợp trên RAM, báo cáo không lưu dữ liệu
cá nhân. Tùy chọn `--image`/`--camera-rect X1 Y1 X2 Y2` dùng để đọc một ảnh
được người dùng cung cấp trên RAM. Không upload ra dịch vụ ngoài.

Module 4/5 giữ kiểm tra chống giả, 4 động tác/180 giây và so khớp cùng người.
Giới hạn chống màn hình/deepfake của [bản PAD](ocr_and_pad.md) vẫn áp dụng.
