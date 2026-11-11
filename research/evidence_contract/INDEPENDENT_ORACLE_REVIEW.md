# Protocol IFV cho pilot development TASK 5.5

Đối tượng đánh giá là cảnh báo trên output đã chuẩn hóa của reader từ cache TASK 5. IFV thu bằng chứng thị giác, rồi cho người chấm xác định đúng/sai trên đầu ra đã ẩn danh. Đây là nguồn đánh giá chính. Control chèn output và mutation oracle được báo riêng. Tất cả ảnh trong phiếu hiện tại là fixture giấy tờ giả lập. [Sampling](IFV_SAMPLING_PLAN.md) · [Hướng dẫn thao tác](IFV_REVIEW_GUIDE.md) · [Trạng thái](IFV_REVIEW_STATUS.md)

## Tách người đánh giá và thứ tự

1. Pha 1 chỉ hiển thị ảnh và tên semantic key để giới hạn công việc. Không có output reader, giá trị tác giả, trạng thái nguồn kỳ vọng hay cảnh báo. Mỗi ảnh chấm riêng theo thứ tự trộn cố định. Ghi các nguồn thực sự quan sát, vị trí, chữ nhìn thấy, mức đọc được và exposure. Các mục thiếu được giữ dưới dạng nháp. Reviewer khai vai trò và mức đã biết output.
2. Sau khi import JSON pha 1 thực sự, hệ thống kiểm image hash, slot, schema và đóng băng cả export. Pha 2 chỉ mở từ snapshot đó. Mặc định cần pha 1 hoàn chỉnh. Nếu chủ động đóng một phần, chỉ dùng các cặp đã có quan sát ở cả hai ảnh, giữ các cặp còn lại là chưa đánh giá và không bổ sung bù bằng ca khác. Mã reviewer đã mở pha 2 bị ràng buộc vào snapshot cũ. Mã tự khai chỉ dùng quản lý phiên, không dùng xác thực danh tính.
3. Pha 2 hiển thị cặp ảnh, quan sát pha 1 và ngữ cảnh cần kiểm. Người chấm ghi tình trạng phép thử và lý do trước khi nút mở hai output ẩn danh và tham chiếu tác giả có tác dụng. Kết quả A/B3, danh tính reader và arm không có trong HTML. Pha 2 là phiếu offline cho reviewer tin cậy, thứ tự hiển thị kiểm soát UI và chưa phải cơ chế chống cố tình xem mã nguồn. Analyst giữ bản nối với verdict trong thư mục riêng.
4. Nhập phiếu pha 2 để chốt các phán đoán của người trước khi join verdict. Một reviewer có thể hoàn thành pilot. Báo vai trò, exposure và trạng thái chưa adjudicate. Khi có người thứ hai, hai người khóa riêng pha 1 và pha 2 trước khi so phiếu. Ghi bất đồng, chỉ dùng đồng thuận có dẫn chứng hoặc adjudication có provenance. Trạng thái không giải được giữ INCONCLUSIVE.

## Bằng chứng và các endpoint

| Phép thử | Điều kiện kết luận |
|---|---|
| C1 | Có giá trị thật quan sát ở ảnh gốc. Pha 1 chưa thấy nguồn còn lại trên ảnh sau. Pha 2 kiểm cả ảnh, cùng scope tác giả đủ bao phủ, xác nhận không còn nguồn hợp lệ. Nếu đầu ra vẫn có giá trị, có thể ghi unsupported đã xác minh trong phạm vi ảnh. Nếu chưa chứng minh đầy đủ scope thì INCONCLUSIVE. Nếu phát hiện nguồn hợp lệ còn tồn tại thì quan hệ xóa hết nguồn là INVALID_TEST |
| C2 | Nguồn chính bị che và còn nguồn thay thế có thể xác minh. Nếu chỉ dùng MRZ TD3 cho số giấy tờ trong fixture, cần dòng chép bởi người, độ dài, định dạng, field và composite checksum. Bộ kiểm độc lập kiểm một tập định dạng bảo thủ, giữ kiểu khác là chưa đủ chứng cứ. Với nguồn lặp thân thẻ, cần chữ quan sát và vị trí. Hợp thức hóa nguồn không đồng nghĩa suy ra reader đã đọc từ nguồn đó |
| C3 | B và ngữ cảnh semantic của B còn đủ, A đã thay đổi đúng ý định. Chỉ tính endpoint quan hệ khi output B ảnh gốc được xác minh đúng. Lỗi B ảnh sau có thể vẫn tính ở endpoint pointwise |
| C4 | Chữ và nhãn có ý nghĩa được bảo toàn sau biến đổi, xác nhận trên cặp ảnh. Điều kiện output ảnh gốc đúng áp dụng cho endpoint quan hệ. Pilot chỉ có tịnh tiến, không diễn giải là lỗi của phiên bản rectifier |

Nhãn `CONFIRMED_FAULT` của phiếu là vi phạm hành vi trên case có bằng chứng ở **mức một người chấm**, chưa xác nhận lỗi phần mềm hay nguyên nhân. `NO_FAULT` dành cho phán đoán đúng trên test hợp lệ. `INVALID_TEST` và `INCONCLUSIVE` có mẫu số riêng. `language_unknown`, thiếu nguồn, mâu thuẫn người/tác giả, cấu trúc output không dùng được hoặc scope không chắc được ghi nhận và không tự chuyển thành lỗi. Tách `wrong_value`, `readable_omission` và `unsupported_verified`. Các giá trị không rõ nguồn không được gọi là hallucination. [Schema](IFV_REVIEW_SCHEMA.json)

## Phân tích sau khi có dữ liệu

- TP/FP/FN/TN so phán đoán của người với cờ cảnh báo trên **cùng phần đã chấm có thể kết luận**. Báo `TP/(TP+FP)`, `FP/(FP+TN)` và độ nhạy mô tả `TP/(TP+FN)` của phần này nếu mẫu số dương. Báo riêng test invalid, INCONCLUSIVE, ca chưa chấm, alarm rơi vào các nhóm này và ID theo cụm.
- Báo endpoint pointwise và relation riêng. B3 có thể đúng khi phát hiện lỗi sẵn có ở ảnh sau; việc A abstain do ảnh gốc sai không tự tạo FP cho B3. B1 là selector nên dùng provenance arm trong audit, B0/B2/B3 là checker trên cùng pack. Ghi riêng các chẩn đoán, không gộp vào panel chính.
- Xác suất lấy mẫu đã chốt nhưng không bù được phiếu thiếu. Bản import hiện tính mô tả có mẫu số trên subset, không báo weighted population recall hay CI suy rộng. Nhóm cùng ID, contract và field chỉ là cụm hành vi quan sát, không gọi là unique software root causes. Tỷ lệ lỗi theo ngân sách và chi phí người chỉ tính sau khi đo đúng mẫu số. Ghi riêng phút làm và thời gian tạm dừng.
- Analyst giữ raw transcripts, mã reviewer, output và join trong `local/` bị ignore. Chỉ xuất báo cáo tổng hợp có provenance. Phiếu và mô tả công khai dùng ảnh giả lập có quyền sử dụng. Không gửi giấy tờ thật, embedding hoặc metadata cá nhân.
