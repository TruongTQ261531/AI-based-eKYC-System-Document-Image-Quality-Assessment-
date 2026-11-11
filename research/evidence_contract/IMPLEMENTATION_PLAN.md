# Kế hoạch Source-Aware Evidence-Contract Testing

Ngày lập 05/11/2026. Mục tiêu là nghiên cứu một phương pháp kiểm thử phần mềm OCR/VLM trong bối cảnh eKYC. TASK 0 dừng ở tài liệu, bản kê bảo toàn và kiểm tra an toàn. Các mốc M1 trở đi trong tài liệu này là kế hoạch, chưa được thực hiện.

## Đối chiếu EASE 2027

CFP Research Track chấp nhận Software Testing, Software Quality, SE for AI, benchmarking và kết quả âm. Hạn abstract là 15/01/2027, bài đầy đủ 22/01/2027, theo AoE. Giới hạn bài là 10 trang nội dung và tối đa 2 trang chỉ dành cho tài liệu tham khảo. Bài và artifact kèm theo cần ẩn danh. Lập luận phải cho thấy đóng góp Software Engineering và phương pháp đánh giá thực nghiệm phù hợp. Các yêu cầu này được tra ngày 05/11/2026. [Nguồn chính thức](https://conf.researchr.org/track/ease-2027/ease-2027-papers)

Đánh giá phù hợp của project là một case study về test oracle và regression testing của phần mềm AI xử lý tài liệu. Dữ liệu eKYC cung cấp tình huống nhiều nguồn, trường tùy chọn, mất góc và precision. Muốn nộp Research Track cần đo chất lượng kiểm thử, khả năng tái lập và phạm vi áp dụng. Tăng F1 hoặc đổi tên logic V3 chưa tạo ra bằng chứng về một phương pháp kiểm thử mới.

Tên Source-Aware Evidence-Contract Testing là nhãn làm việc. Novelty còn phải được đối chiếu với metamorphic testing, contract/oracle testing, mutation testing cho phần mềm AI, document unanswerability và source-aware OCR. Các tài liệu related work cũ là đầu vào rà soát, chưa phải systematic review cho EASE.

## Đặc tả làm việc cần chốt trước khi xây

Với mỗi key, một realization gồm các component và provenance của nguồn. Hỗ trợ của key được tính theo OR giữa các realization và AND giữa component trong một realization. Đây là cấu trúc đã có trong `v3_sources.py`, được giữ làm đối chứng legacy.

Contract mới cần phân biệt ít nhất bốn điều kiện khi đánh giá một case.

1. Có nguồn hỗ trợ được xác định theo chính sách đã ghi và đủ mức precision.
2. Mọi nguồn trong phạm vi đã khai báo đều bị loại bỏ, với coverage đủ để kết luận trong phạm vi đó.
3. Chưa xác định được coverage hoặc legibility, gồm MRZ không parse được, barcode/QR chưa hỗ trợ, nguồn nằm ngoài schema và ngôn ngữ reviewer chưa đọc được.
4. Biến đổi không đạt precondition hoặc gây ảnh hưởng ngoài ý định, cần đánh dấu invalid/inapplicable.

Giá trị đúng vẫn còn trong MRZ sau khi che body không tạo thành lỗi mất bằng chứng. Chuỗi trùng nhau ở hai key khác nghĩa không tự tạo liên kết. Label và value, nguồn nhiều dòng, năm hai chữ số, raw output và normalized output cần có chính sách tường minh.

Các họ thử dự kiến gồm remove-one-source/retain-backup, remove-all-declared-sources, preserve-neighbor, multiline-component, precision và format/schema. Đây là gợi ý thiết kế. M1 phải loại hoặc sửa những quan hệ không có oracle hợp lệ. Model được yêu cầu xử lý ảnh theo một contract nghiệp vụ cụ thể; vi phạm cần được xác nhận, thay vì tự diễn giải thành nguyên nhân hallucination.

## Câu hỏi nghiên cứu dự kiến

| RQ | Câu hỏi | Kết quả cần đo |
|---|---|---|
| RQ1 | Oracle source-aware làm thay đổi việc phát hiện và phân loại lỗi ra sao so với oracle một vùng hoặc source-agnostic? | Fault-detection rate/recall trên lỗi có tham chiếu, false alarm trên known-good controls, unknown/invalid rate và độ bao phủ nguồn |
| RQ2 | Các biến đổi hợp lệ có phát hiện regression ở SUT/model version mà schema validation hoặc test ngẫu nhiên cùng budget bỏ sót không? | Lỗi thực và seeded faults báo riêng, unique fault types, detection per test/chi phí, trường bị bỏ sót hoặc điền sai |
| RQ3 | Kết quả giữ được ở backend, schema, bố cục và nguồn nào, với tài nguyên máy hiện tại? | Phân tầng theo nguồn/ID/operator/backend, latency và RAM/VRAM đúng phạm vi, biến thiên khi lặp có log |

Đơn vị thống kê phải phù hợp với claim. Nếu cùng một ID có nhiều view, lấy ID hoặc connected pixel components làm cụm. Nếu claim về phát hiện lỗi phần mềm, còn phải xét cụm theo fault/version. Chỉ bootstrap ID không tự tạo ra bằng chứng trên quần thể fault hoặc training seed.

## Mốc, dependency và nghiệm thu

| Mốc | Phụ thuộc | Công việc dự kiến | Tiêu chí nghiệm thu |
|---|---|---|---|
| M0 Audit | Không có | Kiểm kê, bảo toàn, đọc mã/báo cáo, test fixture, bốn tài liệu TASK 0 | Manifest kiểm tra sau cùng, HEAD/refs và file cũ khớp trước/sau; có log cho các test thực sự chạy |
| M1 Nghiên cứu và đặc tả | M0 | Rà prior art theo SE, chọn contribution hẹp, định nghĩa source coverage/precision/unknown, lập taxonomy lỗi lịch sử có commit/issue provenance | Mỗi claim gắn RQ, baseline và endpoint; phân biệt lỗi thực, lỗi cài có chủ đích, lỗi OCR và test invalid. Có kết luận go/reframe nếu trùng công trình gần nhất |
| M2 Adapter read-only | M1 | Chuẩn hóa graph, source provenance, review snapshot và SUT input/output trong namespace mới | Fixtures cover OR/AND, duplicate semantics, checksum-invalid, YYMMDD, multiline, optional fields và missing coverage. Không ghi dataset/result cũ và không đưa GT vào predictor |
| M3 Operators và validator độc lập | M2 | Triển khai các contract đã chọn, negative controls và kiểm soát mask/coordinate/collateral damage | Operator có precondition, expected relation, validity proof/limitation; validator không chỉ lặp lại target generator. Case unknown/invalid có mẫu số và lý do riêng |
| M4 Pilot hồi cứu và thiết kế test adequacy | M3 | Dùng raw outputs lịch sử ở chế độ read-only khi có đúng ảnh tương ứng, xác định failure taxonomy và chi phí | Mọi số hồi cứu ghi exploratory; cache reuse/rescoring tách khỏi model calls; có cùng case và ngân sách cho baseline. Chưa nhận kết quả cũ là xác nhận mới |
| M5 Khóa đánh giá prospective | M4 và tham chiếu đủ chất lượng cho endpoint đã chọn | Chốt RQs, fault corpus, development/future-evaluation roles, operator/version/model hashes, phân tích thống kê và tiêu chí dừng | Không tuning trên tập xác nhận. Kiểm tra ID/pixel/answer exposure, số người gán nhãn, unknown handling, multiplicity và equal-budget rõ trước execution |
| M6 Thực nghiệm có giới hạn | M5 và task thực thi riêng | Chạy SUT đã khóa trên plan vừa đủ, không retrain mặc định; repeat panel đo độ ổn định; audit output/score/cost | Mỗi lượt có begin/end/error, raw checkpoint/hash và đúng số mẫu. Báo tất cả baseline, invalid cases, kết quả âm và CI đúng đơn vị |
| M7 Replication package và manuscript | M6 | Tổng hợp bằng chứng SE, threats to validity, artifact ẩn danh và đường dẫn chạy an toàn | Script tái lập có dry-run mặc định; package tôn trọng license và dữ liệu cá nhân, claim giới hạn theo kết quả thực tế |

M1–M3 có thể tiến hành song song với việc người dùng hoàn thành 48 phiếu. M5 cho endpoint về legibility cần nhãn tương ứng đã được đánh giá phù hợp. Một người có thể cung cấp pilot; độ đồng thuận nhiều người cần người chấm độc lập thực sự và xử lý bất đồng. Không nhận hai mã của cùng người thành hai người.

## Đối chứng và tài nguyên

Baseline dự kiến gồm kiểm schema/format, oracle một vùng body, oracle hình học V3 hiện có và bộ test source-agnostic/ngẫu nhiên cùng số case. Đối chứng thêm/bớt nguồn phải được chọn theo câu hỏi nghiên cứu, không thêm hàng loạt model chỉ để tăng số lượng.

SUT có thể bắt đầu bằng parser/normalizer/geometry và backend đã có, rồi Vintern `partial_42` cùng OCR CPU khi task thực nghiệm cho phép. RapidOCR v4 và Latin-v5 hiện chia sẻ detector/classifier, nên không được đếm thành hai hệ thống hoàn toàn độc lập. Hai seed LoRA cùng Vintern cũng chỉ là một họ backbone.

Dùng venv và overlay sẵn có, chạy GPU tuần tự, kiểm lock trước mỗi experiment. Chỉ cache hit có input/preprocessing/model hash khớp mới được dùng lại. Test mới chưa có output phải được đo thực tế khi được giao triển khai. TASK 0 có 0 lượt neural inference và 0 optimizer step.

## Rủi ro và cách xử lý

| Rủi ro | Cách xử lý dự kiến |
|---|---|
| Oracle tự xác nhận do cùng code sinh và chấm | Construction-exact microcases, validator độc lập và review subset có provenance; báo mức bất định |
| Không biết hết MRZ, barcode, bản ngữ hoặc nguồn encoded | Giới hạn source coverage theo schema. Dùng unknown khi chưa đủ, không sửa nhãn cũ |
| Che một vùng làm đổi ngữ cảnh hoặc hỏng vùng lân cận | Kiểm precondition và ảnh raster; negative controls; báo collateral damage và fallback |
| Model inference dao động hoặc hết token | Khóa cấu hình, repeat panel có log, phân biệt lỗi định dạng với vi phạm nội dung |
| Nhiều field/view gây pseudoreplication | Ghép case đúng hash, cụm ID/fault/version theo claim, CI và multiplicity đăng ký trước |
| Tập cũ đã bị dùng để điều chỉnh | Chỉ dùng làm hồi cứu/development, tạo đánh giá prospective riêng trước khi kết luận tổng quát |
| Thay fixture hoặc import chạy nhầm pipeline | White-list entry point, read-only adapter, output path riêng và content-integrity gate |
| Dữ liệu/ảnh/weights/Windows fonts bị công bố sai | Package chỉ chứa thứ được phép chia sẻ; giữ attribution/license, giả lập nội dung công khai, artifact ẩn danh riêng |
| Một ứng dụng, ít ID, ít seed và một người chấm | Thu hẹp claim case study. Tăng độc lập của bằng chứng trước khi nhận generalization rộng |

## Điều kiện dừng sau TASK 0

M0 chỉ hoàn tất khi bốn file tài liệu tồn tại, log test khớp số báo cáo và manifest kiểm tra sau cùng không có thay đổi ngoài vùng cho phép. Chưa tự gọi generator, framework runner, retrain, model inference, sửa API mentor hoặc công bố Git. Task tiếp theo cần được giao riêng theo kế hoạch đã xem xét.
