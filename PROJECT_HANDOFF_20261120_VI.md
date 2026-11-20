# Hồ sơ bàn giao dự án eKYC — trạng thái 20/11/2026

Tài liệu này là điểm vào cho người tiếp nhận công việc. Nó tổng hợp sản phẩm eKYC, các luồng nghiên cứu đang lưu trong repository, bằng chứng đã có, giới hạn của bằng chứng, cổng quyết định và thứ tự công việc tiếp theo. Các phiếu, ghi chú nhận diện người đánh giá, ảnh chưa được duyệt phát hành, dữ liệu thô, weights và cache riêng tư vẫn ở máy; GitHub chỉ nhận mã, tài liệu, kết quả tổng hợp và receipts an toàn.

## 1. Mục tiêu và phạm vi

Dự án có hai mục tiêu liên quan nhưng phải báo cáo tách biệt:

1. Xây dựng hệ thống eKYC chạy cục bộ: camera, chụp giấy tờ, kiểm tra ảnh, tìm vùng thẻ, OCR, người dùng xác nhận thông tin, kiểm tra thử thách khuôn mặt và đối chiếu selfie với chân dung trên giấy tờ.
2. Nghiên cứu kiểm thử phần mềm dựa trên bằng chứng cho EASE 2027. Hướng nghiên cứu hiện tại xem xét cách kiểm soát reference/oracle, propagation lỗi và abstention khi hệ thống không có đủ bằng chứng đáng tin để kết luận. Mục tiêu là tạo ra một bài báo có claim đúng mức bằng chứng; hiện dự án chưa đủ điều kiện scientific GO hoặc sẵn sàng nộp bài.

Kết quả OCR/crop, chất lượng phần mềm eKYC và nghiên cứu Oracle Reliability là các luồng bằng chứng khác nhau. Thành công của một luồng không tự chứng minh luồng kia đạt yêu cầu EASE. Tài liệu này không khẳng định chấp nhận hội nghị hoặc bảo mật PAD/identity verification cấp sản xuất.

## 2. Sản phẩm và kiến trúc repository

- Ứng dụng mentor chạy ở cổng 8000; luồng web OCR nghiên cứu hiện tại ở cổng 8003. Một workbench nghiên cứu khác chạy tại cổng 8001. Chỉ dùng localhost theo hướng dẫn repository.
- Luồng chính: camera → chụp và xác nhận giấy tờ → kiểm tra chất lượng → nắn phối cảnh/tìm vùng → OCR → người dùng xem/sửa thông tin → thử thách liveness → chụp selfie → đối chiếu với chân dung giấy tờ.
- Giá trị người dùng sửa được đánh dấu là đã xác nhận bởi người dùng, không phải đã được xác minh độc lập. Liveness pass không đồng nghĩa PAD được chứng nhận hoặc identity_verified=true.
- Mã sản phẩm và nghiên cứu được gộp trên branch main. Các mốc cũ vẫn được giữ bằng tags và trong thư mục versions/; không viết đè reader/model đóng băng.
- Bằng chứng nghiên cứu EASE tập trung tại research/evidence_contract/. Nghiên cứu khôi phục crop/document support ở research/. Tài liệu lưu trữ các thay đổi ứng dụng nằm dưới engineering/application_20261114/.
- Hướng dẫn chạy sản phẩm và giới hạn đầu vào nằm trong README.md; kết quả, protocol và runbook tương ứng nằm dưới research/.

## 3. Các nhánh nghiên cứu và kết quả chính đã có

### 3.1 Khôi phục tài liệu và OCR

Nhánh research/document-recovery-core-b được bảo toàn bằng tag và đã tích hợp vào main. Luồng V4 tập trung khôi phục vùng tài liệu/crop có bảo toàn nội dung, so với reader và các baseline hình học. Báo cáo lưu trong research/RECOVERY_RESULTS_VI.md, protocol trong research/RESEARCH_V4_PROTOCOL.md và các cổng claim trong research/CORE_B_SUBMISSION_GATES.md.

Theo báo cáo hiện có, benchmark chính có 304 ảnh từ 56 ID, 224 ảnh test; kiểm tra bổ sung có ảnh MIDV-2020. Các kết quả ghi nhận lợi ích theo key-value exact trên một số tập stress/layout nhưng không cho thấy mọi cascade đều thắng raw hoặc baseline đơn giản. Không có bộ camera khách hàng mới hay annotation legibility độc lập. Không gọi đây là SOTA, kiểm chứng danh tính, bảo đảm CORE B hoặc bằng chứng duy nhất cho EASE.

Các luồng OCR khác gồm dữ liệu nhãn OCR, hard-pair, fair controls, benchmark external và V3/V4 model comparisons. Hãy đọc protocol trước khi diễn giải số liệu; nhiều kết quả là benchmark tham chiếu tác giả, exploratory hoặc post-hoc. Không gộp test rows/fields/views thành số giấy tờ độc lập. Các báo cáo tương ứng được liên kết trong README.md, research/README.md và research/PRIORITY_PROGRESS_VI.md.

### 3.2 Evidence-Contract / Oracle Reliability & Abstention

Đây là trọng tâm hiện tại cho bài EASE. Tên B trong tài liệu này là Oracle Reliability & Abstention; nó không phải B3 hoặc nhánh cũ có tên Failure Propagation Analysis.

Policy nền v2 và reader/phiếu cũ được giữ đóng băng. Mục tiêu là đánh giá khi nào nguồn tham chiếu được phép kết luận, cách lỗi lan truyền, và khi nào hệ thống cần trả UNKNOWN thay vì khẳng định đúng/sai. Quy trình reference registry có demo synthetic; production authority và approved references hiện đều bằng 0.

Kết quả lịch sử B không cho thấy superiority. Trong constructed controls, tier nghiêm ngặt hơn làm giảm coverage và vẫn có counterexample khi nhiều nguồn cùng sai. Replay pilot 46 cặp không có approved reference nên pointwise và relation đều UNKNOWN; selective risk ở hai endpoint là NA. Trạng thái structural parser là kết quả parser, không phải nhãn chân lý đã adjudicate.

## 4. Đánh giá con người và tình trạng dữ liệu

- Người tổ chức dự án đã hoàn thành pha 1 86/86 mục và pha 2 46/46 ca.
- R02 đã hoàn thành pha 1 86/86 và pha 2 46/46. Vai trò ban đầu bị chọn nhầm thành tác giả; người dùng xác nhận người chấm không tham gia xây dựng project. Raw export được giữ nguyên; hiệu chỉnh vai trò được ghi riêng.
- R03 đã hoàn tất 86/86 mục pha 1 trên 31 ảnh và khai đã gặp ảnh hoặc giá trị ở 68 mục. Tính độc lập của phiếu này còn chưa xác minh. Gói pha 2 gồm 46 ca đã sẵn sàng, đang chờ phiếu. Round 1 vẫn OPEN. [Biên bản tiếp nhận R03](research/evidence_contract/R03_PHASE1_REVIEW_INTAKE_20261120.md).
- Chưa chốt cutoff hoặc tiến hành phân xử. Giữ kín bảng bất đồng, kết quả, đáp án và raw phiếu với người đang chấm độc lập.
- Agreement tác giả/R02 trên 42 ca primary: pointwise 30/42, Cohen κ=0,5862; relation 33/42, κ=0,6619. Có một ca binary pointwise đối nghịch. Đây là mức agreement quan sát được, không phải gold truth. Pha 2 primary chỉ gồm 3 physical IDs; không coi nhiều trường hoặc ca là nhiều ID độc lập.
- Theo phiếu R02, A có TP/FN 4/5 trên nhóm lỗi pointwise được tính; B3 9/0; C2 không có primary binary được gán. Đây là báo cáo theo người chấm, chưa phân xử và không phải đánh giá toàn bộ quần thể.
- Audit exposure xác nhận tối thiểu 192/1.000 instance MIDV-2020 đã có exposure; 808 UNKNOWN, không được gọi là unseen. Metadata của 1.000 instance đã được truy cập. Pixel/near-duplicate, cross-corpus lineage và pretraining overlap chưa được khép kín.
- Inventory cũ ghi 5.428 ảnh dưới research/data, khoảng 15,76 GB, gồm cả bản sinh/copy. Đây không phải số ID/giấy tờ độc lập và không phải cohort được duyệt.
- C2 có 1.100 cặp nguồn tiềm năng trên 400 instance và hiện 0 cặp đủ điều kiện. Còn thiếu chứng cứ provenance, support sau mutation và reference/semantic approval.

Xem chi tiết và phạm vi chính xác trong research/evidence_contract/R02_PHASE2_REVIEW_INTAKE_20261117.md, research/evidence_contract/B_CONTINUATION_REPORT_20261117.md, research/evidence_contract/REVIEWER_HANDOFF_VI.md và các thư mục execution/master_01/. Đừng đưa dữ liệu cá nhân người đánh giá hoặc local joins vào GitHub.

## 5. Mốc mới nhất: D4 P1 comparator development

Người dùng đã chọn D4 để triển khai development: so sánh checked v2 với một ablation hẹp mrz-metadata-asserted. Comparator ở research/evidence_contract/oracle_reliability/mrz_ablation_v1.py dùng cùng frozen evaluate/admission boundary và chỉ thay đúng một điểm gọi xác thực literal TD3. Nó giữ chung authority, liên kết ảnh/trường/mutation, nguồn output, tính dùng được của parser, kiểu/precision, semantic key, conflict, missing support, C1/C2 transition, tính hợp lệ của chuyển đổi và tier. Frozen policy SHA-256 được ghim trong adapter; không monkeypatch global.

Kết quả development đã lưu tại research/evidence_contract/execution/master_01/d4_development_20261117/:

- 72 ca constructed, 2 tier, 144 paired evaluations, 288 lần đánh giá arm, 3 endpoint.
- 144 kết quả checked khớp chính xác policy đóng băng.
- 8 ca (16 cặp tier) chỉ lệch ở can thiệp literal MRZ; 0 divergence ngoài điều trị. Bốn profile MRZ hợp lệ đạt parity ở cả hai tier.
- Ba counterexample về reference sai/chia sẻ cùng sai vẫn được giữ. Kết quả này chỉ ra giới hạn của cả hai arm.
- Replay 46 ca lịch sử: hai arm giống nhau; 46/46 UNKNOWN cho semantic pointwise/relation, structure 46/46 NO_FAULT theo parser; 0 approved reference, 0 nhãn truth dùng, 0 model call/training mới.
- Một phép đo warm-process trên hàm synthetic được ghi trong summary.json. Đây là timing phần mềm cục bộ, không phải latency eKYC end-to-end, hiệu quả chi phí hoặc thời gian người chấm.
- Full suite Evidence Contract: 579 passed, 6 subtests passed, 0 failed. Receipt và log là p1_full_tests_01.json/.log. Targeted run đầu có 2 kỳ vọng sai về hành vi C2 frozen; cả log lẫn amendment đều được giữ. Sau khi sửa kỳ vọng để phản ánh đúng policy, targeted run và full suite đều qua.
- Không có inference/training, ảnh/ID độc lập mới, review mới, approved reference hoặc prospective cohort trong D4.
- Kết luận hiện hành: PASS_CONSTRUCTED_DEVELOPMENT, scientific gate NO_GO_SUPERIORITY. Không dùng các con số này để tuyên bố phương án A/B nào tốt hơn ngoài phạm vi constructed controls.

Các module D4: d4_controls.py, d4_run.py, d4_historical.py, verify_d4.py, mrz_ablation_v1.py; test: research/evidence_contract/tests/test_d4_comparator.py. P0 audit/hash baseline và các receipts cũ nằm cạnh outputs. P1 chỉ là development implementation; P2 pixel/lineage/C2 evidence audit chưa hoàn tất.

## 6. Vì sao hiện chưa thể kết luận đạt scope EASE 2027

1. Chưa có protocol prospective được phê duyệt. D4–D9 còn endpoint, coverage/fault floor, margin, clustering, cỡ mẫu, ngân sách và stop rules chưa khóa.
2. Reference authority/approvals thật bằng 0; C2 eligible pairs bằng 0; truth độc lập và quy trình phân xử chưa có.
3. Round 1 OPEN và đang chờ pha 2 của R03. Reviewer feedback không được thay bằng số lượng test phần mềm.
4. Exposure chưa được khép kín. UNKNOWN không chứng minh unseen; lineage nội dung/pixel và overlap pretraining còn thiếu.
5. Constructed controls không phải lỗi tự nhiên, ảnh độc lập hay hiệu quả trên người dùng. Kết quả hiện có gồm counterexample làm cả hai arm thất bại.
6. Novelty comparison chưa hoàn chỉnh, manuscript B chưa hoàn thành/được review; anonymous release và quyền phát hành artifact chưa được duyệt.
7. Chỉ code/test pass không đóng scientific gate.

Các trạng thái cần giữ: GO_PREPARATORY_ONLY cho phát triển chuẩn bị; NO_GO_SUPERIORITY cho kết luận khoa học; B Research chưa submission-ready. Short/Emerging hoặc RENE là phương án lập kế hoạch nếu đúng với bằng chứng, không phải đường tắt để gọi một kết quả yếu là thành công. Ngày CFP trong các tài liệu được kiểm tra ngày 17/11/2026; phải xác minh lại trang chính thức trước khi lập lịch nộp.

## 7. Công việc tiếp theo theo thứ tự

### Làm được ngay, không cần phiếu review mới

1. Đã rà soát D4 adapter và đối chiếu mã nguồn với manifest P1. Bộ kiểm tra độc lập hiện đối chiếu từng endpoint, lý do của mỗi arm và hash đầu vào cho từng cặp có kết quả khác nhau. Lệnh tái kiểm tra ở mục 9. Ba phản ví dụ ở mục 5 vẫn giới hạn kết luận trên các nguồn tham chiếu cùng sai.
2. Hoàn thiện audit pixel/near-duplicate và lineage cho các asset được phép dùng; báo riêng file, image instance, physical ID, template và cluster. Không chọn cohort xác nhận từ audit kết quả thuận lợi.
3. Tiếp tục C2 evidence audit: phân biệt PASS/FAIL/UNKNOWN, xác minh source support sau mutation, provenance và authority. Không tự cấp approved reference.
4. Cập nhật literature/novelty matrix bằng nguồn sơ cấp, lập related-work claims có citation và ghi rõ khác biệt với oracle validity, metamorphic testing, selective prediction và abstention hiện có.
5. Hoàn thiện threat-to-validity, protocol implementation notes và reproducible analysis; mọi kết quả đều giữ mẫu số, missingness, NA, ID clustering, counterexample và lệnh/hash.
6. Có thể tiếp tục regression kỹ thuật sản phẩm eKYC độc lập, nhưng không đổi frozen research reader/model hoặc biến kết quả runtime thành chứng cứ EASE nếu chưa có protocol liên kết.

### Cần quyết định/ủy quyền trước prospective hoặc claim efficacy

Chốt D1–D3 về cutoff, authority và adjudication; D4–D9 về contrast, endpoint, floors, margin, sample/cluster, ngân sách và stop rules; D10–D11 về rights/exposure; rồi D12 về track/claim. Bảng hiện có là research/evidence_contract/B_OWNER_DECISIONS_20261117.md. Việc “tiếp tục” hoặc test pass không tự phê duyệt các quyết định này.

Sau khi các quyết định và quyền dữ liệu được ghi nhận: tạo lock protocol/version; chuẩn bị cohort và artifact manifest; chạy prospective có giám sát và receipts; tái tính độc lập; mở/khóa phiếu đúng thứ tự; đo agreement trước adjudication; đánh giá claim theo ledger; hoàn thiện manuscript và anonymous supplement theo track.

## 8. Điểm vào và tài liệu chính

| Nhu cầu | Điểm vào |
|---|---|
| Tổng quan ứng dụng và cách chạy | README.md, docs/, start.ps1 |
| Đồng bộ GitHub và phạm vi dữ liệu riêng tư | PROJECT_SYNC_POLICY.md, AGENTS.md |
| Trạng thái master EASE | research/evidence_contract/MASTER_EXECUTION_STATUS.md |
| Quyết định khoa học | research/evidence_contract/REVISED_GO_NO_GO.md |
| Bước tiếp theo | research/evidence_contract/NEXT_ACTIONS.md |
| Roadmap/track | research/evidence_contract/EASE2027_ROADMAP_VI.md |
| Dữ liệu review/recipient workflow | [REVIEWER_HANDOFF_VI.md](research/evidence_contract/REVIEWER_HANDOFF_VI.md), [reviewer_tools/README.md](research/evidence_contract/reviewer_tools/README.md) |
| B Oracle Reliability | [B_CONTINUATION_REPORT_20261117.md](research/evidence_contract/B_CONTINUATION_REPORT_20261117.md), [B_ORACLE_RELIABILITY_20261116.md](research/evidence_contract/B_ORACLE_RELIABILITY_20261116.md) |
| Protocol/sizing/owner decisions | [Protocol v2](research/evidence_contract/B_PROSPECTIVE_PROTOCOL_DRAFT_v2_20261117.md), [sizing](research/evidence_contract/B_SIZING_AND_POWER_DRAFT_20261117.md), [D1–D12](research/evidence_contract/B_OWNER_DECISIONS_20261117.md) |
| Manuscript claims/readiness | [B claim ledger](research/evidence_contract/paper/B_CLAIM_TO_EVIDENCE_20261117.md), [B EASE readiness](research/evidence_contract/paper/B_EASE_READINESS_20261117.md) |
| D4 current outputs | research/evidence_contract/execution/master_01/d4_development_20261117/ |
| D4 code/tests | [ablation adapter](research/evidence_contract/oracle_reliability/mrz_ablation_v1.py), [controls](research/evidence_contract/oracle_reliability/d4_controls.py), [runner](research/evidence_contract/oracle_reliability/d4_run.py), [historical replay](research/evidence_contract/oracle_reliability/d4_historical.py), [verifier](research/evidence_contract/oracle_reliability/verify_d4.py), [tests](research/evidence_contract/tests/test_d4_comparator.py) |
| V4 crop research | research/PROTOCOL.md, research/RECOVERY_RESULTS_VI.md, research/CORE_B_SUBMISSION_GATES.md |

## 9. Lệnh tái kiểm tra D4

Chạy từ repository research-document-recovery với Python hiện có tại thư mục cha:

~~~powershell
D:\laptrinhcuatao\Ekyc\.venv\Scripts\python.exe -B -m research.evidence_contract.oracle_reliability.verify_d4 research/evidence_contract/execution/master_01/d4_development_20261117/controls_01
$qa = Join-Path 'research/evidence_contract/local' ('d4_review_' + [guid]::NewGuid().ToString('N'))
D:\laptrinhcuatao\Ekyc\.venv\Scripts\python.exe -X utf8 -B -m pytest -q -p no:cacheprovider research/evidence_contract/tests --basetemp $qa
~~~

Lần rà soát ngày 20/11 xác nhận hash của 9 tệp nguồn khớp manifest P1. Bộ kiểm tra D4 chạy đạt cả ở chế độ thường và với `-O`. Lần chạy toàn bộ đầu tiên có 3 kiểm thử ghi tệp thất bại vì dùng thư mục tạm hệ thống. Khi dùng thư mục tạm trong phạm vi cho phép như lệnh trên, toàn bộ 585 kiểm thử và 6 subtest đều đạt.

Lệnh đầy đủ và output hash của mốc P1 được ghi trong p1_full_tests_01.json. Để chạy lại runner tạo output mới, truyền một thư mục execution chưa tồn tại và bảo toàn output cũ; replay lịch sử còn tạo rows.json trong local, tuyệt đối không stage thư mục local.

## 10. Quy tắc bàn giao và GitHub

- Làm việc trên main; trước khi push phải fetch, xem remote delta và diff. Chỉ stage đường dẫn đã rà soát; commit/push bình thường, không force. Sau push xác nhận git HEAD khớp origin/main.
- User yêu cầu mỗi milestone hoàn tất phải đồng bộ GitHub. Bản commit local chưa được tính là đồng bộ.
- Có thể push mã, tài liệu, aggregate, receipts và hashes đã kiểm tra. Không push raw reviewer JSON, identity/notes, analyst joins, local rows, dữ liệu chưa cấp quyền, weights, caches hoặc credentials.
- Giữ nguyên raw reviews và log thất bại; không sửa câu trả lời người chấm, frozen output hoặc policy để làm đẹp kết quả.
- Đọc PROJECT_SYNC_POLICY.md và AGENTS.md trước khi thay đổi phạm vi lưu trữ.

## Snapshot ngắn để người nhận bắt đầu

Mốc P1 ban đầu có 579 tests + 6 subtests PASS. Sau commit `46af24d`, đã rà soát D4 và kiểm lại 144 cặp trên 72 ca dựng sẵn. Cả 16 cặp có khác biệt đều thuộc nhóm can thiệp kiểm tra literal MRZ. Việc kỹ thuật tiếp theo là đối chiếu pixel/near-duplicate và truy nguồn các asset được phép dùng, sau đó kiểm tra nguồn hỗ trợ C2. Pha 2 của R03 vẫn chờ phiếu. Scientific gate giữ ở `NO_GO_SUPERIORITY`.
