# Tái lập đợt fine-tune local

Đợt V1 dùng Windows x64, Python3.11, RTX3050 6GB và RAM16GB. Runtime tùy chọn
nằm trong cache riêng; không tạo venv và không sửa môi trường OCR hiện tại.
Không chạy huấn luyện/benchmark GPU đồng thời với web LoRA đang giữ model.

Chạy các lệnh từ worktree `versions/research-document-recovery`, dùng Python
đã có tại `D:\laptrinhcuatao\Ekyc\.venv\Scripts\python.exe` thay cho `python`
nếu PATH đang trỏ trình thông dịch khác.

```powershell
python -m research.vlm_setup all
python -m research.vlm_setup run -- -m research.vlm_prepare_data
python -m research.vlm_setup run -- -m research.vlm_train smoke
```

Script chuẩn bị kiểm tra checksum từng wheel/model. Hai font Noto cũng được
ghim checksum; corpus sinh lại phải khớp720raster và reference đã công bố.
Downloader giữ các đoạn tải dở để tiếp tục. Tổng tải model/CUDA nhiều GB;
thời gian này khác thời gian optimizer chạy.

Để tái lập huấn luyện **đã công bố**, dùng thư mục đầu ra riêng:

```powershell
python -m research.vlm_setup run -- -m research.vlm_reproduce --seed 42
python -m research.vlm_setup run -- -m research.vlm_reproduce --seed 31415
```

Kết quả vào cache/vlm_lora_v1/reproductions, không ghi đè study/test lock.
So checksum adapter với lần công bố; khác GPU/driver có thể khác số học.
Đây là reproduction, không được gọi tập test đã công bố là test mới chưa thấy.
Các lệnh Train/Seal/Test ở start-vlm-training.ps1 dành cho lần nghiên cứu mới
chưa khóa; bản study đã sealed sẽ từ chối train đè lên cùng tập test.

Adapter chỉ khoảng4.35MB. Nó thuộc **language_model bên trong full Vintern**,
vẫn cần weights/tokenizer/mã nguồn Vintern đúng revision. Chạy
`python -m research.vlm_package` để xuất adapter được chọn và descriptor.
Không dùng nhầm metadata text-Qwen trong adapter_config để bỏ mất phần ảnh.
Giữ checkpoint seed đầy đủ nếu cần resume optimizer/RNG; gói export để suy
luận không chứa optimizer. Có thể sao lưu gói hoàn tất vào Drive for desktop;
chương trình vẫn tính toán bằng RAM/VRAM của máy local.

Mở bản thử LoRA bằng `powershell -NoProfile -ExecutionPolicy Bypass -File
.\research\start-vlm-web.ps1`, địa chỉ http://127.0.0.1:8002/ . API chỉ bật sau
cổng development và audit, dùng ảnh camera trong bộ nhớ, không ghi ảnh/text
ra file. Bản OCR nghiên cứu cũ ở8001 và bản mentor được giữ riêng. Demo trong
web dùng ảnh train để thử giao diện, không dùng làm bằng chứng accuracy test.
