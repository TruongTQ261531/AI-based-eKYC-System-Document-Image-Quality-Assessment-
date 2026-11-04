# Mục1: chạy dữ liệu, benchmark và đánh giá ở localhost

Dùng môi trường hiện có, từ PowerShell:

```powershell
cd D:\laptrinhcuatao\Ekyc\versions\research-document-recovery
& D:\laptrinhcuatao\Ekyc\.venv\Scripts\python.exe -u -X utf8 -m research.labels_workflow
```

Một supervisor; không xóa cache/checkpoint/raw outputs khi tiếp tục. Bộ chạy
kiểm tra lock đã công bố trước khi đọc OCR mới. Sau usage limit, lệnh này tiếp
tục từ output có hash khớp, không tính output cache thành lượt model mới.
Theo dõi `research/cache/ocr_labels_v1/workflow.json`, `progress.json`, log từng
stage và `execution_events.jsonl`. Muốn xác minh kết quả cần `audit.json` và
`software_verification.json` status passed, không chỉ thấy progress100%.

Mở trang nhãn bằng terminal riêng:

```powershell
.\start-ocr-labels.ps1
```

Hoặc dùng Python trực tiếp nếu terminal chặn PowerShell script:

```powershell
& D:\laptrinhcuatao\Ekyc\.venv\Scripts\python.exe -m uvicorn research.labels_web:app --host 127.0.0.1 --port 8005 --no-access-log
```

URL: http://127.0.0.1:8005/ . Chỉ bind loopback. Khi benchmark cần GPU,
supervisor chỉ dừng đúng server SourceV3 ở8003 và khôi phục sau đó; mentor8000
giữ nguyên. Trang nhãn8005 chạy CPU, không phê duyệt eKYC.

`annotations.sqlite3` và `exports/annotations.jsonl` ở
`research/data/ocr_labels_v1/` chứa text riêng và vị trí từng trường.
Nguồn tác giả, reference_text, frame_visibility và readability là các mục khác
nhau. Không lấy Clean/Blur hoặc in_frame làm nhãn đọc được. Field native không
có semantic_key được giữ nguyên, không đoán họ tên/CCCD theo vị trí.

Xuất lại dữ liệu local:

```powershell
& D:\laptrinhcuatao\Ekyc\.venv\Scripts\python.exe -m research.labels_export --mode annotations
& D:\laptrinhcuatao\Ekyc\.venv\Scripts\python.exe -m research.labels_export --mode verified
```

Chế độ verified phải rỗng khi chưa có đánh giá thực. Người đánh giá làm riêng,
ghi ngôn ngữ mình đọc, không mở đáp án/OCR hoặc ảnh khác của cùng ID. Chế độ mù
không gửi transcript/glyph/output. Ghi đúng phần chữ nhìn thấy; không biết ngôn
ngữ khác với ảnh mờ. Kéo trên ảnh để đề xuất vùng mới. Lưu đề xuất ghi một event
mới trong `research/cache/ocr_labels_v1/reviews.sqlite3`, không sửa bản phát hành.

Mã A/B và ô tự khai không chứng minh hai người độc lập. Chỉ khi người quản lý
đã có bằng chứng độc lập mới tạo file local `reviewer_registry.json` với
`independence_evidence_confirmed: true` và danh sách `verified_reviewer_codes`.
Không có API tự xác nhận reviewer. Bộ xuất verified chỉ lấy trường đồng thuận
giữa ít nhất hai reviewer được xác nhận; bất đồng cần xử lý và phát hành bổ sung,
không thay âm thầm test cũ. Không ghi fixture/model predictions thành nhãn người.

Code/protocol/aggregates/hashes lên Git; ảnh, transcript, đề xuất cá nhân và
weights ở local. Bộ gốc có50 giấy tờ lặp nhiều frame; không gọi21.050 ảnh là
21.050 danh tính độc lập. Ảnh mới chọn MIDV-2020 là cùng bộ công khai, không
phải camera quần thể mới tự thu thập. Xem protocol và báo cáo để hiểu giới hạn.
