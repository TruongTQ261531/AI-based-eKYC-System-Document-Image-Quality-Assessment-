# Chạy nghiên cứu nguồn thông tin trên máy hiện tại

Nhánh `research/vlm-v2-evidence`; toàn bộ V1/V4 và bản mentor giữ riêng.
Không tạo môi trường hay cài hàng loạt dependency. Lệnh dưới dùng Python hiện có.

```powershell
cd D:\laptrinhcuatao\Ekyc\versions\research-document-recovery
& D:\laptrinhcuatao\Ekyc\.venv\Scripts\python.exe -m research.v3_workflow
```

Chỉ chạy một supervisor. Nó đợi R2 development và file implementation_ready,
huấn luyện hai seed bổ sung, chọn trên development, đẩy hai khóa lên nhánh
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

Nếu cổng đang được dùng, kiểm tra đúng server đang chạy. Launcher không tự tắt
dịch vụ khác. Camera thật chưa được kiểm thử thay người dùng. Các nút SPECIMEN
dùng ảnh train để thử giao diện, không được tính vào độ chính xác test. Kết quả
web chạy suy luận mới trên pixel, không tìm ảnh trong database hay trả nhãn GT.

Tài liệu kết quả chỉ được tạo khi audit qua: `research/V3_RESULTS_VI.md`.
Mọi số liệu công bố đi kèm hash đầu vào, model, output và khóa đã xuất bản.
Các đoạn văn bản/nhãn riêng, ảnh gốc và weights không đẩy lên Git.
