# Novelty risk review — mô phỏng phản biện EASE

TASK 1, 06/11/2026. Đây là **tự phản biện của project**, không phải review thật từ EASE. Đã đọc related work và code được kiểm kê; chưa có main experiments mới. Quyết định: **conditional go cho prototype/validity pilot nhỏ; chưa đủ bằng chứng chốt contribution mạnh của Research Track**.

## Reviewer khó tính sẽ phản đối ở đâu?

| Phản biện | Mức rủi ro | Trả lời chấp nhận được / bằng chứng còn thiếu |
|---|---|---|
| “Đây là V3/hard-pair được đổi tên thành contracts.” | Rất cao | V3 đã có source OR/AND, precision và pair metrics. Cần ablation giữ nguyên graph/annotation, thêm admissibility/unknown/verified version-fault analysis; phải chỉ ra ích lợi tăng thêm trước baseline V3 |
| “MT và kiểm evidence đã có, có gì mới?” | Rất cao | R06/R09–R13 là prior art gần. Không claim MT/grounding/gated generation là mới. Chỉ ứng viên domain-specific oracle method có semantics, coverage, precision, falsification và empirical utility rõ |
| “Giảm false alarms là vì luôn từ chối phán xét.” | Cao | Coverage và sensitivity guards, negative controls độc lập, unknown giữ trong mẫu số burden; nếu không đạt guard thì H1' không được hỗ trợ |
| “Body/MRZ chỉ là một if-statement.” | Cao | Backup-source example chỉ sanity check. C1 cần xử lý conflicts, precision, semantic duplicates, missing coverage và valid regression witnesses ở nhiều stage; nếu không hơn adapter đơn giản thì chỉ là engineering |
| “Accuracy aggregate bỏ sót lỗi là điều ai cũng biết.” | Rất cao | H2 rộng bị loại. Phải so generic per-field checker có common gate; gold per-field upper bound. Nếu bằng nhau, không claim algorithmic improvement |
| “Các anh đã tự cài những lỗi phương pháp mình bắt được.” | Rất cao | Fault-family holdout, taxonomy độc lập, lịch sử có reproduction/patch/revert; mutants báo riêng. Không có real bug corpus thì không claim phát hiện lỗi thực của phần mềm |
| “Guided masking thắng random vì random cố ý yếu.” | Rất cao | Primary baseline nhận cùng annotation, operator pool, area strata và validator; tính mọi proposal/call/setup/triage. Nếu chỉ thắng pixel random thì H3' thất bại |
| “Source graph vừa sinh test vừa xác nhận test, oracle circular.” | Rất cao | Independent raster/semantic validation và blinded reference review, audit cả rejected/negative cases. Fixtures cùng implementation không đủ chứng minh oracle validity ngoài construction scope |
| “Dataset đã mở và đã train; test mới ở đâu?” | Cao | Legacy tất cả exploratory. Khóa prospective ancestry/IDs/fault families; re-render cùng ID không độc lập. Pretraining exposure chưa biết phải thừa nhận |
| “Một người tự chấm không phải ground truth độc lập.” | Rất cao với ảnh tự nhiên | Giữ pilot-only. Core construction-exact có independent implementation validation; natural legibility extension đòi người thật độc lập, không nhân đôi reviewer codes |
| “Nhiều field nhưng chỉ vài bug, p-value không đáng tin.” | Cao | Fault/root-cause unit, ID/source clusters và CI đúng scope; không đủ effective N thì descriptive finite-pool case study, không suy luận rộng |
| “Đây vẫn là benchmark OCR, chưa phải SE.” | Cao | Endpoint về oracle error, verified regression/fault recall và testing cost; SUT versions/non-ML stages và developer actions có provenance. F1/CER chỉ secondary |
| “Paper hứa eKYC an toàn hoặc chống giả từ thí nghiệm OCR.” | Cao | Bỏ claim đó. Module 4–5 và production security nằm ngoài case study hiện tại |

Các mô tả chi tiết từng bài và nguồn gốc xem [RELATED_WORK](RELATED_WORK.md); bảng này là đánh giá của project từ phép đối chiếu, không gán lời reviewer giả thành trích dẫn.

## Phân loại đúng contribution

**Ý tưởng đã biết:** metamorphic relations/preconditions, counterfactual masking, uncertainty/refusal, source spans, redundant realizations, visible/full reference, semantic gates, paired version correctness, matched-budget evaluation, mutation analysis. Không đặt tên mới để biến chúng thành phát minh.

**Engineering cần làm nhưng không tự là novelty:** adapter chuẩn hóa V3/hard-pair, record schema/logging, hash/cache guard, viewer localhost, parser tracing, replay runner và report. Chúng có giá trị tái lập, không đủ một mình chứng minh thuật toán.

**Điểm khác biệt có thể kiểm chứng:** phối hợp admissibility, bounded semantic source coverage và typed precision để đánh giá **chất lượng test oracle của document pipeline**, kèm verified regression/fault provenance. Lợi ích tăng thêm phải vượt V3 và per-field/common-gate controls, không chỉ một ví dụ MRZ thuận lợi. Đây là contribution ứng viên C1; chưa có kết quả ủng hộ.

**Dataset hỗ trợ C2:** case/fault/validity annotations và lineage cho audit, không phải thêm ảnh chưa có transcript rồi gọi thành benchmark mới. Chỉ có giá trị nghiên cứu khi lỗi/phạm vi nguồn và cách tạo oracle được kiểm độc lập, có license và splits/exposure rõ.

**Replication hỗ trợ C3:** đủ logs để người khác kiểm claim; tính minh bạch là điều kiện chất lượng, không tự chứng minh method hiệu quả hơn.

## Claim ledger tại cuối TASK 1

| Claim | Trạng thái | Điều kiện để thay đổi trạng thái |
|---|---|---|
| Topic phù hợp scope EASE | Có cơ sở từ CFP; suitability do project đánh giá | Giữ SE endpoint và empirical method; không bảo đảm acceptance |
| H1' giảm FAR mà giữ sensitivity/coverage | Giả thuyết | RQ1 và independent reference/guards đạt |
| H2' cải thiện verified regression detection | Giả thuyết, rủi ro novelty cao | RQ2 hơn per-field+gate; trace/root-cause evidence và controls đủ |
| H3' cải thiện fault yield cùng budget | Giả thuyết, prior art rất gần | RQ3 hơn validity-filtered random; cold-start annotation/call costs đầy đủ |
| Đã có phương pháp đầu tiên trên thế giới | **Không có bằng chứng; không được tuyên bố** | Review này không có khả năng chứng minh ưu tiên toàn cầu |
| Đã có algorithmic superiority / paper đạt EASE | **Chưa có bằng chứng** | Thực nghiệm không tự quyết định acceptance; cần review khoa học |
| Đã xây framework/train/chạy main tests trong TASK 1 | **Chưa thực hiện** | Chỉ task triển khai/thực nghiệm riêng sau các gate |

## Go / narrow / stop

**Go có điều kiện:** xây prototype read-only nhỏ cho C-BACKUP/C-NI/C-PRECISION và independent validity fixtures ở task sau. Không cần tiếp tục fine-tune model. Chốt source semantics và fault provenance trước model calls; bắt đầu construction-exact để phù hợp việc chỉ có một reviewer.

**Narrow nếu thiếu bằng chứng:** nếu không có natural reference độc lập, giới hạn construction/in-family case study. Nếu không có historical faults, chỉ báo mutation study. Nếu generic checker + common gate giải quyết hết, chuyển câu chuyện sang empirical oracle-validity findings; không giữ tên “thuật toán mới vượt trội”. Nếu H3 không hơn strong random, bỏ H3 superiority khỏi contribution chính và báo kết quả âm.

**Stop mở rộng nếu:** precondition không kiểm được độc lập; không có fault pool còn holdout; thiếu ngân sách/power để phân biệt tác động có ý nghĩa; hoặc chỉ tái hiện các khái niệm prior art mà không có insight thực nghiệm mới. Dừng claim/mở rộng framework, giữ artifacts và lập scope nhỏ hơn; không xóa baseline hoặc chạy lại đến khi kết quả đẹp.

## Những việc phải chốt trước main experiments

1. Fault/version corpus nào thực sự có reproduction và độc lập với thiết kế contracts; hiện chưa được kiểm chứng trong TASK 1.
2. Reference đủ mạnh cho từng endpoint, nhất là coverage completeness và readability; một người không đáp ứng natural independent evaluation.
3. Exact case/fault manifests, annotation/time caps, statistical adequacy và decision margins trước lock.
4. Thêm một vòng tìm prior art tập trung vào visual evidence contracts/source redundancy và regression oracle; review hiện tại có giới hạn, cập nhật trước manuscript.

Tài liệu này không chặn việc hoàn thành TASK 1: ba RQ đã rõ, baseline mạnh và phương pháp có điều kiện bác bỏ. Nó chặn việc nhảy thẳng sang thực nghiệm chính hoặc tuyên bố novelty đã đủ mạnh khi các điều kiện trên chưa có.
