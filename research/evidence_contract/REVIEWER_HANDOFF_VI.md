# Gửi cho người đánh giá độc lập

**Ngày 20/11, R02 và R03 đã nộp đủ hai pha.** Phần thu phiếu của hai người chấm đã hoàn tất. Chủ dự án đang chờ chốt vòng và phân xử.

**Mốc 17/11 · [R02 đã hoàn tất cả hai pha](R02_PHASE2_REVIEW_INTAKE_20261117.md)**,
86/86 pha 1 và 46/46 pha 2. Không cần gửi lại gói hoặc yêu cầu R02 làm lại.
Đã tính agreement trước phân xử tác giả/R02 theo canonical join organizer;
không gộp nhãn hoặc thay đáp án. R03 tiếp tục gói pha 1 riêng; chỉ cấp pha 2
sau khi khóa pha 1 của R03. Round 1 OPEN; chưa áp dụng cutoff hay authority.
Không gửi báo cáo kết quả, bảng bất đồng hoặc đáp án tác giả/R02 kèm ZIP chấm.
Hai người hoàn tất pha 2 hiện gồm 1 tác giả + 1 external theo organizer;
chưa xác minh tính độc lập bằng chỉ riêng JSON. Bằng chứng và gói cũ giữ nguyên.

Cập nhật organizer **17/11**: giữ nguyên các ZIP đã phát. Lớp
[strict intake mới](reviewer_tools/README.md) kiểm hash gói được cấp, thứ tự pha,
schema và duplicate, giữ raw bytes; không bắt người chấm đổi giao diện hay cài
thêm gì. Workflow reference/adjudication chỉ được kiểm bằng synthetic, không
đóng Round 1 hoặc tạo gold. R02 pha 2 đã nhận; tiếp tục nhận R03 theo hướng dẫn dưới;
không gửi tài liệu tiến độ B hoặc bảng bất đồng kèm gói chấm độc lập.

Cập nhật 16/11/2026. Không cần gửi toàn bộ project hoặc cài Python/model.
Gói điền phiếu cần **ảnh + giao diện + manifest**, không chỉ một JSON trống.
Người chấm điền trên trình duyệt, rồi gửi lại JSON đã xuất.

**Đã nhận R02 pha 1: 86/86 mục**, vai trò ngoài dự án do organizer đính chính
riêng; phiếu gốc giữ nguyên. [Kết quả và giới hạn](R02_REVIEW_INTAKE_20261116.md).
Gói **`local/reviewer_exports/r02_20261116/reviewer_R02_phase2.zip`** đã được R02
hoàn thành: 46 ca (42 primary + 4 diagnostic), 30 file ảnh, khoảng 0,67 MB.
Giữ nguyên gói/manifest để đối chiếu; không cần gửi lại pha 1 hay toàn project.
R03 vẫn dùng ZIP pha 1 v2 phía dưới. Không chuyển gói pha 2 của R02 cho R03.

Kế hoạch nội bộ organizer sau mốc B: **Round 1 vẫn OPEN**, đề xuất snapshot
author + R02 + R03 khi hoàn tất, hoặc khi organizer ghi rõ một cutoff phân tích
có ngày và thành phần thực nhận. Chưa áp dụng cutoff/đóng tuyển trong lượt này.
Người đến muộn vào Round 2/amendment, giữ raw, phiên bản và exposure. Đọc phần
[reviewer rounds](B_PROSPECTIVE_PROTOCOL_DRAFT.md) để nối tiếp. ZIP đã phát giữ
nguyên; không gửi kèm báo cáo B, đáp án tác giả hoặc bảng bất đồng cho người
đang chấm độc lập. Mốc kỹ thuật không tạo thêm phiếu đánh giá.

## Bao nhiêu người là phù hợp?

Không có số người chấm nào tự bảo đảm kết quả đúng. Pilot pha 1 và pha 2 hiện
có tác giả + R02 hoàn tất; R03 chưa nộp, vẫn chưa là gold độc lập.
Thêm người giúp đo bất đồng; vẫn phải kiểm hướng dẫn, lỗi annotation, nguồn
tham chiếu và phân xử. Agreement cao cũng không tự chứng minh annotation đúng.
[Phân tích chất lượng annotation](https://aclanthology.org/2024.cl-3.1/)

Đề xuất riêng cho dự án này, không phải một định mức bắt buộc của hội nghị:

| Mức | Nhân lực | Giá trị / giới hạn |
|---|---|---|
| Tối thiểu để bắt đầu đối chiếu | Thêm 1 người ngoài dự án: tác giả + 1 external = 2 | Có thể so agreement/bất đồng; vẫn có một bên tham gia xây dựng hệ thống |
| Khuyến nghị cho vòng tiếp | Thêm 2 người ngoài dự án: tác giả + R02 + R03 = 3 | Có hai đánh giá độc lập với tác giả và có thể so riêng R02/R03 trước phân xử |
| Ca còn bất đồng | Trao đổi có biên bản sau khi khóa đánh giá độc lập, hoặc nhờ thêm một người phân xử phù hợp | Không tự lấy đa số làm truth; giữ raw labels và lý do quyết định |

Thu agreement **trước phân xử**, trên cùng ảnh/ô/cặp. Báo exact agreement,
Cohen kappa khi hai người và nominal Krippendorff alpha khi thích hợp; giữ
NA khi không có biến thiên hoặc thiếu dữ liệu. Với transcript, báo exact match
riêng, giữ O/0 khác nhau. Công cụ `task55.agreement` hiện hỗ trợ **pha 1**,
đã có agreement tác giả/R02; xem báo cáo intake ở trên. Chưa có agreement giữa
hai người ngoài vì R03 chưa nộp.
Pha 2 hiện có `reviewer_tools.phase2_comparison` và báo cáo R02 ngày 17/11;
kappa/exact agreement được báo riêng cho câu trả lời và nhãn guard suy ra.
Đối chiếu pha 2 cần nối các mã ca riêng từng reviewer về cùng frozen sample
trên máy organizer; không ghép trực tiếp bằng case ID hoặc gộp thành gold.
[Tài liệu alpha của tác giả](https://www.asc.upenn.edu/krippendorffs-alpha-reliability) ·
[Quy trình xử lý bất đồng](https://aclanthology.org/2021.humeval-1.15/)

Nhiều người không thay được nhiều ID/layout/điều kiện chụp. Primary hiện chỉ
có ba ID; chưa thể dùng thêm người chấm để biến các view/field thành mẫu độc
lập hoặc tự mở confirmatory.

## Hai gói pha 1 đã phát trước khi nhận R02

Hai ZIP được chuẩn bị riêng, khoảng 0,7 MB mỗi gói:

**Cả hai đều là pha 1 với cùng 31 ảnh/86 mục, dành cho hai người R02/R03.**
Chúng không lần lượt là pha 1 và pha 2. Pha 2 có 46 ca đối chiếu output, không
phải 46 ảnh khác nhau; chỉ tạo sau khi khóa pha 1 của chính người đó.

- `local/reviewer_exports/v2/reviewer_R02_phase1.zip`: gửi riêng cho người thứ nhất.
- `local/reviewer_exports/v2/reviewer_R03_phase1.zip`: gửi riêng cho người thứ hai.

Mỗi ZIP gồm `index.html`, hai file JavaScript, `images/` chứa 31 PNG giả lập,
`packet_manifest.json`, `REVIEW_JOB.json`, `MANIFEST.json`, `README_VI.txt`.
Phiếu có 86 mục, mã người chấm gợi ý sẵn; mức đã xem output vẫn cần tự khai.
Không có phiếu tác giả, đáp án tác giả, predictions, model weights hoặc analyst
join. Các trường availability xét trên toàn ảnh, gồm nguồn thay thế hỗ trợ đúng
semantic key; hướng dẫn này không cung cấp giá trị cần chép.

Người chấm giải nén nguyên folder, mở `index.html` bằng Chrome/Edge, đọc hướng
dẫn và chọn đúng role/exposure. Nếu đã xem báo cáo/chat/repo, khai đúng mức
exposure; một pseudonym mới không tự tạo tính độc lập. Có thể lưu/xuất nháp
qua nhiều buổi. Khi đủ mục, xuất phiếu hoàn chỉnh và gửi lại **file JSON**.
Không cần gửi lại project hoặc cả folder. Giữ ZIP để đối chiếu hash khi cần.

Không gửi kèm kết quả pilot, lựa chọn của tác giả hoặc bảng A/B3 trước pha 1.
Nếu muốn nhận góp ý về phương pháp từ cùng người đó, thực hiện sau pha 1 hoặc
khai đúng exposure. Không trao đổi đáp án giữa R02/R03 trước khi khóa riêng.

## Quy trình cấp pha 2 sau khi khóa pha 1

Sau khi nhận JSON pha 1 của R02/R03, organizer import bằng công cụ hiện có.
Khi đủ schema, snapshot của **chính người đó** được khóa rồi mới mở output:

```powershell
python -B -m research.evidence_contract.task55.review import --submission '<JSON pha 1 mới>'
python -B -m research.evidence_contract.task55.portable_review phase2 --snapshot '<SHA snapshot vừa import>'
```

ZIP pha 2 chứa 46 ca output đã ẩn reader/phương pháp, ảnh và quan sát pha 1
của chính người chấm. Đáp án tác giả bị loại khỏi portable view. Export giữ
canonical packet ID để importer đối chiếu bản niêm phong trên máy organizer.
Pha 2 yêu cầu ghi validity trước khi mở output; lựa chọn omission/empty được
kiểm logic, và chênh O/0 so với bản chép cần ghi chú nếu vẫn chọn đúng. Các kiểm
tra này không tự sửa lựa chọn hoặc cấp nhãn độc lập.

Sau pha 2, họ chỉ gửi lại JSON đã xuất. Organizer nhập đúng snapshot của người đó:

```powershell
python -B -m research.evidence_contract.task55.ifv import-stage2 --snapshot '<SHA pha 1 của người đó>' --submission '<JSON pha 2 mới>'
```

Để đo agreement pha 1 trước phân xử, dùng hai export thật của hai người:

```powershell
python -B -m research.evidence_contract.task55.agreement --submissions '<JSON pha 1 R02>' '<JSON pha 1 R03>'
```

Các JSON/notes thực tiếp tục nằm dưới
`local/`, không đăng lên repo public. GitHub giữ code, hướng dẫn, aggregate và
hash; các ZIP chấm ảnh được gửi riêng cho người đánh giá.

Nếu cần feedback về quy trình, gửi thêm mô tả ngắn mục tiêu kiểm độ tin cậy
của phép kiểm trích xuất trường trên ảnh giả lập và hỏi về hướng dẫn khó hiểu,
trường/nguồn khó xác định, thao tác lỗi và số phút thực làm. Nhận góp ý chi tiết
về phương pháp/kết quả sau khi khóa phần đánh giá độc lập. Ghi nhận góp ý riêng
với nhãn từng ca; không thay nhãn chỉ vì một ý kiến tổng quát.

## Thông điệp có thể gửi kèm ZIP

Mình nhờ bạn đánh giá độc lập bộ ảnh giấy tờ giả lập trong ZIP. Bạn chỉ cần
giải nén và mở index.html, không cần cài project. Hãy khai đúng mức đã xem kết
quả, chỉ chép chữ nhìn thấy trên ảnh hiện tại và giữ chưa chắc khi thiếu căn cứ.
Có thể làm nhiều buổi và sao lưu nháp. Khi hoàn tất, xuất JSON và gửi lại cho
mình; ghi thêm số phút thực làm nếu thuận tiện. Đừng xem phiếu người khác hoặc
trao đổi đáp án trước khi hoàn tất. Mình sẽ gửi bộ đối chiếu output pha 2 sau
khi phần quan sát này đã được khóa.

[Receipt ZIP v2](execution/master_01/development_20261116/reviewer_package_receipts_v2.json) ·
[Kết quả pilot cũ](IFV_RESULTS_VI.md)
