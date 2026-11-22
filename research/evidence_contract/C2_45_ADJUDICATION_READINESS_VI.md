# Bàn giao chữ ký Round 1 và phân xử C2 · 22/11/2026

Round 1 đã đóng thu nhận theo D1, cutoff 21/11/2026. D2 và D3 có hiệu lực. Đã đối chiếu sáu bản gốc, ba view, 86 mục trong hàng đợi sàng lọc pha 1, 33 ca cần rà soát pha 2 và một coherence flag giữa hai pha. Giữ từng nguyên bản và căn cứ của hàng đợi. Các số này đo khối lượng xem xét. [Biên bản đóng vòng và ba hash view đầy đủ](ROUND1_CLOSURE_20261122_VI.md)

**Trạng thái vận hành.** `SIGNATURE_PENDING`, chưa có packet phân xử đã ký. Cấu hình production có 0 authority, chưa có public key được chỉ định cho round_owner, reviewer, adjudicator và reference_approver, chưa có checkpoint của nhật ký và chưa có chữ ký Round 1 thật. Hai assessor đã được chỉ định là R02/R03. Tính độc lập và exposure phải ghi riêng cho từng ca C2.

## Chủ dự án hoàn tất closure

1. Kiểm aggregate baseline `81557747d9f1a3467b0f6bdb0dad6f60805a9fe4`. Bản private `local/post_p6/run_20261122094004/closure_payload.canonical.json` có SHA-256 `ebce9c02ac81ec415ef40adf85fb68423b86201f0e35a7e53d5bb7eb0921f4c4`. Hai trường đang chờ là authority_id và timestamp.
2. Qua kênh được chủ dự án xác thực, chỉ định ID, vai trò và public key Ed25519 tương ứng. Giữ private key tại người ký. Chỉ định người phân xử khác AUTHOR, R02 và R03. Người duyệt cuối là chủ dự án, khác assessors và người phân xử. Lưu căn cứ danh tính, phân quyền, phiên bản protocol ở hồ sơ riêng.
3. Điền đúng authority_id của round_owner và thời điểm ký thật có múi giờ vào bản payload. Giữ nguyên round_id, cutoff_basis và danh sách hash. Dùng `reviewer_tools.strict.canonical(payload)` để lấy đúng byte UTF-8. Chủ dự án ký bằng công cụ của mình rồi bàn giao JSON gồm `payload` và `signature_hex`.
4. Organizer chạy từ gốc nghiên cứu, dùng tên run mới cho record ký.

```powershell
$py = '..\..\.venv\Scripts\python.exe'
& $py -X utf8 -B -m research.evidence_contract.human_gate.closure $newPrivateRun $ownerEnvelope
```

Adapter đối chiếu bản canonical, snapshot và roster rồi gọi `adjudication.workflow.build_packet`. Packet và envelope hợp lệ được khóa trong một record riêng. Sau đó, `workflow.record_decision` nhận quyết định ACCEPT, REJECT hoặc UNRESOLVED với evidence hash và văn bản lý do liên kết qua basis. UNRESOLVED giữ UNKNOWN. ACCEPT chỉ đề xuất reference.

## Hồ sơ C2 độc lập với phiếu IFV

Sau khi D10 cho phép truy cập, organizer chỉ cấp workspace của chính assessor theo chỉ đạo gửi riêng của chủ dự án. Mỗi người xem ảnh và điền bốn câu hỏi, nghĩa trường, độ chính xác, exposure theo ca, lý do và hash trước/sau. Mẫu có thể ghi UNKNOWN. Trang ngoại tuyến xuất từng ca thành JSON. Lưu riêng hai luồng nộp bài. Receipt của validator ghi digest nội dung. Khi có registry candidate thật, sự kiện `REVIEW_PROPOSED` do người được chỉ định ký phải dẫn digest của phiếu trong `basis_sha256`. Registry candidate ID và ID inventory được nối qua phiếu, field, source và pixel trước/sau. Trường hợp authority ID dùng mã khác R02/R03, adapter hỗ trợ bảng gán hai mã do round_owner ký và gắn baseline.

Sau khi có closure hợp lệ, hồ sơ quyền và hai đề xuất của đúng hai người, chuyển tranh chấp hoặc uncertainty cho người phân xử đã chỉ định. Kiểm sự kiện ký, hash căn cứ, candidate ID và binding trước khi chấp nhận trạng thái. Dùng registry hiện hành cho chuỗi REVIEWER_PROPOSED → ADJUDICATED → OWNER_APPROVED. Quyết định owner độc lập với adjudication, có rights_record_sha256 và checkpoint thật. Khi có dữ liệu mới, lập run kế tiếp, đối chiếu `reference_registry.approved_ids(candidates,events)` và tính lại đủ tám điều kiện cho từng candidate. [Quy trình reference](oracle_reliability/REFERENCE_WORKFLOW.md) · [Schema phiếu C2](human_gate/review.schema.json)
