# Phiếu trình chủ dự án · D10 C2-45 · 23/11/2026

**Đề xuất giữ cả hai workspace tại máy organizer.** 45 ca trên 24 giấy tờ, 0 submission C2, 0 reference được duyệt. Bản có đủ 45 ca chứa ảnh nguyên khung của 6 hộ chiếu Hy Lạp. Trang nguồn được bảng MIDV chỉ đích danh đã bị xóa vì thiếu bằng chứng cho phép. Điều này ảnh hưởng cả khi giao riêng một bản sao. Chủ dự án có thẩm quyền quyết định D10 trong dự án. Quyền còn thiếu từ bên thứ ba cần căn cứ độc lập.

## Đánh giá chứng cứ pháp lý

| Phạm vi đề xuất | Mức | Cơ sở và điều kiện để chuyển bước |
|---|---|---|
| Chuẩn bị nội bộ, receipt và số đếm an toàn | READY_FOR_OWNER_APPROVAL | Có đủ căn cứ tiếp tục trong phạm vi chuẩn bị và công bố tổng hợp vốn được phép. Loại nhận diện, ảnh, ghi chú, raw hoặc ô nhỏ có thể suy người. |
| Giao nguyên hai workspace hiện tại | BLOCKED_RIGHTS | Cần tài liệu xác nhận quyền cho mẫu Hy Lạp áp dụng tới bản ảnh và biến đổi thực dùng, hoặc căn cứ pháp lý cụ thể được thẩm định. Điền thêm credit đơn thuần chưa khắc phục được. |
| Giao phiên bản thu hẹp 37 ca / 18 giấy tờ | CONDITIONAL_REVIEW | Chủ dự án chọn có đổi phạm vi hay không. Trước khi trình ký, lập run mới loại cả asset dư của Hy Lạp, rà quyền chân dung và điều khoản lúc nhận, hoàn tất notice, kiểm lại binding ảnh–form, số ca và hash. |
| Thu và lưu phản hồi mới | CONDITIONAL_REVIEW | Chờ thông báo tham gia, phương thức đồng ý nếu cần, quyền truy cập, thời hạn và rút lại. R02/R03 tự quyết định tham gia. |
| Ảnh công khai hoặc supplement nguyên gói | BLOCKED_RIGHTS | Vướng mẫu Hy Lạp, phạm vi quyền chân dung, lựa chọn hình và điều kiện nhà xuất bản. Nếu chỉ chọn một số hình, lập danh sách, duyệt quyền và phiên bản phát hành riêng. |

## Quyết định vận hành để trống cho chủ dự án

Sao chép phần này vào **record mới trong local/**, đính kèm chứng cứ và hash. Đề xuất về vai trò bên dưới chỉ có hiệu lực sau khi người có thẩm quyền xác nhận. Đối chiếu đủ năm version_digest ở [ma trận](D10_RIGHTS_RISK_MATRIX.json). Manifest quyền lịch sử có SHA-256 `1317a5b4957b9908562dad198e01e38617f808625b7eb0535278ff462398c44b`.

| Trường chủ dự án quyết định | Nội dung cần ghi trong bản ký |
|---|---|
| Phạm vi và quyết định gửi riêng | [duyệt / hoãn / từ chối], R02 và R03 mỗi người một bản, số ca/ID, mục đích đánh giá độc lập cho C2. Nếu phiên bản thay đổi, ghi lại cả năm digest. |
| Căn cứ và credit | [record/hashes cho nền, chân dung, acquisition, notice đi kèm, lý do đủ căn cứ]. |
| Hệ thống và quyền xem | [người được chỉ định]. Đề xuất assessor chỉ thấy gói và phiếu của mình, organizer quản lý giao nhận, người phân xử và chủ dự án xem phiếu cần thiết theo giai đoạn; xác định ai được xem liên kết danh tính. |
| Thu và lưu phiếu | [quyết định riêng], [căn cứ tham gia], [nơi lưu], [đầu mối], [thời hạn hoặc ngày xóa], [backup và thủ tục rút lại/xóa], [xử lý dữ liệu đã tổng hợp]. |
| Công bố | [số đếm đã khử định danh được phép]. [Quyết định riêng về ảnh, dữ liệu gốc, trích lời và supplement]. |
| Hiệu lực và xác thực | [ngày giờ/múi giờ], [authority của chủ dự án], [chữ ký thực và hash record], [ngày rà lại]. |

Sau quyết định hợp lệ, organizer liên kết hash record mới với từng candidate được duyệt và lưu receipt trong run mới. Thẩm quyền, chữ ký closure Round 1, hai proposal độc lập, phân xử và reference vẫn theo quy trình riêng. [Hướng dẫn ký và phân xử](C2_45_ADJUDICATION_READINESS_VI.md)

## README giao nhận · bản nháp cho từng người

Bạn được mời đánh giá độc lập các ca trong workspace mang mã của mình. Trước khi nhận, đọc phạm vi tham gia, quyền truy cập phiếu, thời hạn lưu và hướng dẫn rút lại trong thông báo đã được chủ dự án điền. Bạn có thể từ chối qua kênh riêng của organizer. Khi đó organizer dừng cấp quyền hoặc thu phiếu, ghi tối thiểu trạng thái từ chối, xử lý bản đã nhận theo thông báo, để ca ở trạng thái chờ. Việc thay người cần chủ dự án chỉ định và ghi exposure mới.

1. Organizer kiểm đúng phiên bản và người nhận qua kênh xác thực. Gửi kèm README, file license/URI, [bộ ghi công và mô tả crop/mask](MIDV2020_ATTRIBUTION_AND_DERIVATIVES_VI.md) dưới dạng tài liệu đọc được ngoại tuyến. Đặt các tài liệu kèm bên ngoài thư mục workspace đã đóng băng. Tạo manifest mới bao gồm tài liệu kèm, băm gói vận chuyển và chuyển digest qua kênh xác thực.
2. Kiểm SHA-256 gói nhận bằng `Get-FileHash -Algorithm SHA256 <duong-dan-goi>` và đối chiếu digest organizer gửi. Nếu lệch, dừng mở và báo riêng. Organizer đối chiếu manifest đã kiểm và ghi nhận người nhận theo mã, phiên bản, thời điểm, hash; digest manifest workspace khác digest ZIP.
3. Mở index.html ngoại tuyến trong gói của bạn. Đánh giá theo ca, khai exposure, xuất JSON. Giữ phiếu, lý do và nhận xét riêng; chỉ nộp theo kênh nghiên cứu đã chỉ định, không đưa lên GitHub hoặc chuyển cho assessor kia. Quyền dùng ảnh theo CC và các notice đi kèm được bảo toàn. Quyền vào hệ thống, xem dữ liệu người khác hay công bố hồ sơ nội bộ cần thẩm quyền riêng.
4. Khi nhận phiếu, organizer băm byte gốc, xác nhận hash qua kênh riêng, kiểm mã assessor và binding ca/ảnh bằng validator, lưu nguyên bản và receipt theo quyền lưu đã duyệt. Phiếu hợp lệ về cấu trúc vẫn cần xác thực theo registry. Nếu thiếu quyết định lưu thì dừng trước khi yêu cầu nộp.

## Thư nháp để chủ dự án xét gửi

**Subject — Historical MIDV-2020 distribution and third-party image rights for two research assessors**

Dear MIDV-2020 team,

Our project uses selected members from the Smart Engines MIDV-2020 photo and template archives. We are assessing whether two independent research assessors may receive offline copies of 24 full mock-document photographs, with cropped or masked derivatives, under the accompanying CC BY-SA 2.5 notice. Image publication would be a separate decision.

Could you confirm the notice applicable to this FTP release and any historical access conditions for downstream recipients? Could you point us to the permission or other basis for reusing the Greek passport specimen in MIDV-500 row 25, including its photographic source, and the terms covering embedded Generated Photos portraits and redistribution of derived document images? The cited Greek source file has a Commons deletion entry dated 9 February 2026. A dated rights reference or the appropriate rights contact would help us decide whether to exclude that template.

Thank you,
[Project owner / institution / contact]

Ưu tiên gửi cho đầu mối Smart Engines trong readme sau khi chủ dự án duyệt. Nếu cần điều khoản riêng sFTP, hỏi đầu mối trên trang L3i về phiên bản form và đối tượng áp dụng. Chỉ chuyển tiếp câu hỏi đến chủ thể quyền liên quan khi bên cung cấp chưa giải đáp được; dùng mã mẫu công khai, không đính kèm ảnh, phiếu hay danh tính.
