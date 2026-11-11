# Trạng thái lúc phục hồi TASK 5.5

Kiểm kê ngày 09/11/2026 theo giờ Asia/Bangkok, trước khi sửa mã phục hồi. Đã đọc tài liệu bàn giao 695 dòng và kiểm SHA256 `edd876c329c364b51b77e594473d62815d89eebd094b9c7bd757113a669ab1ee`. Báo cáo này chụp trạng thái khi tiếp nhận. [Tài liệu bàn giao](<D:/App/EASE2027_EVIDENCE_CONTRACT_RECOVERY_MASTER_PLAN.md>) · [Bằng chứng local](RECOVERY_EVIDENCE.json)

Worktree nghiên cứu ở `D:/laptrinhcuatao/Ekyc/versions/research-document-recovery`, nhánh `main`, HEAD `f5d130d93525e7633053edc03e6d9f6edeba7a6f`. Tracked và staged diff rỗng. Git báo năm mục untracked có sẵn, gồm `research/evidence_contract/`, `research/priority2_tiles.py`, `research/results/priority2_tiles_v1/` và hai thư mục UI cũ. Worktree mentor sạch, detached ở `4110f22b94699d30950cd1c0b23532ee9ccaaa59`. Cả ref tracking và kết quả đọc trực tiếp GitHub `main` khớp HEAD nghiên cứu. Phần việc Evidence Contract hiện nằm trong các file local. [Commit GitHub](https://github.com/TruongTQ261531/AI-based-eKYC-System-Document-Image-Quality-Assessment-/commit/f5d130d93525e7633053edc03e6d9f6edeba7a6f)

| Phần | Trạng thái xác minh lúc phục hồi | Bằng chứng |
|---|---|---|
| TASK 0 | DONE, có inventory, preservation và reuse map | [PROJECT_INVENTORY](PROJECT_INVENTORY.md) · [REUSE_MAP](REUSE_MAP.md) |
| TASK 1 | DONE trong phạm vi đặc tả, prior work và RQ draft | [METHOD_SPEC](METHOD_SPEC.md) · [RESEARCH_QUESTIONS](RESEARCH_QUESTIONS.md) |
| TASK 2 | PARTIAL về bàn giao riêng. Có nền schema, nguồn và công cụ review từ nghiên cứu cũ. Chưa tìm thấy bộ giao TASK 2 độc lập | [GENERATOR_AUDIT](GENERATOR_AUDIT.md) · [Source graph](source_graph.py) |
| TASK 3 | DONE trong phạm vi generator, validator và control/pilot giả lập | [Delivery validation](execution/task3_generator/delivery_validation.json) |
| TASK 4 | DONE trong phạm vi runner, oracle và smoke | [TASK4_RESULTS_VI](TASK4_RESULTS_VI.md) · [Final checks](execution/task4_runner/final_checks.json) |
| TASK 5 | DONE, development pilot và quyết định NO-GO | [DEVELOPMENT_PILOT](DEVELOPMENT_PILOT.md) · [GO_NO_GO_REVIEW](GO_NO_GO_REVIEW.md) |
| TASK 5.5 audit A/B3 | DONE. Có JSON theo từng dòng, nhóm và ba lượt timing, cùng log. Đối chiếu với cả hai bản score TASK 5 đều khớp | [Audit JSON](execution/task55_audit/audit_run_01.json) · [Log](execution/task55_audit/audit_run_01.log) |
| TASK 5.5 IFV | PARTIAL. Có mã dựng phiếu, form và importer. Tại thời điểm kiểm kê chưa có packet sinh ra, test phiên bản này, pha chấm output hoặc phiếu thật | [Mã review](task55/review.py) · [Mẫu giao diện](task55/review_template.html) |
| TASK 5.5-AUTO | NOT_FOUND trong hai worktree và các vùng cache, kết quả, nghiên cứu đã dò. Có các mutation/control thuộc TASK 3 và TASK 5 | [Controls TASK 5](tests/test_task5_baselines.py) |
| TASK 6 | BLOCKED theo gate đã lưu | [TASK6_GATE_REVIEW](TASK6_GATE_REVIEW.md) |

Đối chiếu 93 payload cache với SHA của ảnh, reader/config/code và event hoàn tất. Trong 93 kết quả có 84 lượt chạy mới của TASK 5 và 9 kết quả TASK 4 dùng lại. Sáu log inference khớp hash với audit 5.5. Đã kiểm 23 tài sản theo manifest, gồm ONNX, adapter `partial_42/step_0320`, config và các file Vintern. Model config ghi `rect2`, seed 42, tối đa 384 token. Toàn bộ 2.622 file trong snapshot trước 5.5 còn khớp hash. Snapshot lúc nối lại chứa 2.632 file có trước phiên này. [Recovery evidence](RECOVERY_EVIDENCE.json) · [Snapshot](execution/task55_recovery/resume_snapshot.json)

Kiểm kê process không thấy Python/Uvicorn hoặc các listener 8000, 8001, 8003, 8005, 8055. Máy từ chối truy vấn CIM, và `nvidia-smi` không cho định danh owner của các PID hiển thị. Vì vậy thông tin command line của process và owner GPU ở trạng thái chưa xác nhận. Không có tiến trình nào bị dừng. Database review OCR-labels cũ có 81 sự kiện trên 35 mẫu và một mã tự khai. Đây là snapshot SQLite đọc bất biến, WAL 0 byte, chưa xác nhận số người độc lập. Phần IFV mới bắt đầu với 0 phiếu. [Bằng chứng local](RECOVERY_EVIDENCE.json)

Tài liệu bàn giao nhầm B3 với `A_flat`. Audit đã lưu xác nhận **A/B3 trùng verdict 78/120**, trùng cờ cảnh báo 79/120, còn **A/`A_flat` trùng 120/120**. Đơn vị là các lượt so sánh contract–trường–reader theo lịch pilot. Các RQ tham khảo trong bàn giao được giữ như đề xuất, còn RQ đang áp dụng lấy từ file khóa local. Báo cáo GitHub 6/48 là snapshot cũ của OCR-labels, trong khi 35/48 là trạng thái database trên máy ở lần kiểm này. [Audit gốc](execution/task55_audit/audit_run_01.json) · [RQ local](RESEARCH_QUESTIONS.md)

Công đoạn nối tiếp là hoàn thiện bộ review mù đang dở, bổ sung quy trình hai pha IFV và chốt quyết định từ audit đã có. Các control tự động sẵn có phục vụ kiểm chứng bổ trợ. Nhãn và xác minh lỗi thực phụ thuộc vào phiếu người đánh giá. Phần thay đổi protocol được ghi thành amendment riêng.
