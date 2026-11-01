# Phạm vi đóng góp và đối chiếu nguồn gốc

Đọc nguồn gốc ngày 01/11/2026, trước khi mở test R2/V3. Đây là rà soát có
giới hạn, không phải chứng minh không còn công trình tương tự.

| Nguồn | Đã làm gì | Phần nghiên cứu này cần phân biệt |
|---|---|---|
| [KIE-HVQA, He et al., NeurIPS 2025](https://arxiv.org/abs/2506.20168) | Benchmark thông tin bị suy giảm trên giấy tờ và huấn luyện SFT/GRPO để giảm hallucination. | Không nhận việc fine-tune mô hình với ảnh che/cắt hoặc chống bịa OCR là mới. Thử nghiệm ở đây đo ảnh hưởng của hợp đồng nhãn nhiều nguồn trên cùng pixel, cùng ngân sách. |
| [BoundingDocs, Giovannini et al., IJDAR 2025](https://flore.unifi.it/retrieve/271bfa4d-4b12-4bd3-8ec1-a5f64ce8ca0b/s10032-025-00563-5.pdf) | Mục 3.2.2 chấp nhận nhiều vị trí trả lời; mục 3.4 kiểm tra trường hợp trùng chữ nhưng khác ý nghĩa. | Không nhận OR giữa vị trí là phát minh đầu tiên. V3 giới hạn liên kết bằng semantics gốc và TD3, kiểm tra mất từng nguồn và độ đầy đủ của ngày; vẫn thiếu kiểm tra legibility độc lập. |
| [Improving OCR using internal document redundancy, Belzarena et al., 2025](https://arxiv.org/abs/2508.14557) | Dùng sự lặp lại của hình dạng ký tự, GMM/EM và căn chỉnh cụm để cải thiện OCR tài liệu suy giảm. | Đây là redundancy ở mức hình dạng ký tự, không phải cùng thuật toán MRZ/nhãn V3. Không mô tả sai thành nghiên cứu chỉ về trường định danh lặp lại. |
| [ICAO Doc 9303 Part 4, bản hợp nhất có sửa đổi 2026](https://www.icao.int/sites/default/files/publications/DocSeries/9303_p4_cons_en.pdf) | Quy cách TD3, vị trí trường và chữ số kiểm tra; ngày MRZ dùng năm hai chữ số. | Parser/checksum là kiến thức chuẩn, không phải novelty. Checksum không chứng minh giấy tờ thật; không thêm thế kỷ từ YYMMDD. |
| [MIDV-2020, Arlazarov et al.](https://arxiv.org/abs/2107.00396) | Giấy tờ mẫu và ảnh/video có annotation do tác giả cung cấp. | Đây là phép biến đổi/đánh giá mới trên dữ liệu có sẵn, không phải thu thập người thật mới hoặc tạo ra các giấy tờ gốc. Giữ attribution và license nguồn. |

Giả thuyết có thể kiểm chứng: nhãn gắn với một vùng có thể làm sai cả mục tiêu
huấn luyện lẫn cách đếm lỗi khi thông tin còn tồn tại ở nguồn khác. Hai model
V3 chỉ đổi giám sát, giữ nguyên ảnh và ngân sách so với R2 partial cùng seed.
Hiệu quả và độ lớn sai lệch phải lấy từ kết quả đã audit; kết quả âm cũng giữ lại.
Đồ thị nguồn, độ chính xác ngày và kiểm soát thực nghiệm là đóng góp ứng viên,
chưa có cơ sở để khẳng định đủ CORE B trước phản biện và kiểm chứng rộng hơn.
