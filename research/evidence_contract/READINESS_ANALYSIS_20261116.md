# Phương án A và mức sẵn sàng EASE — 16/11/2026

**Đúng phạm vi chủ đề; chưa đủ căn cứ cho tuyên bố A vượt baseline hoặc cho bài
Research hoàn chỉnh.** Đây là hai kết luận khác nhau. CFP nhận Software Testing,
Software Engineering for AI và nghiên cứu thực nghiệm, kể cả kết quả âm. Đánh giá
còn xét phương pháp, giá trị đóng góp, tính mới, khả năng kiểm chứng và trình bày.
Không có tỷ lệ accuracy hay số người chấm duy nhất làm project tự động “đạt EASE”.
[CFP Research](https://conf.researchr.org/track/ease-2027/ease-2027-papers), kiểm tra 16/11.

Mốc này đã hoàn thành hai thực nghiệm không cần phiếu mới, một bộ replay độc lập
và phương án bản thảo Emerging Results. Mục tiêu Research vẫn mở. Không sửa A,
baseline, phiếu đã niêm phong hoặc ZIP R02/R03 đang được gửi.

Kiểm cuối: **260 Python + 6 subtests PASS**, 460 tài sản được bảo toàn, báo cáo
IFV cũ replay đúng và 2 ZIP reviewer không đổi. Đã cài compiler local, xuất
[PDF ACM 3 trang](paper/output/pdf/emerging_20261116.pdf), xem đủ trang và sửa lỗi
dàn trang. [Gói public replay 22 file](paper/readiness_replay_20261116.zip) đã được
giải nén và chạy riêng thành công; không cần toàn project, model hoặc phiếu riêng.
[Receipt build](execution/master_01/readiness_20261116/pdf_build_receipt.json) ·
[Receipt package](execution/master_01/readiness_20261116/package_receipt.json).

## Đã có gì

| Bằng chứng | Khối lượng đúng | Có thể kết luận |
|---|---|---|
| Pilot reader cũ | 93 output thực; 132 lượt so sánh, 120 sau bỏ trùng; 3 reader, hai reader cùng họ | Hành vi development có thể replay; không phải 132 tài liệu độc lập |
| Đánh giá cá nhân | 86 ô pha 1, 46 ca pha 2; 42 primary/3 physical ID | Mô tả một tác giả; 0 người ngoài đã nhập |
| A so với flat | 120/120 lượt primary cũ giống nhau | Chưa có lợi ích riêng của biểu diễn đồ thị tại oracle |
| Reference controls trước mốc này | 252 lượt output tiêm, 131 so sánh khác nhau/13 cặp pixel | Kiểm tra cơ chế, không phải 252 suy luận model |
| Phân tích mới | 255 cấu hình nguồn; 164 control oracle | Giải thích sự tương đương có điều kiện và ngoại lệ |
| Parser mới | 118 ca/115 input; 5 bản mã; 2 lỗi lịch sử | Bằng chứng sửa–hoàn tác trên mã thực; 0 lỗi mới được phát hiện |

Teacher classifier đã từng train 7 epoch. Train thêm classifier chất lượng ảnh
không giải quyết tính mới của oracle, nguồn tham chiếu hoặc tính độc lập của mẫu.
Mốc này thực hiện **0 inference model, 0 training và 0 nhãn người chấm mới**.

## Tồn đọng ngoài việc chờ người khác chấm

| Vấn đề | Vì sao còn vướng | Xử lý đã làm / điều kiện đóng |
|---|---|---|
| Lợi ích riêng của A | A/flat giống nhau; A_dual có kênh field đúng bằng B3 | Đã rút gọn điều kiện quyết định và giữ counterexample. Chỉ mở lại claim đồ thị nếu đo được sinh test hợp lệ, chẩn đoán hoặc chi phí tốt hơn trên dữ liệu mới, cùng thông tin |
| Trộn pointwise với relation | Original sai khiến C3/C4 abstain dù follow-up sai; A có FN 5/7 trên tập tác giả chấm | Đã có hai kênh riêng ở prototype. Không lấy giảm alarm làm giảm lỗi; khóa sensitivity, coverage và FAR cùng nhau |
| Tham chiếu sai dùng chung | A và B3 có thể đồng thời sai; hash chỉ ràng buộc nội dung | Prototype kiểm nguồn, kiểu giá trị và provenance; vẫn cần inventory độc lập. Không dùng sự đồng thuận model làm gold |
| C2/MRZ và chính sách nguồn | Cả 10 ca C2 primary được chấm vẫn inconclusive; checksum/precision/semantic link chưa có đủ kiểm chứng | Có control backup tốt/xấu. Cần bổ sung trường có/không check digit, xung đột nguồn, độ chính xác ngày; không suy ra thế kỷ từ YYMMDD |
| Đại diện dữ liệu | Nhiều biến thể từ 3 ID không thay thế tài liệu/layout/capture độc lập | Chọn corpus ngoài renderer và split theo physical ID/template; khảo sát MIDV-2020. Chưa tải hoặc công bố corpus mới |
| Lỗi thực và nguyên nhân | Output bất thường chưa phải bug đã định vị; injected fault không phải lỗi tự nhiên | Đã bổ sung 2 lỗi parser có before/fix/revert. Cần thêm lỗi pipeline được phát hiện tiến cứu, khác family; không đếm 76 biến thể thành 76 lỗi |
| Chi phí | Thời gian parser không gồm OCR, annotation, triage | Đã đo timing và budget curve có giới hạn. Cần chi phí end-to-end, thời gian người xem và unique fault yield tại cùng ngân sách |
| Kiểm chứng độc lập và overfitting | Các ca mới được thiết kế sau khi biết lỗi; sửa A trên pilot rồi chấm lại không là confirmatory | Giữ development riêng; khóa protocol/endpoint/baseline trước cohort mới, báo mọi seed/run âm; xác định sample size từ effect/precision và đơn vị cụm |
| Tính mới so với paper | MT, source grounding, selective prediction và patch reproduction đã có trước | [Evidence map](METHODS_EVIDENCE_MAP_20261116.md) tách phần áp dụng, chưa triển khai, và không có cơ sở dùng; cần đánh giá novelty của đóng góp hẹp |
| Bài viết và artifact | Draft Research cũ còn bảng pending, public repo có danh tính | Draft Emerging đã build và kiểm 3 trang; gói replay public chạy được riêng. Còn gói ẩn danh cuối, quyền phân phối và tác giả duyệt. Public GitHub không phải supplement double-anonymous |

## Kết quả mới: giới hạn của A/flat

[Artifact](execution/master_01/readiness_20261116/representation_run_01/results.json)
và [mã audit](master/representation_audit.py).

- **255/255** cấu hình nguồn khớp phép tổng hợp phẳng: 0–3 nguồn, 4 trạng thái,
  3 mức completeness. Đây là cấu hình trừu tượng, không phải nhãn ảnh.
- **64/64** primary control khớp A/flat. Với nguồn/validity/reference giống nhau,
  các điều kiện C1–C4 giải thích kết quả; chạy thêm seed cùng miền không tạo ra
  lợi thế riêng của đồ thị.
- **153/164** control tổng thể khớp. 8 khác biệt là C1 limited inventory: A phát
  candidate chưa được xác minh, flat abstain. 3 khác biệt là graph/mutation/origin
  binding bị cố ý làm sai. Probe image binding bị cả hai từ chối.
- Bản rút gọn giữ các điều kiện trên tái tạo A **164/164**. Đây là phân tích mã,
  không là detector mới hoặc kiểm chứng độc lập sự thật. Ngoài miền đã xét không
  tuyên bố tương đương phổ quát; certificate/gold, policy khác, typed dates còn
  cần kiểm riêng.

Vì vậy, hướng giữ A có căn cứ nhất là **đo giá trị nguồn trong sinh phép thử,
kiểm tra validity và giải thích nguyên nhân**, với baseline phẳng nhận cùng
thông tin. Nếu không có lợi ích, giữ kết quả âm có điều kiện và thu hẹp claim.

## Kết quả mới: chạy mã parser trước/sau/hoàn tác

[Kết quả đầy đủ](execution/master_01/readiness_20261116/parser_run_01/results.json),
[input và yêu cầu](execution/master_01/readiness_20261116/parser_run_01/cases.json),
[output thực](execution/master_01/readiness_20261116/parser_run_01/outputs.json).

| Phiên bản | Pass trên 118 ca |
|---|---:|
| Trước sửa | 42 |
| Sau sửa | 118 |
| Hoàn tác sửa giá trị một ký tự | 92 |
| Hoàn tác sửa tên mâu thuẫn | 68 |
| Hoàn tác cả hai | 42 |

Có 50 biến thể của lỗi ghép tên mâu thuẫn, 26 biến thể của lỗi bỏ giá trị một ký
tự, và 42 control pass ở mọi phiên bản. Chỉ có **2 fault family đã biết**.
Nguồn trước sửa khớp byte với Git `4110f22`; nguồn sau sửa khớp archive application
14/11. Hai hoàn tác cùng lúc có AST giống mã cũ. Các yêu cầu được viết sau khi
biết lỗi; A đóng băng không được đánh giá bằng panel parser này.

Delta debugging bỏ noise và giữ witness 1 dòng cho custom value, 2 dòng cho tên
mâu thuẫn. Tính tối giản là theo xóa từng dòng và giữ tiền điều kiện yêu cầu,
không phải input tối giản toàn cục. Mốc chính có **590 parser calls**, giảm input
có **18 calls**, đo 30 lần mỗi phiên bản có **17.700 calls**. Bộ verifier riêng
chạy lại **596 calls**; không cộng chúng thành số ca độc lập.

Trên 115 input bỏ trùng, 500 hoán vị cho tỷ lệ gặp cả hai family như sau:

| Ngân sách input | Random đều | Luân phiên loại input |
|---|---:|---:|
| 2 | 20,0% | 10,6% |
| 5 | 68,2% | 73,8% |
| 10 | 93,0% | 100,0% |

Không có chính sách thắng ở mọi ngân sách. Pool/type được xây sau khi biết lỗi,
nên đây không phải xác suất phát hiện lỗi chưa biết. Median cho một batch 118 ca:
mã cũ 19,82 ms, mã sửa 19,84 ms; warm process, thứ tự subject cố định, có cả dựng
token và đối chiếu yêu cầu. Không suy ra cải thiện tốc độ hay chi phí con người.

## Thứ tự tiếp tục và tiêu chí hoàn tất

1. **Đóng mốc development:** kiểm code, replay public, bảo toàn 460 tài sản, ghi
   receipt, commit/push nhánh progress và kiểm HEAD remote. Không gộp main tự động.
2. **Đóng góp hẹp:** dùng draft Emerging Results cho phân tích parity, validity
   và provenance. Hoàn tất đối chiếu tính mới, PDF, artifact ẩn danh và tác giả
   duyệt. Đây là phương án phù hợp độ chín hiện tại, không phải cam kết được nhận.
3. **Cohort ngoài pilot:** kiểm license và schema MIDV hoặc nguồn tương đương;
   chỉ chuyển annotation có sẵn thành source inventory khi đủ semantic mapping.
   Chia physical ID/template trước chạy; chưa dùng test để chọn tham số.
4. **Sinh test và chẩn đoán:** so random, stratified/coverage và source-aware
   dưới cùng ngân sách, cùng validator và input information; ghi số test hợp lệ
   khác nhau, false alarms trên known-good, fault family xác minh, thời gian.
5. **Nghiên cứu Research:** chỉ khóa confirmatory khi đủ reference, cluster,
   fault provenance và cơ sở effect/precision. Không có một con số test, người
   chấm hay epoch chung áp dụng cho mọi claim.

Research: abstract 15/01, full 22/01/2027 AoE. Emerging/Short: abstract 22/02,
full 01/03/2027 AoE, tối đa 6 trang gồm references. Track này cho phép bằng chứng
sơ bộ có giới hạn, vẫn cần claim đúng độ chín và minh bạch.
[Short/Emerging CFP](https://conf.researchr.org/track/ease-2027/ease-2027-short-papers-and-emerging-results).
RENE cũng cần kết quả âm có phương pháp và giải thích, không chỉ “chưa thấy khác”.
[RENE CFP](https://conf.researchr.org/track/ease-2027/ease-2027-reproducibility-and-negative-results).

**Trạng thái khoa học: NO_GO_SUPERIORITY; EXPLORATORY_RESULT_DRAFT.** Hoàn tất
code/kiểm thử của một mốc không đồng nghĩa toàn bộ nghiên cứu đã đủ để nộp hoặc
được chấp nhận. [Quy trình replay](execution/master_01/readiness_20261116/README.md).
