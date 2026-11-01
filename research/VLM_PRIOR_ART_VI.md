# Đối chiếu prior art cho đợt LoRA V1

Kiểm tra ngày2026-11-01. Đây là đánh giá phạm vi đóng góp, không phải chứng
nhận novelty hoặc cam kết được nhận tại hội nghị. Không đổi model, prompt,
checkpoint hoặc metric chính dựa trên test đang chạy.

| Nguồn gốc | Nội dung liên quan đã công bố | Hệ quả cho project |
|---|---|---|
| [KIE-HVQA / Seeing is Believing?, NeurIPS2025; arXiv v2 ngày22/09/2025](https://arxiv.org/abs/2506.20168v2) | Nghiên cứu OCR bịa dưới suy giảm hình ảnh trên ID/invoice; sử dụng SFT và GRPO với cơ chế xử lý bất định. | Không thể gọi học bỏ thông tin không rõ trên ID card là ý tưởng mới chỉ vì dùng LoRA. |
| [SHC / ConfRoute, IJDAR,30/09/2026](https://link.springer.com/article/10.1007/s10032-026-00620-7) | Đánh giá riêng chữ nhìn thấy/chữ đầy đủ, xuất thông tin không được hỗ trợ, abstention và routing OCR–VLM. Bài báo cũng công bố giới hạn tách nguồn. | Dual reference, abstention hay confidence routing không tự là novelty của project. Tách ID/source và công bố lỗi vẫn là yêu cầu thực nghiệm. |
| [VRD-UQA, arXiv14/11/2025](https://arxiv.org/abs/2511.11468) | Thay thực thể/bố cục/câu hỏi để tạo tình huống không trả lời được trong tài liệu nhiều trang, đánh giá12model. | Không thể xem bài toán unanswerability của tài liệu là chưa ai nghiên cứu. Bài này khác KIE toàn thẻ và không phải baseline cùng metric. |
| [VeriOCRBench, preprint31/08/2026](https://arxiv.org/abs/2609.00232) | Benchmark kiểm tra task OCR có thể thực hiện được, tách chẩn đoán lỗi và từ chối quá mức, có kiểm tra của người. | Cần đánh giá đọc đúng và từ chối nhầm cùng nhau; không đổi số output che kín bằng0 thành tuyên bố an toàn. Chưa xác nhận venue nhận bài từ nguồn này. |

Nguồn dataset tác giả cho KIE-HVQA:
[dataset card](https://huggingface.co/datasets/bytedance-research/KIE-HVQA),
[mã eval](https://huggingface.co/datasets/bytedance-research/KIE-HVQA/blob/main/eval.py).
Mã eval đo ba chuỗi OCR clear/not-clear/final; không phải microF1 cặp
khóa–giá trị của corpus này. Không lấy số trên hai benchmark để xếp hạng
model trực tiếp. Đợt V1 chưa chạy benchmark KIE-HVQA chính thức.

## Phần hiện tại có thể chứng minh

Đây là nhận định của project từ thiết kế/kiểm thử của chính mình: adaptation
của VLM nhỏ với supervision bỏ trường thiếu nội dung, so với model gốc, OCR
CPU sẵn có và một LoRA không có hai dạng field_clip/value_mask. Điểm cần
kiểm chứng là thay đổi F1/định dạng/output của trường che, compute thực đo
và mức nhất quán khi chạy lại. Kết luận chỉ áp dụng corpus SPECIMEN cùng họ
generator/font/bố cục. Không gọi đây là thuật toán LoRA mới, dataset giấy tờ
camera thật, hay phương pháp đầu tiên chống OCR hallucination.

Đối chứng được thúc đẩy bởi development và khóa trước test. Compute/IDs
khớp nhưng số raster/epoch và checkpoint được chọn có thể khác. Không thể
quy mọi thay đổi chỉ cho một yếu tố như trong ablation hoàn toàn kiểm soát.

## Thiếu gì để lập luận paper mạnh hơn

1. Đánh giá chuyển miền bằng ảnh/layout/font/camera độc lập và bản chép do
   người chấm; không dùng nhãn Clean/Blur để thay transcript hoặc dùng LLM
   tự tạo đáp án rồi gọi là ground truth.
2. Thiết kế thêm đối chứng cùng số raster/presentations ở checkpoint được
   so, tách lợi ích định dạng khỏi đọc chữ và bỏ trường không thấy.
3. So với closest prior trên cùng nhiệm vụ/metric hoặc giữ một benchmark
   ngoại bộ riêng với prompt/scorer tác giả. Chạy khác task phải nói rõ,
   không đổi metric để tạo vẻ hơn baseline.
4. Chỉ đóng khung đóng góp dataset/protocol khi có quy trình nhãn, nguồn,
   tách nguồn, license và bản tái lập đủ rõ; kích thước720ảnh tự sinh hoặc
   con số F1 cao một mình không đủ chứng minh đóng góp CORE B.

Các mục này là việc còn thiếu, không được tính là thí nghiệm đã hoàn thành
trong báo cáo V1. Không triển khai GRPO/QLoRA, không gọi API model trả phí
và không đưa ảnh cá nhân lên dịch vụ ngoài trong đợt này.
