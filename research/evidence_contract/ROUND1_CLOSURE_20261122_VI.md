# Quyết định D1–D3 ngày 22/11/2026

**D1 DECIDED.** Chủ dự án đóng thu nhận kể từ 21/11/2026. AUTHOR, R02 và R03 mỗi người nộp đủ 86/86 quan sát và 46/46 ca. Hồ sơ đến sau thuộc Round 2 hoặc amendment có phiên bản. Đối chiếu byte của cả sáu bản gốc, snapshot nội dung và join theo từng người. Mỗi view pha 2 gắn hash bản gốc, bản chuẩn hóa và join. Riêng AUTHOR dùng hash publication organizer thời kỳ trước portable job.

| Thành viên | SHA-256 snapshot pha 1 | SHA-256 snapshot pha 2 | SHA-256 view dùng đóng vòng |
|---|---|---|---|
| AUTHOR | 00ff0a49d4df5a84c2d78511bcf2d9ed36e19945747a93c08d6788e3b9a9da79 | 812605bbab3940be838ac9da07ed903c0098717ace789f703f080869dde3267d | c2bc0cbc4c8615f4079f08c708e4a04bb9b775e7a97503afb3b0060039e45155 |
| R02 | b25d59d918c7cd0ba01702bc0c16b3c19acd973245ab2c7ebe83352dcbeb074b | 4813ecabf57899329f11dae31c47063154cfd35e51bbbd7982b10cd31827d3d1 | 4d7e52e736212ed015de23e5ca6fdc062b41621dc027e4f8e762ce437d4ec22c |
| R03 | d57613872163de808ce8c5ac9a5e9657f142b2d51264db1e10bc095eecd9e0b8 | 79cbb88301989080b2bc26931bc2bef4e3a76a1ab09c2134ba3b721ea07e081d | 7f6916259dc49a6fc878e354b39ac3f6e821a4d37fd61c26497f82da985e7f0b |

| Cặp | Nhìn thấy / đọc được / đúng trường trên 86 mục | Trùng cả 4 câu trả lời trên 46 ca | Trùng pointwise / relation trên 46 ca |
|---|---|---:|---|
| AUTHOR–R02 | 78 / 78 / 67 | 23 | 32 / 35 |
| AUTHOR–R03 | 80 / 80 / 82 | 19 | 33 / 34 |
| R02–R03 | 77 / 77 / 70 | 22 | 34 / 36 |

**D2 DECIDED.** AUTHOR là tác giả nội bộ. R02 và R03 là assessors. R02 tự khai 86/86 mục chưa gặp và chưa xem output. Vai trò ngoài dự án dựa vào đính chính của organizer. R03 khai đã gặp 68/86, chưa gặp 12 và chưa chắc 6. Tính độc lập còn chưa xác minh. Mỗi candidate C2 cần hai đề xuất riêng kèm khai báo exposure. Người phân xử phải khác cả ba. Chủ dự án giữ quyền duyệt reference và vai trò duyệt tách khỏi người đề xuất và người phân xử.

**D3 DECIDED.** Chuyển hồ sơ bất đồng, chưa chắc và mâu thuẫn giữa hai pha cho người phân xử. Hồ sơ riêng lưu 33 ca pha 2 cần xem và chi tiết cảnh báo coherence. Danh sách sàng lọc pha 1 so cả nội dung nguồn tự do nên có thể rộng hơn bất đồng phân loại. Gắn văn bản lý do và các hash bằng chứng vào basis_sha256 của quyết định ký. ACCEPT chỉ đề xuất candidate. REJECT loại đề xuất. UNRESOLVED giữ UNKNOWN. Mỗi reference cần sự kiện phê duyệt riêng và hồ sơ quyền. Đáp án và nhãn gốc được bảo toàn.

Intake CLOSED_BY_OWNER_DECISION. Agreement COMPLETE. Envelope SIGNATURE_PENDING. Adjudication PENDING. Reference được duyệt 0. Cấu hình production hiện có 0 authority. Bản canonical riêng đã gắn cả ba view. Hai trường authority_id và timestamp để null cho đến khi có định danh được chỉ định và thời điểm ký thật. Dùng unsigned_payload với hai giá trị thật, ký byte canonical rồi cung cấp envelope cho workflow.build_packet. Chỉ workflow.record_decision tiếp nhận quyết định ký của người phân xử. GO_PREPARATORY_ONLY và NO_GO_SUPERIORITY.
