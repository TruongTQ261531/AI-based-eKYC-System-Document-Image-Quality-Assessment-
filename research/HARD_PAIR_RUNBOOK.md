# Tiếp tục vòng cải thiện hai nhóm lỗi đối nghịch

Trong repository hiện có, branch main, dùng môi trường Python đã có:

```powershell
cd D:\laptrinhcuatao\Ekyc\versions\research-document-recovery
& D:\laptrinhcuatao\Ekyc\.venv\Scripts\python.exe -u -m research.hp_workflow
```

Chỉ chạy một supervisor. Nó giữ khóa, lưu stage/log/PID, tiếp tục checkpoint
80/160/240/320 và bỏ qua kết quả hoàn tất. Không xóa dữ liệu/checkpoint khi hết
usage. Không sửa các file hp_common/acquire/data/metrics/study hoặc protocol
khi đã huấn luyện; signature sẽ chặn tiếp tục nếu khác. Code báo cáo/audit và
nhật ký bổ sung được giữ riêng với hợp đồng can thiệp đã khóa.

Theo dõi `research/cache/hard_pairs_v1/workflow.json`, `progress.json`, logs
và `research/results/hard_pairs_v1/`. Trạng thái hoàn tất phải có audit passed,
không chỉ dựa vào một dòng báo tiến độ trong chat. Dữ liệu/weights chỉ ở local.

Nguồn OCR nghiên cứu8003 cần tạm nhả GPU trong lúc chạy; supervisor tự khôi
phục app Source V3 khi kết thúc hoặc gặp lỗi. Mentor8000 vẫn giữ nguyên. Model
mới không được tự đưa vào eKYC hoặc thay model đã chọn bằng test. Quyết định
development được lưu trước khi mở test mới và báo rõ nếu gate không đạt.

Phương pháp: `HARD_PAIR_PROTOCOL.md`. Dữ liệu640 train/96 dev/192 test,
64 slot train thay đổi trên32 giấy tờ, hai seed và hai checkpoint control
V3 có cùng ngân sách.18 trường hợp dev/test không có cặp giữ/che phù hợp
được giữ bằng fallback và đếm riêng, không loại khỏi đánh giá.192 test views
không đồng nghĩa192 giấy tờ độc lập; có48 giấy tờ mới,24 ảnh chụp và24 giả lập.
