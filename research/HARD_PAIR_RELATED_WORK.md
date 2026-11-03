# Đối chiếu nghiên cứu cho vòng cặp che/giữ

Tra cứu ngày 2026-11-03 từ bài gốc. Ghi chú được viết sau khóa test
`f27ecb68b47483279caae29f9ba9894c57326878`; không thay đổi phương pháp,
checkpoint, prompt, phép chấm hoặc quyết định development. Không dùng output
test để lập các nhận định dưới đây. Đây là đối chiếu có giới hạn, không phải
tổng quan hệ thống hay chứng minh rằng chưa ai làm một ý tưởng tương tự.

## Những phần đã có tiền lệ

| Bài gốc | Điểm liên quan và giới hạn so sánh |
|---|---|
| [Seeing is Believing? / KIE-HVQA, 2025](https://arxiv.org/html/2506.20168v2) | Đánh giá OCR trên tài liệu suy giảm chất lượng; dùng SFT và GRPO để bám bằng chứng và từ chối phần không chắc chắn. Vì thế, huấn luyện bỏ nội dung không đọc được trên giấy tờ không phải ý tưởng mới riêng của project. Nhiệm vụ QA của bài khác đầu ra JSON nhiều trường ở đây. |
| [Analyzing and Mitigating Object Hallucination / POPEv2, 2025](https://arxiv.org/abs/2508.04567) | Dùng ảnh phản thực có vật thể bị che; nghiên cứu thiên lệch từ dữ liệu train và đề xuất cập nhật LM head. Vì thế, ảnh che phản thực hoặc fine-tune ít tham số tự chúng chưa chứng minh novelty. Đây là bài về vật thể, không phải phép chấm nguồn body/MRZ của OCR. |
| [CIPHER, 2026](https://arxiv.org/abs/2603.10470) | Dùng chỉnh ảnh bằng diffusion để xây nguồn phản thực và hiệu chỉnh đặc trưng bằng một không gian con; tác giả mô tả phương pháp không cần huấn luyện model. Đây là tiền lệ về dùng phản thực để giảm hallucination; không phải cùng thuật toán LoRA hoặc cùng ngân sách ở project. |
| [SHC / ConfRoute, IJDAR, 2026](https://link.springer.com/article/10.1007/s10032-026-00620-7) | Tách transcript nhìn thấy và transcript đầy đủ, đo cả đầu ra thiếu bằng chứng và từ chối; thử chuyển tuyến PaddleOCR/VLM theo confidence. Bài công bố 30-09-2026 và nêu rõ hạn chế overlap nguồn. Vì thế, tách độ đúng/độ an toàn hoặc thêm routing không đủ để tự nhận là đóng góp mới. |

## Phạm vi có thể kiểm chứng của vòng hiện tại

Phép thử cụ thể là can thiệp vào 64/640 slot train: chọn cặp trường gần nhau,
che toàn bộ các nguồn **đã khai báo** của A trong khi giữ một nguồn body nguyên
vẹn của B, rồi đảo chiều. Thành công đòi hỏi vừa bỏ A vừa đọc đúng B. Nguồn
thay thế như MRZ được tính trước khi kết luận trường mất bằng chứng.

Hai seed được đối chiếu cùng backbone, ID/slot exposure và số update. Toàn bộ
192 view của 48 giấy tờ mới được giữ, kể cả fallback và raster trùng. Tính
toàn vẹn, khoảng tin cậy theo ID và các kết quả âm được báo riêng với hiệu
quả. Cấu trúc này tạo một giả thuyết hẹp, đo được; nó chưa chứng minh tính
mới so với toàn bộ nghiên cứu liên quan.

Nhận định của project: nếu muốn quy tác động riêng cho **cách chọn ca khó**,
cần thêm đối chứng cặp che/giữ chọn ngẫu nhiên với cùng lượng thay đổi. Nếu
muốn quy riêng cho **cặp đảo chiều**, cần đối chứng mask đơn có cùng ngữ cảnh
và mức phơi nhiễm. Vòng hiện tại thay đồng thời ngữ cảnh, chính sách mask và
số token đáp án, nên chỉ kiểm tra cả gói can thiệp. Những đối chứng đó chưa
được chạy và không được ngầm coi là đã có kết quả.

## Ý nghĩa đối với mục tiêu paper

Development hiện không cho phép thay model web. Test mới vẫn phải hoàn tất
và audit như đã đăng ký; không đổi tiêu chí sau khi nhìn kết quả. Bằng chứng
minh bạch giúp đánh giá một phương pháp nhưng không tự biến một kết quả âm
thành thuật toán hiệu quả hơn hoặc bảo đảm chấp nhận CORE B.

Chưa có đánh giá legibility độc lập của người, bộ camera mới được phép tự
thu thập, hay kiểm chứng trên dân số người dùng eKYC thật. Ground truth hình
học và giấy tờ mẫu không thay được các bằng chứng đó. Không diễn giải kết
quả OCR thành chứng nhận chống giả hoặc xác minh danh tính.

Liên quan: [protocol](HARD_PAIR_PROTOCOL.md),
[phương pháp](HARD_PAIR_METHOD.md), [độ bao phủ nguồn](HARD_PAIR_COVERAGE_NOTE.md).
