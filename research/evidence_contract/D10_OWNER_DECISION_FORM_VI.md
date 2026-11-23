# Phiếu quyết định D10 của chủ dự án

**Trạng thái phiếu: PENDING.** Hai workspace R02/R03 hiện tại gồm 45 ca trên 24 giấy tờ. Đánh giá quyền của nguyên gói là **BLOCKED_RIGHTS**. Chọn một phương án ở mỗi nhóm. Bạn có thể trả lời ngay trong chat bằng mã lựa chọn. Mọi ô bên dưới đang để trống.

## 1. Quyền chia sẻ riêng cho R02/R03

- [ ] **1A** Chưa duyệt, cần kiểm tra quyền.
- [ ] **1B** Đồng ý về nguyên tắc nếu quyền hợp lệ.
- [ ] **1C** Không cho phép chia sẻ.

**Khuyến nghị 1A.** Trong cả hai gói, 8 ca trên 6 giấy tờ dùng mẫu Hy Lạp có bản nguồn bị Commons xóa vì thiếu chứng cứ cho phép. Cần xác minh quyền đối với mẫu và phạm vi sử dụng chân dung. Chọn 1B chỉ ghi ý định có điều kiện. Muốn xét 37 ca còn lại phải lập và kiểm phiên bản mới. [Bằng chứng theo mẫu](MIDV2020_ATTRIBUTION_AND_DERIVATIVES_VI.md)

## 2. Nơi lưu phiếu đánh giá

- [ ] **2A** Máy organizer, thư mục private.
- [ ] **2B** Kho lưu trữ dự án có giới hạn truy cập.

**Khuyến nghị 2A** vì organizer đang vận hành workspace ngoại tuyến và giữ riêng hai luồng phản hồi. Dùng tài khoản được phân quyền, bảo vệ bản sao lưu và tắt đồng bộ sang kho công khai. Với 2B, ghi tên kho nội bộ, người quản lý và vai trò được phép đọc. Đây là quyết định bảo vệ phản hồi của dự án. Giấy phép ảnh không cấp quyền truy cập phiếu.

## 3. Thời hạn lưu

- [ ] **3A** 6 tháng.
- [ ] **3B** 12 tháng.
- [ ] **3C** Ngày kết thúc do chủ dự án phê duyệt riêng.

**Khuyến nghị 3A** nếu sáu tháng đủ để phân xử và kiểm tra kết quả. Đây là thời hạn quản lý đề xuất, do chủ dự án cân nhắc theo lịch nghiên cứu và quy định áp dụng. Với 3A/3B, đề xuất tính từ ngày nhận từng phiếu. Với 3C, điền ngày cụ thể. Thông báo mốc xóa, cách xử lý backup và yêu cầu rút lại cho người tham gia trước khi thu phiếu.

## 4. Quyền phát hành ảnh/crop

- [ ] **4A** Không công khai, giữ private.
- [ ] **4B** Chỉ xem xét bằng quyết định phát hành riêng sau này.

**Khuyến nghị 4A** cho hai phiên bản hiện tại. Cả 4A và 4B đều giữ ảnh ngoài kho công khai trong đợt này. Lựa chọn điều chỉnh việc phát hành của dự án. Khi người nhận được giao tác phẩm CC hợp lệ, phải bảo toàn quyền của họ theo CC BY-SA 2.5, kèm ghi công, liên kết license và mô tả crop/mask. [Điều khoản §4 và §8](https://creativecommons.org/licenses/by-sa/2.5/legalcode)

**Xác nhận của chủ dự án** · Chỉ đánh dấu điều đã kiểm tra. Có thể ghi “chưa” và nêu phần còn thiếu.

- [ ] **X1** Tôi đã kiểm tra giấy phép MIDV-2020 và quyền của các thành phần liên quan. Căn cứ đã xem hoặc phần còn thiếu: __________.
- [ ] **X2** Tôi đã xác định người nhận R02/R03, phạm vi truy cập, cách lưu và bảo vệ phản hồi. Vai trò được xem phiếu, vị trí lưu, bảo vệ bản sao và xử lý rút lại: __________.

**Mẫu trả lời trong chat** (không cần sửa JSON)

> Lựa chọn: 1__, 2__, 3__, 4__.
> X1: [đã/chưa] — [căn cứ hoặc điểm còn thiếu].
> X2: [đã/chưa] — [phạm vi và cách bảo vệ].
> Tính thời hạn từ / ngày kết thúc: ____. Người có thẩm quyền và ngày hiệu lực: ____.

Có thể gửi chứng cứ hoặc thông tin nhận diện qua hồ sơ riêng, trong chat chỉ dẫn mã hồ sơ. Khi nhận được xác nhận, organizer lập **record mới** trong local/ ghi nguyên các lựa chọn, người quyết định, thời điểm, phạm vi và hash bằng chứng. Gắn cả năm version_digest theo [ma trận kiểm toán](D10_RIGHTS_RISK_MATRIX.json) và kiểm lại với manifest gốc SHA-256 `1317a5b4957b9908562dad198e01e38617f808625b7eb0535278ff462398c44b`. Nếu thay gói, dùng manifest và digest của phiên bản mới. Quyết định hoãn/từ chối cũng được ghi nhận. Chỉ lập receipt cập nhật quyền chia sẻ sau khi kiểm đúng thẩm quyền, bằng chứng quyền, quyết định cho phép có hiệu lực và đúng phạm vi. Bản ghi đồng ý về nguyên tắc hoặc hai ô xác nhận tự chúng chưa mở cổng.

[Phiếu trình, thư nháp, README và quy trình giao nhận](D10_OWNER_APPROVAL_PACKET_VI.md) · [Receipt của kiểm toán](D10_AUDIT_VERIFICATION.json)
