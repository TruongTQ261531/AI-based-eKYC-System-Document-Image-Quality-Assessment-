# Độ phủ contract và các ca phân biệt

Đơn vị lịch sử là dòng contract–field–reader. Các dòng cùng ảnh và ID phụ thuộc nhau. Cột control dùng output được cài trong fixture và báo riêng. [Số liệu lịch sử](execution/master_01/method_decision_replay.json) · [Controls M1–M7](execution/master_01/controlled_faults.json)

| Contract | Lượt chính / A / B3 cảnh báo | Strong B3 đã bao phủ | Khác biệt cần kiểm độc lập |
|---|---:|---|---|
| C1 bỏ hết nguồn | 36 / 3 / 3 | Phát hiện trường vẫn có giá trị sau khi loại toàn bộ nguồn theo scope đã khai báo | Che thiếu hoặc còn nguồn chưa khai báo. Xác minh absence trên toàn ảnh, ghi invalid/bất định. C1 triage của A có thể báo cả khi scope thiếu |
| C2 giữ nguồn thay thế | 12 / 12 / 12 | Giữ tập giá trị chấp nhận được từ nguồn body/MRZ hợp lệ và chấm bỏ sót/sai | Thêm positive thực có reader trả đúng từ ảnh còn backup. MRZ cần kiểm điều kiện, checksum và precision. Control M1 cho thấy A và B3 đều bắt lỗi bỏ backup, B2 bỏ sót |
| C3 B không bị tác động | 36 / 1 / 21 | Bắt sai giá trị B sau che nếu B còn nguồn | A yêu cầu B đúng trên ảnh gốc. Kiểm riêng giữ ký tự, giữ ngữ cảnh và đối chứng ảnh gốc đã sai. Control M3 làm rõ ca giá trị B còn mà semantic context mất |
| C4 bảo toàn qua hình học | 36 / 1 / 22 | Bắt giá trị sai trên ảnh sau khi có reference khả kiến | C4 lịch sử chỉ kiểm tịnh tiến đã xác thực. Rectification projective của pilot mới dùng phân tích stage hình học, nằm ngoài operator C4 đã xác minh |

Panel chẩn đoán 12 dòng dùng chung gồm 6 invalid và 6 bất định. Raw V3 báo 9 cảnh báo. V3 với gate chung đưa về cùng phân loại với A, nên phần giảm này do gate trong phép đối chứng hiện có. Đối chiếu ablation bỏ validator đổi 6/12 verdict chẩn đoán, trong khi 120 dòng chính giữ nguyên. Gọi một báo động invalid là chi phí chẩn đoán, không cộng vào FAR trên ca hợp lệ.

M6 là lỗi ở khai báo nguồn dù chuỗi cuối đúng. M7 làm cấu trúc output không dùng được. Hai lỗi thuộc giao diện bổ trợ và có checker phẳng riêng. Chúng không làm tăng số lỗi model tự nhiên hoặc số lỗi mà A phát hiện.
