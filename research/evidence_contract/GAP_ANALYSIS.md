# Research gap và claim ledger

TASK 1, 06/11/2026. Trạng thái: **giả thuyết phương pháp đã thu hẹp; chưa chứng minh superiority hoặc novelty đủ cho EASE**. Bảng literature và trạng thái đọc/venue nằm trong [RELATED_WORK](RELATED_WORK.md).

## Vấn đề Software Engineering được chọn

Khi nâng cấp crop/rectification, OCR/VLM, parser hoặc normalizer, pipeline có thể trả output khác. Tester phải phân biệt: một thay đổi hợp lệ; lỗi đọc vốn đã có; regression mới; một test được tạo sai; hoặc oracle không đủ bằng chứng. Nhầm các loại này làm developer sửa nhầm thành phần và đánh giá sai chất lượng bản cập nhật.

Ví dụ giả lập: body bị che nhưng document number vẫn đọc được trong MRZ. Oracle chỉ nhìn body báo sai một output được hỗ trợ. Ví dụ khác: che A làm B rõ ràng bị mất ở bản mới, trong khi nhiều field khác được cải thiện nên F1 tổng tăng. Cả hai là ví dụ minh họa, **không phải lỗi thực mới đã tìm thấy trong TASK 1**. Để gọi ví dụ thứ hai là regression phần mềm phải có version/fault provenance và ground truth phù hợp.

Đơn vị đóng góp là **cách xác lập test admissibility và xác minh cảnh báo regression theo evidence contract**, trong một empirical case study của software AI xử lý tài liệu. Không thay thế bằng bài cải thiện OCR hoặc huấn luyện nhận dạng danh tính.

## Điều đã biết và phần còn cần kiểm chứng

| Ý tưởng | Bằng chứng có trước | Quyết định |
|---|---|---|
| Visible/full references, abstention | R01–R04 | Tái sử dụng làm nền; không claim mới |
| Multiple spans, coordinates, grounded extraction | R05–R06 | Giữ baseline semantic/source; source graph không tự mới |
| Counterfactual occlusion | R07–R08; hard-pair hiện có | Không dùng masking hoặc LoRA làm đóng góp |
| MR validity và FP/FN | R09 | Không claim phát minh oracle validity |
| MT cho OCR-VQA, document workflows, evidence drift | R10–R12 | Bác claim “accuracy không thấy lỗi nên MT là mới” |
| Guided generation có validation | R13 | H3 rộng bị prior art bao phủ |
| Regression sau model evolution, matched testing budget | R14 | Before/after correctness và budget cũng không mới |
| Coverage/precision/unknown gắn source-loss contract và fault verification | Chưa thấy được đo đồng thời theo đúng thiết kế này trong 14 bài đã đọc | Chỉ là **candidate gap hẹp**; cần kiểm strong baselines và mở rộng tìm kiếm trước manuscript |

Không suy ra một bài “không có” tính năng từ việc abstract không đề cập. Đối chiếu trên sections thực đọc, với giới hạn tìm kiếm đã khai báo.

## Phản biện H1–H3 và phiên bản giữ lại

### H1: source-aware giảm false alarms

H1 gốc dễ thành tautology: oracle được cho thêm MRZ đương nhiên tránh một số lỗi body-only. V3 của chính repository đã có OR các realization và AND các component. So với body-only là sanity check, không đủ chứng minh phương pháp mới.

**H1' giữ lại:** so với V3 đóng băng, contract có kiểm semantic coverage, precision và admissibility giảm tỷ lệ cảnh báo sai trên panel độc lập, với giới hạn mất sensitivity và decision coverage đã khóa trước. So thêm source-agnostic để giải thích cơ chế. Không được thắng bằng cách trả `unknown` mọi ca khó. Claim bị bác/không được hỗ trợ nếu lợi ích chỉ do thêm annotation, giảm coverage quá mức hoặc chỉ có ở control tự dựng thuận lợi.

### H2: field non-interference phát hiện regression

H2 gốc đã gần R10/R12. Non-interference còn là yêu cầu nghiệp vụ cần precondition: giữ pixel của B không đảm bảo vẫn xác định được ý nghĩa B khi label hay context phân biệt đã mất.

**H2' giữ lại:** các contract hợp lệ cung cấp cảnh báo regression có độ chính xác và fault recall hữu ích qua phiên bản, so với generic per-field differential/metamorphic checks và legacy V3/hard-pair, trên cùng output/budget. Chỉ gọi regression do transformation khi có witness bốn execution; chỉ gọi software fault khi có provenance độc lập. Aggregate F1 là đối chứng mô tả. Gold per-field oracle là upper bound; không nhận công “vượt” nó bằng cách giảm thông tin của baseline.

Nếu một normalized per-field diff có chung validity gate đạt cùng kết quả, H2' không chứng minh thêm thuật toán. Khi ấy giá trị có thể còn là empirical taxonomy/measurement, cần đổi framing trung thực.

### H3: evidence-conditioned generation tốt hơn random masking

R13 đã làm guided mutation và semantic verification; R04 đã tạo traps từ evidence anchors. “Sinh có hướng dẫn và lọc hợp lệ” không còn là novelty độc lập.

**H3' giữ lại:** source-graph-conditioned selection tăng **số fault riêng biệt được xác minh tìm thấy trong cùng ngân sách**, so với box-aware random **được cấp cùng annotation và cùng independent validity gate**. Frozen hard-pair selector là baseline thêm. Tỷ lệ case hợp lệ chỉ là secondary endpoint; tăng tỷ lệ này không tự chứng minh tìm thêm lỗi. Tính cả chi phí lập source graph, mọi proposal bị loại, annotation/triage, cache và mọi inference phục vụ selection.

## Một đóng góp chính, tối đa hai hỗ trợ

**C1 — chính, có điều kiện:** phương pháp đánh giá regression bằng evidence contracts với precondition, semantic source scope, typed precision và verdict có bất định; kiểm chứng chất lượng oracle bằng controls/faults độc lập. Đây là domain-specific testing method, chưa có thuật toán mới được chứng minh vượt prior art.

**C2 — hỗ trợ:** bộ case/fault có provenance, nhãn admissibility và trace qua stage/version, được phép công bố. Đóng góp dữ liệu là test artifacts có giá trị chẩn đoán; không gọi tập SPECIMEN là dataset người dùng eKYC thật mới.

**C3 — hỗ trợ:** replication package và matched-budget evaluation có log, frozen baselines và chi phí annotation. Code adapters/web/report là engineering phục vụ đánh giá, không cộng thêm thành nhiều novelty claims.

## Bằng chứng hiện có và những thứ không được suy diễn

| Có từ TASK 0 / báo cáo cũ | Dùng được cho TASK 1 | Không chứng minh |
|---|---|---|
| `v3_sources.py`, scorer precision, hard-pair masks | Khởi điểm đặc tả, legacy baselines | Oracle hoàn chỉnh hoặc legibility đúng của người |
| OCR labels benchmark, raw outputs đã đóng băng | Hồi cứu exploratory đúng ảnh/hash | Prospective confirmatory test mới |
| Hard-pair: hai mục tiêu có trade-off; fair-controls không xác lập lợi thế hard mining | Negative evidence để tránh lặp lại claim | H3 đã đúng hoặc nên retrain tiếp |
| Một người đang review; snapshot TASK 0 là 35/48, không độc lập verified | Pilot feedback và issue provenance | Hai annotator, agreement hoặc hoàn tất nhãn người |
| Chưa có bộ camera mới được phép thu thập | Giới hạn scope theo construction/public specimens | Khả năng tổng quát camera Việt Nam, bảo mật eKYC hoặc PAD |

Không refresh số phiếu bằng cách sửa snapshot cũ. Không lấy kết quả về Module 1–3 làm chứng nhận Module 4–5.

## Gate chọn phạm vi

Cho phép bước tiếp theo **adapter/fixture nhỏ** khi được giao riêng: RQs và verdict đã đủ rõ để cài đặt rồi bác bỏ bằng dữ liệu. Chưa cho phép coi đây là protocol confirmatory đã đăng ký: còn cần fault corpus thực, lock cases/budget/statistical adequacy và đánh giá oracle độc lập.

Nếu chưa có reviewer độc lập hoặc ảnh tự nhiên đủ tham chiếu, bắt đầu bằng **construction-exact specimens và controlled faults**, báo riêng giới hạn. Nếu không có lỗi lịch sử có thể tái hiện, chỉ claim mutation/case study; không đổi tên mutants thành real bugs. Nếu không hơn V3 + validity-filtered random, hạ claim xuống nghiên cứu thực nghiệm về failure modes của test oracle, cân nhắc short/emerging hoặc negative-result scope thay vì ép Research Track superiority.

Chi tiết falsification: [RESEARCH_QUESTIONS](RESEARCH_QUESTIONS.md). Quy trình và khóa trước execution: [PROTOCOL_DRAFT](PROTOCOL_DRAFT.md).
