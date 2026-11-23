# Bộ ghi công và quyền đối với ảnh C2 · 23/11/2026

## Ghi công kèm mỗi bản phân phối được duyệt

**Nguồn ảnh và annotation** — K. B. Bulatov, E. V. Emelianova, D. V. Tropin, N. S. Skoryukina, Y. S. Chernyshova, A. V. Sheshkus, S. A. Usilin, Z. Ming, J.-C. Burie, M. M. Luqman, V. V. Arlazarov. *MIDV-2020: A Comprehensive Benchmark Dataset for Identity Document Analysis*. Computer Optics, 46(2), 252–270 (2022). [Bài báo](https://doi.org/10.18287/2412-6179-CO-1006) · [Nguồn dataset](https://l3i-share.univ-lr.fr/MIDV2020/midv2020.html)

Ảnh gốc thuộc bản phân phối MIDV-2020. Nhóm nghiên cứu B đã cắt khung, che vùng trên ảnh dẫn xuất và trích vùng trường dữ liệu/MRZ trước và sau biến đổi. Đối với phần được cấp phép, áp dụng [Creative Commons Attribution-ShareAlike 2.5 Generic](https://creativecommons.org/licenses/by-sa/2.5/) cho ảnh gốc và chọn cùng giấy phép cho ảnh phái sinh khi phân phối. Giữ nguyên notice nguồn/miễn bảo đảm, URI và bộ credit này với bản sao. [Toàn văn §4](https://creativecommons.org/licenses/by-sa/2.5/legalcode)

**Chân dung tổng hợp do Generated Photos cung cấp.** Bài báo §1.1 mô tả có thể in lặp chân dung trên cùng mẫu. License đi cùng archive khuyến khích credit cả trong tác phẩm phái sinh. Điều khoản dịch vụ công bố 16/10/2023 §§3–4 phân biệt quyền theo cách mua, giới hạn chuyển dataset cho bên thứ ba (§3d), ghi công tạp chí và tái phân phối phần có thể trích riêng (§4). Chưa có chứng từ về quyền nhúng, tái phân phối hoặc thỏa thuận riêng tại thời điểm tạo dataset. Ghi công bảo toàn nguồn, không tự giải quyết nghi vấn quyền. Xin căn cứ của nhóm MIDV nếu đây là yếu tố quyết định. [Generated Photos](https://generated.photos/) · [Điều khoản dịch vụ](https://generated.photos/terms-and-conditions)

### Mẫu nền thực sự xuất hiện trong C2-45

Đây là nền **in trên giấy tờ**, còn điều kiện chụp như mặt bàn được mô tả riêng trong readme. Đã nối 4 mã trong queue với bảng DOCTYPES của readme, bảng 1 và §1.1 của bài báo, rồi đọc các dòng tương ứng trong [bảng ghi công gốc MIDV-500](ftp://smartengines.com/midv-500/documents.pdf). SHA-256 PDF là `afdf190963ed5c4f1183a970d9355b624bd5472226fca5dc386356fdddd04572`. Các bản ghi Commons dưới đây đã kiểm ngày 23/11/2026. Tên người dùng công khai trong bảng là credit của tác phẩm nguồn.

| Mẫu, số ca / giấy tờ | Credit theo bảng và nguồn Commons | Thay đổi MIDV-500 ghi nhận | Bằng chứng quyền của tệp |
|---|---|---|---|
| 05 Azerbaijan · 12/7 | Government of Azerbaijan / Twofortnights / Wikimedia Commons. Nguồn trang tệp ghi EdisonTD. | Crop, bỏ chữ SPECIMEN | Trang tệp ghi public domain theo Điều 5, 7 Azerbaijan. Đây là tuyên bố về tài liệu chính thức tại nguồn. [Phiên bản trang](https://commons.wikimedia.org/wiki/Special:PermanentLink/1229515210) |
| 25 Hy Lạp · 8/6 | Greek Government / Bonus bon~commonswiki / Wikimedia Commons. Tệp *Greek passport biodata page.png*. | Thêm lề trên và dưới | Tệp bị xóa ngày 09/02/2026, lý do thiếu permission. Dòng upload cũ nhắc European Communities và ghi nguồn nhưng phần trích không đầy đủ. Chưa đủ căn cứ cho bản C2 có nền này. [Nhật ký xóa](https://commons.wikimedia.org/w/api.php?action=query&format=json&list=logevents&letitle=File%3AGreek%20passport%20biodata%20page.png&letype=delete) |
| 32 Latvia · 11/4 | Government of Latvia / Twofortnights / Wikimedia Commons. Nguồn trang tệp ghi EdisonTD. | Thêm lề trên, bỏ chữ SPECIMEN | Trang tệp ghi public domain theo §6 về tài liệu chính thức. [Phiên bản trang](https://commons.wikimedia.org/wiki/Special:PermanentLink/1222085856) |
| 41 Serbia · 14/7 | Government of Serbia / Twofortnights / Wikimedia Commons. Nguồn trang tệp ghi EdisonTD. | Crop | Tệp đổi tên năm 2024, bản 2009. Trang ghi public domain theo quy định Serbia về tài liệu chính thức. [Phiên bản trang](https://commons.wikimedia.org/wiki/Special:PermanentLink/862517415) |

Ba mô tả public domain là bằng chứng ở cấp trang tệp, không xác lập mọi quyền tại mọi nước. Bảng nguồn không gắn hash pixel nguyên thủy của từng template. Với Hy Lạp, quyết định xóa của Commons là thiếu căn cứ cụ thể, không phải phán quyết vi phạm. Liên kết PRADO dùng để nhận diện mẫu. Điều khoản hiện hành của Hội đồng EU có hạn chế tái sử dụng nội dung PRADO; chỉ dẫn sang trang đó không cấp quyền đối với ảnh này. [Chính sách của Hội đồng, mục PRADO](https://www.consilium.europa.eu/en/about-site/copyright/)

### Áp dụng theo lớp

Annotation thuộc bản phát hành nhà cung cấp, tạo bằng VGG Image Annotator. Tên công cụ không quyết định giấy phép của dữ liệu. Ảnh gốc kết hợp nền, thông tin giả lập, chữ ký mô phỏng và chân dung. Ảnh dẫn xuất/crop kế thừa các thành phần thực sự còn nhìn thấy. Một crop chỉ gồm ký tự vẫn cần kiểm phần đồ họa ở nền. Không thể giải quyết quyền cho workspace bằng cách kiểm riêng crop vì workspace phát cả khung đầy đủ. Code HTML, schema và phiếu trống do dự án chuẩn bị, rationale và chữ ký tương lai thuộc hồ sơ người tham gia. Không phát hiện bộ ảnh bên ngoài MIDV được bổ sung vào 198 asset ảnh của mỗi workspace. [Ma trận 5 nhóm](D10_RIGHTS_RISK_MATRIX.json)

Bản hiện tại của hai workspace vướng mẫu Hy Lạp. Có thể xin căn cứ quyền cho mẫu đó hoặc trình riêng phương án **37 ca / 18 giấy tờ** với đủ credit và đánh giá chân dung, tạo phiên bản mới, kiểm từng member và xin D10 riêng. Con số này là phạm vi tiềm năng, chưa có hai gói đã kiểm của phiên bản thu hẹp. Public supplement cần kiểm riêng hình thực sự công bố, quyền của bên thứ ba, notice và điều khoản xuất bản. §4 không buộc phải đăng ảnh công khai.
