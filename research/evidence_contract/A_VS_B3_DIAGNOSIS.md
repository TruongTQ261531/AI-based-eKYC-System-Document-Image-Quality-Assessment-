# A và baseline tham chiếu khả kiến B3

## Đơn vị và kết quả đối chiếu

Bản audit trước gián đoạn đã khớp cả 132 dòng chấm gốc và replay, 93 đầu ra cache và 41 artifact thực thi. Bảng chính dùng 120 lượt contract × trường × reader theo lịch. Hai nhánh chọn ca có 60 lượt mỗi nhánh, với lặp theo seed. Khử trùng theo ID vật lý, cặp ảnh, contract, trường, reader và graph cho 108 phép so sánh chính duy nhất. Toàn panel có 31 ảnh duy nhất, 5 ID giả lập, trong đó 3 ID ở panel chính. [Audit đã lưu](execution/task55_audit/audit_run_01.json) · [Báo cáo TASK 5](DEVELOPMENT_PILOT.md)

| A | B3 mạnh | Số lượt |
|---|---|---:|
| CANDIDATE_VIOLATION | CANDIDATE_VIOLATION | 17 |
| INCONCLUSIVE | CANDIDATE_VIOLATION | 41 |
| INCONCLUSIVE | PASS | 1 |
| PASS | PASS | 61 |

Trùng verdict **78/120**, trùng cờ cảnh báo **79/120**. A có 17 cảnh báo, B3 có 58. A không có cảnh báo riêng trong panel chính. **120/120** thuộc cặp **A / A_flat**. B3 và B3 dùng scorer V3 với cùng gate cũng trùng verdict trên 120/120. Không có nhãn lỗi độc lập để gọi 41 cảnh báo riêng của B3 là false positives. [Audit theo dòng](execution/task55_audit/audit_run_01.json)

| Contract / biến đổi | Lượt | Trùng A/B3 | Cảnh báo A / B3 | Trước biến đổi sai hoặc chưa xác minh |
|---|---:|---:|---:|---:|
| C1 / che tất cả nguồn đã khai báo | 36 | 36 | 3 / 3 | 0 |
| C2 / che một nguồn | 12 | 12 | 12 / 12 | 0 |
| C3 / che A, theo dõi B | 36 | 16 | 1 / 21 | 20 |
| C4 / tịnh tiến có đệm | 36 | 14 | 1 / 22 | 22 |

C1 đồng ý về mặt trạng thái nguồn **đã khai báo**, còn 3 output cần xác minh độc lập về thiếu bằng chứng. C2 có 11 omission và 1 mismatch theo B3. Panel lịch sử chưa có ca reader trả đúng nhờ nguồn dự phòng sau che, nên TASK 5 chưa đo được khả năng tránh báo sai ở chính các ca đó. C3 thêm điều kiện B đúng từ ảnh gốc. A chỉ có một cảnh báo C3, ở arm random và B3 cũng phát hiện. C4 dùng phép tịnh tiến ảnh đã ghim. Thí nghiệm không có hai phiên bản rectifier để xác nhận regression phần mềm.

| Nhóm | Lượt | Trùng verdict | Cảnh báo A / B3 |
|---|---:|---:|---:|
| RapidOCR v4 | 40 | 23 | 5 / 22 |
| RapidOCR Latin v5 | 40 | 27 | 5 / 18 |
| Vintern partial_42 | 40 | 28 | 7 / 18 |
| address | 24 | 7 | 0 / 17 |
| dob | 6 | 6 | 1 / 1 |
| full_name | 15 | 9 | 2 / 8 |
| id_number | 42 | 30 | 13 / 25 |
| school | 33 | 26 | 1 / 7 |
| Một nguồn khai báo | 90 | 60 | 5 / 34 |
| Nhiều nguồn khai báo | 30 | 18 | 12 / 24 |
| Nguồn thuộc trường có body | 120 | 78 | 17 / 58 |
| Có duplicated body | 30 | 18 | 12 / 24 |
| Có MRZ | 30 | 18 | 12 / 24 |
| Body còn được hỗ trợ | 72 | 30 | 2 / 43 |
| Duplicated body còn được hỗ trợ | 18 | 6 | 6 / 18 |
| MRZ còn được hỗ trợ | 24 | 12 | 12 / 24 |
| Không có nguồn hỗ trợ còn lại hoặc chưa rõ | 36 | 36 | 3 / 3 |

Các nhóm nguồn chồng lấp. Số trong bảng dùng nguồn của trường đang chấm. Chúng không xác định reader đã lấy câu trả lời từ vùng nào. Kết quả theo seed, arm, operator và cặp trạng thái được lưu trong nhóm `groups`. [Audit JSON](execution/task55_audit/audit_run_01.json)

## So sánh phương pháp và chi phí

| Đối chứng | Chức năng và kết quả trên pilot |
|---|---|
| B0 conventional | Đối chiếu tham chiếu đầy đủ, 91/120 cảnh báo, gồm cả giá trị chủ đích bị che. Phản ánh lỗi chép theo full reference. Không có cảnh báo A nằm ngoài B0 trong panel này |
| B1 random | Bộ chọn ca ngẫu nhiên trên cùng miền ứng viên hợp lệ. Dùng chung checker A. A-conditioned 8/60 và B1 9/60 cảnh báo. Mỗi arm chịu 60 yêu cầu logic. Tính theo ảnh–reader duy nhất là 48 và 51 qua hai seed |
| B2 source-agnostic | 9/120 cảnh báo với gate chung. Có 6 giao với A, 11 riêng A và 3 riêng B2. Quy tắc từ chối theo mask danh nghĩa bỏ qua nguồn thay thế và có thể bỏ sót lỗi ở trường còn nguồn |
| B3 mạnh | Chấm sau biến đổi theo nguồn còn khả kiến và đối chiếu typed reference. Dùng chung cache, validation report, source state và matching. Không yêu cầu đầu ra ảnh gốc đúng trước khi chấm lỗi sau biến đổi |
| B3 legacy V3 / gated | Gọi mã V3 đóng băng qua adapter. Gated V3 trùng B3 chính trên toàn panel chính. Trong 12 dòng chẩn đoán, raw V3 bật 9 cảnh báo, gồm 6 ca quan hệ không hợp lệ và 3 ca backup bất định. Gate chung đưa cả A lẫn gated V3 về 6 INVALID_TEST và 6 INCONCLUSIVE |
| A_flat | B3 cộng điều kiện gốc đúng của C3/C4 và policy operator của C4. Trùng A 120/120 ở panel chính. Việc giữ trạng thái nguồn từ upstream làm đây là ablation biểu diễn tại biên oracle |

Không có chênh inference giữa A và B3 trên cùng execution set. Lượt audit có 3 lần timing chấm lại trên 132 cache pack, với median mỗi lần gọi A 11,49 / 13,27 / 14,21 ms và B3 0,070 / 0,075 / 0,071 ms. A có thêm provenance, hash và chẩn đoán. Đây là chi phí của hai triển khai cụ thể, chưa có ablation cân bằng tracing. TASK 5 đo 16,990 giây chuẩn bị chung, 1,032 giây chọn A và 0,841 giây chọn B1. Latency gốc quy về 60 yêu cầu logic lần lượt 148,321 và 143,688 giây. Worker chạy mới mất tổng 254,418 giây, gồm cả phần nạp và cache. Phút công review và chi phí trên lỗi xác minh chưa có mẫu số. [Chi phí pilot](DEVELOPMENT_PILOT.md) · [Timing audit](execution/task55_audit/audit_run_01.json)

## Giá trị có thể phân biệt

Trên cùng input, A làm rõ vì sao một lỗi giá trị có thể là vi phạm quan hệ. B3 vẫn phát hiện lỗi trường sau biến đổi kể cả khi đầu ra gốc đã sai. Hai endpoint phải báo riêng. Việc cùng một gate loại ca mất ngữ cảnh hoặc tẩy thiếu glyph cho thấy ích lợi kiểm tra phép thử, còn gated V3 đã thu được ích lợi này trên chẩn đoán hiện có. Bằng chứng về hiệu quả chọn ca theo ngân sách còn giới hạn bởi hai seed và cùng pool hợp lệ trước. [Audit tính độc lập](ORACLE_INDEPENDENCE_AUDIT.md)

Control mới tái hiện một nhánh khác biệt ngoài panel output lịch sử. Khi đầu ra khẳng định giá trị và chỉ các nguồn khai báo được che, oracle A bật cảnh báo ứng viên dù scope nguồn còn thiếu. B3 không bật. Nguồn dự phòng ngoài chú thích được xác nhận còn nguyên pixel trên fixture. Khác biệt này làm rõ chi phí triage khi scope thiếu. Nó không chứng minh A phát hiện thêm lỗi thật. [Control kết quả](DEVELOPMENT_STRESS_RESULTS.md)
