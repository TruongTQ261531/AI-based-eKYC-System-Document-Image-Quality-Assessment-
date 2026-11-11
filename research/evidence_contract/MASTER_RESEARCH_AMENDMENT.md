# Amendment prospective sau master_01

Giữ lịch sử và RQ của A. Phạm vi bổ sung gồm control M1–M7, stage pilot có giới hạn trên development, prep 6A, replay 7A và paper 9A. Pilot stage không thuộc IFV và không đi vào primary comparison. Các lựa chọn dưới đây chỉ dùng cho quyết định nghiên cứu kế tiếp.

| Hướng | Bằng chứng ủng hộ | Điều có thể bác bỏ / quyết định |
|---|---|---|
| A là hướng chính | Có schema source, phép thử admissibility, hai endpoint và audit có thể replay | A_flat trùng A 120/120. Gated V3 mạnh. Chưa có lỗi field riêng, lợi ích FAR/coverage/yield hoặc cost đã xác minh. **Giữ hướng chính, NO-GO confirmatory** |
| A+B có điều kiện | Can thiệp M2 tạo mất nguồn, trace phân biệt thiếu bằng chứng và output đã sai dù còn vùng | Cần so với cùng metadata ở flat baseline, thêm lỗi vùng còn và stage/version provenance. Đo chính xác triage và thời gian. **Giữ exploratory** |
| B là hướng chính | Có thể phù hợp nếu giải thích lỗi có giá trị riêng ngoài việc chấm field | Hiện có 1 reader CPU, 3 ID, 0 target đọc đúng trước crop. Chưa có cơ sở đổi hướng chính. Cần protocol mới và quyết định sau IFV |

Contribution đáng kiểm chứng nhất là **định lượng tác động của tiền điều kiện nguồn và cách xử lý bất định lên độ tin cậy của test oracle**, trên baseline mạnh được cấp cùng annotation. Nếu flat gate tái hiện đầy đủ, công bố boundary condition dưới dạng nghiên cứu thực nghiệm hoặc kết quả âm có cỡ mẫu đủ. Đừng quy equivalence về quần thể từ pilot. MR synthesis, localization và data fault injection đã có trong prior work, nên phần khác biệt phải nằm ở bằng chứng thực nghiệm domain, cách phân biệt nguyên nhân và điều kiện áp dụng. [Prior work đã rà](RELATED_WORK.md) · [GenMorph](https://search.usi.ch/index.php/en/publications/56279) · [LMDX](https://aclanthology.org/2024.findings-acl.899/) · [Data fault injection](https://researchportal.helsinki.fi/en/publications/software-framework-for-data-fault-injection-to-test-machine-learn/)
