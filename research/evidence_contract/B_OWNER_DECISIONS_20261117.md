# Các quyết định cần chủ dự án — 17/11/2026

## Trạng thái hiện hành · 22/11/2026

D1, D2 và D3 đã được chủ dự án quyết định. Cutoff Round 1 có hiệu lực ngày 21/11. R02 và R03 là hai người đánh giá, AUTHOR là tác giả nội bộ. Người phân xử phải là một người khác cả ba. Chủ dự án phê duyệt reference sau phân xử và kiểm quyền D10. Trạng thái D4–D12 theo từng quyết định đã ghi. [Biên bản và snapshot](ROUND1_CLOSURE_20261122_VI.md)

## Bảng lịch sử tại ngày 17/11/2026

Cột “Hiện tại” trong bảng dưới ghi trạng thái tại ngày 17/11. Đối với D1–D3, quyết định có hiệu lực là mục hiện hành phía trên. D10 theo phiên bản của nhóm 45 ở [hồ sơ quyền](C2_45_D10_RIGHTS_VI.md).

Đây là các lựa chọn khoa học và phân quyền chưa được chốt, **không phải yêu cầu
bạn làm lại phiếu cá nhân**. Mã kiểm thử/audit đã hoàn tất mốc chuẩn bị; bảng này
giúp chốt một thiết kế cụ thể trước cohort mới. Không mục nào dưới đây được tự
coi là đã duyệt vì test pass, hết thời gian chờ, hoặc bạn nói “tiếp tục”.

| Mã | Quyết định | Phương án để xem xét | Đầu ra cần ghi nhận | Hiện tại |
|---|---|---|---|---|
| D1 | Cutoff Round 1 | Chờ author + R02 + R03 hoàn tất các pha cần phân tích; hoặc cutoff có ngày, nêu rõ thành viên/pha còn thiếu | Ngày, danh sách snapshot, mục đích phân tích; người đến sau sang round/amendment | OPEN, chưa cutoff |
| D2 | Authority duyệt reference | Chỉ định riêng người chấm, người phân xử và người phê duyệt; khai quan hệ với project | Mã riêng tư, vai trò, khóa public được xác thực, quyền và phiên bản protocol | Chưa chỉ định; production authority rỗng |
| D3 | Quy tắc phân xử | Giữ hai đánh giá ngoài độc lập; phân xử riêng có chứng cứ; còn mơ hồ thì UNRESOLVED | Quy trình được duyệt, người phân xử, evidence basis, cách sửa phiên bản | Có demo synthetic; chưa duyệt quy trình thật |
| D4 | Primary contrast | Checked v2 vs MRZ-metadata-asserted ablation hẹp; hoặc contrast rộng hơn nhưng tách rõ guard | Arm/guard matrix, tập can thiệp, implementation và parity checks trước lock | Đặc tả có, asserted arm chưa triển khai |
| D5 | Primary endpoint | Paired FAR trên nonfault có truth độc lập trong panel defect đã định trước; hoặc chọn estimand khác và sửa sizing | Định nghĩa endpoint/panel/chiều hiệu ứng, missingness và secondary endpoints | Đề xuất, chưa chốt |
| D6 | Minimum useful coverage | Chọn floor có ý nghĩa sử dụng, nêu all-case hay labeled; không chọn từ lát kết quả thuận lợi | Giá trị, mẫu số, lý do thực tiễn và cách đánh giá bất định | null |
| D7 | Minimum all-fault sensitivity | Chọn floor với mọi fault có truth, kể cả fault bị abstain | Giá trị, scope, lý do và cách xử lý CI/NA | null |
| D8 | Effect / superiority / noninferiority margin | Chọn ý nghĩa thay đổi FAR; nếu noninferiority phải có rationale và thiết kế riêng | Margin, precision target, alpha/family, power hoặc precision rationale | null; số minh họa chưa phải margin |
| D9 | Cluster/sample và ngân sách | Physical-ID stratified design với quota/cases; characterization hẹp nếu nguồn lực không đủ | N/cap, strata, seed, reader/model, unique call budget, phút công, thời hạn, stop rule | Có 384 sensitivity scenarios, chưa khóa |
| D10 | Quyền dùng/phát hành corpus | Duyệt từng artifact/version/attribution; chỉ phát aggregate khi chưa được phép phát ảnh | Rights record, consent/provenance cần thiết, anonymous-release decision | Provider license đã tìm; release approval chưa có |
| D11 | Quy tắc exposure | EXPOSED chỉ development; UNKNOWN không được gọi unseen; chọn scope prospective mới có khai exposure hoặc nguồn khác | Rule cho instance/template/content/pixel/capture; cách ghi metadata đã xem | 192 exposed, 808 unknown; không có certified-unexposed |
| D12 | Track và giới hạn claim | Research nếu có đóng góp/bằng chứng đủ; Emerging nếu preliminary phù hợp; RENE chỉ khi negative finding đủ cơ sở | Chủ đề/claim/track và các mốc khả thi, tác giả duyệt; scientific GO tách riêng | Chưa sẵn sàng nộp; NO_GO_SUPERIORITY |

Thứ tự thực tế: D1–D3 cho round/reference; D4–D8 cho estimand; D9–D11 cho
feasibility và quyền; D12 sau khi thấy kế hoạch có khả thi. Có thể trả lời theo
mã từng phần, không cần điền thêm một bộ 86/46 phiếu. Không gửi bảng này, kết quả
B, đáp án tác giả hoặc bảng bất đồng cho người đang chấm độc lập.

Với tình hình hiện tại, thêm **R03 là người ngoài thứ hai** giúp có cặp đánh giá
R02/R03 tách khỏi tác giả, nhưng vẫn cần R02 pha 2 và các pha tương ứng của R03.
Đó là đề xuất panel, không phải “đủ 3 người là khách quan”. Quy trình registry
development còn yêu cầu người phân xử và người duyệt tách khỏi các assessor;
chủ dự án có thể duyệt hoặc yêu cầu sửa quy trình trước production.

[Protocol để duyệt](B_PROSPECTIVE_PROTOCOL_DRAFT_v2_20261117.md) ·
[Sizing và giới hạn](B_SIZING_AND_POWER_DRAFT_20261117.md) ·
[Tiến độ/bằng chứng](B_CONTINUATION_REPORT_20261117.md)
