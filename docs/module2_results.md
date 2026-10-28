# Kết quả đợt cải thiện Module 2 — 26/10/2026

**Đã cải thiện một số lỗi định vị và có bộ đo tái lập. Chưa thể kết luận Module 2 luôn tìm đúng giấy tờ trên ảnh thật.**

Code dùng trong ứng dụng: `ekyc/module2_homography.py`. Bản trước sửa: `outputs/module2_review/baseline_module2_homography.py`. Các file `Module2*.py` cũ ở thư mục gốc được giữ nguyên. Xem lý thuyết, luồng và lệnh chạy trong [module2_method.md](module2_method.md).

## 1. Đo trên ảnh biến đổi có góc chuẩn

| Bộ đo | Trước sửa | Sau sửa | Diễn giải |
|---|---:|---:|---|
| Synthetic validation: 40 ca, 8 giấy tờ | 38/40 đạt hình học | 39/40 | Sửa được một ca tối có góc xấp xỉ bị lệch vào trong |
| Synthetic test: 40 ca, 8 giấy tờ khác | 40/40 | 40/40 | Không giảm kết quả trên bộ kiểm tra nhỏ này; chưa chứng minh cải thiện trên camera thật |
| Hai đối chứng không có thẻ mỗi split | Từ chối cả hai | Từ chối cả hai | Chỉ gồm ảnh đồng màu và gradient; không đại diện mọi nền phức tạp |
| Nắn với góc chuẩn được cung cấp | Không chấm detector | 40/40 trả ảnh ở mỗi split | Xác nhận nhánh biến đổi chạy được; không phải chứng minh chữ được đọc đúng |

Tiêu chí: IoU vùng ≥0,90 và khoảng cách góc trung bình / đường chéo ảnh ≤0,03. Các biến thể gồm phối cảnh, tối, tương phản thấp, xoay 90° và lóa cục bộ. Ảnh gốc của hai split thuộc giấy tờ vật lý khác nhau, nhưng cùng cách sinh biến đổi; mức khái quát còn hạn chế.

Ca `doc47_low_contrast` ở validation vẫn cắt hụt dải dưới. Nó được giữ trong gallery và tính là thất bại. Không hạ tiêu chí để biến ca này thành đạt.

- [Validation report](../outputs/module2_review/val_final/report.md) · [gallery](../outputs/module2_review/val_final/gallery.html)
- [Test report](../outputs/module2_review/test_final/report.md) · [gallery](../outputs/module2_review/test_final/gallery.html)

## 2. Kiểm tra ảnh chụp thật

Chọn cố định 4 ảnh mỗi nhóm Clean/Blur/Cropped/Dark/Distorted cho từng split, cân bằng theo giấy tờ. Chạy trực tiếp Module 2, không chặn qua Module 1. Local chưa có nhãn góc chuẩn, nên **không báo accuracy trên ảnh thật**.

| Tập | Bản cũ trả tứ giác | Bản mới trả tứ giác | Chú ý |
|---|---:|---:|---|
| Real validation, 20 ảnh | 15/20 | 14/20 | Trả ít hơn không tự đồng nghĩa kém hơn; bản cũ có ca lấy khung nền |
| Real test, 20 ảnh | 12/20 | 11/20 | Bản mới từ chối cả 4 ảnh nhãn Cropped trong mẫu test; vẫn cần nhãn góc để chấm đúng/sai |

Quan sát trực tiếp ở các ảnh validation:

- `img_04257.jpg`: bản thử đầu tiên chọn khung chân dung trong thẻ; bản hiện tại chọn vùng toàn thẻ nhờ xét quan hệ bao chứa. Đây là lỗi được phát hiện và sửa sau khi unit test ban đầu đã pass.
- `img_15284.jpg`: ảnh tối; bản trước sửa từ chối, bản hiện tại tìm được đường bao thẻ, đã chạy CLI xuất ảnh nắn để xem.
- `img_19031.jpg`: bản trước sửa chọn một vùng nền bàn; bản mới từ chối, nhưng vẫn chưa tìm được thẻ đúng trong ảnh đó.
- `img_11572.jpg`: còn trường hợp chọn vùng nền thay vì thẻ. Thuật toán hình học chưa có bộ phân loại ngữ nghĩa giấy tờ; không được coi mọi tứ giác là đúng.

Đây là review định tính trên ảnh đã xem, không thay thế nhãn chuẩn độc lập.

- [Real validation gallery](../outputs/module2_review/real_val_final/gallery.html)
- [Real test gallery](../outputs/module2_review/real_test_final/gallery.html)
- [Ví dụ ảnh tối đã nắn](../outputs/module2_review/single_dark_example/rectified.png)

## 3. Chi phí xử lý

Thời gian median của riêng lời gọi Module 2, đã bao gồm diagnostics sau nắn, trên máy local trong lần đo:

| Bộ đo | Bản cũ | Bản mới |
|---|---:|---:|
| Synthetic validation | 68,4 ms | 82,8 ms |
| Synthetic test | 74,7 ms | 80,7 ms |
| Real validation | 68,4 ms | 139,8 ms |
| Real test | 66,8 ms | 122,9 ms |

Đã giảm thời gian so với bản thử đầu tiên bằng loại ứng viên trùng sớm, nhưng **bản mới vẫn chậm hơn bản cũ**, nhất là nền nhiều đường biên cần tinh chỉnh. Số này không gồm toàn bộ API/OCR và không phải benchmark tải đồng thời. Không tuyên bố tối ưu tốc độ tổng thể.

## 4. Kiểm thử phần mềm và ý nghĩa

`tests/test_module2.py` kiểm tra góc/matrix, dạng đứng, tỷ lệ được cung cấp, giữ màu/pixel nguồn, ảnh tối, phối cảnh, thẻ gần mép, thiếu cạnh và đầu vào suy biến. Có thêm hai ca hồi quy cho tinh chỉnh góc lệch vào trong và chọn toàn thẻ thay vì khung chân dung tương phản mạnh. Các test API/pipeline liên quan được chạy để kiểm tra tương thích.

Lần kiểm tra cuối: **59 passed**, gồm 35 ca Module 2 và 24 ca core/camera/quality/API liên quan. Có một cảnh báo deprecation của Starlette TestClient/httpx, không có test thất bại.

```powershell
.\.venv\Scripts\python.exe -u -m pytest tests/test_module2.py tests/test_core.py tests/test_camera_workflow.py tests/test_quality_feedback.py tests/test_api.py -q
```

Unit test pass chỉ xác nhận các điều kiện trong test; không chứng minh mọi ảnh thật được nhận đúng.

Đã chạy thêm [chẩn đoán OCR với nội dung biết trước](../outputs/module2_review/ocr_probe/report.md) bằng model English có sẵn, không tải model mới. Ba cảnh là chụp thẳng, phối cảnh, và phối cảnh tối; mỗi cảnh so sánh ảnh thô, bản nắn cũ và bản nắn mới.

| Cảnh | CER ảnh thô | CER sau nắn bản cũ | CER sau nắn bản mới |
|---|---:|---:|---:|
| Thẳng | 0% | 0% | 0% |
| Phối cảnh | 14,6% | 0% | 0% |
| Phối cảnh tối | 14,6% | 0% | 0% |

CER được tính trên chuỗi đã chuẩn hóa so với nội dung biết trước. Ảnh thô vẫn nhận đủ các từ trong ba cảnh; phần sai ở hai cảnh nghiêng chủ yếu do thứ tự ghép từ. Kết quả cho thấy nắn giúp thứ tự đọc trong ví dụ này, **không chứng minh bản mới OCR tốt hơn bản cũ**. Đây chỉ là ba cảnh chữ in giả lập, chưa đánh giá tiếng Việt có dấu hoặc OCR trên giấy tờ thật. Không dùng confidence OCR làm độ chính xác nhận dạng.

## 5. Phần chưa được giải quyết

1. Nhầm vùng khi nền phức tạp hoặc biên thẻ yếu; hiện vẫn có ví dụ thất bại.
2. Chưa biết giấy tờ có đủ nội dung cần thiết, chưa xác định hướng đọc chữ.
3. Chưa có ground truth góc và text độc lập cho ảnh camera thực để chấm accuracy và OCR end-to-end.
4. Không khôi phục vùng chữ đã mất do lóa, cắt hoặc nhòe nặng; chưa hỗ trợ giấy cong/méo ống kính.
5. Tăng độ chặt của bằng chứng biên có thể từ chối ảnh còn sử dụng được khi biên bị che; cần đo bằng nhãn thật trước khi tiếp tục nới hoặc thêm mô hình.

Module 1 và model OCR chưa được thay đổi trong đợt này. Bộ đo đã sẵn sàng để kiểm tra nâng cấp tiếp theo trên cùng input và tiêu chí.
