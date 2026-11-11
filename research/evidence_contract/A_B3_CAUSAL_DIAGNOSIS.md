# Vì sao A và B3 khác verdict trong pilot

Đối chiếu dùng quyết định đã lưu của TASK 5. Đây là phân rã theo đường chấm của chương trình trên cùng output, không gán nguyên nhân cho OCR/VLM. [Replay quyết định](execution/master_01/method_decision_replay.json) · [Audit gốc](A_VS_B3_DIAGNOSIS.md)

| Cơ chế | Dấu hiệu kiểm được |
|---|---|
| Chung thông tin đầu vào | Hai checker dùng chung output chuẩn hóa, báo cáo validity, state nguồn và bộ so sánh giá trị typed. Matcher này có thể làm cả hai cùng sai. Control trước đó ép matcher luôn đúng làm hai bên cùng bỏ sót |
| A_flat giữ lại thông tin nguồn | A_flat gọi B3, rồi áp tiền điều kiện ảnh gốc đúng của C3/C4 và policy C4. A_flat giữ metadata nguồn đã giải, nên ablation này kiểm biểu diễn tại biên oracle. A và A_flat trùng **120/120** verdict chính |
| Khác mục tiêu của B3 và A | B3 hỏi giá trị sau biến đổi có đúng theo bằng chứng đang còn không. C3/C4 của A còn hỏi lỗi xuất hiện sau biến đổi từ một ảnh gốc mà reader đọc đúng. Tất cả **42** khác biệt verdict chính có cùng lý do ảnh gốc sai hoặc chưa được xác minh, gồm 20 C3 và 22 C4 |
| Cờ cảnh báo | Trong 42 khác biệt, 41 là B3 báo và A chưa kết luận. Một ca là B3 PASS và A chưa kết luận. 17 cảnh báo A đều có ở B3. Một lỗi pointwise hợp lệ có thể vẫn thiếu tiền đề cho lỗi quan hệ |
| Ngoại lệ C1 ngoài panel chính | A có thể bật cảnh báo ứng viên khi nguồn đã khai báo bị xóa nhưng scope chưa đầy đủ. Control cũ cho thấy hai nguồn dự phòng thực tế còn nguyên. Cần kiểm toàn ảnh để phân xử. B3 giữ ca bất định |

### Phân biệt các giả thuyết

- **Tương đương trong điều kiện đã thử.** Trên phần hợp lệ của pilot, A_flat tái hiện mọi verdict của A với cùng metadata và tiền điều kiện. B3/gated V3 tái hiện cùng kết quả pointwise. Đây là quan sát hữu hạn, có giải thích bằng code. Ngoại lệ scope C1 làm việc mở rộng kết luận sang mọi ảnh thiếu căn cứ.
- **Thiếu độ phủ.** Panel chính có 3 ID giả lập. 12 dòng C2 đều là cảnh báo đọc sai hoặc bỏ sót, nên không có ca reader đọc đúng nguồn dự phòng để ước lượng giảm báo sai trên dữ liệu model. Nguồn MRZ còn trên ảnh cũng không xác định reader đã sử dụng MRZ.
- **Thiếu độc lập.** Các quyết định chia sẻ matcher, state và phần lớn schema. IFV phải giữ riêng việc đọc bằng chứng và xác nhận lỗi. Các ca lỗi gốc, invalid và không cảnh báo cần được đưa vào mẫu.
- **Giá trị ngoài số alarm.** A giữ quan hệ, tiền điều kiện và lý do abstain. C3 cho biết khi nào một lỗi B có thể gắn với biến đổi A. Trong dữ liệu hiện có, per-field B3 vẫn phát hiện mọi lỗi pointwise mà A báo. Chưa đo giảm thời gian triage hoặc giảm chi phí review.

Tách các estimand trong vòng tiếp theo. FAR chỉ tính trên ca hợp lệ được xác minh không lỗi. Cờ trên invalid/bất định có mẫu số riêng. So sánh B3 và A trên endpoint pointwise và relation riêng. Trên một ca ảnh gốc đã sai, không dùng việc A abstain để gán B3 một false positive. [IFV protocol](INDEPENDENT_ORACLE_REVIEW.md)
