# Tiến độ bốn ưu tiên: đối chiếu với bằng chứng

Bản cập nhật ngày 2026-11-03. Đây là chẩn đoán hậu nghiệm từ train/development; không huấn luyện lại hoặc sửa các kết quả đã công bố.

| Ưu tiên | Đã thực hiện | Còn thiếu |
|---|---|---|
| 1. Nhãn OCR | R2/V3 có transcript tác giả/giả lập, vị trí và trạng thái hiển thị theo hình học; train 128 ID/640 slot mỗi arm, dev 24 ID/72 ảnh, test 48 ID/144 ảnh | Chưa có người gán nhãn legibility độc lập; chưa có bộ camera Việt Nam mới. Clean/Blur không được dùng thay transcript |
| 2. Ảnh vào VLM | Bốn profile raw2/raw4/rect2/rect4 trên cùng 16 ảnh từ 8 ID development; chọn rect2 trước train/test; có probe backward 2/4 tile và đo suy luận từ pixel | Probe ngắn không phải full training mọi profile; VRAM allocated không phải tổng VRAM vật lý; camera quần thể mới chưa kiểm chứng |
| 3. Hai lỗi đối nghịch | Huấn luyện complete/partial hai seed; thêm source supervision hai seed. Bổ sung kiểm kê lỗi dev và danh sách ca train khó trong cập nhật này | Danh sách ca khó chưa được dùng huấn luyện; chưa có kết quả test mới cho một can thiệp hard mining |
| 4. Đối chứng | R2/V3 cùng 128 ID, 640 slot, 320 update, 1280 lượt ảnh/arm, hai seed; test mới so với V1; giữ nguyên V1 | V1 là transfer baseline khác budget, không phải đối chứng nhân quả. Test R2/V3 đã mở; mọi sửa phương pháp sau đây cần test mới khác |

## Vì sao thời gian lượt hoàn tất ngắn

Sáu run đã có đủ checkpoint trước lượt chốt. Tổng bộ đếm wall ở update cuối của sáu run: 100.15 phút. Số này không gồm chuẩn bị feature, development, benchmark, audit và chờ tiến trình; không phải tổng thời gian GPU hoạt động. Một lượt benchmark V1 còn chứa 5 giờ 20 phút máy sleep do pin, có nhật ký riêng. Không quy toàn bộ thời gian treo máy thành thời gian huấn luyện.

| Run | Update | Lượt ảnh | Wall update cuối (phút) | Peak allocated GiB |
|---|---:|---:|---:|---:|
| train_control_31415 | 320 | 1280 | 15.10 | 2.802 |
| train_control_42 | 320 | 1280 | 15.02 | 2.802 |
| train_partial_31415 | 320 | 1280 | 17.84 | 2.802 |
| train_partial_42 | 320 | 1280 | 15.03 | 2.801 |
| train_source_31415 | 320 | 1280 | 18.92 | 2.802 |
| train_source_42 | 320 | 1280 | 18.24 | 2.801 |

## Thử ảnh đầu vào đã chạy

| Profile | F1 development panel | Thời gian trung bình từ pixel (s) |
|---|---:|---:|
| raw2 | 0.1633 | 17.04 |
| raw4 | 0.1951 | 17.90 |
| rect2 | 0.2176 | 16.85 |
| rect4 | 0.1801 | 17.57 |

Chọn rect2 trên development. Backward smoke probe: raw2 2.625 GiB; raw4 3.508 GiB allocated. Đây là bốn bước với ảnh smoke riêng, không phải bốn full training run.

## Hai nhóm lỗi trên development

Cạnh vùng thiếu: khoảng cách hai bounding box tối đa 8% đường chéo ảnh; chỉ xét thân chữ còn nguyên và có nguồn hỗ trợ. Đây là quy tắc chẩn đoán hình học, không phải nhãn đọc được của người. Key còn nguồn MRZ không bị gọi là vắng chỉ vì ô thân thẻ bị che.

| Model | Ảnh dev | Output key mất toàn bộ nguồn khai báo | Bỏ sót key rõ cạnh vùng thiếu | Sai key rõ cạnh vùng thiếu |
|---|---:|---:|---:|---:|
| control_42 | 72 | 119 | 16 | 31 |
| partial_42 | 72 | 53 | 16 | 30 |
| source_42 | 72 | 59 | 16 | 30 |
| control_31415 | 72 | 122 | 13 | 41 |
| partial_31415 | 72 | 54 | 20 | 27 |
| source_31415 | 72 | 54 | 20 | 26 |

Đã chọn 32 ca train từ 32 ID, mỗi ID tối đa một ca, để có cả phần bị che/cắt và phần thân chữ rõ bên cạnh. Loại lỗi được lấy từ model partial_42 đã chọn bằng dev. Không đưa ID development vào train, không mở output test để chọn ca. Danh sách/đáp án riêng ở cache local; public chỉ có số lượng và hash. Đây mới là inventory; không tính thành lần train, ảnh mới hay cải tiến test.

## Kiểm thử bản cập nhật

278 kiểm tra Python và 1496 subtest đã qua. Môi trường chính qua 274 bài và bỏ qua 4 bài cần training cache; chạy riêng cả 4 bằng overlay có sẵn đều qua. Frontend: 48 bài qua, gồm mentor và các bản nghiên cứu. Test camera/network là mô phỏng, không phải benchmark người dùng thật.

Lần chạy bị giới hạn quyền local đã kẹt trong Windows socketpair. Bản wrapper chẩn đoán đầu thiếu đường dẫn repository khi import; lần sửa wrapper xác nhận chỗ chờ socket. Bộ test chạy lại với quyền local đã qua; không sửa runtime để né lỗi. Các nhật ký thất bại/gián đoạn được giữ trong cache và băm trong [verification.json](results/current_progress/verification.json).

## Bước còn dang dở

Thiết kế và đăng ký vòng huấn luyện dùng ca khó, tạo đối chứng cùng exposure, chuẩn bị một tập test chưa từng dùng để điều chỉnh phương pháp, rồi mới huấn luyện/chấm và báo cáo tất cả seed. Người đánh giá và bộ camera mới hiện chưa có; không thay bằng nhãn do model tự viết. Không gọi bốn ưu tiên là hoàn tất hoàn toàn hoặc khẳng định đạt CORE B.

Bằng chứng máy đọc: [progress.json](results/current_progress/progress.json). Kết quả benchmark cũ: [V3](V3_RESULTS_VI.md), [R2](V2_RESULTS_VI.md).
