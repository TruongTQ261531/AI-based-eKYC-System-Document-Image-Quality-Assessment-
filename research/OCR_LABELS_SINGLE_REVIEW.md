# Bổ sung: pilot một người, không thay benchmark đã khóa

Người dùng xác nhận hiện chỉ có chính mình kiểm thử. Một người vẫn có thể
kiểm tra web và gán nhãn khả năng đọc sơ bộ. Dùng mã A; không dùng A/B hay hai
lượt của cùng người để nhận là hai người độc lập. Không có nhãn người nào được
tạo tự động từ GT hoặc OCR. Mức hoàn thành là số phiếu thực đã lưu.

Mở http://127.0.0.1:8005/ và chọn **Đánh giá độc lập**. Ghi mã A, các ngôn ngữ
bạn đọc được; xem từng vùng, chọn trạng thái và chép đúng phần chữ thấy được.
Chưa chắc chắn hoặc không biết ngôn ngữ là những trạng thái hợp lệ, không đoán.
Chỉ tích ô độc lập nếu chưa xem đáp án/OCR/ảnh khác cùng ID. Mỗi mẫu phải đánh
giá các trường đang liệt kê rồi bấm lưu. Nếu chỉ thử chức năng bằng giá trị giả,
không gửi vào bộ đánh giá thật; test tự động có database riêng.

Bản **Xuất đánh giá đơn** giữ text quan sát, trạng thái, vùng đề xuất, mã người,
hash ảnh và event gốc; luôn ghi chưa có đồng thuận giữa người gán nhãn. Có thể
dùng làm pilot với giới hạn một người, không báo hệ số đồng thuận giữa hai người.
Kiểm tra lặp lại cùng người là tự nhất quán, không phải inter-rater agreement.
Các lần gửi lại cùng người/cùng mẫu lấy bản mới nhất khi xuất, nhưng lịch sử
append-only vẫn được giữ.

Không chọn mẫu ưng ý nhất. Đánh giá từng mẫu theo chữ thực thấy và lưu sau khi
đã chọn trạng thái cho từng trường. Mặc định của form là **Chọn trạng thái**,
không tự ghi mọi vùng thành chưa chắc chắn. Ảnh mờ/che/cắt và không biết ngôn ngữ
là những tình huống cần nhãn, không phải lý do tự bỏ mẫu để tăng điểm.

Nếu thật sự sai loại giấy tờ, lỗi dựng hoặc khung chữ lệch, mở **Báo mẫu không
phù hợp**, chọn vấn đề, ghi lý do rồi gửi. Có thể chuyển tiếp mà không phải tạo
nhãn đọc được giả. **Rút đề nghị của tôi** lưu một event mới, không xóa lịch sử.
Mẫu được báo vẫn nằm trong48 tác vụ và trong benchmark304 ảnh đã khóa; không
âm thầm giảm mẫu số. Có thể xuất riêng đề nghị để sửa/loại ở một phiên bản dữ
liệu sau, kèm quy tắc và lý do. Các phiếu đọc được và các đề nghị kiểm tra được
đếm riêng.

```powershell
& D:\laptrinhcuatao\Ekyc\.venv\Scripts\python.exe -m research.labels_export --mode single
```

Bản verified vẫn yêu cầu ít nhất hai **person ID khác nhau** được người quản lý
xác nhận độc lập, không chỉ hai mã reviewer. `reviewer_registry.json` local có
thể ánh xạ nhiều mã về cùng một người qua reviewer_people; chúng không được đếm
hai lần. Registry ban đầu chỉ ánh xạ A sang participant-001 và chưa xác nhận
đồng thuận độc lập. Mọi thống kê phải ghi một người nếu chỉ có A.

Bộ mô hình/dữ liệu/đáp án/thống kê chính đã khóa trước OCR vẫn giữ nguyên. Bổ
sung human pilot được lập khi benchmark tự động đang chạy; đây là đánh giá
chất lượng nhãn bổ sung, không phải thay main test hoặc chọn lại model bằng nhãn
mới. `human_review_plan.json` lưu thời điểm, số phiếu đã tồn tại và manifest48
mẫu. Nếu chưa có phiếu, loại ID000 đã dùng xem QA trước đó để tránh lộ đáp án
cho người dùng đã đọc chat. Nếu đã có phiếu thì giữ bộ cũ và ghi rõ ca QA bị lộ,
không âm thầm bỏ các phiếu đã nhận.

Nhãn một người và đề xuất chỉnh vùng không ghi đè bản annotation phát hành hay
các kết quả test cũ. Khi cần dùng làm tham chiếu mới, phát hành supplement có
provenance và giữ kết quả chính; không biến nó thành test chưa từng xem.
