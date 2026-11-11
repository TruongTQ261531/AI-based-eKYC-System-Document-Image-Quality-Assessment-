# Amendments của TASK 5.5

Ngày 09/11/2026, Asia/Bangkok. Phạm vi là audit development và bổ sung IFV cho kết quả TASK 5 đã có. Confirmatory chưa mở và amendment này không thay các RQ, checkpoint, split hay kết quả lịch sử.

| Thay đổi | Căn cứ local | Ảnh hưởng |
|---|---|---|
| Đính chính cặp trùng 120/120 | A/flat trùng 120/120. A/B3 mạnh trùng 78/120 verdict, 79/120 cờ cảnh báo | Chỉ thêm báo cáo đính chính. Audit JSON và log TASK 5 giữ nguyên |
| IFV làm đánh giá chính | Mã review đang dở. Chưa có gold và phiếu thật cho TASK 5.5 | Đóng băng census 31 ảnh / 86 trường và lấy mẫu output 46 ca trước nhãn. Hai pha riêng. Báo pointwise và quan hệ riêng |
| Thống kê tiến độ OCR-labels cũ | Bản nhắc bàn giao 6/48 khác snapshot local 35/48, 81 sự kiện, một mã tự khai | Phạm vi khác IFV. Không nhập lại nhãn cũ và không đếm các sự kiện thành số người |
| Controls bổ trợ | Không thấy TASK 5.5-AUTO, có fixture, generator, validator và diagnostics TASK 3/5 | 12 kiểm chứng nhỏ, gồm một mutation in-memory của chính checker. Báo riêng, không hồi tố thành ground truth OCR |
| Xử lý C1 scope thiếu | Control cho A candidate do nhánh triage; contract và B3 chưa kết luận | Giữ độc lập giữa eligibility, alarm và xác nhận lỗi. Ghi log kỳ vọng thất bại và lý do chỉnh diễn giải |
| Reviewer và exposure | Hiện có thể chỉ một người tham gia | Một mã/người, vai trò và exposure tự khai. Partial export được giữ. Reviewer đã mở pha 2 không chuyển sang snapshot khác dưới cùng mã. Người độc lập thực sự chưa xác nhận |

Chọn mẫu development dùng seed 550055 và xác suất theo stratum. Bản bàn giao đề nghị các RQ khác được giữ như lựa chọn tham khảo. Việc đổi claim cần amendment prospective sau phân tích, trước khi khóa confirmatory. [Trạng thái khôi phục](RECOVERY_STATE.md) · [Lấy mẫu](IFV_SAMPLING_PLAN.md) · [Quyết định](REVISED_GO_NO_GO.md)
