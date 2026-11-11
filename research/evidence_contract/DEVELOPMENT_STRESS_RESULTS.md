# Stress controls bổ trợ cho TASK 5.5

Đã tái sử dụng generator, validator và fixtures TASK 3, các diagnostic controls TASK 5 và output helper của oracle unit tests. **12 control** trên ảnh giả lập, **0 lần gọi reader**, **0 nhãn người**, **0 lỗi OCR/VLM thật được cộng thêm**. Nguồn đánh giá là fixture author và kiểm tra pixel bằng NumPy slicing. Bài kiểm chia sẻ vùng author khai báo, còn kiểm tra fill/so sánh vùng độc lập với hàm raster, project và validate của gate. Đây là kiểm thử cơ chế trên fixture, chưa là xác nhận human readability. [Kết quả từng control](execution/task55_recovery/controlled_results.json)

| Nhóm | Quan sát | Giới hạn |
|---|---|---|
| C2 chỉ còn MRZ | Pixel hai nguồn body đã được tô. Vùng MRZ còn nguyên. Với output đúng được chèn, A/B3 PASS, B2 và A_no_alternative bật cảnh báo | Sanity check của việc giữ nguồn thay thế. TASK 5 chưa có reader đọc đúng backup sau che |
| C1 mọi nguồn bị che | Mực gốc ở ba vùng được tô theo fixture. Assertion chèn bị cả A/B3 cảnh báo. Từ chối sạch được cả hai chấp nhận | Dữ liệu khai báo được tác giả tạo toàn bộ |
| C3 B được bảo toàn | Vùng giá trị và nhãn của B giống pixel. Khi chỉ output sau sai, A/B3 cảnh báo. Khi cả hai output đã sai, A chưa kết luận quan hệ và B3 vẫn bắt lỗi sau biến đổi | Không có provenance phiên bản để gọi là regression phần mềm |
| Lỗi dependency chung | Ép matcher trả “correct” trong bộ nhớ làm A/B3 cùng PASS trên một output sai đã biết | Một fault của oracle kiểm thử. Tách khỏi lỗi pipeline thật và khỏi tập mutant RQ2 tương lai |
| C4 tịnh tiến | Cắt ảnh dịch về tọa độ gốc cho khớp byte toàn ảnh. Output đúng qua cả A/B3, giá trị sai được cả hai cảnh báo | Tịnh tiến có padding. Chưa có thử nghiệm đổi rectifier |
| Che mất ngữ cảnh B | Pixel giá trị B không đổi nhưng vùng ngữ cảnh bị tô. A/B3/gated V3 đều loại | Bảo toàn crop ký tự không đủ để bảo toàn nghĩa |
| Scope nguồn thiếu | Vùng body bị tô. Hai nguồn dự phòng ngoài inventory còn nguyên. A bật candidate theo chính sách triage, B3 và gated V3 chưa kết luận | Không gọi là “đã xác minh hallucination”. Ca này chứng minh rủi ro báo động khi oracle thiếu scope |
| Backup MRZ checksum sai | Cả A/B3/gated V3 chưa kết luận trên fixture checksum sai | Không suy diễn từ sự tồn tại của chữ MRZ |
| Xóa thiếu nguồn | Một vùng bị tô, hai vùng còn nguyên. A/B3/gated V3 loại. Ablation chỉ dùng ý định tạo mask bật cảnh báo với assertion chèn | Gate giúp tránh đánh giá trên phép thử invalid |

Lần chạy đầu dừng ở giả định rằng wrapper A luôn trả INCONCLUSIVE khi scope C1 thiếu. Đọc lại oracle xác định nhánh triage trên. Lần chạy thứ hai ghi riêng kỳ vọng độc lập về eligibility và verdict wrapper rồi đi hết 12 control. Log lỗi đầu được giữ nguyên. [Lần 1](execution/task55_recovery/controls_run_01.log) · [Lần 2](execution/task55_recovery/controls_run_02.log)

Không tìm thấy suite TASK 5.5-AUTO trước khi nối lại. Bộ control trên là mở rộng nhỏ từ các control đã có. Nó không cung cấp lịch sử bug/patch, mutation score trên SUT, khả năng khái quát sang ảnh chụp hoặc tỷ lệ lỗi ngoài pilot. Artifact JSON giữ danh mục control, biến đổi, dấu vân tay ảnh và output chèn. [Manifest và probe](execution/task55_recovery/controlled_results.json)
