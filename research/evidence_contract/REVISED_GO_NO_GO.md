# Quyết định nghiên cứu sau phục hồi TASK 5.5

**NO-GO cho confirmatory của A theo claim phát hiện lỗi vượt baseline hiện tại. TASK 6 tiếp tục BLOCKED.** Tình trạng phần IFV là **BLOCKED_ON_HUMAN_REVIEW**. Phần kỹ thuật của audit, controls và thiết lập IFV đã thực hiện trong scope development. Quyết định giữ cổng vì cả hai điều kiện về nhãn độc lập và phần đóng góp phân biệt được với baseline mạnh vẫn chưa đạt.

| Điều kiện | Kết quả tại thời điểm này |
|---|---|
| Giải thích A/B3 và dùng baseline công bằng | Đã giải thích trên cùng cache và gate. A/B3 trùng 78/120 verdict. A/flat trùng 120/120. Gated V3 trùng B3 ở panel chính |
| Có nhãn đủ cho primary endpoint | Chưa có phiếu IFV. Không thể báo precision/FAR/sensitivity hoặc lợi ích từ 41 cảnh báo B3 riêng |
| Có bằng chứng phân biệt đóng góp | Cơ chế có kiểm thử, song A chưa phát hiện lỗi riêng trên các output model đã lưu. A-only triage ở fixture scope thiếu chứng minh rủi ro cảnh báo trên precondition chưa xác minh |
| Có version/fault provenance phù hợp RQ2 | Chưa có historical fault pool, quad hay patch/revert. Một mutation in-memory của oracle chỉ là control |
| Có kế hoạch test mới độc lập và đủ lực thống kê | Chưa khóa. Frame hiện tại chỉ là development và có 3 ID chính, 5 ID tính cả diagnostic |

## Điều kiện để TASK 6 có thể bắt đầu

1. Hoàn tất hai pha IFV trên ca có và không có cảnh báo. Phân xử độ phủ nguồn, readability, semantic mapping và validity trước khi tính metric. Báo exposure, thiếu phiếu và độ phủ mẫu. Một reviewer tự khai cho số mô tả pilot. Claim về độc lập cần người đánh giá thật khác hoặc nguồn chuẩn độc lập có thể kiểm chứng cho endpoint, tách machine-checkable controls khỏi review tự nhiên.
2. Phân tích A so với B3, V3 cùng gate và A_flat trên cùng nhãn. Phân biệt lỗi pointwise và vi phạm quan hệ. Ghi đủ mẫu số, chi phí người, abstention và tỷ lệ alarm trên ca không hợp lệ. Với claim chọn ca, đối chiếu B1 trên cùng quota và cache. Với claim regression phần mềm, bổ sung version quad và provenance của fault theo RQ2.
3. Chốt một claim có thể bác bỏ và có giá trị riêng trước baseline mạnh. Nếu vẫn không phân biệt được, đề xuất protocol prospective cho nghiên cứu về oracle validity hoặc failure characterization và giữ lịch sử này. Chỉ báo GO khi phạm vi claim, nhãn, ngân sách và nguồn dữ liệu mới đã rõ.
4. Sau **một quyết định GO mới**, TASK 6 mới lập exposure audit cho dữ liệu V1–V4, hard-pair, fair-controls, OCR-labels và development này. Cần manifest SPECIMEN độc lập về physical ID, nội dung, pixel và khi có thể cả layout/generator, cùng reviewer provenance, kế hoạch thống kê theo cụm, số inference, loại trừ và hash lock. TASK 7 chỉ mở khi xác minh khóa theo protocol.

Chưa tạo manifest confirmatory, test lock hoặc kết quả IFV. Không dùng kết quả control làm đường tắt qua gate. [Gate cũ](TASK6_GATE_REVIEW.md) · [Các bước còn lại](NEXT_ACTIONS.md)
