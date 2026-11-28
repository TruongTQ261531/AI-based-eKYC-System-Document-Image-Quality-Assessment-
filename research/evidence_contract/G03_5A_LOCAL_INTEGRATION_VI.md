# G03.5A · Tích hợp local C2-37 có kiểm tra tương thích

**Pipeline Python đã nối đủ 37 candidate trên 18 giấy tờ theo thứ tự queue đã khóa. Frame đầu vào D4 có 0 ca.** 11 ca trên 11 ID vướng ô nguồn identifier và 26 ca trên 16 ID vướng precision của ngày. Một giấy tờ có thể xuất hiện ở cả hai nhóm. Tình trạng tiếp nhận phiếu thực tế nằm ngoài snapshot này. [Receipt thực thi và kiểm thử](human_gate/receipts/g03_5a_20261128/validation.json)

## Dữ liệu đi qua adapter như thế nào

1. `load_panel()` đọc queue theo thứ tự và đối chiếu hash selection, hồ sơ quyền, aggregate và cả hai manifest R02/R03 với bản C2-37 được ràng buộc trong receipt G04.5. Hàm kiểm membership và hash byte của 155 asset ở mỗi manifest. Chỉ các đường dẫn asset đã khóa được mở. Không duyệt thư mục tìm phiếu hoặc đọc HTML.
2. Mỗi dòng private giữ candidate, cụm physical ID, template, field, native key, vùng chính/dự phòng, precision hai nguồn, hash byte/pixel trước–sau và digest của toàn bộ item. Adapter đọc metadata VIA của ba template, kiểm chỉ mục vùng, mapping và chỉ hỏi frozen parser về **đúng kind đã khóa**. Identifier được so với ô số giấy tờ TD3. Ngày đầy đủ được kiểm ở `date_full`; kết quả là unsupported. Các tổng theo ca và ID phải khớp G04.5 trước khi trả panel. Receipt chỉ xuất digest gộp của các dòng theo thứ tự. [Adapter local](human_gate/integration37.py) · [Căn cứ G04.5](G04_5_C2_37_COMPATIBILITY_AUDIT_VI.md)
3. `snapshot()` lập bảng theo các điều kiện riêng bên dưới. Cả hai endpoint đều có `metrics: null` trong kết quả tương ứng. Guard chỉ đếm các điều kiện đầu vào; module không có lệnh gọi đánh giá D4. Nhờ đó một phiếu hợp lệ, một checkpoint hoặc một cặp OCR đủ phía đều không thể biến lỗi trường/precision thành đủ điều kiện. [Protocol phân tích](C2_37_ANALYSIS_PROTOCOL_VI.md)

| Trục | Kết quả (ca/ID) | Căn cứ và thời điểm |
|---|---:|---|
| Ghi danh | 37/18 | Queue giữ đủ thành viên, kể cả khi thiếu chứng cứ |
| Tương thích D4 | 0/0 | Kiểm lại từng dòng local với field, nguồn và precision gốc |
| Eligibility C2 | 0/0 tại thời điểm khóa | Đủ tám điều kiện mới được tính; bốn quan sát nguồn và semantic đều UNKNOWN. Chỉ dùng phân bố theo ca khi cả panel có cùng trạng thái trên điều kiện đó |
| D10 | 37/18 pending tại thời điểm khóa | Hash hồ sơ quyền và aggregate của chính gói 37 |
| Reference | 0/0 được duyệt tại thời điểm khóa | Kiểm thêm cấu hình trust hiện hành. Registry chưa có authority, protocol approval hay journal checkpoint |
| Paired output | 0/0 đã xác minh trong preflight cache | Kế thừa báo cáo đã ghim hash. Cache một phía vẫn có thể tồn tại; G03.5A không mở raw OCR |
| Truth độc lập | 37/18 chưa cung cấp cho adapter | Không suy truth từ reference, phiếu, compatibility hay trạng thái oracle |

Membership và các blocker đều đếm theo candidate và ID riêng biệt. Việc thiếu truth chỉ ảnh hưởng phép tính cần truth. Không diễn giải 37 ca bị chặn thành 37 lần oracle trả UNKNOWN. Báo cáo preflight xác định phiên bản và phạm vi nguồn cache đã kiểm. [Preflight cache](C2_37_OCR_CACHE_PREFLIGHT_VI.md)

## Tiếp nhận phiếu và thẩm quyền trên fixture

Đường fixture chỉ nhận item tổng hợp và submission trong bộ nhớ. Trước khi đọc nội dung, adapter yêu cầu quyền chia sẻ và lưu phiếu của fixture. Validator phiếu hiện có kiểm candidate, digest toàn item, bằng chứng hai phía và câu trả lời. Adapter kiểm chữ ký Ed25519 theo reviewer được gán, đúng manifest, role, item và digest nội dung. Hai vai trò phải dùng hai khóa riêng. Registry verifier phát lại journal trong miền SYNTHETIC và so head với checkpoint do harness cung cấp ngoài submission. Phiếu có chữ ký và journal rỗng hợp lệ vẫn cho `approved_reference=False`. Kiểm thử gồm sự kiện đã ký viện dẫn candidate chưa đăng ký, rollback checkpoint, tráo người ký và sửa nội dung. Chưa triển khai liên kết proposal hay quyết định reference thật cho C2-37. [Adapter fixture](human_gate/integration37_fixture.py)

Đường fixture output kiểm hash byte/pixel của đúng phía, reader/version, checkpoint, config, preprocessing, runtime và digest nội dung. Kiểm thử riêng trường hợp thiếu một hoặc hai phía, tráo ảnh, đổi checkpoint và sửa output. Với mọi điều kiện đầu vào khác giả định đạt, riêng mỗi lỗi nguồn/precision vẫn loại ca khỏi **frame D4**, đồng thời giữ ca trong panel C2. [Tests](tests/test_g03_5a_integration.py)

## Kiểm chứng và bàn giao G03.5B

Trên máy organizer, chạy `python -B -m research.evidence_contract.human_gate.integration37` từ gốc repo để thu lại snapshot tổng hợp. So JSON trên stdout với trường `snapshot` của receipt. Bốn module kiểm thử chạy bằng fixture công khai, **96 tests và 12 subtests đạt**, 0 lỗi, 0 bỏ qua. Receipt ghi lệnh, phiên bản Python, hash mã và tests. [Receipt](human_gate/receipts/g03_5a_20261128/validation.json)

G03.5B có thể dùng adapter này để mô tả panel và chuẩn bị kiểm tra nhập phiếu. Trước khi tiếp nhận thật cần đối chiếu quyết định D10 theo đúng phiên bản artifact, quyền lưu, danh sách người nhận, khóa được chỉ định và checkpoint production. Khi có thẩm quyền mới nối từng proposal đã ký với item, phân xử và reference đã được chủ dự án duyệt. Thống kê lỗi đầu ra còn cần cặp output đã xác minh và truth độc lập cho các estimand dùng truth. Cần chốt cách diễn giải frame trước khi xem kết quả mới. [Handoff G03](G03_V2_HANDOFF_20261124_VI.md)

**Blocker D4 vẫn tồn tại ngay cả khi đủ phiếu.** Giữ phân tích mô tả nguồn cho 37/18. Muốn kiểm một câu hỏi khác về ngày YYMMDD hay optional data cần amendment và review riêng. G03.5A dừng ở PREPARATORY ONLY, giữ GO_PREPARATORY_ONLY, NO_GO_SUPERIORITY, P5B INFEASIBLE và TASK 6B/7B BLOCKED.
