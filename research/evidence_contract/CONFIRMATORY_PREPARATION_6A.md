# TASK 6A · Chuẩn bị test độc lập

**Draft only.** TASK 6B vẫn BLOCKED. Kiểm tiền điều kiện đọc metadata đã được phép xem từ các nghiên cứu lịch sử và development. Chưa sinh hoặc mở bộ ảnh confirmatory. [Preflight](execution/master_01/prelock_readiness_v2.json) · [Exposure audit](execution/master_01/exposure_audit_final.json)

## Exposure có thể xác minh

Đã lập chỉ mục 14 nhóm, gồm V1, V2, V2-R2, V3, V4, hard-pair, fair-controls và train arms, OCR-labels, e2e v1/v2, TASK 5 và hai pilot mới. Chỉ mục cuối có **626 nhãn ID**, 3.693 UID, 3.417 hash file, 1.330 hash pixel và 453 dấu vân tay nội dung author. Các nhãn ID theo registry cũ, có thể còn alias của cùng thẻ. Chỉ mục pixel chỉ bao phủ phần có hash decode sẵn. Ví dụ V1 và V4 thiếu pixel hash trong manifest tương ứng. Tập external chỉ kiểm metadata cho phép. Chưa đối chiếu near-duplicate do rescale hoặc crop nếu file, pixel và nguồn đều thiếu liên kết. Không biết exposure trong pretraining.

So khớp UID và physical ID đã chuẩn hóa, hash bytes và pixel decode RGB, cùng hash nội dung đầy đủ của thẻ giả lập từ tham chiếu tác giả. Nội dung OCR, annotation đã che và prediction không dùng làm fingerprint chuẩn. Một ID có nhiều bản ghi nội dung do provenance có thể được lập chỉ mục bảo thủ. Số liệu cùng tên giữa các panel phản ánh reuse đã biết, không suy rằng tất cả panel đều độc lập. Chỉ mục chi tiết nằm dưới `local/`.

## Thiết kế specimen dự kiến

1. Dùng danh tính, mã thẻ và ảnh chân dung giả đã rõ quyền sử dụng. Ghi lineage renderer/template hoặc setup camera. Ghi physical ID chuẩn và cùng nhóm cho mọi view, mask, ảnh chụp lại và ảnh nắn của một thẻ.
2. Kiểm trùng exact ID/pixel/file/content trước khi phân vai. Kiểm bằng tay hoặc bằng phiên bản công cụ gần trùng có threshold chốt trước khi khóa, theo canonical layout, ảnh gốc hoặc họ font nếu đủ dữ liệu. Không dùng lại các panel 192/224 lịch sử để gọi là unseen.
3. Có ca body/MRZ đọc đúng khi chỉ một nguồn còn, trường B hợp lệ gần mask, C1 scope thiếu, C3 mất nhãn ngữ cảnh và C4 có operator đã xác thực. Cài một phần known-negative controls và field-positive controls trước khi đọc output. Ghi nhóm script/layout và độ khó. Ảnh chụp nhiều thiết bị chỉ thêm nếu thu thực sự và có quyền; ước lượng cỡ mẫu trên ID/cụm, không lấy số view thay ID.
4. Ghi inventory tác giả, semantic linkage, thành phần bắt buộc và checksum MRZ. Kiểm khả năng đọc riêng. Rater xem bằng chứng trước output, giấu method. Nếu review tự nhiên chưa xác minh được, giữ unassessed và báo tỷ lệ. Reviewer độc lập phải là người thực sự khác hoặc dùng nguồn chuẩn độc lập phù hợp với endpoint đã chọn.

## Cổng trước lock

Schema [manifest](master/specimen_manifest.schema.json) và [lock draft](master/test_lock_draft.schema.json) có validator thực thi. Test fixture gồm hai PNG encode khác nhau nhưng pixel giống nhau, trùng content, các đường dẫn ngoài scope và trạng thái lock giả. Phần kiểm metadata ảnh thật, quyền và tính đủ cỡ mẫu vẫn phải xác nhận riêng.

Sau GO mới, ghim protocol, inventory dữ liệu, code A/B0–B3/V3, validator và oracle, parser, reader/version/weights/prompt, cấu hình thread, seed và preprocessing, plans, target metrics, exclusions, mã thống kê, giới hạn inference và hash của từng input. Giữ snapshot lock và protocol public ẩn danh nếu được phép. Bước 6A hiện chỉ có `DRAFT_ONLY`. Nó trả `confirmatory_executable=false` kể cả khi schema fixture hợp lệ.

Rà soát 11/11/2026 đã sửa ba đường chấp nhận dữ liệu mâu thuẫn. Hai path chỉ khác chữ hoa hoặc dấu phân cách được xét là cùng đường dẫn Windows. Một physical ID có hai hash nội dung author khác nhau bị chặn để đối chiếu provenance. Hai semantic key trùng sau chuẩn hóa cũng bị từ chối thay vì ghi đè giá trị trong fingerprint.

Kiểm binding ở draft đã đối chiếu hash protocol, exposure index và hai manifest stage với receipt cũ. Validator báo rõ MATCH, HASH_MISMATCH hoặc MISSING. Kết quả kiểm hash PASS giữ trạng thái scientific gate BLOCKED. Phần metadata lịch sử được xác minh từ receipt đã có, không dựng lại dataset hoặc chạy lại inference. [Binding](execution/master_01/continuation_20261111/draft_binding_verification.json) · [Exposure receipt](execution/master_01/continuation_20261111/exposure_metadata_verification.json)
