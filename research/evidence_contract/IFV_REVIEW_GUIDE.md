# Hướng dẫn chấm ảnh development

Mở [phiếu đọc ảnh](local/task55_blind_review_v1/index.html) trong trình duyệt trên máy. Bộ này dùng riêng 31 ảnh giấy tờ giả lập và tách khỏi các phiếu OCR-labels 48 mẫu trước đó. Có thể chia nhiều buổi. Nếu chỉ có một người, dùng một mã xuyên suốt và khai đúng vai trò, chẳng hạn có tham gia dự án. Giữ riêng ghi chú về số phút thực làm nếu thuận tiện.

1. Chọn tình trạng xuất hiện của từng trường, khả năng đọc và mình đã biết ảnh/giá trị từ trước hay chưa. Chỉ chép phần nhìn thấy trên **ảnh đang mở**. Có thể mở ảnh kích thước gốc.
2. Nếu cùng giá trị xuất hiện ở nhiều chỗ, thêm mỗi chỗ một nguồn và ghi vị trí. Nếu có MRZ và đọc được, ghi chính xác cả hai dòng, kể cả dấu `<`. Trường mờ, bị che, không chắc hoặc ngôn ngữ không đọc được đều có lựa chọn riêng. Giữ ô chữ trống nếu không đọc được. Không dựa vào giá trị đã thấy ở ảnh khác.
3. Nếu một mẫu có vấn đề, giữ lại ảnh và mô tả lý do trong ghi chú. Phiếu không yêu cầu xóa hoặc sửa dataset. Có thể lưu nháp khi chưa điền đủ. **Xuất bản nháp JSON** để có bản sao, và nạp lại từ mục **Nạp JSON đã lưu**. Nếu trình duyệt từ chối lưu cục bộ, dùng bản JSON để tiếp tục.
4. Khi có trường đã đủ thông tin, bấm **Xuất phiếu đã đánh giá** và giữ file. Gửi đường dẫn file trên máy để kiểm và khóa pha 1. Chỉ mở phiếu pha 2 sau khi bản quan sát đã khóa. Pha 2 cho xem giá trị đã ẩn danh để nhận xét, vẫn giấu A/B3.

## Thao tác analyst sau khi nhận JSON thật

Chạy từ worktree nghiên cứu bằng Python venv hiện có. `--submission` là đường dẫn file đã xuất. Chỉ dùng `--close-partial` nếu người chấm đã chủ động kết thúc pha 1 với phiếu thiếu và hiểu những ca còn lại sẽ giữ chưa đánh giá.

```powershell
$py = 'D:\laptrinhcuatao\Ekyc\.venv\Scripts\python.exe'
& $py -B -m research.evidence_contract.task55.review import --submission '<đường dẫn phiếu đọc ảnh JSON>'
& $py -B -m research.evidence_contract.task55.ifv open-stage2 --snapshot '<SHA256 từ bước import>'
& $py -B -m research.evidence_contract.task55.ifv import-stage2 --snapshot '<SHA256 ở trên>' --submission '<đường dẫn phiếu đối chiếu JSON>'
```

Sau khi mở pha 2, ghi phép thử hợp lệ, không hợp lệ hay chưa xác định và lý do rồi mới xem output. Kiểm nguồn còn lại và ngữ cảnh giữa hai ảnh. Giá trị gốc tác giả chỉ dùng đối chiếu sau khóa. Nếu không xác định được nguồn/đọc được hay không, giữ bất định. Ghi lý do quan sát cho mỗi giá trị sai, bị bỏ sót, hoặc xuất hiện dù đã xác minh mọi nguồn bị che. Phiếu đã lưu ở máy chưa tự được gửi.
