# Lấy mẫu IFV trước khi có nhãn người

Pha đọc ảnh dùng toàn bộ **31 ảnh duy nhất và 86 ô trường** của panel development đã tồn tại. Mỗi ảnh có xác suất đưa vào phiếu bằng 1. Thứ tự trộn seed 550086. Phiếu bao phủ mọi ô tác giả đã định nghĩa, kể cả ô không còn xuất hiện sau che. Ghi nguồn mới quan sát được trong chính trường đó. Phạm vi field khai báo không chứng minh danh sách nguồn hay field đã đầy đủ. [Phiếu và hash](IFV_PACKET_MANIFEST.json)

Pha chấm output được chọn trước nhãn từ audit đã lưu. 132 lượt theo lịch rút thành 120 phép so sánh, gồm 108 chính và 12 chẩn đoán. Khoá nhận diện gồm ID vật lý, cặp pixel SHA, contract, field, reader và graph SHA. Giữ 12 alias lặp với seed/arm để truy vết và kiểm rằng các dòng trùng có cùng verdict, validity. Những kết luận theo 120 lượt chính của TASK 5 dùng đơn vị theo lịch cũ. Phần IFV dùng 108 phép chính khử trùng làm frame.

| Nhóm pha 2 | Frame | Lấy |
|---|---:|---:|
| A có cảnh báo, gộp C1–C4 | 14 | 14 |
| A không cảnh báo, B3 có cảnh báo, C3 | 19 | 6 |
| A không cảnh báo, B3 có cảnh báo, C4 | 18 | 6 |
| A và B3 không cảnh báo, C1 | 30 | 6 |
| A và B3 không cảnh báo, C3 | 13 | 5 |
| A và B3 không cảnh báo, C4 | 14 | 5 |
| Bốn họ chẩn đoán, mỗi họ có 3 reader | 12 | 4 |

Seed 550055. Mỗi stratum A không cảnh báo lấy mẫu đều không hoàn lại, quota chia vòng cho 5 stratum có dữ liệu đến tổng 28. C2 trên pilot này đều có cảnh báo A. Mỗi họ chẩn đoán chọn 1/3 reader. Xác suất chọn từng nhóm là cột “Lấy” chia “Frame”. Mẫu cuối gồm **46 ca** trên 5 ID, có 42 chính và 4 chẩn đoán. Có B2/B0 verdict để đối chiếu hậu kiểm, và arm A/B1 trong join. Source, field, reader và perturbation là biến báo cáo. Không có ảnh chụp vật lý trong frame này. [Tóm tắt sampling](execution/task55_recovery/ifv_sampling_summary.json)

Manifest riêng chứa ca được chọn lẫn ca không được chọn, alias, gốc và biến đổi, ID đã hash, graph SHA, source group, lý do và xác suất chọn. Manifest analyst nằm ngoài gói reviewer. Reviewer chỉ mở gói pha 1. Pha 2 không chỉ ra nhóm cảnh báo hoặc lý do được chọn. Nếu pha 1 đóng sớm, ca thiếu một trong hai quan sát giữ ở nhóm chưa chấm, không thay bằng ảnh mới. Mọi cỡ mẫu confirmatory phải tính lại theo cụm độc lập sau quyết định GO.
