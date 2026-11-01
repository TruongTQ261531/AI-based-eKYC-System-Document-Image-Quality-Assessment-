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

Kết quả hoàn chỉnh đọc ở `research/VLM_RESULTS_VI.md`. Để kiểm tra lại số
từ raw output/checkpoint còn trên chính máy này, không chạy lại training:

```powershell
python -m research.vlm_analysis
python -m research.vlm_errors
python -m research.vlm_final_report audit
python -m research.vlm_final_report report
```

Audit này cần cache private, không chỉ các file số trên Git. Clone mới phải
chuẩn bị lại corpus/runtime và tái lập model/inference; checksum adapter khác
sẽ không được thay vào khóa nghiên cứu cũ. Reproduction training ở trên so
checksum trong thư mục riêng, không tuyên bố test đã công bố là test mới.
`vlm_final_workflow` là supervisor của đợt chấm đã khóa, có lưu log từng giai
đoạn và tiếp tục từ các prediction cache hoàn tất khi bị ngắt. Nó yêu cầu cả
khóa chính và đối chứng đã được commit trước khi mở test. Không dùng
`vlm_report.py` bản scaffold để thay audit có đối chứng ở trên.

Phạm vi train là SPECIMEN có target từng trường. Ảnh full_dataset_original
và nhãn chất lượng của manifest hiện tại không được giả thành transcript OCR.
Kiểm kê phạm vi thật nằm ở results/vlm_lora_v1/input_scope.json.
