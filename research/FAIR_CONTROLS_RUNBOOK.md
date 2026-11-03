# Chạy và tiếp tục mục4 trên main

Giữ môi trường Python hiện có. Từ PowerShell:

```powershell
cd D:\laptrinhcuatao\Ekyc\versions\research-document-recovery
& D:\laptrinhcuatao\Ekyc\.venv\Scripts\python.exe -u -X utf8 -m research.fc_workflow
```

Chỉ một supervisor. Theo dõi `research/cache/fair_controls_v1/workflow.json`,
`progress.json`, log từng stage và `research/results/fair_controls_v1/`.
Mất usage không xóa checkpoint/output trên đĩa. Chạy tiếp cùng lệnh; không xóa
cache, không sửa các file phương pháp đã khóa, không khởi động hai supervisor.
Checkpoint80/160/240/320 lưu cả optimizer/RNG; event sau checkpoint được giữ
trong backup và ghi riêng nếu phải tính lại.

Trình tự: publish trước train → bốn train mới → development → khóa tám adapter
và publish trước test → tám lượt test mới → lặp từ pixel → audit → báo cáo →
publish. Git phải truy cập được để kiểm tra remote seal trước train/test.
Không có file `audit.json` với status passed thì chưa gọi là hoàn tất.

Web nghiên cứu8003 tạm nhả GPU trong lúc chạy. Supervisor kiểm tra đúng app/PID
trước khi dừng và khôi phục SourceV3/partial42 khi kết thúc hoặc lỗi. Mentor8000
giữ nguyên. Kết quả này không tự thay model eKYC. Ảnh/nhãn/output OCR/weights ở
local; Git chỉ chứa code, số liệu và hashes.

Protocol: [FAIR_CONTROLS_PROTOCOL.md](FAIR_CONTROLS_PROTOCOL.md).
Các checkpoint cũ và kết quả HP vẫn được bảo toàn. Hai đối chứng mới khớp token
với hard; uniform cũ chỉ là đối chứng phụ cho toàn bộ can thiệp. Số ID có thể
thay trong đối chứng ngẫu nhiên bị giới hạn bởi hỗ trợ dữ liệu và được công bố,
không gọi32 ID đã chọn là32 ca khác hoàn toàn. Những tổ hợp chọn dữ liệu đã xét
không phải số lần huấn luyện hoặc số lần gọi model.
