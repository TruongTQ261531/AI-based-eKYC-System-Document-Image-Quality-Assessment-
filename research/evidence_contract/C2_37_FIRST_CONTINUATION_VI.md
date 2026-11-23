# C2-37-first · Tiếp tục nghiên cứu B khi quyền mẫu Hy Lạp chưa được xác nhận

**Quyết định định hướng của chủ dự án, 23/11/2026 (chưa phải D10 approval hay chữ ký điện tử):** Ưu tiên tiến độ Research Papers EASE 2027 dựa trên phạm vi không chứa sáu giấy tờ Hy Lạp. Không khởi động xin phép mẫu Hy Lạp trong nhánh hiện tại; không hủy hồ sơ 45 ca. Chỉ mở lại vấn đề quyền của tám ca nếu có một lý do khoa học được xác định độc lập, và phải qua phê duyệt quyền/trình tự mới trước bất kỳ lần chia sẻ hay bổ sung phân tích nào.

## 1. Bốn phạm vi phải giữ khác nhau

| Nhãn phạm vi | Số candidate | Số physical IDs | Vai trò | Trạng thái |
|---|---:|---:|---|---|
| C2_MASTER_45 | 45 | 24 | Snapshot gốc, bao gồm 8 ca Hy Lạp; không chỉnh sửa/ghi đè | FROZEN_HISTORICAL |
| C2_37_PROPOSED | 37 | 18 | Phạm vi ưu tiên, không gồm 6 giấy tờ Hy Lạp | PREPARATION_ONLY; D10 pending |
| C2_GREEK_HOLD_8 | 8 | 6 | Trạng thái quyền chưa rõ; không cấp reviewer, không đưa vào kết quả chính | HOLD_RIGHTS |
| C2_45_FUTURE | 45 | 24 | Chỉ có thể trở thành phạm vi nghiên cứu mới sau bằng chứng quyền và amendment phù hợp | NOT_AUTHORIZED |

Số 37/18 là phép loại trừ dựa trên audit nguồn; **không** được suy diễn 37 đã có đủ quyền. Quyền chân dung Generated Photos và điều kiện nhận/phân phối dữ liệu còn phải kiểm cho cả phần 37.

Cần phân biệt **candidate** với **ca có human truth được phê duyệt**. Hiện 0 proposal C2 mới, 0 approved reference, 0 đủ tám điều kiện và 0 candidate được phép cấp trong snapshot 45. Không được đẩy trạng thái này thành PASS bằng cách lọc tập.

## 2. Khóa quy tắc chọn mẫu, không chọn theo kết quả

- Lọc đúng sáu **physical IDs** có template Greek document type 25 theo readme/bảng nguồn và organizer evidence; loại toàn bộ candidate của sáu ID này. Không đoán ID từ tên ảnh hoặc số thứ tự phiếu.
- Chứng minh tập giao rỗng, hợp đủ 45, số đếm 37+8 và 18+6; không lọc theo output OCR, nhãn con người, hiệu ứng hay bất đồng.
- Quy tắc chính phải được ghi trước quan sát C2 mới: **37 ca là phạm vi nghiên cứu ưu tiên theo giới hạn quyền**. Báo số physical IDs làm đơn vị cụm, không coi 37 ca là 37 mẫu độc lập.
- Không bổ sung tám ca vì thấy kết quả 37 không đạt significance hoặc claim superiority. Nếu 37 không đủ sức hỗ trợ claim, phải thu hẹp claim, tăng nguồn độc lập hợp pháp theo protocol, hoặc báo kết quả không xác định.
- Chỉ xét nghiên cứu mở rộng 8 ca khi có câu hỏi khoa học hợp lý được ghi trước khi truy cập kết quả mới của nhóm 8, quyền sử dụng/chia sẻ hợp lệ, và amendment về selection/exposure/estimand. Kết quả mở rộng phải phân biệt primary và sensitivity/exploratory; không được trình bày việc thêm sau kết quả 37 là thiết kế có sẵn từ đầu.

## 3. Công việc tiếp theo trên máy organizer, không tạo quyền chia sẻ

**A. Tạo C2-37 trong run mới (private)**

1. Xác minh original 45 snapshot bằng `python -X utf8 -B -m research.evidence_contract.human_gate.verify human_20261122144027Z` trong môi trường repo đã đủ cache và receipt. Nếu có signature/journal mới, dừng và dùng workflow reconciliation phiên bản phù hợp; không vượt gate bằng cách sửa original.
2. Từ `local/human_gate/human_20261122144027Z/queue.json`, đối chiếu physical ID và loại template với nguồn MIDV; lập danh sách loại trừ **private**, không đưa các candidate IDs vào repo công khai.
3. Tạo run mới, chỉ chứa 37 item, ảnh full before/after thực sự được tham chiếu, crop thực sự được tham chiếu và hai phiếu riêng. Không sao chép nguyên cả thư mục 198 assets rồi chỉ ẩn 8 form. Cập nhật chỉ số 37 trong UI; không tự điền đánh giá.
4. Sinh `R02_manifest.json`, `R03_manifest.json`, `artifact_rights.json`, `aggregate.json` và receipt **mới**. Tính lại SHA-256 và cả năm artifact digests cho phạm vi mới; không dùng digest 45 để cấp quyền 37. Gói cần notice/credit khi được cấp, nhưng không phát hành.
5. Kiểm từng ảnh thuộc đúng physical ID và thuộc danh sách 37; kiểm toàn bộ HTML forms, references, assets, manifest, missing/extra files, hash byte, isolation giữa các phiên và `source precision`.
6. Giữ nguyên toàn bộ source queue, original 45 manifests, sealed reviewer exports, historical receipts, source byte hashes và baseline. Run mới chỉ được ghi dưới `research/evidence_contract/local/`.

**B. D10 cho đúng phiên bản 37**

- Lập ma trận riêng của 37; xác minh các lớp quyền ảnh mẫu Azerbaijan, Latvia, Serbia và Generated Photos, phạm vi sửa/crop và notice CC BY-SA.
- Xin quyết định owner về quyền *phân phối gói 37* trên năm digest mới, retention, người được truy cập và cách bảo vệ phản hồi. Chọn chiến lược 37-first **không tự nó là D10 clearance**.
- Chưa được gửi gói khi một trong các căn cứ quyền/owner approval còn pending. Quyền public supplement là một quyết định khác.

**C. Bằng chứng khoa học và bài Research**

- Khóa phiên bản protocol B, cohort membership, exclusions và estimand trước khi nhận C2 observations. Không chỉnh threshold/cỡ mẫu dựa trên kết quả.
- Dùng kết quả đủ thẩm quyền/rights và approved reference để phân tích điều kiện đọc được, semantic precision, source reliability, tỷ lệ abstention, loại false alarms, missed detections và coverage; báo `UNKNOWN`/thiếu truth đúng mẫu số.
- Báo riêng constructed-controls, replay lịch sử và kết quả thực tế của phạm vi 37. Không lấy controls tổng hợp thay cho truth của dữ liệu thật.
- Kiểm hiệu quả, utility, novelty và khả năng tái lập trước khi chọn claim cho Research Papers. P5B hiện `INFEASIBLE`; không tự bật claim superiority, không mở TASK 6B/7B nếu không có protocol khoa học mới đạt gate.
- Chuẩn bị anonymous replication bằng code, protocol và aggregate có thể công bố hợp pháp; không yêu cầu public GitHub ảnh, và không dựa vào private asset như bằng chứng công khai nếu không giải thích hạn chế.

## 4. Acceptance gate của milestone 37-first

Chỉ ghi **PREPARED_TECHNICAL_37** khi: hai gói 37 được tạo ở private run mới; 37 candidate/18 IDs đúng theo source; gói không mang ảnh/crop/HTML/thông tin từ sáu ID Hy Lạp; tất cả manifest/hash/rights digests khớp; tests và independent verification qua; 45 baseline bất biến. Không gọi là shareable, reviewed, adjudicated hay approved.

Chỉ ghi **D10_REVIEW_ACCESS_PERMITTED_37** sau khi đủ bằng chứng quyền cho đúng các artifact và có owner decision record hợp lệ. Không được kế thừa status của 45 hoặc cấp quyền chỉ dựa trên license chung.

Chỉ ghi **C2_REFERENCES_APPROVED_37** khi có phiếu con người thực, independent adjudication/reference workflow có xác thực và tám điều kiện thật sự PASS. Không giả lập chữ ký, nhãn hay sự đồng thuận.

## 5. Đường thời gian Research Papers

- **Cuối tháng 11:** xây và kiểm private run 37, kiểm D10 riêng, khóa quy tắc chọn mẫu. Song song chỉnh claim-to-evidence matrix.
- **Đầu tháng 12:** chỉ triển khai human review khi gate chia sẻ đã đạt; hoàn thiện authority/closure theo quy trình.
- **Giữa–cuối tháng 12:** xác minh phê duyệt reference, phân tích có kiểm toán và đánh giá readiness; nếu không đạt, giữ negative/inconclusive findings đúng giới hạn.
- **15/01/2027 AoE:** abstract Research Papers; **22/01/2027 AoE:** full paper. Deadline không tự mở cổng khoa học hoặc quyền dữ liệu.

## 6. Các trạng thái không được thay đổi chỉ vì quyết định này

`REVIEW_ACCESS_PENDING` cho original 45; `BLOCKED_RIGHTS` cho original 45 package; `RETENTION_PENDING`; `RELEASE_PENDING`; `GO_PREPARATORY_ONLY`; `NO_GO_SUPERIORITY`; P5B `INFEASIBLE`; TASK 6B/7B `BLOCKED`.

**Bước ngay lập tức:** Codex trên máy organizer tạo và kiểm bản 37 trong run mới, báo đầu ra theo tiêu chí mục 4. Không yêu cầu xin quyền nhóm Hy Lạp lúc này, không chuyển dữ liệu ra public repo.
