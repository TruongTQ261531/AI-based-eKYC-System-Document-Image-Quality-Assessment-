# Protocol B v3 · Đánh giá độ tin cậy của oracle OCR

**Quyết định ngày 21/11/2026.** Chủ dự án đã chọn ba ngưỡng và năm trần tài nguyên ở dưới cho bản thiết kế. Quyền chạy prospective hiện bằng 0. Phiên bản này kế tiếp [v2](B_PROSPECTIVE_PROTOCOL_DRAFT_v2_20261117.md). Cổng khoa học vẫn là `NO_GO_SUPERIORITY`. Các lựa chọn về panel, thống kê và xử lý thiếu dữ liệu dưới đây là quyết định thiết kế kỹ thuật cho v3. Mọi thay đổi cần ghi thành phiên bản trước khi xem kết quả mới.

## Câu hỏi và đối chứng

Khi thông tin khai báo về vùng máy đọc bị lỗi, kiểm lại literal TD3 có giảm cảnh báo sai về **giá trị trường trên ảnh sau biến đổi** mà vẫn đưa ra đủ kết luận và bắt đủ lỗi OCR không? Đơn vị là một ca ghép cặp gồm giấy tờ, trường, ảnh trước/sau, phép biến đổi, phiên bản reference và đầu ra của cùng một reader. Hai arm nhận cùng tất cả đầu vào, cùng chi phí tạo nhãn và cùng tier. Truth đánh giá được giữ riêng.

| Arm | Khác biệt được phép | Vai trò |
|---|---|---|
| Checked v2 | Đọc literal, kiểm cấu trúc TD3, checksum, giá trị và độ chính xác của trường | Phương pháp đánh giá, tier 1 |
| MRZ metadata asserted | Dùng giá trị đã khai ở đúng điểm phân giải MRZ với cùng profile kiểu/precision | Baseline chính, tier 1 |
| Tier 2 của cả hai | Đổi cùng ngưỡng yêu cầu về nguồn | Phân tích độ nhạy mô tả |
| Flat dùng chung guard và A/A_flat/B3 lịch sử | Giữ định nghĩa và tập mẫu từng mốc | Bối cảnh kỹ thuật |

Hai arm chính dùng chung kiểm tra thẩm quyền, liên kết ảnh/trường/phép biến đổi, parser, xung đột nguồn, semantic key và tính hợp lệ của chuyển tiếp. D4 đã có 13 guard chung và một can thiệp literal. [Ma trận thực thi](execution/master_01/d4_development_20261117/controls_01/guard_matrix.json)

## Khung mẫu và thu nhận truth

Panel chính là panel *lỗi reference được chủ động tạo* của TD3 trên giấy tờ có quyền. Với mỗi ID, chọn tối đa một ca cho mỗi loại đã định trước: literal sai checksum, thiếu literal, giá trị khai báo lệch literal, định dạng literal hỏng. Lập danh sách ứng viên và loại biến đổi khả dụng trước khi chạy reader. Trong mỗi loại, chọn trường đủ điều kiện theo thứ tự hash của khóa ID–field–mutation với seed 20261121. Cố định manifest, thứ tự và phiên bản reader trước khi xem output. Mỗi ca đóng góp một hàng, trọng số bằng nhau; báo số hàng theo loại và ID. Phân bố khuyết tật này chỉ hỗ trợ kết luận có điều kiện trên panel.

Reference gốc phải có provenance, quyền, ảnh và vùng nguồn xác định. Bản can thiệp phải có phiên bản, log thay đổi và phạm vi sử dụng cho thử nghiệm do người có thẩm quyền duyệt. Người xác minh chứng cứ vùng không được xem kết luận của arm. Người gán truth lỗi OCR so đầu ra với chứng cứ độc lập, mù với arm và loại can thiệp. Hai kết quả của arm luôn được ghép theo cùng khóa ca. Phiếu bất đồng chỉ trở thành truth sau quy trình phân xử đã duyệt. Giữ truth chưa xác định là null. Đối với C2 cần đủ tám điều kiện ở [audit nguồn](P2_AUDIT_VI.md). Hiện số cặp đủ điều kiện bằng 0.

Chỉ lấy ID có quyền sử dụng phiên bản cụ thể và đáp ứng quy tắc exposure được duyệt. Nhóm mọi crop/frame/field của cùng giấy tờ dưới một ID. Kiểm nguồn cha, pixel trùng và ứng viên gần trùng trước khi chia tập. Nếu hai ID có cùng nội dung chưa giải thích được thì giữ ngoài khung xác nhận, ghi mẫu số loại. Nếu nhiều ID phụ thuộc cùng template/capture, báo kết quả từng nhóm và kiểm độ nhạy ở mức nhóm trước scientific lock. Dữ liệu lịch sử, gồm ba ID chính có phiếu, phục vụ development.

## Tiêu chí và mẫu số

Trên **cùng panel pointwise tier 1 đã ghi danh**, đặt D là số ca, F là số ca có truth lỗi, N là số ca có truth không lỗi. Một arm báo động khi trả FAULT. UNKNOWN và INVALID_TEST là hai trạng thái riêng. Ca chưa rõ truth vẫn ở mẫu số coverage. Ca có truth lỗi nhưng arm hoãn kết luận vẫn ở F. Một trường hợp không có đầu ra cho một hay hai arm phải có biên bản thiếu kết quả và dừng đánh giá ngưỡng đến khi tái lập được frame ghép đầy đủ; không tự mã hóa timeout thành quyết định của oracle.

| Tiêu chí thiết kế do chủ dự án chọn | Đại lượng | Điều kiện trên cận dưới một phía 95% |
|---|---|---|
| Coverage checked | (FAULT + NO_FAULT của checked) / D | ≥ 0,80 |
| All-fault sensitivity checked | FAULT của checked trên lỗi có truth / F | ≥ 0,80 |
| Giảm FAR tuyệt đối | (Số cảnh báo asserted − số cảnh báo checked) trên cùng N ca không lỗi, chia N | **> 0,05** |

Phải đạt cả ba trên cùng panel. Biên đúng 5 điểm phần trăm chưa đạt. Báo kèm FAR và sensitivity của từng arm, số hoãn, số invalid, truth availability và selective risk (quyết định sai / quyết định có truth). Mẫu số bằng 0 cho NA. Relation, structure, tier 2 và từng loại can thiệp là kết quả phụ mô tả. Nếu phải hoãn nhiều khi nguồn lỗi, tiêu chí coverage có thể thất bại dù FAR thấp. Với truth thiếu, trình bày thêm khoảng nhạy cảm khi gán cực trị cho phần thiếu trước mọi diễn giải ra ngoài tập có nhãn.

Phép phân tích tính tỷ số từ tổng đếm, lấy lại mẫu toàn bộ cụm physical ID cùng hai arm, đều xác suất giữa các ID, có hoàn lại. Dùng 10.000 lượt, seed 20261121, phân vị thứ 5 theo nearest rank. Một phép quyết định đồng thời yêu cầu vượt cả ba điều kiện (intersection–union). Không chọn endpoint sau khi xem dữ liệu. Nếu có dưới 30 cụm đóng góp cho F hoặc N, có bất kỳ lượt bootstrap thiếu mẫu số, hoặc một phân bố bootstrap suy biến, báo `INSUFFICIENT_INFORMATION`. Đây là chốt bảo thủ để ngừng suy luận. Trước scientific lock vẫn cần kiểm sai số loại I và độ phủ khoảng bằng mô phỏng theo phân bố cụm, tỷ lệ lỗi, truth thiếu và tỷ lệ bất đồng phù hợp. [Mã tính và mẫu số](oracle_reliability/protocol_v3.py)

### Đầu vào để tái lập phép tính

Từ gốc repository, chạy `python -B -m research.evidence_contract.oracle_reliability.protocol_v3 frame.json` trên bản chiếu pointwise tier 1 đã kiểm tính đầy đủ. JSON là mảng các hàng ghép cặp, mỗi hàng có `case_id` duy nhất, `physical_id`, `truth` (true/false/null) và hai trạng thái `checked_v2`, `mrz_metadata_asserted`. Bước tạo frame phải đối chiếu danh sách case ID với manifest, kiểm reference/rights và xác minh nhãn trước khi gọi hàm thống kê. Mã thống kê trả số đếm từng arm, khoảng cực trị do thiếu truth và kết quả thiết kế. Với 1 ca không lỗi, checked trả UNKNOWN và asserted trả FAULT, chênh lệch FAR bằng 1, coverage checked bằng 0 và sensitivity bằng NA. [Ví dụ kiểm thử trên ca dựng sẵn](tests/test_protocol_v3.py)

## Ngân sách và quy tắc dừng

Nếu có hơn 200 ID đủ điều kiện, sắp theo SHA-256 của chuỗi UTF-8 `20261121|physical_id` (thay `physical_id` bằng mã chuẩn trong manifest), lấy 200 ID đầu. Nếu ít hơn, giữ tất cả ID đủ điều kiện và đánh giá lại độ chính xác trước khi khóa. Chọn ca trong mỗi loại theo cùng quy tắc với chuỗi `20261121|physical_id|field|mutation`. Mã, trường và loại mutation trong manifest phải có biểu diễn chuẩn duy nhất trước bước này.

| Trần thiết kế được chủ dự án chọn | Cách hạch toán |
|---|---|
| 200 physical ID × tối đa 4 ca/ID | Tối đa 800 hàng chính, một reader, một lần lấy đầu ra cho mỗi ảnh–reader duy nhất |
| 1.600 lượt đọc ảnh | Hai ảnh/ca × 800 ca. Tái sử dụng đầu ra đã khóa cho cả hai arm. Mọi lần gọi thực, kể cả lỗi và retry, tính vào trần |
| 120 giờ công | Cộng phút hoạt động của mọi người cho chuẩn bị, gán nhãn, kiểm tra và phân xử |
| 7 ngày chạy | Thời gian liên tục từ lúc bắt đầu chạy đã được phê duyệt |
| 50 GiB | Dung lượng tối đa của đầu ra, log, cache và bản trung gian mới trong lần chạy |

Dừng ở điều kiện đến trước: hết manifest, chạm bất kỳ trần nào, mất quyền, thay đổi hash reader/reference hoặc mất ràng buộc giữa hai arm. Ghi lại số ca kế hoạch, đã chạy, lỗi, thiếu truth và lý do dừng; không thêm ID theo kết quả. Trước khi mở, phải kiểm thiết kế có đủ độ chính xác trong các trần: với 800 ca và giả định 5% lỗi, 90% có nhãn, kỳ vọng chỉ 36 hàng lỗi trước điều chỉnh tương quan. Con số này chưa bảo đảm 30 ID mang lỗi. Nếu không khả thi, báo mô tả hoặc sửa protocol trước dữ liệu. [384 kịch bản sizing và các giả định](B_SIZING_AND_POWER_DRAFT_20261117.md)

## Trạng thái phê duyệt

D4–D9 có đặc tả thiết kế v3. Các trần là mức tối đa trên giấy; không có ngân sách chạy được cấp. Round 1 chờ D1–D3 về cutoff, thẩm quyền reference và phân xử. D10–D12 còn quyền theo artifact, quy tắc exposure, phạm vi claim/track và quyết định khoa học. Chỉ sau các quyết định này, quyền chạy riêng, xác minh tính khả thi, manifest và reader cụ thể mới có thể tạo scientific lock. [Biên bản trạng thái checklist](CHECKLIST_P0_P4_20261121.md)
