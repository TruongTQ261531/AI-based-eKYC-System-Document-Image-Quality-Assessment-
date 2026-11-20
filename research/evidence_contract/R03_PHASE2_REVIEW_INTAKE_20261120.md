# Kết quả khảo sát R03 pha 2 · 20/11/2026

R03 đã hoàn tất 46/46 ca pha 2 sau khi chấm 86/86 mục trên 31 ảnh ở pha 1. Cả tác giả, R02 và R03 đã nộp đủ hai pha. Có 42 ca chính trên 3 giấy tờ và 4 ca chẩn đoán. Round 1 đang mở, chờ quyết định chốt bộ phiếu và phân xử. [Biên bản tiếp nhận](execution/master_01/reviewer_intake_20261120_r03_phase2/intake_summary.json)

## R03 đánh giá đầu ra OCR thế nào?

Trên ảnh biến đổi của 46 ca, R03 chọn đúng hoặc để trống phù hợp ở 21 ca, bỏ sót giá trị đọc được ở 11 ca, sai giá trị ở 10 ca, điền giá trị dù đã xác minh hết nguồn ở 3 ca và chưa xác định ở 1 ca. Về điều kiện kiểm thử, R03 ghi nhận 35 ca hợp lệ, 4 ca không hợp lệ và 7 ca chưa đủ bằng chứng. Đây là các lựa chọn trực tiếp trên phiếu.

Khi áp dụng quy tắc của dự án cho **42 ca chính**, việc kết luận còn phụ thuộc vào chữ đọc được, nguồn còn lại và điều kiện của phép biến đổi. Với tiêu chí thứ hai trong bảng, một số phép thử còn đòi hỏi đầu ra trên ảnh gốc phải đúng mới đánh giá được tác động của phép biến đổi.

| Tiêu chí | Lỗi theo phiếu và quy tắc | Không lỗi | Chưa kết luận | Phép thử không hợp lệ |
|---|---:|---:|---:|---:|
| Giá trị trường trên ảnh biến đổi (pointwise) | 10 | 13 | 17 | 2 |
| Quan hệ giữa ảnh gốc và ảnh biến đổi (relation) | 4 | 13 | 23 | 2 |

Riêng 4 ca chẩn đoán, tiêu chí quan hệ có 2 ca chưa kết luận và 2 ca không hợp lệ. Đối chiếu bản chép pha 1 với lựa chọn pha 2 của R03 phát hiện 1 ca chính được đánh dấu đúng dù chuỗi đầu ra và bản chép khác nhau. Ca này được giữ để người phân xử xem lại.

## R02 và R03 đồng ý ở đâu?

Hai phiếu được ghép theo cùng giấy tờ, trường và cặp đầu ra của từng ca. Bảng tính trên 42 ca chính, tính cả khi hai người cùng chọn chưa kết luận hoặc cùng xác định phép thử không hợp lệ. κ là hệ số đồng thuận Cohen. [Bảng đối chiếu R02–R03](execution/master_01/reviewer_intake_20261120_r03_phase2/r02_r03_agreement.json)

| Tiêu chí | Số ca khớp / 42 | κ |
|---|---:|---:|
| Điều kiện của phép thử | 31/42 | 0,250 |
| Đánh giá giá trị trên ảnh gốc | 30/42 | 0,568 |
| Đánh giá giá trị trên ảnh biến đổi | 35/42 | 0,754 |
| Xác minh còn nguồn hay đã hết nguồn | 42/42 | 1,000 |
| Kết luận về giá trị trên ảnh biến đổi | 32/42 | 0,670 |
| Kết luận về quan hệ giữa hai ảnh | 34/42 | 0,713 |

Ở tiêu chí giá trị trên ảnh biến đổi, có 22 ca chính mà cả hai cùng đủ bằng chứng kết luận lỗi hoặc không lỗi. Họ đồng ý 21 ca và kết luận ngược nhau ở 1 ca. Ở tiêu chí quan hệ, cả hai đưa ra được kết luận lỗi hoặc không lỗi ở 17 ca và đồng ý cả 17.

Trên toàn bộ 46 ca, R02 và R03 khác nhau ở ít nhất một trong sáu tiêu chí trên ở 26 ca. Xét cả ba người, kết luận trùng nhau ở 26/42 ca chính về giá trị và 29/42 ca chính về quan hệ giữa hai ảnh. R03 khai đã gặp ảnh hoặc giá trị ở 68/86 mục pha 1. Kết quả mô tả sự đồng thuận trên bộ khảo sát nhỏ này. Tính độc lập và độ chính xác OCR trên giấy tờ mới còn cần đánh giá riêng. [Đối chiếu tác giả–R03](execution/master_01/reviewer_intake_20261120_r03_phase2/author_r03_agreement.json) · [Phiếu pha 1](R03_PHASE1_REVIEW_INTAKE_20261120.md)

## Tiếp nhận và việc còn lại

Tệp ZIP của R03 được khôi phục từ nội dung gói còn lưu. SHA-256 của ZIP khớp dấu kiểm đã ghi khi phát. Công cụ tiếp nhận đã kiểm tra gói, snapshot pha 1 của R03, đủ 46 mã ca duy nhất và bản xuất hoàn chỉnh. Bản lưu riêng khớp từng byte với tệp người dùng gửi. Việc tính lại từ các phiếu đã khóa cho cùng bảng đối chiếu tác giả–R02 như mốc 17/11.

Danh sách các ca bất đồng được lưu riêng cho bước phân xử. Chủ dự án cần chốt phạm vi và thời điểm khóa vòng (D1), chỉ định người có thẩm quyền (D2) và duyệt quy tắc xử lý bất đồng (D3). Ca kết luận ngược nhau là một điểm cụ thể để xem xét khi phân xử. [Các quyết định của chủ dự án](B_OWNER_DECISIONS_20261117.md)
