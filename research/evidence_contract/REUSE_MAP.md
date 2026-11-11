# Bản đồ tái sử dụng cho Evidence-Contract Testing

Ngày đánh giá 05/11/2026. Các adapter và thành phần mới trong bảng là thiết kế dự kiến cho công việc sau TASK 0. Lượt này chưa tạo module, operator, runner hoặc API framework.

## Các thành phần và cách dùng

| Component hiện có | Phân loại | Cách dùng dự kiến | Ràng buộc phải giữ |
|---|---|---|---|
| `research/v3_sources.py::source_graph`, `body_sources` | Cần adapter | Chuyển nguồn body, body duplicate và TD3 sang các realization có key, provenance, components và phạm vi độ chính xác | Giữ OR giữa realization, AND giữa component. Đây là logic đã có; mỗi kiểu nguồn cần trạng thái coverage rõ ràng |
| `v3_sources.py::parse_td3`, `check_digit`, `span_quad` | Tái sử dụng có chọn lọc | Parse chuỗi TD3 đã được nhận dạng hoặc annotation specimen và chiếu span về tọa độ ảnh | Parser giữ cờ checksum sai. Adapter không được coi mọi span được parse là checksum hợp lệ, hoặc coi checksum là xác thực giấy tờ |
| `v3_sources.py::visible_realizations` | Cần adapter | Đối chứng oracle hình học lịch sử, cùng chức năng chiếu/mask khi phù hợp | Ngưỡng giao 0,05 pixel và tiêu chí whole-region là chính sách cũ. Trường hợp không đủ bằng chứng cần trạng thái unknown, không sửa ngưỡng của kết quả cũ |
| `research/hp_data.py::nodes_for`, `regions_for`, `refs_for` | Cần adapter | Tạo mô tả mask all-declared-sources và quan hệ với nguồn còn lại | `nodes_for` có thể yêu cầu cả label_box cho ảnh authored. Tách điều kiện đọc giá trị và điều kiện xác định ngữ nghĩa của key trong đặc tả |
| `hp_data.py::pair_for`, `masked_capture` | Cần adapter | Thử cặp hide A / keep B trên fixture hoặc dữ liệu phát triển có provenance | Giữ khoảng cách 8%, toàn bộ nguồn khai báo và tác động vùng lân cận như một cấu hình legacy. Validator mới phải kiểm độc lập precondition và collateral damage |
| `hp_data.py::build`, `write_capture`, `new_authored` | Không gọi trực tiếp | Tham khảo cách lưu ảnh và metadata | Các hàm ghi vào dataset HP đã đóng băng. Nếu có generator mới phải ghi namespace mới, có seed/ID/split riêng và được giao ở task sau |
| `research/hp_metrics.py::scoring`, `summary` | Cần adapter | Đối chứng hai lỗi đối nghịch, pair success và neighbor omission/wrong | `declared_hidden_outputs` là lỗi tương đối với nguồn khai báo. Giữ mẫu số, pair eligibility và denominator riêng; thiếu trường hợp lệ không được tính thành thành công abstention |
| `research/v3_metrics.py::canonical`, `date_value`, `reference_precision`, `scoring` | Tái sử dụng cho đối chứng legacy, adapter cho contract mới | So giá trị ngữ nghĩa và độ chính xác ngày, giữ raw prediction trước bước chuẩn hóa | YYMMDD không cung cấp thế kỷ. Báo riêng parser failure, value error, absence và precision overreach; giữ scorer cũ theo hash |
| `research/labels_schema.py` | Tái sử dụng kiểm tra hình học, adapter schema | Dùng polygon validity, script và vocabulary readability hiện có trong dữ liệu chuẩn hóa | `unassessed`, `partial`, `language_unknown`, `uncertain` cần được giữ. Clean/Blur và in-frame không thay được legibility. Không ép `field01` thành một key CCCD |
| `research/labels_review.py` | Cần adapter đọc-only | Đọc snapshot các đánh giá đơn, provenance và đối chiếu nhiều người | Giữ event history, ánh xạ nhiều code cùng person, điều kiện operator-confirmed và self-declaration. Không gọi `store` hoặc xuất lại đè snapshot cũ từ audit |
| `research/labels_issues.py` | Tái sử dụng luồng đề nghị kiểm tra, adapter snapshot | Gắn issue với phiên bản case khi đánh giá test validity | Flag/withdraw không xóa ảnh, không thành nhãn readability hoặc lý do giảm mẫu số test đã công bố |
| `research/labels_metrics.py::effects`, `slices` | Cần adapter | Tham khảo ghép bốn điều kiện cùng ID và cách tách lát dữ liệu | `effects` giả định factorial authored 2×2 hoàn chỉnh. Không áp nó nguyên trạng cho tập test contract không có bốn cell |
| `research/fc_statistics.py::holm` | Tái sử dụng | Hiệu chỉnh một family so sánh đã đăng ký trước trong nghiên cứu mới | Family và alpha phải được định trước cho nghiên cứu mới |
| `fc_statistics.py::analyze` | Cần adapter | Tái sử dụng ý tưởng paired ID clusters, source stratification và pixel-component sensitivity | Hàm hiện cố định tám arm và bốn primary contrasts. Không thay SEEDS, metric hoặc số primary test trong file cũ để phục vụ EASE |
| `research/labels_common.py`, `hp_common.py`, `fc_common.py`, artifact indices | Tham khảo và adapter read-only | Kiểm soát path, hash, contract version, atomic outputs và cache provenance | Một số `preserve` có thể tạo manifest khi chưa tồn tại. Audit mới chỉ kiểm file đang có và ghi kết quả kiểm tra vào vùng mới |
| Raw OCR outputs, `dataset_card`, `test_lock`, `analysis_plan`, `report_provenance` cũ | Cần adapter dữ liệu | Phân tích hồi cứu và xác định khả năng chạy phép chấm nào từ cache | Không có raw output cho một ảnh biến đổi mới thì không được suy ra prediction của ảnh đó. Rescoring và cache reuse phải có bộ đếm riêng |
| `research/v2_inputs.py::Views.prepare`, `pixels` | Cần adapter SUT | Một biến thể xử lý ảnh của hệ thống được kiểm thử, có cấu hình/hash cố định | Không đưa box/expected keys/GT vào đường predictor. Các profile và checkpoint cũ được giữ như các đối chứng có phiên bản |
| `research/v2_runtime.py`, `labels_study.py`, OCR CPU wrappers | Cần adapter SUT cho task sau | Các backend đóng băng có thể được gọi với pixel-only khi có kế hoạch inference mới | Không import rồi gọi runner, training, setup/download hoặc thay model selection. Phải có log execution nếu thực sự gọi model |
| `research/tests/test_v3_sources.py`, `test_hp_masks.py`, `test_hp_metrics.py`, `test_labels_*`, `test_fc_statistics.py` | Tái sử dụng làm regression fixtures | Kiểm logic hiện tại và bảo vệ tương thích cho adapter sau này | Những fixture này xác nhận hành vi đã thiết kế. Chúng không thay tham chiếu độc lập để đánh giá chất lượng oracle mới |
| `ekyc/api.py`, `pipeline.py`, `module1..5`, session/challenge/biometric state, UI mentor | Ngoài phạm vi sửa | eKYC cung cấp bối cảnh case study và yêu cầu phần mềm | Chỉ bổ sung adapter phục vụ nghiên cứu sau khi có lý do và task cụ thể. Không thêm database hồ sơ hoặc sử dụng kết quả OCR để tự duyệt danh tính |

## Thành phần cần viết mới ở các task sau

| Thành phần dự kiến | Trách nhiệm | Tiêu chí ranh giới |
|---|---|---|
| Evidence-contract schema có version | Tách schema/key semantics, source graph, coverage, trạng thái hỗ trợ, precision và provenance | Thiếu nguồn đã biết và chưa biết nguồn phải phân biệt được. Có thể biểu diễn unknown hoặc inapplicable |
| Transformation contract | Khai báo precondition, vùng tác động, nguồn cần ẩn/giữ và expected relation | Phân biệt biến đổi invalid với model vi phạm hợp đồng. Không dùng nhãn tự tạo bởi chính SUT làm đáp án |
| Independent validity checker | Kiểm source linking, mask coverage, thành phần nhiều dòng, raster/coordinate consistency | Không chỉ gọi lại cùng hàm sinh target rồi kết luận target đúng |
| SUT/result adapter | Giao diện pixel-only, schema normalization có phiên bản, raw output digest, error taxonomy | Parser làm mất key hoặc sửa chuỗi phải được truy vết trước/sau chuẩn hóa |
| Case registry và experiment lock mới | Tách historical/exploratory/development/future-confirmation; ghi ID, hash và exposure | Không sửa role cũ để tạo cảm giác test chưa mở. Không tái sử dụng feature khi hash xử lý ảnh khác |
| Contract runner và failure report | Kết luận pass/fail/unknown/inapplicable, loại lỗi, nguyên nhân precondition và bằng chứng | Mỗi kết luận có case ID, SUT/config/model hash và log thật. Chưa triển khai trong TASK 0 |
| Bộ đối chứng test adequacy | So với kiểm schema/format, masking một vùng, masking nguồn-agnostic và lựa chọn ngẫu nhiên cùng ngân sách | Đánh giá fault detection, false alarm, validity và cost cùng nhau. Giữ cả kết quả âm |
| Oracle assessment subset | Thiết lập tham chiếu độc lập bằng construction-exact cases, lỗi phần mềm có nguồn gốc và review subset phù hợp nguồn lực | Tách one-person pilot, nhãn hai người, seeded faults và lỗi thực. Không dùng chính mutant/operator làm bằng chứng duy nhất cho chất lượng detector |

## Phụ thuộc và điểm chặn tái sử dụng

Các metric hình học hiện nay có đường import kéo theo `v2_runtime` và torch dù chỉ chạy CPU. Môi trường hiện tại đã chạy được 60 test fixture, nhưng adapter EASE cần kiểm soát side effect và dependency trước khi đưa core contract vào CI. Không thay cấu trúc import của các file đã đóng băng trong TASK 0.

Một lỗi cụ thể đã được ghi trong `HARD_PAIR_COVERAGE_NOTE.md` là MRZ annotation 43/44 ký tự không được parser TD3 nhận. Case này cung cấp ví dụ về coverage gap, không đủ tự thiết lập chân lý rằng mọi output ngoài contract là hallucination. Các lỗi sửa nhãn nhiều dòng/song ngữ ở pilot R2 và alias bố cục ở V4 là đầu mối để kiểm kê lỗi lịch sử ở mốc tiếp theo.

Đọc `IMPLEMENTATION_PLAN.md` để xem gate và thứ tự. Đọc `PROJECT_INVENTORY.md` cùng manifest để phân biệt thành phần tìm thấy với thành phần đã kiểm thử trong lượt này.
