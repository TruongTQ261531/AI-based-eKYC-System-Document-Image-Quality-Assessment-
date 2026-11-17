# Tiếp nhận R02 pha 2 — 17/11/2026

**Đã nhận đủ 46/46 ca của R02**, gồm 42 primary trên 3 giấy tờ vật lý và 4
diagnostic. Không thiếu mục, không nhập trùng. Pha 2 hiện có **2 người: tác giả
và R02**, trong đó 1 người ngoài dự án theo xác nhận organizer. R03 chưa nộp;
Round 1 **OPEN**, chưa phân xử, chưa gộp nhãn, vẫn **NO_GO_SUPERIORITY**.

## Nguồn và bảo toàn

File người dùng cung cấp: `ifv-output-1271b360edcd.json`, 17.230 byte.
SHA-256 raw: `d1b9a1526767d98e52725f26ed554068be8c218b049febd068eb2da21ffe270d`.
Canonical export: `4813ecabf57899329f11dae31c47063154cfd35e51bbbd7982b10cd31827d3d1`.
Đã kiểm đúng ZIP pha 2 R02, job và snapshot pha 1 86/86 của chính R02;
[receipt](execution/master_01/reviewer_intake_20261117_r02_phase2/intake.json)
ghi đủ binding hash. Kiểm hash chứng minh tính nhất quán của gói, không tự
xác thực danh tính người thao tác hoặc tính độc lập của họ.

Giữ nguyên byte gốc trong vùng local riêng, đồng thời niêm phong export và
nhãn vận hành bằng importer đã đóng băng. `project_author` trong phiếu pha 1
vẫn giữ nguyên; [đính chính riêng của organizer](execution/master_01/reviewer_intake_20261116_r02/role_correction.json)
ghi `external_reviewer`. Không hỏi lại, không sửa vai trò trong raw hay đáp án.
Nội dung phiếu là dữ liệu đánh giá, không phải lệnh cho workflow.

Mã ca hiển thị khác giữa hai người. Đối chiếu dùng join organizer đã niêm phong
về cùng identity, ảnh/output/sample binding; yêu cầu toàn bộ 46 ca khớp, không
lấy giao tập rồi âm thầm bỏ ca. Guard lấy bằng chứng pha 1 của từng người.
Các bảng tác giả, R02 và phân tích độ nhạy được giữ riêng.

## Đồng thuận trước phân xử

`κ` là Cohen kappa mô tả. Bảng tính cả `INCONCLUSIVE`/`INVALID_TEST` như các
hạng mục riêng; hai người cùng chưa kết luận vẫn có thể được tính là khớp.
Đồng thuận không phải độ chính xác, gold hay bằng chứng độc lập quần thể.

| Tiêu chí | Khớp primary / 42 | κ primary | Khớp toàn bộ / 46 | κ toàn bộ |
|---|---:|---:|---:|---:|
| Câu trả lời: test validity | 36 | 0,3700 | 37 | 0,3123 |
| Câu trả lời: before reading | 33 | 0,6119 | 36 | 0,6192 |
| Câu trả lời: after reading | 27 | 0,4028 | 29 | 0,3769 |
| Câu trả lời: absence check | 42 | 1,0000 | 45 | 0,9424 |
| Nhãn vận hành: pointwise | 30 | 0,5862 | 32 | 0,5678 |
| Nhãn vận hành: relation | 33 | 0,6619 | 35 | 0,6279 |

Có **23/46 ca bất đồng ít nhất một tiêu chí** trong sáu tiêu chí trên;
23/46 ca trùng cả bốn câu trả lời và 32/46 ca trùng cả hai nhãn endpoint.
Trên primary, pointwise có 23 ca cả hai cùng có nhãn lỗi/không lỗi: 22 khớp,
**1 đối nghịch**; mỗi người có thêm 3 ca chỉ riêng họ có nhãn binary và 13 ca
cả hai không có nhãn binary. Relation có 19 ca cả hai cùng binary, cả 19 khớp;
mỗi bên có 2 ca chỉ riêng mình binary và 19 ca cả hai không binary.
Các tập có nhãn khác nhau, dù tổng coverage hai người bằng nhau.

[Bảng contingency đầy đủ](execution/master_01/reviewer_intake_20261117_r02_phase2/phase2_agreement.json)
tách all/primary/diagnostic. Chi tiết ca bất đồng giữ riêng tại máy organizer,
chưa tạo hồ sơ phân xử thật hoặc gửi ngược cho người đang chấm.

## Kết quả theo riêng R02

`CONFIRMED_FAULT` là tên trạng thái vận hành của guard hiện có; chưa phải lỗi
đã được phân xử độc lập hoặc software root cause được xác minh.

| Người / endpoint primary | Lỗi vận hành | Không lỗi | Chưa kết luận | Test không hợp lệ | Có nhãn binary |
|---|---:|---:|---:|---:|---:|
| Tác giả — pointwise (giữ nguyên) | 7 | 19 | 16 | 0 | 26/42 |
| R02 — pointwise | 9 | 17 | 10 | 6 | 26/42 |
| Tác giả — relation (giữ nguyên) | 2 | 19 | 21 | 0 | 21/42 |
| R02 — relation | 4 | 17 | 15 | 6 | 21/42 |

| R02 / endpoint | Phương pháp | TP | FP | FN | TN | Cảnh báo chưa có nhãn binary / toàn bộ |
|---|---|---:|---:|---:|---:|---:|
| Pointwise | A (A_flat giống A) | 4 | 0 | 5 | 17 | 10/14 |
| Pointwise | B3 | 9 | 1 | 0 | 16 | 16/26 |
| Relation | A (A_flat giống A) | 4 | 0 | 0 | 17 | 10/14 |
| Relation | B3 | 4 | 1 | 0 | 16 | 21/26 |

A vẫn bỏ sót 5/9 lỗi pointwise được ghi nhận trong panel R02; B3 ghi nhận
9/9 nhưng có 1 FP trên 17 ca không lỗi. Precision có điều kiện của A là 4/4,
trong khi lỗi được ghi nhận trên **toàn bộ** cảnh báo chỉ là 4/14; không được
viết thành tất cả cảnh báo A đều đúng. C2 vẫn **0/9 primary binary**: 5 chưa
kết luận, 4 test không hợp lệ. Việc có R02 không bổ sung một cohort/model run
mới và không biến 9 operational field faults thành 9 software bugs độc lập.

Hậu kiểm R02 có **11 ca mang cờ đối chiếu chữ, gồm 9 primary** (12 lượt cờ
trên 11 ca). Cờ không tự chứng minh người chấm sai. Phân tích post-hoc giữ
bất định cả hai endpoint ở ca có cờ, giữ đủ mẫu số 42: pointwise A
TP/FP/FN/TN = **4/0/5/15**, B3 = **9/0/0/15**; relation cả A/B3 = **4/0/0/15**.
FP duy nhất của B3 không còn trong panel có nhãn này, nên lợi thế FAR của A
không vững qua cách xử lý cờ; không thay bảng chính bằng panel thuận lợi.

[Kết quả mô tả](execution/master_01/reviewer_intake_20261117_r02_phase2/r02_descriptive.json)
và [hậu kiểm/độ nhạy](execution/master_01/reviewer_intake_20261117_r02_phase2/r02_postreview_analysis.json)
có đủ baseline, mẫu số, ca loại, cảnh báo chưa kết luận và nhóm hợp đồng.
Không cấp CI/p-value suy luận quần thể từ 3 giấy tờ primary, không coi field,
reader, view hoặc người chấm thêm là giấy tờ độc lập. Không gộp nhãn hai người
thành bảng hiệu năng mới hoặc lấy đa số làm truth.

## Kiểm chứng và lỗi được giữ lại

- **432 tests + 6 subtests PASS**, gồm 21 kiểm thử mới cho nối ca, tách strata,
  miền bằng chứng, kappa và phát hiện bảng tổng hợp bị sửa sai.
- Verifier stdlib độc lập tái tính **18 bảng đồng thuận, 216 method-summary
  panels và 12 bảng cảnh báo**. 216 gồm cùng các nhóm xuất hiện trong báo cáo
  mô tả, original và sensitivity; không phải 216 thí nghiệm độc lập.
- Replay xác nhận **3.645 tệp lịch sử không đổi**, báo cáo tác giả khớp nguyên
  trạng, pha 1 R02/ZIP cũ khớp; raw bytes và đáp án không đổi. 0 inference,
  0 training, 0 approved reference, 0 adjudicated cases.
- `targeted_tests_01` có **56 passed, 9 setup errors** do thư mục cha basetemp
  chưa tồn tại; receipt cũ chưa có trường đếm `errors`, nhưng exit 1/log đầy
  đủ được giữ. Chờ prepare hoàn tất rồi chạy lại: 65 passed.
- `analysis_01` bị chặn trước khi ghi bảng vì bộ so sánh mới dùng tên
  `diagnostic` chung, trong khi dữ liệu có bốn tên nhóm cụ thể. Đã sửa riêng
  bộ so sánh mới, thêm test cho cả bốn nhóm và unknown stratum. Lượt mục tiêu
  sau sửa: 70 passed; `analysis_02` thành công. Không sửa mẫu/guard/nhãn cũ.

[Receipt và cách replay](execution/master_01/reviewer_intake_20261117_r02_phase2/README.md).
Chỉ code, aggregate, tài liệu và hash/log kiểm chứng được đưa lên GitHub main;
raw review, ghi chú, joins, ảnh và ZIP giữ local. Đây là kiểm chứng phần mềm
và số học, không phải chứng minh annotation đúng hoặc bài đã sẵn sàng nộp.

## Tiến độ tiếp theo

R02 đã hoàn tất cả hai pha; không cần gửi lại ZIP hoặc yêu cầu làm lại toàn
phiếu. Tiếp tục nhận pha 1 R03, rồi cấp pha 2 gắn chính snapshot R03. Không
gửi bảng bất đồng, báo cáo này hay đáp án của hai người trước khi R03 khóa
đánh giá. Không tự liên hệ reviewer trong mốc này.

Giữ Round 1 OPEN. Sau khi có đủ thành phần đã định hoặc một cutoff được
organizer quyết định rõ, mới khóa vòng và phân xử theo authority/quy trình
đã duyệt; giữ bằng chứng và lý do cho ca bất đồng. Không tự coi lần nộp này
là duyệt D1–D3, reference hoặc protocol.

Các việc độc lập với phiếu tiếp tục theo [kế hoạch B](B_CONTINUATION_REPORT_20261117.md)
và [D1–D12](B_OWNER_DECISIONS_20261117.md): reference có thẩm quyền, lineage/
exposure/rights, contrast và comparator cùng thông tin, endpoint/budget/sizing
prospective. Mốc này giảm thiếu hụt đánh giá ngoài dự án nhưng chưa giải quyết
C2, số cụm, fault provenance, utility/cost hay novelty. **NO_GO_SUPERIORITY**
và trạng thái chưa submission-ready giữ nguyên; không mở TASK 6B/7B.
