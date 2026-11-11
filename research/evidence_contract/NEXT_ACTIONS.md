# Các bước còn lại theo thứ tự

| Mốc | Đầu vào cần có | Tiêu chí kết thúc |
|---|---|---|
| 5.5 người đánh giá | Phiếu offline. Người hiện có có thể làm một vòng pilot | Nhận JSON thật pha 1, khóa snapshot và mở phiếu pha 2 ẩn danh. Sau khi nhận pha 2, xuất số mô tả với trạng thái một reviewer chưa adjudicate |
| 5.5 đánh giá độc lập | Người thứ hai đánh giá riêng hoặc chuẩn độc lập theo endpoint. Chỉ mở ca có dữ liệu đủ | Lưu nguồn bằng chứng, đối chiếu ca hai bên cùng/khác verdict và bảo toàn ca chưa rõ. Nếu thiếu nguồn lực thì giữ BLOCKED hoặc thu hẹp claim với protocol riêng |
| Gate phương pháp | Có ước lượng paired, coverage, FAR và chi phí đúng mẫu số. Có đủ provenance cho claim chọn | GO mới với phạm vi rõ, hoặc giữ NO-GO / thay framing prospective. Giữ bằng chứng hiện có và nguồn baseline mạnh |
| 6 bộ kiểm chứng độc lập | GO mới và quyền sử dụng dữ liệu. Ảnh camera chỉ ghi nhận nếu có thu thập thật | Exposure audit và dataset card độc lập, ground truth xác minh, kế hoạch thống kê và khóa hash có thể kiểm |
| 7 thực nghiệm khóa | Khóa xác minh được, số lượt gọi và budget đã định | Chạy theo manifest, log inference append-only, báo các ca invalid/bất định, kết quả theo ID và family |
| 8 mở rộng A+B tùy chọn | A đủ cơ sở, còn nguồn lực và có provenance để kiểm lan truyền lỗi qua Module 2–3 | So với field diff/stage logs trên cùng ảnh và reader. Giữ một yếu tố thay đổi mỗi lần. Nếu chưa có ích lợi riêng thì ghi exploratory |
| 9 paper và gói tái lập | Kết quả đã kiểm, CFP và quy định nộp được đối chiếu lại | Nối từng claim với kết quả, chuẩn bị manuscript và artifact ẩn danh có quyền dùng. Demo nghiên cứu nếu cần dùng localhost riêng, tách khỏi production |

Trong phiên phục hồi hiện tại, bước tiếp theo của người dùng là **mở phiếu pha 1 và gửi đường dẫn JSON đã xuất**. Việc đánh giá 48 phiếu OCR-labels cũ có thể lưu riêng. [Phiếu mới](local/task55_blind_review_v1/index.html) · [Cách lưu và tiếp tục](IFV_REVIEW_GUIDE.md)
