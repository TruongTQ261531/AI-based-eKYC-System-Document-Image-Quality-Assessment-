# EASE 2027 · Phân công tiết kiệm Codex và snapshot tiến độ 23/11/2026

> Báo cáo quản lý, không phải receipt xác minh khoa học hay quyết định GO. Baseline nghiên cứu: `5f484ccabe617088a4c41986b25ccbf3350775fc`. Track mục tiêu có điều kiện: Research Papers (abstract 15/01/2027, full paper 22/01/2027, AoE). Quyết định người dùng: `C2-37-first`, hoãn việc xin quyền mẫu Hy Lạp; không xóa C2-45.

## 1. Đã xác minh

- Các nhánh OCR/V4 và LoRA đã có benchmark/checkpoint khóa theo phạm vi lịch sử; `research/STATUS.md`, `research/VLM_STATUS.md`, `research/RECOVERY_RESULTS_VI.md` mô tả kết quả nhưng **không** chứng minh claim của Research B.
- D4/P5/P5B/P6, controls, baseline checks, pixel/lineage và statistical calibration đã hoàn thành giai đoạn phát triển/kiểm toán. P5B = `INFEASIBLE` cho ngưỡng superiority đã chọn. `NO_GO_SUPERIORITY`, `GO_PREPARATORY_ONLY`, TASK 6B/7B `BLOCKED`.
- IFV Round 1: AUTHOR, R02, R03 đã hoàn thành hai pha. Có agreement trước adjudication; còn chữ ký closure Round 1, adjudication và reference production.
- C2 master: 45 candidate / 24 physical ID; giữ bất biến. C2-37: 37 candidate / 18 physical ID, loại 8 candidate / 6 ID Hy Lạp theo *rights exclusion*, không chọn theo outcome.
- `C2-37` đã **PREPARED_TECHNICAL_37**: hai gói, mỗi gói 37 phiếu trống và 155 ảnh (18 original, 27 derived, 110 crop); 74 phiếu tổng. Hai manifest, 5 rights digests và hash đã kiểm; 0 asset/form từ sáu giấy tờ loại. Receipt: `human_gate/receipts/c2_37_20261123/{aggregate,verification,validation}.json`. Validation lưu 82 targeted Python, 667 full Python + 6 subtests, 15 Node tests.
- C2-37 D10: `CONDITIONAL_REVIEW`, `REVIEW_ACCESS_PENDING`, `RETENTION_PENDING`, `RELEASE_PENDING`; chưa xác minh đầy đủ quyền chân dung Generated Photos và điều khoản tiếp nhận. 0/37 được phép gửi, 0 C2 proposal mới, 0 approved reference, 0 eligible theo tám điều kiện.
- B Research: có protocol, outline, claim/evidence và các artifact replay mô tả; chưa có full paper B và confirmatory evidence đủ cho claim superiority. Emerging PDF cũ **khác** manuscript B; không được coi là paper B hoàn thành.

## 2. Ước lượng % — phương pháp minh bạch

Không có % tiến độ chính thức trong repo. Đây là **ước lượng quản lý theo trọng số**, có chủ quan; hoàn thành công cụ không thay được bằng chứng khoa học.

| Workstream | Trọng số tổng | Hoàn thành ước lượng trong workstream | Đóng góp điểm |
|---|---:|---:|---:|
| V4/LoRA/ứng dụng — milestone lịch sử đã khóa | 10 | 100% | 10.0 |
| B foundations: D4, P5/P5B/P6, audit, design | 20 | 90% | 18.0 |
| IFV Round 1: intake, agreement, closure/reference còn thiếu | 10 | 90% | 9.0 |
| C2-37: chuẩn bị kỹ thuật và kiểm chứng | 10 | 100% | 10.0 |
| D10-37, production authority, quyền lưu và signed closure | 10 | 20% | 2.0 |
| Thu C2-37 truth thực, adjudication, approved reference | 15 | 0% | 0.0 |
| Prospective/independent real evaluation và xác nhận claim | 15 | 0% | 0.0 |
| Research B paper/anonymous replication/release | 10 | 20% | 2.0 |
| **Tổng điểm công việc có trọng số** | **100** | | **51/100** |

**Diễn giải:** khoảng 50% công việc theo cách chia này; **không** phải xác suất accept, không phải 51% paper submission-ready, không phải 51% đủ bằng chứng C2. Critical path khoa học còn chặn: D10, authority, real truth/reference, prospective design, novelty/claims, manuscript. Với nhánh mô tả C2-37, mục tiêu chính là descriptive characterization chứ không cưỡng ép confirmatory superiority.

## 3. Phân công tối ưu theo vị trí dữ liệu

### A — ChatGPT trực tiếp qua GitHub/public inputs, không dùng Codex local

1. `HIGH` — Paper B: làm outline 10+2 trang, claim-to-evidence audit, methods, threats, limitations, Data Availability; sửa Markdown/LaTeX/BibTeX, viết phần rõ ground truth và statistical infeasibility, kiểm ẩn danh **trong mã công khai**; không biến placeholder thành kết quả thật.
2. `HIGH` — Novelty/literature: tìm nearest prior art về test oracles, metamorphic testing, selective prediction, provenance and correlated errors; lập bảng novelty gap, phản biện claim, chủ động giữ kết quả âm.
3. `HIGH` — Công cụ phân tích thuần từ aggregate: viết/test stat calculators, denominator/NA, clustered descriptive analysis, worst-case missing truth, traceability tables, pure synthetic fixtures, không dùng review riêng tư.
4. `MEDIUM` — Code và unit tests không cần file private: schema/parser, rendering compatibility, deterministic fixtures, adversarial tests, static checks; **không** sửa frozen history hoặc gán nhãn C2.
5. `MEDIUM` — Reproducibility: tạo README/cấu trúc replay code-only, kiểm safe artifacts, data-availability statement, public diff scans, kế hoạch lưu trữ phiên bản/DOI; không tung ảnh.
6. `MEDIUM` — D10 drafting: phân tích terms trên nguồn mở, checklist rights C2-37, mẫu owner decision record và thông báo reviewer; **không** giả phê duyệt hay signature.
7. `LOW` — Bảo trì roadmap, bảng trạng thái và đồng bộ GitHub `main`, có thể làm trực tiếp qua connected GitHub.

Giới hạn: ChatGPT/GitHub không thấy các tập `research/evidence_contract/local/`, ảnh/crop, signed envelopes, model weights và ứng dụng trên máy người dùng nếu không được đưa vào môi trường phù hợp. Không thể chứng nhận test/inference trên dữ liệu không có. Có thể chạy phép tính Python/CPU với dữ liệu công khai có thể truy cập, nhưng không mặc định có GPU.

### B — Codex trên máy local (giữ quota cho phần thiết yếu)

1. `HIGH, GATED` — Khi có quyết định quyền hợp lệ: đọc/bảo toàn private D10 evidences, kiểm registry người có thẩm quyền, kiểm đúng 5 digest và run 37. D10 cần quyết định của OWNER, không phải hành động tự động của Codex.
2. `HIGH, GATED` — Chuẩn bị/giao đúng bản 37 qua kênh approved khi được giao việc; xử lý local images/ZIP và private notes. **Hai workspace đã tạo, không làm lại.**
3. `HIGH, GATED` — Nhập phiếu C2-37 thật, verify item hashes và exposure, receipts, append-only journal; adjudication và approval bởi con người được chỉ định, không để Codex quyết định thay.
4. `HIGH, GATED` — Re-run exact local tests / verified 37 package / runtime, chỉ khi phiên bản hoặc inputs private thay đổi; cung cấp cho ChatGPT **aggregate/redacted report** để tiếp tục phần phân tích.
5. `MEDIUM, GATED` — Inference OCR/VLM hoặc real profiling trên checkpoint và ảnh local **chỉ sau approved scientific protocol**; không mở TASK 6B/7B hiện giờ.
6. `LOW/NO-TRAIN` — GPU training mới **không phải tác vụ đang được phép hoặc cần thiết cho Research B**; chỉ mở khi có RQ mới, dữ liệu/GT hợp pháp, ID-disjoint split, budget, model-lock và amendment. V4/LoRA đã có checkpoint trước đây.

### C — Chỉ người thật có thẩm quyền, không giao cho AI

- OWNER: quyết định quyền D10 trên đúng phiên bản; thời hạn lưu, quyền truy cập, authority/keys; ký closure và owner reference approval theo quy trình, khóa Research claim/track cuối cùng.
- Rights-holder/provider: đưa căn cứ cấp quyền nếu cần (trước mắt **không** mở nhánh Hy Lạp); với C2-37 vẫn cần làm rõ Generated Photos/tiếp nhận.
- Assessor/independent adjudicator: tự đánh giá, cung cấp rationale, phân xử, ký thật; Codex/ChatGPT chỉ chuẩn bị và xác minh cấu trúc.
- Không nhập private keys/PII/phiếu thô lên GitHub công khai hoặc chat.

## 4. Trình tự tiết kiệm quota Codex

1. **Ngay:** ChatGPT xử lý novelty matrix, Research B manuscript skeleton, pure-stat scripts, open-science checklist và quyền C2-37 dạng checklist. Không dùng GPU, không cần reviewer files.
2. **Bổ sung minimal inputs:** OWNER cung cấp quyết định D10 + authority qua kênh private; nếu chưa có quyền thì không cố giao gói 37. Không dành Codex cho việc đã hoàn thành.
3. **Một phiên Codex local có gom việc:** khi D10/authority đạt, xử lý all-in-one: kiểm local receipts/digests → phát gói approved (nếu được owner yêu cầu) → nhận phiếu khi có → verify/adjudication pipeline. Tránh mở Codex cho từng cập nhật Markdown/test thuần.
4. **Sau khi có aggregate an toàn:** ChatGPT tiếp tục analysis, graphics, report, manuscript; chỉ dùng Codex để tái lập các kiểm chứng cần ảnh/weights, không chuyển dữ liệu private vào repo.
5. Không mở xin quyền tám ca Hy Lạp theo kết quả không đạt significance của 37. Giữ hold trừ khi có amendment được chốt theo lý do khoa học độc lập và quyền hợp lệ.

## 5. Compute/GPU

Môi trường ChatGPT kiểm tra ngày 23/11/2026: PyTorch CPU, `CUDA available=False`, GPU count=0; không thể dùng VRAM của máy Windows người dùng qua GitHub. GitHub là nơi lưu code và kết quả, không tự cung cấp GPU inference/training. CI CPU không có local dataset có thể chạy tests/fixtures công khai; một self-hosted GPU runner phải do chủ dự án thiết lập và cấu hình, cần kiểm giấy phép, secrets, quota và quyền truy cập trước. **Không đề xuất training mới ở thời điểm này**: nghiên cứu B đo độ tin cậy oracle trên frozen reader; refitting làm lệch error distribution, không thay thế truth độc lập.

## 6. Quy tắc cập nhật

Mọi milestone mới phải phân biệt `PREPARED_TECHNICAL` với `D10_PERMITTED`, `REVIEWED`, `REFERENCE_APPROVED`, `SCIENTIFIC_GO`, `SUBMISSION_READY`. Không tự đổi trạng thái do code/test pass. ChatGPT có thể commit trực tiếp các file text/code an toàn trên main theo `AGENTS.md` và `PROJECT_SYNC_POLICY.md`; diff và remote HEAD phải được kiểm sau write. Không push local-only artifacts, images, weights, identities, raw submissions. Tổng % được rà lại khi có milestone mới và nếu trọng số cần thay đổi phải công bố thay đổi.
