# D10 · Quyền đối với các bản artifact dùng cho C2-45

**Quyết định vận hành ngày 22/11/2026:** được chuẩn bị và kiểm tra hồ sơ trên máy organizer trong phạm vi chủ dự án giao. Hiện **0/45** candidate được phép chuyển cho assessors theo hồ sơ D10 của dự án. Chưa nhận bản duyệt theo phiên bản gắn đủ ảnh nguồn, dẫn xuất, crop và workspace cùng mục đích dùng. Người có thẩm quyền duyệt D10 của dự án là chủ dự án. Những quyền thuộc bên thứ ba cần có căn cứ từ bên nắm quyền.

| Artifact / phiên bản | Số thành phần duy nhất | Dùng nội bộ | Gửi riêng R02/R03 | Lưu bằng chứng đánh giá mới | Phát bảng đếm đã khử định danh | Phát ảnh hoặc supplement |
|---|---:|---|---|---|---|---|
| Annotation template MIDV-2020, archive SHA `75dd3432…ad` | 1 | Cho phép chuẩn bị | Chờ D10 | Chờ phạm vi lưu | Cho phép | Chờ D10 |
| Ảnh nguồn MIDV-2020, tập hash `9240d46a…` | 24 | Cho phép chuẩn bị | Chờ D10 | Chờ phạm vi lưu | Cho phép | Chờ D10 |
| Ảnh lịch sử sau crop/mask, tập hash `7cbe507c…` | 34 | Cho phép chuẩn bị | Chờ D10 | Chờ phạm vi lưu | Cho phép | Chờ D10 |
| Crop vùng body/MRZ, tập hash `7354db87…` | 140 hash byte | Cho phép chuẩn bị | Chờ D10 | Chờ phạm vi lưu | Cho phép | Chờ D10 |
| Hai workspace R02/R03, tập hash `2e921f1a…` | 2 | Cho phép chuẩn bị | Chờ D10 | Chờ phạm vi lưu | Cho phép | Chờ D10 |
| Phiếu, rationale, exposure và chữ ký của người đánh giá | 0 phiếu C2 hiện có | Được chuẩn bị schema trống | Người chấm cần phạm vi truy cập riêng | Chờ xác định người truy cập, mục đích, thời hạn lưu, xử lý rút lại và căn cứ đồng ý nếu cần | Chỉ số đếm thuộc phạm vi đã duyệt | Chờ duyệt riêng |

Tập hash là SHA-256 canonical của danh sách hash thành phần đã sắp xếp. Tệp riêng `artifact_rights.json` liệt kê đầy đủ các thành phần. Ma trận riêng nối từng candidate với các phiên bản bắt buộc. Hai workspace chứa cùng bằng chứng ảnh, mỗi người có phiếu riêng. Số hash crop duy nhất thấp hơn số vị trí crop vì các trường của cùng giấy tờ có thể dùng lại hai dòng MRZ. [Digest đầy đủ và số đếm](human_gate/receipts/human_20261122144027Z/aggregate.json)

**Căn cứ nguồn.** Đã đối chiếu byte với receipt thu nhận. Bản `license.txt` từ nhà cung cấp có SHA-256 `3b6bc8eb8a4a6bba41619051803991d9de949f7f722eee30bc0954c7b38aed7d`, bản `readme.txt` có SHA-256 `02b2b1b562a97c6cfec9cc2986dc55dd711ef20b92454150a072815373d07eb4`. License ghi CC BY-SA 2.5 Generic và khuyến khích ghi công Generated Photos cho chân dung. Tài liệu công bố của tác giả dẫn tới danh sách ghi công ảnh nền Wikimedia Commons theo loại giấy tờ. Trang L3i yêu cầu dẫn công trình MIDV-2020 và chấp nhận license khi xin tải. Việc đối chiếu trang công khai không chứng minh ai đã chấp nhận điều khoản cho bản cụ thể. [Receipt của dự án](../results/recovery_v4/dataset_source_documents.json) · [Bulatov và cộng sự, Computer Optics 46(2), 2022](https://doi.org/10.18287/2412-6179-CO-1006) · [Trang MIDV-2020 của L3i](https://l3i-share.univ-lr.fr/MIDV2020/midv2020.html)

CC BY-SA 2.5 cho phép chia sẻ và sửa đổi tác phẩm theo điều kiện của giấy phép. Khi xét phát hành, kiểm ghi công, liên kết license, mô tả phần đã sửa và điều kiện ShareAlike cho bản phái sinh. Cần kiểm cả phạm vi quyền liên quan đến ảnh nguồn và dữ liệu người đánh giá. Ghi công tác giả, nguồn chân dung và thao tác crop/mask đã có trong bản chuẩn bị. [Tóm tắt giấy phép Creative Commons](https://creativecommons.org/licenses/by-sa/2.5/)

**Cách đọc trạng thái.** `INTERNAL_USE_PERMITTED` giới hạn ở công việc nội bộ đã giao. `REVIEW_ACCESS_PENDING` chặn việc cấp gói cho assessor. `RETENTION_PENDING` chờ quyết định lưu phản hồi thật. `AGGREGATE_ONLY_PERMITTED` áp dụng cho số đếm, mã và receipt an toàn theo chính sách đồng bộ của dự án. `RELEASE_PENDING` giữ ảnh/crop ngoài GitHub. Chưa ghi nhận quyết định từ chối quyền.

**Đầu ra cần từ chủ dự án.** Lập rights record dẫn hash artifact/phiên bản và căn cứ nguồn, nêu người nhận R02/R03, phạm vi xem riêng, nơi và thời hạn lưu câu trả lời, cách ghi công, quyền phát hành từng loại, người duyệt và ngày hiệu lực. Gắn hash của record vào hồ sơ candidate. Quyền gửi riêng, nếu được cấp, cần được ghi tách khỏi quyền xuất bản supplement.
