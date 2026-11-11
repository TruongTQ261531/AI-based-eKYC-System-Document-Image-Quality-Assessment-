# Protocol development cho can thiệp M2–M3

Chọn cố định backup fixture và hai bản dựng development có sẵn, không dựa vào kết quả OCR của trường đích. Cho mỗi ID, giữ ảnh tác giả, render ảnh projective từ bốn góc cố định, rồi dùng cùng ảnh projective làm input cho bypass, Module 2 với góc chuẩn và Module 2 với crop lỗi. Crop được chọn theo vùng trường đích và kích thước tối thiểu. Góc đã biết giúp cô lập warp/crop; thiết kế này không đo độ chính xác của bộ tìm góc tự động. [Plan trước inference](execution/master_01/ab_development_plan.json)

Trace lưu hash input, thống kê chất lượng M1 ở chế độ chẩn đoán, bốn góc và ma trận M2, trạng thái vùng nguồn khai báo, output M3 có receipt và hash output chuẩn hóa. Reader RapidOCR v4 dùng cấu hình đã ghim, gồm preprocessing nội bộ rect2. Reader chỉ nhận pixel. Sau suy luận, analyst chấm với tham chiếu tác giả. Đánh giá hình học dùng tọa độ render và khung crop biết trước, không suy human readability từ vùng còn lại.

| So sánh | Câu hỏi |
|---|---|
| F1 trường gộp | Bao nhiêu kết quả đúng và sai trên toàn bộ field của input |
| So raw/rectified theo trường | Trường nào đổi đúng–sai hoặc sai–đúng trên cùng ID |
| Stage không dùng nguồn | Interface nào đổi hash đầu tiên khi giữ nguyên input |
| Visible-reference trên ảnh sau M2 | Bao nhiêu giá trị sai với tập nguồn sau biến đổi. Báo riêng mẫu số thay đổi |
| Phân tích nguồn và quan hệ | Nguồn bị loại hoàn toàn, còn vùng, hay chưa đủ scope. Khi vùng còn nhưng output sai, giữ nguyên nhân downstream chưa xác nhận |

B3 mạnh của TASK 5 chạy trên bộ M1–M7 có validity tương ứng. Với warp projective, dùng comparator pointwise theo nguồn sau M2. C4 đóng băng chỉ chấp nhận các operator đã xác thực. Pilot không ép C4 chấm một ảnh đã mất bằng chứng. Nghiên cứu về root cause sau này phải có lỗi/activation đã biết, đối chứng stage bình đẳng và xác minh độc lập.
