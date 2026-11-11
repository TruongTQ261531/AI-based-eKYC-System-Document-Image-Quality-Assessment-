# Research Questions và tiêu chí bác bỏ

TASK 1, 06/11/2026. **Ba RQ dự kiến, chưa có kết quả mới và chưa preregister.** H1'–H3' thay thế phiên bản rộng sau review. Định nghĩa thực thi ở [METHOD_SPEC](METHOD_SPEC.md), budget/lock ở [PROTOCOL_DRAFT](PROTOCOL_DRAFT.md).

## Quy ước chung

Đối tượng nghiên cứu là extraction pipeline có version: geometry/preprocessing → reader → parser/normalizer → structured fields. Không đo xác thực danh tính, face matching hoặc chống replay. Field names theo document schema của case; không bắt mọi loại thẻ có bộ trường CCCD.

- `valid/invalid/unknown/inapplicable`: trạng thái **test precondition** do reference validator độc lập xác định.
- `pass/fail/unknown/inapplicable`: verdict của tester; `fail` mới là cảnh báo contract. `unknown` không tính pass.
- `Z=0/1/?`: tham chiếu độc lập cho không vi phạm/vi phạm/chưa đủ bằng chứng; không lấy verdict của phương pháp làm Z.
- **Case alarm** khác **unique fault**: nhiều ảnh/seed phát hiện cùng root cause chỉ là một fault. Seeded mutants, natural model errors và real historical software faults báo riêng.

Mọi giả thuyết có thể không được hỗ trợ. CI chứa 0 hoặc thiếu power là **inconclusive**, không chứng minh hai phương pháp bằng nhau. Con số ngưỡng/margin dưới đây là đề xuất vận hành cho draft, không phải chuẩn ngành; phải biện minh và khóa trước confirmatory outputs.

## RQ1 — Chất lượng oracle

**Câu hỏi:** contracts có coverage/precision/admissibility làm giảm cảnh báo sai so với oracle V3 đóng băng mà vẫn giữ decision coverage và sensitivity hay không, đặc biệt ở alternative-source cases?

| Thành phần | Thiết kế |
|---|---|
| H0 / H1 | H0: `FAR_new − FAR_V3 ≥ 0`; H1': `< 0`, với hai guard về sensitivity/coverage. So source-agnostic/body-only là secondary sanity check |
| Independent variables | Oracle: body-only, legacy V3, V3 + admissibility, V3 + precision, full proposed contract. Nguồn/coverage/readability là strata, không phải model mới |
| Dependent variables | FAR trên valid known-nonviolations; end-to-end sensitivity; decision coverage; alarm precision; invalid-alarm rate; unknown rate; kiểm thời gian oracle |
| Unit of analysis | Một input/follow-up/output pack và contract-key; cụm ID/canonical source. Packs do cùng fault tạo còn cụm theo fault; fields không được coi độc lập |
| GT/oracle | Correct/incorrect control packs từ construction-exact specimens; source links kiểm riêng. Natural-image extension chỉ nhận reference đủ provenance; đọc được không suy từ bbox/Clean. Rater của reference không xem method/model verdict |
| Baselines | Body-only + V3 có hash, cùng raw outputs; ablations dùng cùng annotation. Baseline thiếu nguồn là weak comparator, không đối chứng duy nhất |
| Metrics | `FAR_valid = FP/N0`, N0 là valid packs có Z=0; `Sens_e2e=TP/N1`, unknown/inapplicable trên known-positive hợp lệ là missed detection; `Coverage=(pass+fail)/(N0+N1)`. Báo thêm conditional metrics, tất cả mẫu số, count Z=? và invalid/inapplicable |
| Threats | Reference tự xác nhận; graph annotation thêm thông tin; correct controls thiên về MRZ; unknown làm hạ FAR; source conflicts, date precision, script expertise |
| Claim criteria | Primary contrast có chiều giảm FAR và Holm-adjusted p<.05, CI effect size theo cụm. Đồng thời lower one-sided CI của chênh sensitivity và coverage phải trên −0.05. Báo riêng panel constructed/natural và source strata; không pooling để che một stratum xấu |
| Falsification | Không hơn V3; guard không đạt; lợi ích biến mất khi annotation bằng nhau; hoặc validator cũng dùng cùng lỗi source linking với generator. Chỉ hơn body-only không đủ C1 |

**Oracle lỗi trên test invalid:** không gộp vào FAR_valid vì expected relation chưa hợp lệ. Báo riêng `invalid_alarm_rate = alarms/N_invalid` và tỷ lệ cảnh báo thực sự được xác minh trên **toàn bộ** alarms, gồm invalid/unknown. Không loại các ca này khỏi bảng tiến trình hoặc chi phí.

## RQ2 — Regression và lỗi truyền qua stage

**Câu hỏi:** contracts có tạo cảnh báo regression được xác minh hữu ích hơn generic per-field checks và legacy pair scoring trên cùng execution set, ở mức báo sai chấp nhận được?

| Thành phần | Thiết kế |
|---|---|
| H0 / H1 | H0: fault recall mới không cao hơn generic normalized per-field checker có chung validity gate; H2': cao hơn, với false-alarm cap và coverage guard. Đây là so sánh khó, có thể kết quả bằng nhau |
| Independent variables | Detector/oracle; phiên bản v0/v1; fault family/stage; contract/operator; SUT family đóng băng. Model errors không có version provenance là analysis riêng |
| Dependent variables | Unique verified fault recall/precision, false alarms, marginal faults so với baseline, transformation-specific regression witnesses, alarm triage time, earliest observed divergence |
| Unit of analysis | Root-cause family trong controlled-fault pool là đơn vị primary; historical faults báo riêng/descriptive. Input quad và ID là cấp lồng/chéo. Không biến 100 alarm của một mutant thành 100 lỗi |
| GT/oracle | Với retained B: `v0(x), v0(Tx), v1(x)` đúng và `v1(Tx)` sai là witness mạnh. Cần mutation provenance hoặc bug/patch/revert có reproduction và intended behavior độc lập. Stage trace hỗ trợ localization; divergence sớm nhất chưa tự là root cause |
| Baselines | Schema/format validation; aggregate field F1 change; normalized per-field version/MR diff; chính checker đó + common validity gate; V3/hard-pair có version wrapper. Gold per-field GT checker là upper bound, không đối thủ bị làm yếu |
| Metrics | `FaultRecall = verified root causes detected / eligible locked root causes`; precision và FAR trên known-good changes; fault-family coverage; real-bug and mutant counts tách; model anomaly counts tách. Không lấy mutation score làm real-bug success |
| Threats | Mutants được tạo theo contract; v0 không thực sự đúng; cải thiện A bù lỗi B; nondeterminism; parser giải cứu raw output; thông tin baseline không bằng nhau |
| Claim criteria | Primary controlled-fault-recall difference dương, adjusted p<.05; observed alarm FAR trên valid known-good ≤5% và coverage NI margin 5pp. Claim population FAR≤5% còn đòi upper CI≤5%; nếu không đạt chỉ báo cap quan sát của finite panel. Cần thêm root causes được xác minh chứ không chỉ nhiều alarms. Gold upper bound không dùng cho superiority |
| Falsification | Field checker + common gate bằng/tốt hơn; chỉ phát hiện contrived mutants; không tái hiện patch/revert; hoặc chênh lệch là lỗi có sẵn của v0. Khi ấy không claim cải tiến regression method |

Giới hạn thực tiễn: có thể có regression thông thường `v0(x)` đúng → `v1(x)` sai mà không cần transformation. Vẫn báo nó, nhưng không tính vào transformation-specific incremental claim. Nếu chỉ so F1 tổng rồi nói “phát hiện lỗi bị che” là chưa đủ.

## RQ3 — Giá trị của test generation theo budget

**Câu hỏi:** structural source conditioning tăng fault discovery sau xác minh so với validity-filtered random cùng annotation, inference và triage budget không?

| Thành phần | Thiết kế |
|---|---|
| H0 / H1 | H0: `Y_conditioned(B) − Y_valid_random(B) ≤ 0`; H3': `> 0`. Y là số root causes xác minh tìm được tại budget B đã khóa, không phải attack-success trên selected cases |
| Independent variables | Generator/ranking: pixel random, box-aware random, validity-filtered box random, legacy hard-pair, proposed source-conditioned; selection seed; budget prefix |
| Dependent variables | Unique verified fault yield, valid-proposal precision/coverage, time-to-first fault, discovery curve, inference/annotation/setup cost |
| Unit of analysis | Paired run block trên cùng ID/fault pool/backend/budget/seed; suy luận qua fault families. Các run chung ID/fault không phải mẫu quần thể độc lập |
| GT/oracle | Common validator và fault adjudication không dùng generator verdict. Mask area/operator distribution cân bằng. Candidate không hợp lệ/không tạo được vẫn lưu và tốn budget generation |
| Baselines | Primary: validity-filtered box-aware random được cấp cùng source annotation. Secondary: raw random, box random, frozen hard-pair. Không dùng random toàn ảnh làm đối chứng mạnh duy nhất |
| Metrics | `Y(B)` primary trên controlled-fault pool; historical faults riêng/descriptive. Fault recall tại prefix; unique faults/100 logical calls; person-minutes/fault; valid fraction = validated-valid/proposals; all-attempt failure yield và valid-only yield báo cùng nhau |
| Threats | Source annotation miễn phí cho proposed; gate dùng chung làm mất khác biệt; chọn ca theo test outputs; nhiều near-duplicate; seed variance; failure yield do một easy fault |
| Claim criteria | Paired gain Y(B)>0, adjusted p<.05 và effect CI; không vượt bất kỳ cap đã khóa. Công bố cold-start và amortized cost. Kết quả phải còn hữu ích trước strong random có common gate; validity fraction cao hơn một mình không đủ |
| Falsification | Chi phí graph/triage xóa lợi ích; không hơn validity-filtered random/legacy; thêm cases chỉ trúng cùng root cause; cải thiện chỉ tồn tại khi bỏ invalid proposals khỏi mẫu số |

## Kế hoạch phân tích chung

Ba primary contrasts ở trên tạo một family, alpha .05, Holm. NI guards là điều kiện đồng thời để nhận claim, không được bỏ khi primary thuận lợi. Không gom mọi secondary ablation thành confirmatory. Đăng ký effect estimates, 95% cluster CIs, direction và zero-denominator policy (`NA`, không thay 0). Nếu có ít cụm hoặc không đủ discordant fault families, báo descriptive/CI và **không** dùng hàng nghìn fields tạo p nhỏ.

RQ1 bootstrap/permutation theo canonical ID, sensitivity thêm connected pixel components. RQ2 resample/paired comparison ở root-cause family; RQ3 paired budget blocks với multiway ID/fault-family sensitivity. Model families cố định báo từng họ; hai seed LoRA không thành hai hệ độc lập. Cách CI/test cụ thể và minimum detectable effect cần simulation/statistical adequacy trước lock; TASK 1 chưa chạy simulation hoặc test thống kê nào.

Không có ngưỡng số lỗi mới nào bảo đảm bài được nhận. Nếu RQ2 không có ít nhất ba historical root causes tái hiện được qua ít nhất hai stage, bỏ claim real-bug utility, giữ controlled mutation study; đây là minimum scope gate thực dụng, không thay power analysis.
