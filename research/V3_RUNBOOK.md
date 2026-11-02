# Chạy nghiên cứu nguồn thông tin trên máy hiện tại

Mã có thể phục vụ web từ main. Việc công bố thí nghiệm vẫn giới hạn ở nhánh
`research/vlm-v2-evidence`; checkout nhánh đó trước khi chạy lại supervisor có
bước ghi Git. Toàn bộ V1/V4 và bản mentor được giữ để đối chiếu.
Không tạo môi trường hay cài hàng loạt dependency. Lệnh dưới dùng Python hiện có.

```powershell
cd D:\laptrinhcuatao\Ekyc\versions\research-document-recovery
git switch research/vlm-v2-evidence
& D:\laptrinhcuatao\Ekyc\.venv\Scripts\python.exe -m research.v3_workflow
```

Chỉ chạy một supervisor. Nó đợi R2 development và file implementation_ready,
huấn luyện hai seed bổ sung, chọn trên development, đẩy hai khóa chính và khóa
baseline ghép bổ sung lên nhánh
nghiên cứu trước khi đọc test, rồi benchmark, phát lại output, audit và báo cáo.
Checkpoint, optimizer và output nguyên văn nằm trong cache local bị Git bỏ qua.
Không xóa checkpoint khi bị usage limit. Log và trạng thái được ghi ra đĩa;
chạy lại supervisor sau khi dừng tiến trình cũ sẽ tiếp tục các bước còn thiếu.
Không coi lời báo tiến độ của chat là bằng chứng đã huấn luyện xong.

Theo dõi:

```powershell
Get-Content research\cache\source_visibility_v3\workflow.json
Get-Content research\cache\vlm_lora_v2_r2\workflow.json
```

Sau audit, mở web riêng tại [localhost:8003](http://127.0.0.1:8003/):

```powershell
.\start-source-v3.ps1
```

Launcher kiểm tra app_id khi cổng đang dùng, chỉ tái sử dụng đúng app và không
tự tắt dịch vụ khác. Có thể truyền `-Port 8004` hoặc cổng khác. V2/V3 mặc định
dùng 8003 vì là hai chế độ thay thế; nếu mở giao diện riêng, truyền cổng khác.
Các phép đo GPU được thực thi tuần tự. Không suy ra khả năng chạy đồng thời nhiều
model từ những kết quả đó. Python hiện có được tìm ở `.venv` trong repository
hoặc workspace cha của worktree; không tạo/cài môi trường.

Trên máy này, `.venv`, dataset và weights thiếu ở worktree được liên kết tới tài
nguyên sẵn có trong `D:\laptrinhcuatao\Ekyc`; liên kết không được Git đưa lên.
Clone trên máy khác cần chuẩn bị các asset công khai theo manifest; không coi
source-only clone là đã có đầy đủ model/dataset.

Camera thật chưa được kiểm thử thay người dùng. Ba nút SPECIMEN đầu
dùng ảnh train; nút mẫu mới là giấy tờ giả lập ngoài tập train. Bốn trường hợp
đã được thử qua trình duyệt với model thật; chúng không tính vào độ chính xác test. Kết quả
web chạy suy luận mới trên pixel, không tìm ảnh trong database hay trả nhãn GT.

Tài liệu kết quả chỉ được tạo khi audit qua: `research/V3_RESULTS_VI.md`.
Mọi số liệu công bố đi kèm hash đầu vào, model, output và khóa đã xuất bản.
Các đoạn văn bản/nhãn riêng, ảnh gốc và weights không đẩy lên Git.

Phần kiểm tra riêng lượt V1 bị sleep và các phân tích CPU hậu nghiệm được mô tả
trong V3_RESUME_NOTES.md và V3_CPU_LABEL_SUPPLEMENT.md. Bản thảo/kết quả hiện tại
đã kèm kết quả kiểm tra lại; không xóa cache để chạy lại từ đầu.
