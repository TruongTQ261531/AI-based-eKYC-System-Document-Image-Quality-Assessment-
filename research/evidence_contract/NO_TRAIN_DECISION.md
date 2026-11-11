# Quyết định NO-TRAIN

SUT cho A hiện có hai họ reader đã đóng băng: RapidOCR CPU v4/v5 Latin và Vintern-1B-v3_5 `partial_42/step_0320`. Lúc tiếp nhận đã kiểm lại 23 tài sản, 93 output cache và cấu hình lịch sử. Pha mới chỉ dùng RapidOCR v4 cho pilot Module 2–3. Kết quả oracle chính có thể chấm lại trên cùng output nên training không tạo nhãn độc lập và sẽ làm đổi phân bố lỗi của phép so sánh.

Nếu cần kiểm transfer, trước hết kiểm trên checkpoint Rapid Latin/Vintern hiện có dưới protocol, dữ liệu và quota ngang nhau. Mở reader khác hoặc huấn luyện chỉ khi một RQ cụ thể cần SUT mới và có design cân bằng model, exposure, ngân sách và checkpoint chọn từ development. Phiên này 0 training, 0 GPU inference, 10 CPU inference development. [Intake](execution/master_01/intake.json) · [Stage run](execution/master_01/ab_execute.json)
