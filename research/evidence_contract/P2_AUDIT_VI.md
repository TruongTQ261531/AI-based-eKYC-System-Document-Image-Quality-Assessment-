# P2 · Tái sử dụng ảnh lịch sử và bằng chứng C2 · 21/11/2026

Đọc được khung chính của cả 5.428 tệp trong phạm vi kiểm kê. Có 3.324 khung chính khác nhau theo pixel sau chuẩn hóa. Trong 1.100 cặp nguồn C2 do metadata của nhà cung cấp gợi ý, chưa có cặp nào đủ bằng chứng về hai vùng trước và sau biến đổi cùng các phê duyệt cần thiết. Quyết định khoa học vẫn là `NO_GO_SUPERIORITY`. [Kết quả tổng hợp](execution/master_01/p2_20261120/aggregate.json)

## Ảnh nào xuất hiện nhiều lần?

| Đơn vị đếm | Kết quả | Cách đọc |
|---|---:|---|
| Tệp raster | 5.428 tệp, 3.499 giá trị SHA-256 khác nhau | 1.159 nhóm có từ hai tệp giống từng byte |
| Khung chính | 5.428 khung, 3.324 giá trị hash pixel khác nhau | 1.241 nhóm trùng pixel sau khi xử lý hướng EXIF và chuyển RGB |
| Khung phụ MPO | Đọc được 12/24 | 12 khung còn lại báo lỗi khi Pillow chuyển sang khung thứ hai. Khung chính của các tệp này vẫn tham gia so sánh |
| Ảnh ứng viên gần trùng | 362 nhóm liên thông, gồm 4.116 mục | Hai ảnh có thể nối gián tiếp qua ảnh thứ ba. Cùng mẫu giấy tờ cũng có thể tạo ảnh trông giống nhau |
| Mã giấy tờ trong metadata | 678 mã, còn 876 tệp thiếu mã | 129 nhóm bộ dữ liệu–bố cục và 2.998 nhóm mã–nhãn chụp |
| Liên kết ảnh dẫn xuất với tệp nguồn | 944 liên kết | Hash nguồn do metadata khai khớp byte của một tệp khác trong kho |

Có 1.194 nhóm trùng pixel xuất hiện trong nhiều bộ nghiên cứu. Trong 24 nhóm mang nhiều nhãn vai trò, cùng nội dung pixel được ghi là train ở năm bộ và xuất hiện trong `recovery_v4` với vai trò test (10 nhóm), development (8) hoặc calibration (6). Kết quả xác nhận tái sử dụng ảnh giữa các bộ. Để xác định mức ảnh hưởng lên một kết quả V4 cụ thể, cần đối chiếu checkpoint dùng trong phép đo với nhật ký huấn luyện của checkpoint đó. [Các bộ và vai trò theo từng nhóm](execution/master_01/p2_20261120/verification.json)

Với 1.000 instance MIDV-2020 đã kiểm metadata ở mốc trước, 192 có bằng chứng đã được tiếp xúc và 808 còn chưa xác định. [Quy tắc nhóm ảnh và phạm vi dữ liệu](execution/master_01/p2_20261120/REPLAY.md)

## Cặp C2 còn thiếu gì?

Một ca C2 kiểm tra liệu nguồn dự phòng có còn đọc được sau khi vùng thông tin chính bị che. Có 1.100 cặp giữa trường in trên giấy tờ và vùng máy đọc MRZ của 400 mã giấy tờ. Cả 1.100 cặp có hai định danh vùng khác nhau. Sáu điều kiện còn `UNKNOWN` trên toàn bộ các cặp, gồm bốn quan sát vùng trước/sau, xác nhận hai nguồn biểu đạt cùng giá trị và xác minh nguồn gốc cặp. Điều kiện phê duyệt reference là `FAIL` trên 1.100 cặp vì sổ đăng ký chưa có reference được duyệt.

| Đầu mối hiện có | Cặp nguồn | Mã giấy tờ |
|---|---:|---:|
| Có ảnh cùng mã và có liên kết tới tệp nguồn | 110 | 40 |
| Có ảnh cùng mã, chưa có liên kết tới tệp nguồn | 96 | 35 |
| Chỉ có metadata nhà cung cấp trong phạm vi đã xét | 894 | 325 |
| **Tổng** | **1.100** | **400** |

Việc kỹ thuật tiếp theo có thể bắt đầu với 110 cặp thuộc 40 mã đã có liên kết nguồn. Mỗi cặp cần gắn đúng hai vùng với ảnh trước/sau, ghi nhận khả năng đọc và độ chính xác của trường, rồi đối chiếu quyền sử dụng và thẩm quyền duyệt. Cả ba người chấm đã hoàn thành hai pha. Việc chốt Round 1, chỉ định người có quyền duyệt reference và chọn quy tắc phân xử thuộc D1–D3. [Quyết định của chủ dự án](B_OWNER_DECISIONS_20261117.md)

## Kiểm chứng

Bộ Evidence Contract đạt 595 kiểm thử và 6 subtest. Các kiểm thử hồi quy dùng tệp MPO thiếu khung phụ để kiểm tra cách đếm khung chính và dùng metadata lặp để kiểm tra cách đếm nhóm trùng pixel giữa các vai trò. [Biên bản kiểm thử](execution/master_01/p2_20261120/tests.json)

Lượt xác minh P2 đối chiếu hash của 84 tệp đã khóa, kiểm lại các nhóm ảnh, tái lập bảng C2 và chạy lại D4. [Biên bản xác minh](execution/master_01/p2_20261120/verification.json) · [Lệnh tái lập](execution/master_01/p2_20261120/REPLAY.md)
