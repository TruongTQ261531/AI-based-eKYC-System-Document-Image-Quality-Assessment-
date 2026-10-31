# Quyết định sau thực nghiệm, 31/10/2026

Đã hoàn thành đợt benchmark và web của nhánh nghiên cứu. **Chưa khuyến nghị
khẳng định bài đã đủ CORE B hoặc gửi ngay với claim thuật toán mới vượt trội.**
Các số dưới đây có log, model lock, dữ liệu từng ca và audit trong
[báo cáo V4](RECOVERY_RESULTS_VI.md).

| Nội dung | Bằng chứng hiện có | Diễn giải được phép |
|---|---|---|
| OCR đầu cuối |588 lượt chính, 15.288 hàng kết quả, 2 cấu hình OCR, 7 view; chấm lại 8.232 hàng native và replay 7.056 quyết định selector|Khoảng trống chưa đo OCR đầu cuối đã được xử lý|
| Nắn ảnh |Latin MIDV: 42,82% raw lên 57,29% completion; spatial stress: 87,81% raw xuống 80,94% completion|Lợi ích phụ thuộc miền; không ép mọi ảnh qua nắn hình|
| Cascade học |Bằng completion trên cả bốn đối chiếu nguồn–reader chính|Không có bằng chứng ưu thế thuật toán cascade mới|
| Điền form theo vị trí |66,67% lên 76,27% key–value exact trên SPECIMEN test; 42,19% lên 79,69% trên layout stress|Cải thiện ứng dụng với cùng OCR; so sánh V4 là post hoc, assignment là kỹ thuật đã biết|
| Tốc độ |144 yêu cầu online fresh; parser bổ sung trung bình 2,78 ms/ảnh khi replay; đã đo setup riêng|Không lấy chi phí exhaustive tái dựng làm HTTP latency|
| Dữ liệu |540 ảnh chính/150 mock document IDs; 80 ảnh stress/20 IDs; 24 MIDV-UP photo IDs|Phân biệt ảnh dẫn xuất/tổng hợp với ảnh tác giả chụp; không phải 194 người được tuyển mới|
| Tái lập |162 Python + 21 frontend; không có audit/repeat mismatch; khóa trước chấm test|Bằng chứng tính đúng của artifact, không bảo đảm novelty/acceptance|
| Web |Localhost 8001, OCR thật, form sửa được, cảnh báo cắt chữ, xóa và xác nhận lại|Demo document processing; không phê duyệt danh tính/PAD|

Ứng viên đóng góp phù hợp hơn là **bài đánh giá hệ thống và artifact về mất
thông tin khi chụp giấy tờ thiếu góc/nội dung**, kết hợp transcription,
semantic extraction, review và chi phí. Không dùng tên thuật toán mới để che
việc raw hoặc completion đơn giản có thể thắng. SHC/ConfRoute, DocXPand,
DocAttentionRect và các công trình chọn OCR đã có những ý tưởng liên quan;
[bảng closest prior](RESEARCH_V4_RELATED_WORK.md) ghi rõ phần trùng.

Ba việc còn quan trọng trước một lần nộp full paper:

1. **Kiểm chứng camera độc lập:** hiện người dùng chưa có ảnh mới. Cách ít
   vướng dữ liệu cá nhân là in thẻ SPECIMEN mới từ generator, chụp vật lý
   bằng hai điện thoại. Một pilot khả thi là 24 mock IDs, hai camera, ba điều
   kiện, 144 ảnh; ghim giao thức và chia theo physical ID trước khi chạy.
   Dùng chỉ số mới và thư mục riêng; không ghi đè ảnh/kết quả V4. Đây là
   đề xuất thu thập tiếp, không phải dữ liệu đã được tạo trong báo cáo này.
2. **Nhãn legibility độc lập:** nhờ hai người chấm một panel phân tầng về
   chữ thực sự đọc được và thông tin bị mất. Công bố hướng dẫn, mức đồng
   thuận và xử lý bất đồng. Support rectangle từ font không thay cho hai
   người đánh giá và không được ghi là human ground truth.
3. **Chốt claim và bản thảo:** đối chiếu trực tiếp closest prior, giới hạn
   claim vào bằng chứng có thật, tách phần prespecified/post hoc và giải
   thích domain shift/extra keys. Mẫu sinh viên trên browser vẫn ghép sai
   trường Trường; mẫu giấy phép thiếu tên. Không dùng một ảnh demo đúng để
   thay cho accuracy hoặc che những lỗi còn lại.

[ACM DocEng được ICORE2026 xếp B](https://portal.core.edu.au/conf-ranks/2003/).
[Trang DocEng 2027](https://doceng.org/doceng2027) nêu 24–27/08/2027 và chưa
công bố hạn nộp tại ngày kiểm tra 31/10/2026. Đây là đích có thể cân nhắc cho
bài document-system/evaluation, không phải cam kết được nhận. Bản thảo hiện
có ở [MANUSCRIPT_DRAFT.md](MANUSCRIPT_DRAFT.md); bản mentor được giữ nguyên.
