# Chuẩn bị prospective sau IFV · DRAFT_ONLY

Ngày 15/11/2026. Đây là đề xuất thiết kế development tiếp theo, được viết sau
khi đã xem kết quả pilot. **Không phải preregistration của pilot, scientific GO,
test lock hoặc quyền chạy confirmatory 6B/7B.** RQ1–3, sample, output và nhãn
cũ giữ nguyên. [Kết quả kích hoạt đề xuất](IFV_RESULTS_VI.md)

Cập nhật thực thi 16/11: đã có [A lanes exploratory](A_DEVELOPMENT_20261116.md),
[gói reviewer và agreement](REVIEWER_HANDOFF_VI.md). Đây là tooling development
trên output cũ, không phải reference đã được phê duyệt hoặc một panel prospective
mới. Original A, sample, endpoint labels và superiority gate giữ nguyên.

Mốc không chờ feedback cùng ngày đã hoàn tất [prototype reference và đối chứng](REFERENCE_CONTROLS_20261116.md):
hash/schema binding, typed policy, scope/trust guards, lane cấu trúc và 252 control
executions. Cùng reference đúng giúp cả A_bound_dual và B3_bound; chưa có approval
external hoặc ảnh/model mới. Constructed reference không được dùng cho actual_model.

## Câu hỏi được ưu tiên

Định lượng ảnh hưởng của **reference validity, nguồn thay thế và điều kiện
original-correct** lên độ phủ và cách diễn giải cảnh báo oracle. Chưa đặt
graph superiority làm claim đã có bằng chứng. So sánh A với A_flat nhận cùng
thông tin, B3/gated V3 và các sanity controls trên cùng execution set.

1. Một lỗi pointwise đã tồn tại ở ảnh gốc khác thế nào với lỗi relation hoặc
   regression có witness? Báo cả hai endpoint, không dùng nhãn của endpoint
   này để suy endpoint kia.
2. Độ đầy đủ nguồn, checksum/type của backup và semantic context ảnh hưởng
   eligibility và unresolved alarms thế nào?
3. Các ước lượng thay đổi thế nào khi có/không có bằng chứng reference đủ
   provenance? Chốt chính sách và sensitivity trước output của panel mới.

## Reference cần hoàn thiện trước inference mới

| Thành phần | Yêu cầu kiểm được | Ca không đủ |
|---|---|---|
| Đọc chữ và semantic key | Annotation gắn đúng ảnh/hash và trường; liên kết body/duplicate/MRZ có nguồn xác minh | Unassessed/inconclusive; không chép từ prediction hay từ ảnh khác |
| C2 backup | Thực sự có nguồn còn đọc được cho đúng field; MRZ chỉ hỗ trợ semantic key phù hợp, checksum/format theo policy đã chốt | Không tự suy tên trường từ MRZ hoặc sửa transcript bằng đáp án tác giả |
| C1 removal | Có inventory nguồn đủ scope và bằng chứng mọi realization hợp lệ đã mất | Bbox mục tiêu hoặc not_seen riêng một vị trí không chứng minh absence toàn bộ |
| Giá trị và cách đánh giá | Kiểm literal, normalization theo kiểu và khả năng empty/omission trước export; giữ O/0 khác nhau | Ghi discrepancy riêng; không tự sửa human choice |
| Tính độc lập | Reviewer khác thật hoặc chuẩn độc lập thích hợp endpoint, provenance/exposure rõ | Một tác giả + script kiểm logic chưa thành adjudication độc lập |

Với panel constructed controls, reference máy có thể chứng minh tính đúng
của chuỗi, kiểu và phép xóa theo construction. Validator reference phải tách
khỏi graph/scorer đang được đánh giá và có đối chứng phát hiện sai. Kết quả
đó chỉ áp dụng constructed endpoints, không cấp human legibility cho ảnh tự
nhiên. Không dùng chính graph vừa sinh làm bằng chứng độc lập duy nhất.

Danh sách 17 cờ hiện tại nằm riêng dưới `local/master_01/ifv_analysis_812605bbab3940be.json`.
Nếu cần phân xử, dùng provenance/amendment mới; phiếu cũ không ghi đè. Chưa
nhận thêm review ngoài; đã chuẩn bị hai ZIP pha 1 cho R02/R03. Pha 2 của từng
người chỉ được tạo sau seal riêng. Không yêu cầu tác giả chấm lại toàn bộ.

## Thiết kế panel cần chốt

Các factor dự kiến gồm: nguồn đơn/backup hợp lệ/backup không xác minh; scope
đầy đủ/thiếu; semantic context giữ/mất; output gốc đúng/sai/trống; control
field fault/known-good. Giữ matched information, operator, mask area và budget
giữa các phương pháp. Báo no-alarm cases, failed proposals và unknown cùng
mẫu số, không refill chỉ để đạt nhiều ca favorable.

Fictional identity, content, image và lineage mới phải được đối chiếu exposure
index hiện có. Các mẫu đã xem được dùng development, không gọi unseen.
Phân tầng theo contract, ID và reader. Sizing theo ID/fault family; số view,
field, reader hoặc seed không được thay số cụm độc lập. Cỡ mẫu, effects,
margins và inference budget còn **PENDING**, không tự lấy số tròn từ pilot.

## Kế hoạch phân tích phải khóa trước panel mới

- Pointwise/relation có eligibility và reference tương ứng, confusion counts,
  valid/inconclusive/invalid rates, decision coverage và all-alarm accounting.
- So A/flat bằng cùng annotation; so B3/gated V3 với cùng endpoint, không
  diễn giải pre-existing error là transformation regression.
- Primary contrast, sensitivity policies, zero-denominator rule, cluster CI
  guards, multiplicity và cost measurement được chốt trước output. Báo effect
  estimates mô tả khi thiếu adequacy; không suy equality từ CI/p-value thiếu.
- Natural behavior, authored controls, mutants và software faults có patch/
  revert provenance là các panel riêng. Không chuyển 7 operational field
  errors của pilot thành 7 historical root causes.

## Trình tự triển khai

| Bước | Công việc / đầu ra | Trạng thái |
|---|---|---|
| P0 | Nhập, replay, hậu kiểm 46 ca và quyết định claim | DONE ngày 15/11; [receipt](execution/master_01/ifv_20261115/analysis.json) |
| P1 | Chốt schema reference, typed-normalization policy và các điều kiện trên bằng control fixtures | VALIDATED DEVELOPMENT PROTOTYPE ngày 16/11: schema/binding, typed policy v1, source/approval guards và 252 controls đã chạy; policy áp dụng bộ mới và approval reference external còn pending |
| P2 | Kiểm nguồn lực reference, quyền dùng, exposure, sizing và budget | PENDING đầu vào xác minh được |
| P3 | Quyết định GO mới cho claim/phạm vi cụ thể | NO-GO hiện tại cho superiority |
| P4 | Sau GO mới, tạo manifest và lock theo prep 6A | NOT STARTED |
| P5 | Chỉ sau lock hợp lệ, thực thi 7B và hoàn thiện paper | NOT STARTED |

Song song có thể hoàn thiện manuscript, gói tái lập tổng hợp và profiling
ứng dụng. Chưa cần training lại reader đóng băng: việc đổi subject không giải
quyết reference hay thiết kế endpoint. [Tiến độ](EASE2027_ROADMAP_VI.md)
