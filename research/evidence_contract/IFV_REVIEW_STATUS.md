# Trạng thái IFV

**BLOCKED_ON_HUMAN_REVIEW · USER_ACTION_REQUIRED.** Bộ pha 1 đã được xuất. Frame pha 2 đã được chọn và lưu hash, còn phiếu output thật chỉ mở sau khi nhận bản đọc ảnh đã khóa. [Mở phiếu](local/task55_blind_review_v1/index.html) · [Cách chấm](IFV_REVIEW_GUIDE.md)

| Mục | Trạng thái hiện tại |
|---|---|
| Pha 1 | 31 ảnh giả lập, 86 ô, không có answer key hay output |
| Pha 2 | 46 ca được chọn. 0 output packet đã phát hành |
| Review thực | 0 phiếu pha 1, 0 phiếu pha 2, 0 người chấm TASK 5.5 |
| Giá trị từ nhãn người | 0 adjudication, 0 gold label, 0 readability certificate |
| Precision, FPR, recall, phút công | NA. Chưa có mẫu số từ phiếu người |
| Review OCR-labels trước đây | 35/48 mẫu có sự kiện, 1 mã reviewer tự khai. Tách biệt với IFV |
| Test kỹ thuật | Kiểm tra schema, khử trùng và sampling, embargo pha 2, lưu và nạp nháp, tính metric có mẫu số. Control tự động báo riêng |

Mốc hoàn thành kế tiếp là có file đọc ảnh thật đã import và kiểm hash. Bước sau là phán đoán ẩn danh của cùng reviewer ở pha 2. Một reviewer đủ để xem tính khả thi và phát hiện vấn đề quy trình. Để dùng claim cần đánh giá độc lập, ghi đúng vai trò/exposure và thực hiện đối chiếu với reviewer thật khác hoặc nguồn chuẩn độc lập phù hợp endpoint. [Kế hoạch nghiên cứu](NEXT_ACTIONS.md)
