# Module 2: tìm giấy tờ và nắn phối cảnh

Phiên bản làm việc ngày 26/10/2026. Phạm vi: Module 2 và công cụ đo riêng, không huấn luyện lại Module 1, không thay model OCR hoặc thêm chức năng sinh trắc khác.

## 1. Mục tiêu và giới hạn

Chấp nhận ảnh giấy tờ có phối cảnh, tối hoặc tương phản thấp nếu vẫn quan sát được biên và còn thông tin hữu ích. Có tứ giác và xuất được ảnh không đồng nghĩa đã nhận đúng giấy tờ. Module 3 và kiểm tra nội dung sau nắn vẫn cần thiết.

Module 2 gồm hai bài toán riêng:

1. **Định vị:** tìm đúng bốn góc của toàn bộ giấy tờ, tránh chọn chân dung, ô chữ hoặc vật nền.
2. **Nắn ảnh:** chuyển bốn góc đó thành bốn góc hình chữ nhật bằng homography.

Khi cung cấp bốn góc đúng và nắn thành công nhưng chế độ tự tìm góc thất bại, cần sửa định vị trước. Nắn thành công chưa chứng minh chữ rõ: thông tin đã mất vì lóa trắng, nhòe nặng, bị che hoặc bị cắt không được khôi phục bởi phép biến đổi hình học.

## 2. Nguyên lý homography

Với một bề mặt giấy tờ gần phẳng, ánh xạ giữa ảnh chụp và hình chữ nhật đích có thể biểu diễn bằng ma trận 3×3 H:

```text
s [u, v, 1]^T = H [x, y, 1]^T
```

`(x,y)` là pixel trong ảnh gốc, `(u,v)` là vị trí sau nắn; chia hai tọa độ đầu cho tọa độ thứ ba. Bốn cặp điểm nguồn–đích xác định phép biến đổi khi hình học không suy biến. Code dùng `cv2.getPerspectiveTransform` và `cv2.warpPerspective`, nội suy tuyến tính từ pixel nguồn.

**Tỷ lệ vật lý không tự suy ra chính xác từ bốn cạnh trong ảnh xiên.** Khi chưa biết loại giấy tờ, kích thước đầu ra được ước lượng từ độ dài cạnh nhìn thấy và ghi `aspect_ratio_source=edge_estimate`. Nếu biết tỷ lệ rộng/cao theo thứ tự góc hình học, có thể cung cấp `aspect_ratio`; code không mặc định ép mọi giấy tờ về tỷ lệ CCCD. Giấy tờ dạng đứng được giữ nếu hình học đầu vào là dạng đứng.

Thứ tự góc gần trên-trái → theo vòng quanh tứ giác chỉ xác định hướng hình học. Nó không chứng minh văn bản đã xoay đúng chiều đọc; kết quả luôn ghi `reading_direction_unverified`.

Tài liệu: [OpenCV geometric transformations](https://docs.opencv.org/4.x/da/d54/group__imgproc__transform.html), [OpenCV homography](https://docs.opencv.org/4.x/d9/d0c/group__calib3d.html).

## 3. Luồng xử lý hiện tại

```text
Ảnh BGR gốc
  → kiểm tra dữ liệu đầu vào
  → tạo bản phân tích có cạnh dài tối đa 1200 px
  → grayscale + CLAHE để hỗ trợ tìm biên
  → Canny nhiều ngưỡng và vùng nhị phân Otsu
  → tìm đường bao / convex hull → ứng viên tứ giác
  → loại ứng viên trùng và hình học suy biến
  → đo bằng chứng từng cạnh + tương phản qua biên
  → tinh chỉnh cạnh yếu bằng các pixel biên gần đó nếu đủ bằng chứng
  → xếp hạng; giảm ưu tiên khung nhỏ nằm trong vùng lớn hơn hợp lệ
  → đổi tọa độ về ảnh gốc
  → homography, nắn trực tiếp pixel gốc
  → ảnh + ma trận + tọa độ + thông số chẩn đoán
```

CLAHE và nhị phân chỉ dùng để tìm giấy tờ. Ảnh trả về không bị tự làm sáng, đổi màu hoặc tăng nét. Điều này giữ được phép so sánh tác động hình học và tránh tạo cảm giác đã khôi phục chữ mất.

## 4. Những thay đổi so với bản ban đầu

| Thay đổi | Lý do |
|---|---|
| Đánh giá bốn cạnh riêng | Điểm trung bình cao của ba cạnh không được che việc thiếu hẳn cạnh thứ tư |
| Thêm Canny ngưỡng thấp và ứng viên vùng Otsu | Có thêm cơ hội tìm biên tối/tương phản thấp; không loại ảnh chỉ vì nhãn Dark/Distorted |
| Loại ứng viên trùng trước kiểm tra hình học | Giảm tính lặp trên cùng một đường bao |
| Tinh chỉnh đường cạnh và giao điểm | `approxPolyDP` có thể cắt vào góc bo tròn, làm điểm góc lệch vào trong dù biên thật còn rõ |
| Ưu tiên biên bao ngoài đủ điều kiện | Giảm chọn nhầm khung chân dung bên trong thẻ |
| Hỗ trợ thẻ chiếm gần toàn khung | Bỏ giới hạn cũ 95% diện tích; vẫn không dùng mép ảnh làm bằng chứng cạnh thẻ |
| Kiểm tra input/góc và ma trận | Dữ liệu sai, NaN, điểm trùng, tứ giác mỏng suy biến trả `StageError` thay vì lỗi mơ hồ |
| Diagnostics sau nắn | Có độ sáng, độ nét, tương phản, vùng sáng cao; các số này không tự quyết định OCR thành công |

## 5. Các quy tắc hiện là heuristic

- Diện tích ứng viên: 6%–99,5% khung phân tích. Thẻ nhỏ hơn ngưỡng vẫn có thể bị bỏ sót.
- Bằng chứng cạnh: mỗi cạnh ≥0,45 và trung bình ≥0,65. Đây là phần điểm lấy mẫu gần biên ảnh, không phải xác suất đúng giấy tờ.
- Tinh chỉnh chỉ tìm trong dải hẹp 4–14 pixel trên bản phân tích, yêu cầu pixel biên thật rồi fit đường thẳng. Không dựng một cạnh mất hoàn toàn.
- Xếp hạng kết hợp hỗ trợ cạnh, diện tích và tương phản. Khung nằm ≥95% trong một ứng viên lớn gấp ≥1,8 lần, có điểm thô gần nhau, bị giảm 0,15 điểm để ưu tiên vùng bao ngoài.
- Cảnh báo cạnh tranh khi có vùng khác biệt (IoU <0,8) và chênh điểm <0,05.
- Cạnh ngắn đầu ra cần ≥80 px; cạnh dài tối đa 1600 px. Không phóng to để giả tạo độ phân giải.

Các ngưỡng này chưa được hiệu chỉnh trên tập ảnh camera khách hàng. Detector hình học vẫn có thể chọn khung nền hoặc bỏ sót thẻ có biên đứt. `requires_review=true` cho kết quả tự tìm góc; giữ tương thích API hiện tại, không gọi score là confidence xác minh.

## 6. Cách đánh giá và chạy lại

Bản gốc được lưu tại `outputs/module2_review/baseline_module2_homography.py` để đối chiếu. Script đánh giá bỏ qua Module 1 chỉ trong thí nghiệm; luồng ứng dụng vẫn gọi Module 1 như cũ.

```powershell
# Ảnh biến đổi có bốn góc biết trước, tập phát triển.
.\.venv\Scripts\python.exe scripts/evaluate_module2.py --mode synthetic --split val --baseline outputs/module2_review/baseline_module2_homography.py --output outputs/module2_review/val_final --visuals 5 --oracle

# Tập kiểm tra có giấy tờ vật lý khác tập phát triển.
.\.venv\Scripts\python.exe scripts/evaluate_module2.py --mode synthetic --split test --baseline outputs/module2_review/baseline_module2_homography.py --output outputs/module2_review/test_final --visuals 5 --oracle

# Ảnh chụp thật: chưa có ground truth local, chỉ chẩn đoán và review trực quan.
.\.venv\Scripts\python.exe scripts/evaluate_module2.py --mode real --split test --per-label 4 --baseline outputs/module2_review/baseline_module2_homography.py --output outputs/module2_review/real_test_final --visuals -1
```

Synthetic dùng ảnh tham chiếu giấy tờ với các biến đổi cố định: phối cảnh, tối, giảm tương phản, xoay 90°, lóa cục bộ; thêm hai đối chứng không có giấy tờ. Không phải ảnh camera mới hay benchmark lóa toàn diện. Tiêu chí chẩn đoán hình học: IoU ≥0,90 và sai số góc trung bình chuẩn hóa theo đường chéo ảnh ≤0,03. Hướng xoay không được đánh giá bởi hai chỉ số này.

`--oracle` đưa góc chuẩn vào nhánh nắn riêng để kiểm tra phép biến đổi; không cộng kết quả đó vào độ chính xác detector. Với ảnh thật, có thể bổ sung `--annotations corners.json` dạng đường dẫn ảnh → bốn tọa độ pixel gốc. Chưa có nhãn góc thì không báo accuracy.

Mỗi report ghi seed, danh sách ảnh, hash input, hash code và phiên bản runtime. `gallery.html` cho xem vùng tìm được cùng ảnh nắn. Chạy lại cùng output sẽ ghi đè report; dùng output mới nếu muốn giữ lần chạy trước.

Để thử riêng một ảnh của bạn, chọn thư mục output chưa tồn tại:

```powershell
.\.venv\Scripts\python.exe scripts/rectify_document.py --image "duong_dan_anh.jpg" --output outputs/thu_module2_01
```

Lệnh ghi `overlay.jpg`, `rectified.png` và `result.json`. Đây là artifact nghiên cứu có chứa giấy tờ; luồng web vẫn xử lý trên RAM như trước.

## 7. Kết quả và việc còn thiếu

Kết quả tổng hợp và các lỗi còn thấy được ghi ở [module2_results.md](module2_results.md). Không dùng số test unit pass hay số ảnh trả về để kết luận hệ thống đã nhận đúng giấy tờ.

Chưa tự nhận diện loại giấy tờ, chưa xác định chiều đọc bằng nội dung, chưa sửa méo ống kính/giấy cong, chưa phục hồi chữ mất do lóa. Các nội dung này không được coi là đã hoàn thành trong bản sửa hiện tại.
