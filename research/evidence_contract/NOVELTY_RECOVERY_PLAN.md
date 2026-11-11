# Các hướng phục hồi đóng góp sau audit

Kết quả đã có ích cho EASE theo hướng kiểm thử phần mềm. Trên panel có nguồn khớp, một checker phẳng và gate chung đủ tái hiện toàn bộ verdict chính của A. Khi thay đổi ngữ cảnh semantic hoặc inventory nguồn không đầy đủ, điều kiện phép thử và chính sách triage có thể thay đổi cả kết luận. Đây là quan sát development trên fixture nhỏ. Nó đặt ra câu hỏi về soundness của oracle trong pipeline tài liệu, với đơn vị lỗi và phán đoán độc lập xác định được. [A/B3](A_VS_B3_DIAGNOSIS.md) · [Controls](DEVELOPMENT_STRESS_RESULTS.md)

| Phần | Điều đã có | Giới hạn và việc cần chứng minh |
|---|---|---|
| RQ1 chất lượng oracle | Sanity check MRZ đúng, gate loại ca che sai, phát hiện điểm yếu chung của matcher. Có IFV hai pha để thu nhãn độc lập | Đo FAR, sensitivity và coverage cùng lúc trên nhãn đủ bằng chứng. B3 mạnh, V3 cùng gate và A_flat là đối chứng bắt buộc. Nếu giảm cảnh báo chủ yếu do abstain, lợi ích giảm báo sai chưa được hỗ trợ |
| RQ2 regression và lan truyền lỗi | Endpoint quan hệ C3/C4 giải thích trường hợp gốc sai. Tịnh tiến và shared context kiểm tra cơ chế. Có một fault chèn ở chính matcher của tester | Để claim software fault, cần ít nhất version quad với cùng pixel, điều kiện activation hoặc bug–patch–revert và nhãn intended behavior độc lập. Chấm theo root-cause family. Khi thiếu bằng chứng thì giữ phân tích hành vi và lớp nguyên nhân chưa xác nhận |
| RQ3 hiệu quả bộ sinh | Có random masking cùng pool và ngân sách, 8 so với 9 ứng viên ở pilot | Đo thêm chi phí chuẩn bị, rejected proposals, annotation, duplicate/cache và lỗi xác minh theo quota. Nếu lợi ích mất khi cùng gate và cùng budget, không mở rộng thiết kế hiện tại |

## Phương án nếu RQ hiện tại vẫn không được hỗ trợ

Ưu tiên nghiên cứu thu hẹp về **độ hợp lệ của oracle và phân loại cảnh báo**. Một phép thử khả bác bỏ là đo bao nhiêu cảnh báo thay đổi khi bổ sung các nguồn bị bỏ chú thích hoặc ngữ cảnh semantic đã xác minh, dưới cùng output, validity gate và mức coverage. B3/gated V3/A_flat được hưởng cùng nhãn. Nếu oracle đơn giản có cùng độ hợp lệ, chi phí và khả năng phân loại, kết quả hợp lệ là negative/replication trên pipeline tài liệu, thay vì claim thuật toán mới. Cần protocol prospective và đồng ý lại framing trước test mới.

Hướng phân tích lỗi lan qua stage chỉ đáng theo nếu có version và fault provenance thật hoặc mutant pipeline độc lập đủ đa dạng. Đặt giả thuyết mới về thời gian triage hoặc độ chính xác xác định stage trên cùng pack, đo với per-field baseline có cùng thông tin. Earliest divergence chỉ là quan sát. Bộ controls hiện tại không đủ để chuyển hướng này tự động.

Điểm novelty của dataset khả thi nằm ở schema provenance và tập phép thử có khả năng phân biệt các trường hợp như source lặp, context chia sẻ, MRZ và annotation scope thiếu. Tập pilot chỉ chứng minh schema chạy được. Trước khi claim dataset, cần SPECIMEN mới, kiểm exposure, tài liệu về quyền, provenance, nhãn độc lập và phân nhóm nguồn/định dạng/thiết bị thực sự thu thập được.
