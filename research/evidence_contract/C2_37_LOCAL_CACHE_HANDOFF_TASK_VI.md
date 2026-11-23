# C2-37 · Một nhiệm vụ local Codex: kiểm OCR-output cache và bàn giao phần public cho ChatGPT

**Bối cảnh:** C2-37 đã đạt `PREPARED_TECHNICAL_37`, 37 candidate / 18 physical IDs, 8 candidate Hy Lạp vẫn giữ riêng. Đích là EASE 2027 Research Papers theo hướng *descriptive characterization*. Codex còn rất ít quota: thực hiện **một cuộc kiểm tra read-only, gọn, không refactor lớn**. Baseline `main` tính tại thời điểm nhận việc; đọc `AGENTS.md`, `PROJECT_SYNC_POLICY.md`.

## Mục tiêu duy nhất

Dựa trên `research/evidence_contract/local/human_gate/c2_37_20261123/queue.json`, kiểm tra những **đầu ra reader/OCR đã lưu** có thể được ràng buộc chính xác (không phải trùng filename) với từng ảnh **before/after** của 37 candidate hay không. Báo những khoảng trống khiến việc phân tích tiếp cần local data hoặc chạy mới.

**Không** khẳng định nhãn, kết luận đúng/sai, fault, human truth, quyền sử dụng hay đủ điều kiện scientific GO chỉ từ cached OCR. Đầu ra OCR lịch sử không phải approved reference.

## Quy trình cho Codex

1. Kiểm tồn tại `queue.json`, trạng thái run và số đếm 37 candidate / 18 physical ID; đối chiếu `aggregate.json`, `verification.json` private với receipt công khai tương ứng nếu có. Nếu có mismatch, dừng và báo nguyên nhân; **không** overwrite snapshot.
2. Tìm có giới hạn trong **các manifest/cache receipt đã biết** để biết có đầu ra RapidOCR v4/v5/Vintern hay reader đã khóa nào tương ứng với SHA-256 `full.before.file`, `full.after.file` hay không. Trước khi quét rộng, đọc acquisition và artifact index liên quan để giới hạn phạm vi; không đi recursive toàn bộ ổ đĩa hoặc tải thêm dataset.
3. Xếp mỗi candidate theo khả năng *exact input image-byte + đúng reader/checkpoint/config provenance*: `BOTH_BOUND`, `BEFORE_ONLY`, `AFTER_ONLY`, `NEITHER`, `AMBIGUOUS`. `AMBIGUOUS` bao gồm kết quả chỉ có tên ảnh, thiếu checksum, chỉ có pixel match chưa chứng minh đúng input, không rõ model/version/config, hoặc output từ nguồn khác. Không gộp cache giữa các reader khác nhau thành một pair.
4. Báo theo **từng reader** (nếu có đủ provenance) và một dòng tổng hợp bao nhiêu ca có ít nhất một reader exact-paired. Các nhóm riêng của mỗi reader không nhất thiết cộng thành 37; nhưng **bên trong từng reader** 5 trạng thái phải cộng đúng 37. Báo số physical IDs có cả hai ảnh bound và số lượng output đã tìm có provenance.
5. Không xuất candidate ID, physical ID, ảnh/crop, SHA ảnh từng hàng, OCR text/field, reviewer IDs/phiếu, nhật ký thô, data local path, secret, weights, hoặc các cell có thể tái nhận diện sang GitHub. Nếu thấy không thể bảo đảm an toàn, ghi báo cáo kỹ thuật local và chỉ đưa trạng thái `NOT_SAFE_TO_PUBLISH` lên public.
6. Nêu nguồn cache được kiểm dưới dạng *loại hệ thống hoặc tên artifact công khai đã có*; không ghi raw Windows path. Phân biệt `CACHE_AVAILABLE` với `CAN_RUN_PROSPECTIVE` (đang BLOCKED). Nếu không có cache khớp, báo `0/37` một cách trung thực; không chạy suy luận thay thế.
7. Tạo **một** báo cáo Markdown công khai ngắn: `research/evidence_contract/C2_37_OCR_CACHE_PREFLIGHT_VI.md`. Bao gồm scope, read-only method, bảng năm trạng thái theo reader, mức tin cậy, số ảnh/ID ghép hợp lệ, missingness, cách tao có thể tiếp tục trên GitHub, điều kiện cần quyền/approved truth khi sau này mở analysis. Chỉ nếu cần máy đọc mới tạo script ngắn mới; không đụng file frozen. Có thể lưu receipt machine-readable nhỏ không chứa private binding nếu thực sự hữu ích.
8. Chỉ chạy targeted checks liên quan đến logic mới (nếu có), `git diff --check`, private-data release scan phù hợp. **Không** chạy full regression, training, inference, tests không liên quan hay lại dựng hai workspace đã hoàn tất.
9. Commit và push **duy nhất file báo cáo public an toàn cùng code/check mới thật sự cần thiết** lên `main` theo `AGENTS.md`; xác minh remote HEAD sau push. Nếu không có kết quả local hoặc không an toàn, vẫn báo giới hạn đúng thực tế, không chế ra số liệu.

## Ràng buộc khoa học / quyền

- `GO_PREPARATORY_ONLY`; `NO_GO_SUPERIORITY`; P5B `INFEASIBLE`; TASK 6B/7B `BLOCKED`.
- `REVIEW_ACCESS_PENDING`, `RETENTION_PENDING`, `RELEASE_PENDING` cho run 37. Không xuất/gửi gói.
- Không hỏi/xin phép 8 ca Hy Lạp; không bổ sung vào cohort để cải thiện kết quả.
- Không sửa C2_MASTER_45, frozen model/reader, rights manifest, source queue, historical receipt, input images, reviewer data.
- Read-only availability không làm thay đổi thống kê đã khóa và không cho phép lấy predicted OCR text làm ground truth.

## Handoff cuối cùng cho ChatGPT

Khi xong, trả đúng:
- GitHub commit SHA + link tới `C2_37_OCR_CACHE_PREFLIGHT_VI.md`.
- Kết luận: exact-paired cache thực sự có hay không; còn thiếu gì.
- Nếu có lỗi hoặc thiếu dữ liệu, nói rõ nhưng **không** tự mở lượt inference mới.
- **STOP**. Không nhận thêm nhiệm vụ tiếp theo trong phiên Codex này.

ChatGPT sau đó đảm nhận tiếp qua GitHub: viết post-cache analysis code trên fixture/synthetic, rà claim-to-evidence, đánh giá feasibility và chỉnh Research manuscript; chỉ quay lại local khi có dependency rõ ràng.
