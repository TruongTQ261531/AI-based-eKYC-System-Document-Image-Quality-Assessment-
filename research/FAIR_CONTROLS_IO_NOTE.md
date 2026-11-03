# Khôi phục sau lỗi ghi file tiến độ trên Windows

Sau khi cả bốn LoRA mới đã hoàn tất, evaluation development_repeat_42 dừng
ở lần ghi progress tại56/96 vì WinError5 khi thay progress.json.tmp bằng
progress.json.56 output nguyên văn đã lưu xong; không mất hoặc loại ca OCR.
Lỗi này thuộc metadata I/O, không phải OOM, lỗi model hoặc kết quả quality.

Reader theo dõi được đổi sang FileShare.ReadWrite|Delete để cho phép atomic
replace khi đang đọc snapshot. Launcher fc_runner giữ nguyên fc_study đã khóa,
chỉ bọc hàm save metadata của study/trainer bằng retry PermissionError tối đa
tám lần với chờ ngắn. Cùng serializer và cùng payload; hết retry vẫn báo lỗi,
không xóa file hoặc bỏ qua kết quả. Không sửa ACL, dependency, dataset, weights,
prompt, profile, loss, optimizer, số bước hoặc các phép thống kê.

Tiến trình mới bỏ qua bốn training record hoàn tất và đọc lại56 cache output
đã có, chỉ sinh các output còn thiếu. Lượt OCR trước đó không bị tính lại thành
mẫu độc lập. Log lỗi gốc và record exception được giữ ở cache; public chỉ có
hash, số lượng và phạm vi thay đổi. Khóa phương pháp80df... vẫn giữ nguyên.
Ghi chú và code I/O được công bố trước khi có bất kỳ generation trên test mới.

Kiểm tra bổ sung xác nhận transient lock được retry với payload nguyên vẹn,
permanent lock vẫn báo lỗi sau giới hạn, và lỗi khác không bị nuốt/retry.
Đây là xử lý ghi file tiến độ, không phải một lần điều chỉnh model sau khi
xem test. Web nghiên cứu được tự khôi phục khi dừng và sẽ tạm nhả GPU lại
khi tiếp tục; mentor8000 vẫn giữ nguyên.
