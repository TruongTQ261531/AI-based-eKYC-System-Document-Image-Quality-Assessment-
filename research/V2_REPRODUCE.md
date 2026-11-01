# V2: chạy, tiếp tục và kiểm tra bằng chứng

Các lệnh dưới đây dùng Python đã có trên máy Windows này. Không tạo venv, không
cài package vào môi trường gốc. CUDA/PEFT được nạp từ overlay riêng đã kiểm tra
checksum ở vòng V1. Model nền Vintern được ghim revision và SHA256 trong
`research/results/vlm_lora_v1/assets.json`.

Khi tiến trình đang chạy, không cần chạy lại vì chat bị gián đoạn. Xem trạng thái:

```powershell
Set-Location -LiteralPath 'D:\laptrinhcuatao\Ekyc\versions\research-document-recovery'
& 'D:\laptrinhcuatao\Ekyc\.venv\Scripts\python.exe' -m research.v2_status
```

`workflow.json`, `completion.json`, `progress.json`, log và checkpoint nằm trong
`research/cache/vlm_lora_v2_r2/`. Đây là tiến trình Python riêng, không phải suy nghĩ
ẩn được duy trì trong chat. Trạng thái tồn tại trên đĩa; máy ngủ/tắt hoặc tiến
trình bị dừng vẫn có thể làm gián đoạn công việc. Tiến trình completion yêu cầu
Windows tạm ngăn sleep trong thời gian chạy, không đổi cấu hình nguồn điện.

Sau khi kiểm tra không còn tiến trình cũ chạy, tiếp tục preparation:

```powershell
& 'D:\laptrinhcuatao\Ekyc\.venv\Scripts\python.exe' -m research.v2_workflow prepare
```

Chạy `research.v2_finish` trong terminal thứ hai để chờ khóa và thực hiện phần
test/audit. Nó công bố khóa lên đúng nhánh nghiên cứu đã được người dùng cho
phép, kiểm tra remote trước test, rồi mới đọc tập test. Nó không đẩy model,
ảnh hoặc nhãn riêng lên Git. Nếu Git/network thất bại, nó dừng trước test.

```powershell
& 'D:\laptrinhcuatao\Ekyc\.venv\Scripts\python.exe' -m research.v2_finish
```

Khóa file ngăn mở hai workflow đồng thời. Checkpoint có optimizer, cursor, RNG
và SHA256; chỉ checkpoint có `complete.json` mới được phục hồi. Log giữ cả các
bước từ lần chạy gián đoạn; audit kiểm tra trajectory cuối theo bước toàn cục
và ghi riêng số bước phải làm lại. Không sửa core/data/config sau khi train.
Nếu cần thay phương pháp sau khi mở test, phải tạo vòng mới và test mới.

Web localhost riêng:

```powershell
& '.\start-vlm-v2.ps1'
```

Mở `http://127.0.0.1:8003/` bằng Chrome/Edge trực tiếp. Script chỉ dùng ASCII để
tránh lỗi parser PowerShell Windows do mã hóa tiếng Việt. Chưa có audit thì API
không mở model. Không vượt cổng development thì cần chủ động chọn chế độ nghiên
cứu. Trường thêm/sửa có nhãn riêng, không được tính là OCR. Không có tự duyệt
danh tính hoặc kiểm tra liveness tại trang OCR này.

Để dựng lại dữ liệu trong một bản sao chuẩn bị trước train:

```powershell
& 'D:\laptrinhcuatao\Ekyc\.venv\Scripts\python.exe' -m research.v2_acquire
& 'D:\laptrinhcuatao\Ekyc\.venv\Scripts\python.exe' -m research.v2_data
```

Các lệnh này tái sử dụng metadata TAR/JSON, 80 ảnh MIDV cũ và index của các vòng
MIDV-2020/V4 đã chuẩn bị. Fresh clone cần chạy các bước acquisition tương ứng
của repo trước; cache/ảnh/weights không nằm trong Git. Nguồn chính thức và hash
ảnh được ghi ở acquisition.json; chỉ từng segment TAR được kiểm tra, không có
khẳng định đã xác minh MD5 toàn bộ archive. Không chạy lại acquisition/build
trong workspace đã khóa để thay dữ liệu. Font test là Arial của Windows, không
phân phối lại font; đúng checksum font có trong manifest. Đây chưa phải bản
reproduction độc lập nền tảng Linux.

Kiểm tra hành vi API/camera giả (không phải đo accuracy):

```powershell
& 'D:\laptrinhcuatao\Ekyc\.venv\Scripts\python.exe' -m unittest research.tests.test_v2_evidence research.tests.test_v2_web -v
node --test research/tests/v2_frontend.test.cjs
```

Kết quả chính nằm ở `research/results/vlm_lora_v2_r2/`, báo cáo đo thực tế được tạo
ở `research/V2_RESULTS_VI.md` chỉ sau audit. Output OCR nguyên văn và nhãn được
giữ trong cache/data riêng để có thể phát lại tại máy. V1/V4 được kiểm tra hash,
không sửa lại để làm đẹp phép so sánh. Chưa có tập ảnh người thật mới có phép
và chưa có nhãn legibility độc lập của con người; không dùng kiểm tra code để
thay thế hai phần bằng chứng này.
