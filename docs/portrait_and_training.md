# Chân dung giấy tờ và vai trò dataset

Tài liệu này ghi kết quả ở bản v2.1. Web hiện tại đã chuyển sang v3 với thử thách
cử động bắt buộc trước selfie; xem [kiểm tra liveness hiện tại](active_liveness.md).
Các số đo và smoke thành công bên dưới là kết quả lịch sử của v2.1. Từ v3,
ảnh selfie đơn chưa qua thử thách bị chặn HTTP 409.

Luồng camera không tìm ảnh gần nhất trong dataset, không tra cứu CCCD/người trong
manifest và không yêu cầu giấy tờ đã xuất hiện trong dữ liệu. Module 1 suy luận từ
weights MobileNet; Module 2 tìm biên trên ảnh mới; Module 3 OCR và tìm vùng chân dung
trên chính ảnh giấy tờ; Module 5 chỉ so embedding chân dung này với selfie của phiên.

`data/manifest.csv` dùng cho chuẩn bị dữ liệu, training và đánh giá offline.
50 tham chiếu MIDV2019 bổ sung vẫn được gán Clean; cùng giấy tờ luôn cùng split.
Không dùng validation/test để cập nhật gradient. Nhãn hiện có là năm loại chất
lượng, không phải tọa độ thẻ/khuôn mặt hay nhãn danh tính cho huấn luyện biometric.

## Bản sửa chân dung

- `ekyc/document_portrait.py`: YuNet ở 4 hướng xoay; xếp hướng theo độ tin cậy,
  kiểm tra landmark, cần cùng vùng được tìm thấy trong ít nhất 2/3 lượt
  (cạnh dài 1280, 800, 1600). Lượt cuối dùng CLAHE chỉ để dò mặt.
- Crop/alignment/embedding lấy từ pixel gốc của ảnh nắn; không dùng ảnh CLAHE
  hoặc crop suy đoán theo mẫu CCCD. OCR nhận ảnh đã xoay cùng hướng chân dung.
- Ảnh bảo an/ảnh lặp được chấp nhận nếu embedding SFace tương đồng với chân dung
  chính. Nhiều mặt chưa xác định cùng người thì báo `id_face_ambiguous`.
- Selfie vẫn yêu cầu đúng một mặt. Không thêm tuyên bố liveness.
- Nếu OCR đọc được nhưng thiếu chân dung: vẫn trả form `status=review`, kèm
  `portrait_status=unavailable`, `can_match_selfie=false` và hướng dẫn.
  Cả `/api/confirm` và `/api/selfie` từ chối HTTP 409 nếu thiếu ID embedding.
  Nút chụp lại giấy tờ xóa phiên và thông tin cũ rồi OCR lại ảnh mới.

Thông báo lỗi mô tả phần xử lý chưa làm được, không khẳng định giấy tờ giả,
không hợp lệ hoặc khách hàng chụp sai. Screenshot lỗi không chứa ảnh giấy tờ
gốc, nên chưa tái hiện được chính trường hợp camera của người dùng.

## Đánh giá bộ dò

Lệnh: `.\.venv\Scripts\python.exe -m scripts.audit_portrait`.
Báo cáo đầy đủ: `outputs/portrait_audit.json`.

16 tham chiếu thuộc validation/test, mỗi ảnh xoay 4 hướng: cũ tìm được 22/64,
mới tìm được 56/64. 56 trường hợp mới chọn hướng bù đúng về hướng tham chiếu ban đầu.
Đây là độ phủ phát hiện trên 64 biến thể tương quan, không phải 64 giấy tờ độc lập
và không phải độ chính xác định danh. Hai ảnh tổng hợp không có mặt đều bị từ chối.

40 frame chụp trong các điều kiện khác nhau: 28 dừng ở tìm biên Module 2;
12 đến bộ dò chân dung, cả hai bản tìm được 7/12. Bản mới báo một trường hợp
đa chân dung chưa rõ. Không có nhãn bounding box/identity để khẳng định mọi phát
hiện là đúng. Bộ dò mới chưa giải quyết được toàn bộ ảnh nhỏ/mờ/lóa.

Smoke fixture cũ `TS04_20.tif` hiện dừng với `document_corners_not_found`;
đây là hạn chế hiện có ở Module 2, không được coi là test toàn luồng thành công.
Module 2 không bị sửa trong thay đổi này. Smoke khác chỉ chứng minh luồng API
với fixture được ghi rõ trong báo cáo, không dùng thay một đánh giá tổng thể.

Kiểm thử cuối: 66 test Python và 7 test frontend qua. Smoke với
`27_hrv_passport/images/KS/KS27_30.tif` và weights mới đi qua review →
selfie_required → matched, xóa phiên và không tạo tệp PII. Hook Python `open`
chặn đọc dataset/manifest trong lúc chạy API không bị kích hoạt. Báo cáo:
`outputs/portrait_workflow_smoke.json`. Đầu vào selfie là crop từ ảnh giấy tờ,
**không phải selfie người thật**, không chứng minh khả năng biometric hoặc liveness.

Chạy lại smoke này:

```powershell
.\.venv\Scripts\python.exe -m scripts.smoke_camera_workflow --card full_dataset_original/midv500_dataset/27_hrv_passport/images/KS/KS27_30.tif --output outputs/portrait_workflow_smoke.json
```

## Huấn luyện chất lượng

`python -m ekyc.train_quality_transfer`: đọc TIFF gốc theo manifest, lấy đặc trưng
MobileNet từ checkpoint có sẵn và fine-tune classifier; backbone giữ cố định.
Train 14.314 ảnh, validation 3.368, test 3.368. 50 tham chiếu bổ sung phân bố
34/8/8 theo split; thêm 68 biến thể sáng nhẹ của **34 ảnh train**. Tham chiếu
train được tăng trọng số lấy mẫu để học miền ảnh trước đây bị nhầm.

Chọn checkpoint bằng validation, chỉ đánh giá test sau chọn. Điều kiện kích hoạt
định trước: macro-F1 validation không giảm quá 0,02 và recall Clean trên tham chiếu
validation tăng. `outputs/training_original_transfer/training_report.json` ghi
kết quả thực tế, hash checkpoint và hạn chế. Nguồn training checkpoint cũ không
rõ, có thể đã thấy giấy tờ test; số đo không phải đánh giá tổng quát hóa độc lập.
Cache đặc trưng và manifest chỉ phục vụ training, không được ứng dụng camera tải.

Lần chạy 26/10/2026 hoàn tất 7 epoch, 775,4 giây. Validation macro-F1
0,963759 → 0,966234; tham chiếu Clean validation 0/8 → 8/8. Test mới macro-F1
0,983284; tham chiếu Clean test 8/8. Đã kích hoạt
`models/quality_original_transfer.pth`, SHA256
`b364dd329c472ca104602a7cc09d1b4e5454d3ee6cdf89313144704232a98d8f`.
Bản gốc `best_mobilenet_diqa_local.pth` được giữ nguyên. Script training chỉ tạo
candidate trong outputs; việc kích hoạt lần này thực hiện sau khi kiểm tra báo cáo
validation và hash. Không tự động nạp weights đang được training vào server.
