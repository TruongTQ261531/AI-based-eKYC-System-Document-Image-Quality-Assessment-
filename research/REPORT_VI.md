# Báo cáo nghiên cứu khả thi hướng CORE B

**Cập nhật31/10/2026:** đợt mở rộng đã xong. Đọc
[báo cáo V4](RECOVERY_RESULTS_VI.md) và [bản thảo hiện tại](MANUSCRIPT_DRAFT.md):
588 lượt inference chính,15.288 hàng kết quả, kiểm chứng ngoài miền và web
localhost8001;162 test Python+21 frontend đạt. Bộ gán thông tin theo vị trí
cải thiện key–value exact nhưng cascade không hơn completion. Các phần dưới
giữ nguyên lịch sử feasibility/V2, không phải kết quả mới nhất.

Ngày đối chiếu tài liệu và chạy thử ban đầu: **28/10/2026**; bổ sung OCR
đầu cuối hoàn tất **30/10/2026**. Đây là báo cáo kết quả
thật của các ứng viên nghiên cứu, chưa phải tuyên bố đã hoàn thành một paper
đủ điều kiện được nhận. CORE B là hạng hội nghị, khác với Q2 của tạp chí.

## 1. Kết luận tại thời điểm này

**Cập nhật30/10:** [benchmark OCR đầu cuối](E2E_RESULTS_VI.md) đã xong:
161 ảnh + hai lượt lặp cùng panel32, tổng225 lượt ảnh/2700 hàng kết quả.
VietOCR trên91 ca neural ba góc: raw22,09%, support27,69%, hình bình hành
nới5%32,64% field exact; latency tương ứng14,78/16,25/12,76 giây/ảnh.
Support cải thiện so với raw nhưng không vượt baseline completion đơn giản;
mask không tăng field exact tổng so với bbox. Vì vậy thiếu sót hiện tại đã
chuyển từ **chưa đo OCR thật** sang **chưa chứng minh lợi ích riêng đủ mạnh
của ứng viên mới**. Không thay kết quả âm bằng tuyên bố đủ CORE B.

Hướng phù hợp nhất với máy hiện có là **bảo toàn vùng thông tin khi định vị/cắt
giấy tờ, kết hợp quyết định xử lý tự động hoặc yêu cầu xem xét**. Nó dùng lại
localizer, CPU và nhãn hình học có sẵn; không cần huấn luyện một mạng lớn.

Đã triển khai và đánh giá ba giai đoạn cùng baseline neural và kiểm chứng ngoài.
Bản nới cạnh không calibration cải
thiện một số chỉ số hình học. Bản calibration yêu cầu bao phủ mọi khung hình
trong một giấy tờ thất bại về tính thực dụng. Chính sách giới hạn diện tích
và xem xét ở giai đoạn hai giảm lỗi nhưng giảm đáng kể số ca được tự động xử
lý. **Hiện chưa đủ căn cứ để khẳng định novelty và hiệu quả đạt mức CORE B.**

Ứng viên dùng các cạnh còn quan sát được khi thiếu một góc có lợi ích giữ vùng
nội dung với ít nền hơn full-frame. Nhưng mức tăng coverage cũng đạt được bằng
một control full-frame, còn baseline hình bình hành+nới 5% có utility cao hơn.
Không thể chỉ từ kết quả đó tuyên bố thuật toán mới đã đủ CORE B.

Đây là kết luận từ dữ liệu, không phải do chưa chạy thử. Không loại bỏ kết
quả âm, không chọn riêng seed tốt nhất và không gọi độ giữ vùng chữ là độ
chính xác OCR, xác minh danh tính hoặc khả năng chống giả mạo.

## 2. Tách biệt với hệ thống mentor

- Repo: [AI-based-eKYC-System-Document-Image-Quality-Assessment-](https://github.com/TruongTQ261531/AI-based-eKYC-System-Document-Image-Quality-Assessment-).
- Bản mentor: nhánh `mentor/ekyc-v3.2.0`, commit
  `4110f22b94699d30950cd1c0b23532ee9ccaaa59`.
- Nghiên cứu: nhánh `research/document-recovery-core-b`, worktree riêng trong
  `versions/research-document-recovery`.
- Các file runtime `ekyc/`, `web/`, `tests/` và launcher của mentor không được
  sửa bởi nghiên cứu. Chỉ thêm code/thử nghiệm/tài liệu dưới `research/` và
  quy tắc Git liên quan. Không đưa thuật toán nghiên cứu vào luồng xác minh.
- Dataset gốc được đọc tại chỗ. Không upload ảnh giấy tờ, selfie hay văn bản
  cá nhân lên GitHub. Cache ảnh/nhãn/prediction không công khai.

## 3. Xu hướng và đánh giá điểm mới

Tổng hợp có nguồn gốc nằm trong [LITERATURE_REVIEW.md](LITERATURE_REVIEW.md).
Các hướng gần đề tài gồm quality gắn với OCR, sửa hình học có đánh giá mất
nội dung, chọn lọc ca cần người xem xét và calibration cho định vị.

Các công trình cần phân biệt rõ:

- [DocIQ](https://arxiv.org/abs/2509.17012) và
  [OCR-based DIQA 2026](https://doi.org/10.3389/frsip.2026.1779355): quality
  cho tài liệu/OCR đã là một hướng nghiên cứu có sẵn.
- [Cascaded Robust Rectification](https://arxiv.org/abs/2511.23150) và
  [PreP-OCR](https://aclanthology.org/2025.acl-long.749/): ghép căn chỉnh,
  phục hồi và OCR không tự tạo ra novelty.
- [Timans et al., ECCV 2024](https://arxiv.org/abs/2403.07263) và
  [TriCCOT, BMVC 2026](https://arxiv.org/abs/2609.08659): mở rộng vùng dự đoán
  bằng conformal trước bước nhận dạng có tiền lệ rất gần.
- [Conformal Risk Control, ICLR 2024](https://proceedings.iclr.cc/paper_files/paper/2024/hash/f3549ef9b5ff520a7e41ff3cc306ab2b-Abstract-Conference.html)
  cung cấp nền tảng kiểm soát loss đơn điệu. Công thức CRC sử dụng ở đây là
  của công trình đó, không phải định lý mới của project.
- [Macro Mondrian CRC, preprint ngày 26/10/2026](https://arxiv.org/abs/2610.35035)
  nghiên cứu risk theo các nhóm và mất cân bằng. Không thể coi việc thêm
  trung bình theo nhóm là phát minh mới.

Điểm đáng nghiên cứu của project là **đánh đổi bảo toàn trường thông tin,
diện tích lấy thừa, tỷ lệ tự động và lỗi trên các video giấy tờ có tương quan**.
Phần này có thể thành đóng góp ứng dụng/đánh giá nếu có lợi ích rõ, so sánh
mạnh và kiểm chứng ngoài đủ lớn. Hiện bằng chứng còn thiếu ở các điểm đó.

## 4. Dữ liệu và cách chống đánh giá sai

Đã đối chiếu 21.000 nhãn frame và 100 nhãn reference của MIDV500/2019. Tập
thử nghiệm chính lấy cố định frame **01, 08, 15, 22, 30 của mọi clip**:

| Thuộc tính | Số lượng |
|---|---:|
| Ảnh khác nhau thực sự chạy localizer | 3.500 |
| Giấy tờ vật lý | 50 |
| MIDV500 / MIDV2019 | 2.500 / 1.000 |
| Clean | 1.500 |
| Blur / Cropped / Dark / Distorted | 500 mỗi nhóm |
| Ảnh thiếu trong mẫu đã chọn | 0 |

Đây **không phải** kết quả chạy hết 21.000 ảnh. Nhãn Clean/defect được dùng
để phân tầng báo cáo, không được đưa vào predictor để chọn đáp án.

Nhãn được lấy từ nguồn FTP do tác giả công bố trong các bài MIDV. Kiểm tra
CRC32 từng JSON trong ZIP và SHA256 từng block/ảnh. Đối chiếu thêm 600 quad
với một mirror lịch sử, khớp chính xác; mirror đó chỉ phủ hai loại thẻ nên
không được diễn giải thành xác minh độc lập toàn bộ annotation. Không tuyên
bố đã xác thực MD5 toàn ZIP hay tính xác thực mật mã của FTP.

Reference không được tính như các frame độc lập. Vùng chữ được chiếu từ nhãn
reference sang frame bằng quad ground truth để **chấm điểm/calibration**;
predictor chỉ nhận pixel ảnh, không nhận quad, nội dung chữ hay ID.

Mỗi seed chia **20 giấy tờ calibration, 30 giấy tờ test**, dùng chung ID giữa
MIDV500 và MIDV2019 để tránh một giấy tờ xuất hiện ở cả hai phía trong cùng
lần chia. Seeds: **13, 29, 47, 71, 97**. Các lần chia có chồng lặp; không phải
năm tập test độc lập hay năm lần train. Không huấn luyện model mới.

Localizer hình học đã từng được phát triển/xem xét trên một số ví dụ MIDV
trước nghiên cứu. Tách ID ngẫu nhiên bây giờ không xóa được lịch sử tiếp xúc
đó. Không dùng weights quality có lịch sử chưa rõ làm bằng chứng học máy
không leakage. Tập ngoài cần được diễn giải riêng về ID và template.

## 5. Ứng viên giai đoạn một

Ba lần gọi localizer cố định trên ảnh gốc, CLAHE và downscale-upscale; lấy
quad medoid theo IoU. Các view tương quan, không giả thiết độc lập thống kê.
Ước lượng scale riêng mỗi cạnh từ độ lệch giữa view và hỗ trợ biên ảnh.

Với pháp tuyến hướng vào trong `n_i`, biên `b_i`, scale `s_i`, vùng hỗ trợ:

```
C(lambda) = frame ∩ {x: n_i^T x >= b_i - lambda*s_i, với mọi cạnh i}.
```

Vùng này có thể nhiều hơn bốn đỉnh sau khi giao khung hình. Nó giữ pixel gốc;
không dựng lại ký tự mất ngoài ảnh và không được gọi là phục hồi đúng góc
vật lý. Khi các view không nhất quán, trả full-frame để xem xét.

Calibration v1 lấy residual lớn nhất trên các frame của từng giấy tờ, rồi
dùng order statistic thứ 19/20 tại alpha=.10. Quy trình và code đã được chốt
ở commit `3e3c781` trước dự đoán chính. Ba biến thể calibrated dùng full card,
scale adaptive hoặc target vùng chữ; chi tiết trong [METHOD.md](METHOD.md).

Kết quả trung bình qua cả năm lần chia:

| Phương pháp | Mean IoU | Giữ >=98% mọi vùng chữ (%) | Trung vị diện tích crop/card | Utility hình học (%) | Tự động (%) |
|---|---:|---:|---:|---:|---:|
| Single | .6439 | 85.88 | 1.034 | 38.72 | 68.26 |
| Medoid | .6938 | 79.01 | 1.013 | 42.60 | 81.80 |
| Fixed 5% | .6176 | 81.55 | 1.226 | 38.35 | 81.80 |
| Fixed 10% | .5475 | 83.10 | 1.446 | .85 | 5.10 |
| Fixed 20% | .4553 | 86.35 | 1.853 | .00 | .01 |
| Adaptive không calibration | .6156 | 91.22 | 1.121 | 44.53 | 61.77 |
| CP constant | .2387 | 99.97 | 4.163 | .04 | .00 |
| CP adaptive | .2379 | 99.93 | 4.158 | .01 | .00 |
| CP fields | .2381 | 99.83 | 4.154 | .00 | .00 |

Utility = IoU >=.80 **và** giữ >=98% diện tích card nhìn thấy. Giữ vùng chữ
được tính trên các frame có vùng chữ nhìn thấy/evaluable. Tự động có mẫu số
là tất cả frame. Vì vậy các cột không có cùng điều kiện mẫu số.

SD qua năm split và mọi seed/source nằm trong bảng JSON/CSV. Ví dụ utility
của adaptive không calibration = **44.53 ±1.09 điểm %**, single = **38.72
±1.30 điểm %**. Đây là SD của các split có chồng lặp, không phải SE hay CI.

Bootstrap ghép cặp theo 30 physical ID trên seed13 cho chênh lệch utility
adaptive không calibration so với single là **+5.92 điểm %**, CI95% thăm dò
**[+3.67; +8.37] điểm %**. Khác nhẹ với chênh lệch trung bình frame vì bootstrap
dùng trung bình theo ID và chỉ seed13. Chưa điều chỉnh nhiều phép so sánh.

**Kết quả âm quan trọng:** CP đạt giữ chữ gần 100% bằng cách lấy vùng rộng
hơn card khoảng bốn lần và không có ca nào được tự động xử lý. Không thể
đổi điều đó thành tuyên bố thuật toán an toàn với zero error hay đủ triển khai.

## 6. Giai đoạn hai: giới hạn diện tích và xem xét

Đây là nghiên cứu thăm dò **sau khi đã thấy v1**, chốt protocol/code ở commit
`ccfdac1` trước khi tính kết quả v2. Không chỉnh kết quả hay thay v1.

Ở mỗi giá trị lambda trên grid cố định 15 mức, giữ cùng vùng hỗ trợ. Chỉ
tự động xử lý nếu localization nhất quán, crop/base <=1.35 và crop/frame
<=.95; các ca khác yêu cầu xem xét. Đây là operating point nghiên cứu, chưa
phải ngưỡng an toàn được xác nhận cho sản phẩm.

Loss một frame là `tự_động AND mất_>=2%_ít_nhất_một_vùng_chữ`. Ca tự động
không có target chữ evaluable cũng bị tính lỗi. Lấy trung bình 70 frame trong
mỗi physical ID, rồi dùng CRC có sẵn:

```
lambda_hat = mức nhỏ nhất sao cho (sum_g L_g(lambda) + 1)/(n+1) <= .10.
```

Với n=20, điều kiện tương đương empirical group loss <=.055. Vì thế correction
khá bảo thủ. Vùng cắt tăng thì lỗi hình học giảm; gate diện tích chỉ chuyển
từ tự động sang xem xét, nên loss tích là đơn điệu. Đã kiểm tra trên **105.000
tổ hợp frame/family/lambda**, không có vi phạm. Đây là kiểm tra tính đơn điệu
của định nghĩa loss, không chứng minh lỗi OCR cũng đơn điệu.

| Phương pháp | Tự động (%) | Lỗi tự động / mọi frame (%) | Lỗi trong số ca tự động (%) | Tự động giữ chữ đúng (%) | Utility được tự động (%) |
|---|---:|---:|---:|---:|---:|
| Single v1 | 68.26 | 14.66 | 21.47 | 53.60 | 38.22 |
| Adaptive không calibration v1 | 61.77 | 9.10 | 14.74 | 52.67 | 43.96 |
| Constant ERM cap | 61.95 | 10.11 | 16.32 | 51.84 | 41.36 |
| Constant CRC cap | 27.82 | 1.93 | 6.95 | 25.89 | .94 |
| Constant CRC uncapped | .00 | .00 | Không có ca | .00 | .00 |
| Constant frame-CRC cap | 61.95 | 10.06 | 16.22 | 51.90 | 41.70 |
| Adaptive ERM cap | 61.95 | 10.06 | 16.23 | 51.90 | 41.14 |
| Adaptive CRC cap | 47.30 | 5.22 | 10.78 | 42.09 | 22.63 |
| Adaptive CRC uncapped | .01 | .00 | Chỉ 1 split có ca | .01 | .00 |
| Adaptive frame-CRC cap | 61.95 | 10.06 | 16.23 | 51.90 | 41.14 |

Các hàng frame-CRC chỉ là ablation: video có tương quan nên không được gắn
bảo đảm độc lập frame cho chúng. `CRC uncapped` calibration loss trước gate,
nhưng khi báo cáo tự động vẫn áp dụng cùng gate diện tích.

Adaptive CRC cap chọn lambda=4 ở bốn split và lambda=6 ở seed97. Automatic
coverage trung bình **47.30 ±9.61 điểm %**, cho thấy độ nhạy đáng kể với chỉ
20 calibration ID. Tỷ lệ lỗi trong ca đã nhận **10.78%** khác với **5.22%** có
mẫu số tất cả frame. CRC ở đây không đảm bảo conditional error <=10% trong
ca được nhận, không phải confidence bound cho test set, và không có bảo đảm
cho nguồn/camera ngoài phân phối calibration.

So với adaptive không calibration, trên seed13 bootstrap ghép cặp cho thấy:
lỗi tự động/all frame giảm **3.00 điểm % [2.10; 3.95]**, nhưng automatic coverage
giảm **9.38 điểm % [7.71; 11.00]**, số ca tự động giữ chữ đúng giảm **6.38 điểm %
[4.76; 8.10]**, utility được nhận giảm **15.00 điểm % [11.14; 18.81]**.
Vì vậy không được tuyên bố v2 thống trị baseline. Nó thể hiện một đánh đổi.

## 7. OCR thực tế: kiểm tra được điều gì

Protocol OCR phụ được chốt ở `a808d77` khi inference chính đang chạy, trước
khi xem outcome v1. Chọn bằng hash cố định một vùng chữ Latin đầy đủ cho mỗi
ID/source thuộc test seed13. Có **58 vùng từ 29 ID** đủ điều kiện; một ID không
có vùng thỏa quy tắc. Chạy mọi phương pháp với EasyOCR English và VietOCR:
**1.160 hàng phương pháp/bộ OCR**. Các patch giống hệt dùng lại cùng readout.

| Bộ OCR | CER macro vùng gốc oracle | Single | Adaptive không calibration | Exact match vùng gốc |
|---|---:|---:|---:|---:|
| EasyOCR English | .6067 | .6078 | .6067 | 10.34% |
| VietOCR | .4789 | .4884 | .4884 | 13.79% |

Đây là điều khiển vị trí vùng chữ bằng ground truth để cô lập tác hại do crop.
**Không phải OCR end-to-end**, cũng không phải accuracy đọc CCCD Việt Nam.
CER nền đã cao nên không thể suy từ giữ diện tích vùng chữ sang chất lượng
đọc tốt. Bootstrap mức ID cho chênh lệch VietOCR của adaptive so với oracle
là +.00958, CI [.00000; .02874], chưa cho bằng chứng chắc về cải thiện OCR.

Chỉ lưu ID vùng, số ký tự, edit distance, CER, confidence; không công bố chuỗi
ground truth/chuỗi nhận dạng hay ảnh. Không dùng confidence làm nhãn đúng.

## 8. Khả năng tái lập và kiểm thử

- Chạy suy luận chính một lần trên 3.500 ảnh, ba view/ảnh = **10.500 lần gọi
  localizer**. Tổng thời gian lần chạy gồm phân tích khoảng **686.75 giây** trên
  CPU; đây không phải latency camera hoặc benchmark phục vụ đồng thời.
- Có **631/3.500 ảnh không view nào định vị được**. Giữ fallback và các ca này
  trong báo cáo, không loại bỏ.
- Chạy lại toàn bộ phân tích năm split từ cache: data audit, splits, CSV/JSON,
  bootstrap và bảng per-image nén khớp từng byte. Lần này không suy luận mới.
- Chạy lại suy luận thật, không lấy prediction từ cache, trên **100 ảnh** chọn
  bằng hash, mỗi ID/source một ảnh = **300 lần gọi mới**: input và prediction
  trùng **100/100**; 12.84 giây. Đây không phải chạy lại đủ 3.500 ảnh năm lần.
- **125 kiểm thử Python đạt**, gồm 109 bài runtime và 16 bài nghiên cứu;
  **15 kiểm thử frontend Node đều đạt**.
  Không chạy `tests/test_manifest.py` trong worktree không chứa raw dataset;
  data audit nghiên cứu kiểm tra mẫu đọc từ dataset gốc. Có một cảnh báo
  deprecation FastAPI/Starlette/httpx; không đổi dependency để che cảnh báo.
- Python 3.11.4, NumPy 2.4.6, OpenCV headless 5.0.0.93, Torch 2.14.1 CPU,
  EasyOCR 1.7.2, VietOCR .3.13. Không tạo venv hay cài thêm dependency.
- Model/code/protocol/input hashes, split IDs, mọi hàng kết quả và thời gian
  nằm trong [results/](results/). Các view là các lần gọi xác định, không phải
  ba mẫu độc lập thống kê.

## 8a. Kiểm chứng ngoài: 20 physical ID mới từ MIDV-2020

Đã tải đúng hai JPEG đầu trong mỗi thư mục loại thẻ của TAR tác giả: thực tế
là ID **05 và 59** ở cả mười loại. Theo README, đó là ảnh projective distortion
bằng iPhone XR và table background bằng Samsung S10. Không có low-light trong
mẫu này, không phải mẫu đại diện ngẫu nhiên. Tổng JPEG **77.412.400 byte**,
không tải nguyên gói photo.tar 4 GB. Nhãn và JPEG header nguồn được đối chiếu.

Không có calibration ngoài; chuyển nguyên tham số seed13. ID/text/chân dung
mới so với 50 ID ban đầu, nhưng mười template vẫn trùng: không phải kiểm chứng
unseen-template. Không làm significance test trên chỉ 20 ca.

| Phương pháp | Tự động (số ảnh) | Lỗi mất vùng chữ trong ca tự động | Utility được tự động |
|---|---:|---:|---:|
| Single hình học | 17/20 | 8/17 | 4/20 |
| Adaptive không calibration | 14/20 | 6/14 | 5/20 |
| Adaptive CRC cap | 12/20 | 4/12 | 4/20 |
| Neural single | 18/20 | 0/18 | 16/20 |
| Neural fixed 5% | 18/20 | 0/18 | 18/20 |

Kết quả âm của CRC ngoài phù hợp với việc không có bảo đảm OOD. Zero observed
harm của neural trên 18 ca không có nghĩa zero risk khi triển khai.

Đã phát hiện một lỗi bộ đánh giá: mười ảnh59 có EXIF orientation=6; PIL trả
raw dimensions còn OpenCV giải mã theo chiều hiển thị. Đã sửa kích thước và
thêm assertion/test hồi quy, giữ nguyên 20 ID/tham số. Kết quả sai trước sửa
được lưu ở `pre_exif_correction/` với nhãn **invalid, excluded**, không dùng
cho kết luận. Một lỗi đọc JPEG prefix quá ngắn cũng đã được sửa trước inference.
Chi tiết nằm trong [corrections.json](results/external_midv2020/corrections.json).

## 8b. Baseline neural mạnh hơn: DocAligner FastViT-SA24

Sử dụng [trọng số tác giả](https://docsaid.org/fr/models/docaligner), 83.084.930
byte, SHA256 `7f9f5a8935b2eb22b3ee0245d34996063f54562df390d34714af2d76928695bc`,
đã khớp trước chạy. Dùng ONNX Runtime CPU sẵn có; không cài Capybara/DocAligner
hay dependency mới. Adapter đối chiếu mã tiền/hậu xử lý tác giả, nhưng chưa
có numeric equivalence test với package gốc; lịch sử train/split của weights
chưa được xác minh độc lập. Không gọi đây là so sánh SOTA không leakage.

Lấy cố định **frame15 của mọi clip =700 ảnh**, so sánh các phương pháp trên
đúng cùng ảnh và cùng năm test split, **420 ảnh/split**. Không so trực tiếp số
trong bảng 700 ảnh với bảng chính 3.500 ảnh để tính gain.

| Phương pháp trên cùng 700 ảnh | Mean IoU | Giữ vùng chữ >=98% (%) | Utility (%) | Tự động (%) |
|---|---:|---:|---:|---:|
| Single hình học | .6436 | 87.64 | 36.88 | 65.19 |
| Adaptive không calibration | .6142 | 92.43 | 42.48 | 59.29 |
| Neural single | .7882 | 99.90 | 69.59 | 70.62 |
| Neural fixed 5% | .6697 | 99.90 | 70.74 | 70.62 |

Giữ vùng chữ vẫn tính cả full-frame fallback; phải đọc cùng cột coverage.
Neural inference/scoring 720 ảnh gồm 20 ảnh ngoài mất **179.94 giây**;
203 ảnh trả fallback. Baseline này vượt xa cải tiến quanh localizer hình học,
nên không còn hợp lý dùng localizer cũ làm đối thủ mạnh nhất cho paper.

## 8c. Ứng viên mới: vùng hỗ trợ từ ba góc còn thấy

Protocol chốt ở `4c134a4` trước giải mã partial-corner. Chạy lại 203 ca neural
thất bại để kiểm tra từng channel heatmap, không train mạng mới. Phân bố trên
720 ảnh: **517 có bốn góc hợp lệ; 92 có ba; 89 có hai; 11 có một; 11 không có**.
Chỉ xử lý thêm đúng ba góc; các ca ít góc hơn vẫn yêu cầu xem xét.

Với ba góc theo các channel của model, có hai cạnh quan sát được đủ hai đầu
mút. Chọn phía chứa góc còn lại của mỗi đường, rồi giao hai nửa mặt phẳng với
khung hình. Không đoán góc thứ tư, không sinh chữ hay khôi phục homography đủ
thẻ. Nếu các cạnh chính xác và card lồi, vùng nhìn thấy của card nằm trong
giao này: đây là tính chất hình học cơ bản, không phải định lý mới hoặc bảo
đảm khi neural dự đoán sai. Bản padded thêm nửa đường chéo heatmap cell.

Kết quả trung bình năm split, trên cùng 700 ảnh:

| Policy | Vùng đưa tiếp (%) | Mất vùng chữ/all frame (%) | Utility đưa tiếp (%) |
|---|---:|---:|---:|
| Neural gốc | 70.62 | .095 | 69.19 |
| Triangle ba góc | 84.29 | 13.762 | 69.19 |
| Hoàn thành hình bình hành | 84.29 | 2.619 | 73.71 |
| Observed-side support | 84.29 | .095 | 69.19 |
| Support padded | 84.29 | .095 | 69.33 |
| Full-frame ba góc, control thêm sau kết quả | 84.29 | .095 | 69.19 |
| Hình bình hành +5%, control thêm sau kết quả | 84.29 | .619 | 79.76 |
| Hình bình hành +10%, control thêm sau kết quả | 84.29 | .333 | 69.71 |

Ba control cuối là **post-hoc**, không được mô tả như đã preregistered.
Full-frame control cố ý cho phép chuyển nguyên frame của ca ba góc đi tiếp,
nên override gate .95 ở đúng ca đó; bảng phải giữ rõ khác biệt gate này.

Gain coverage của support so neural gốc là **+13.67 điểm %** trung bình;
seed13 là +13.81, bootstrap CI [10.24;17.38]. Tuy nhiên full-frame control
cũng có đúng gain đó. Vì vậy không quy riêng gain coverage cho crop mới.
Không có gain utility rõ của support; parallelogram+5% đạt utility cao hơn
nhưng có thêm một số lỗi cắt vùng chữ. Đã giữ tất cả baseline trong bảng.

Trong **58 ca ba góc ở test seed13**, full-frame có mean crop/visible-card
area=3.915, support=2.059, triangle=.484 và hình bình hành=.961. Support không
ghi nhận lỗi cắt chữ trên 58 ca này; hình bình hành có 13 ca, triangle có 58 ca.
Đây là lợi ích giữ nội dung trong vùng ít nền hơn full-frame. **Không gọi giảm
diện tích polygon là tăng tốc OCR**, vì bounding box và pipeline OCR thật chưa
được đo. Các ca này vẫn chưa có phép nắn phẳng đủ card.

Ngoài MIDV-2020, support chuyển tiếp 19/20 ca, không ghi nhận harm trên 19 ca,
utility 16/20. Full-frame control và một số control đơn giản cũng đạt kết quả
tương tự; chỉ một ca ngoài được cứu nên chưa có bằng chứng generalization mạnh.

Prior gần về giấy tờ thiếu biên gồm [IRI 2022](https://web.ntpu.edu.tw/~myday/doc/IRI2022/IEEE_IRI2022_Proceedings/pdfs/IRI2022-2biJIxjybiQ3DOmA6IkB2x/660300a262/660300a262.pdf)
và [ICASSP 2025](https://doi.org/10.1109/ICASSP49660.2025.10889411). Chưa đủ để
tuyên bố thuật toán đầu tiên cho missing corners. Giá trị còn phải chứng minh
là ích lợi OCR/KIE khi bảo toàn phần quan sát được với chi phí thấp.

## 9. Mức sẵn sàng cho CORE B và hướng đi tiếp

| Tiêu chí | Đánh giá có bằng chứng |
|---|---|
| Code nhỏ, chạy CPU, dễ triển khai | Đạt về thử nghiệm hình học; chưa tích hợp vào sản phẩm |
| Minh bạch/tái lập | Có protocol theo thời điểm, seed, hashes, raw metrics, kiểm tra tái lập và kết quả âm |
| Ý nghĩa vấn đề | Có: cắt mất thông tin và sai số do frame tương quan là vấn đề thực tế |
| Lợi ích phương pháp | Hỗn hợp; giữ chữ tốt hơn nhưng IoU/throughput/utility có thể giảm |
| Điểm mới thuật toán | Chưa đủ: phần lớn thành phần có tiền lệ gần |
| So sánh neural mạnh | Đã có DocAligner trên cùng 700 ảnh và 20 ảnh ngoài; còn thiếu đối chiếu SOTA/adapter và provenance train |
| OCR/KIE end-to-end | Đã đo OCR với predicted boxes trên161 ảnh + panel lặp; support thua baseline completion về mô tả accuracy/CPU; semantic KIE chưa đo |
| Kiểm chứng ngoài | Đã chạy 20 ID mới, nhưng chỉ hai điều kiện và template trùng; còn quá nhỏ |
| PAD/liveness/face matching | Nằm ngoài giả thuyết nghiên cứu này; không có đánh giá PAD mới |

Hướng dễ và nhanh nhất để tiến thêm là giữ bài ở phạm vi document processing,
không gom cả quality/OCR/PAD thành ba thuật toán mới. Tên làm việc phù hợp:
**“Content-preserving document crops under boundary uncertainty: evaluating
risk and automatic-processing coverage in mobile capture.”**

Các mốc còn cần trước khi viết lời khẳng định mạnh trong paper:

1. **Baseline/provenance:** xác minh adapter với package tác giả và lịch sử
   train; bổ sung một model khác và so sánh với incomplete-boundary methods.
   Không gắn nhãn SOTA chỉ vì đã có neural network.
2. **Sau benchmark OCR đã hoàn tất:** support chưa vượt parallelogram+5%.
   Tìm nhóm lỗi cụ thể của baseline này, dùng tập development khác để phát
   triển selector/refinement nếu có cơ sở, rồi khóa trên ID mới. Giữ cả raw,
   full-frame ba góc, bbox và completion trong so sánh. Không tune trên test
   cũ rồi gọi test cũ là xác nhận độc lập.
3. **Test ngoài đủ lớn và OCR thật:** tăng số ID/camera/điều kiện, có GT text,
   báo cáo CER, field exact match, ID-number exact match, recapture/review và
   latency. Dùng đủ ít nhất hai OCR reader phù hợp ngôn ngữ.
4. **Quyết định viết/nộp:** chỉ đưa ra claim nếu đóng góp mới phân biệt được
   với Timans/TriCCOT/CRC và lợi ích tồn tại khi đối chiếu baseline mạnh.
   Nếu không, công bố kết quả âm/benchmark đúng phạm vi hoặc đổi giả thuyết;
   không đặt acronym mới để thay cho đóng góp.

Nơi ưu tiên là **ACM DocEng**, hạng B theo [ICORE2026 chính thức](https://portal.core.edu.au/conf-ranks/2003/),
phù hợp document workflow/evaluation. [DocEng 2027](https://doceng.org/doceng2027)
diễn ra 24–27/08/2027 tại Calgary; trang chính thức chưa công bố deadline nộp
khi kiểm tra. ICPR và ICIP là lựa chọn khác trong literature review, nhưng
cần kiểm tra đúng kỳ/track. Không bảo đảm được nhận chỉ từ hạng hội nghị.

## 10. Các file để kiểm tra độc lập

- [Báo cáo OCR đầu cuối30/10](E2E_RESULTS_VI.md),
  [mọi hàng OCR](results/e2e_ocr_v2/per_image.jsonl.gz),
  [audit độc lập](results/e2e_ocr_v2/audit.json),
  [chạy lặp thật](results/e2e_ocr_v2/repeat_audit.json).

- [Protocol v1](PROTOCOL.md), [OCR phụ](SECONDARY_OCR_PROTOCOL.md),
  [protocol v2](RISK_POLICY_PROTOCOL.md), [protocol ngoài](EXTERNAL_PROTOCOL.md).
- [Kết quả v1 mọi seed](results/feasibility_v1/summary.csv),
  [mọi hàng v1](results/feasibility_v1/per_image.jsonl.gz).
- [Kết quả v2 mọi seed/stratum](results/risk_policy_v2/summary.csv),
  [lambda và split](results/risk_policy_v2/choices.json),
  [mọi hàng v2](results/risk_policy_v2/per_image.jsonl.gz).
- [Kết quả OCR](results/ocr_diagnostic/summary.json),
  [bootstrap OCR](results/evidence/ocr_paired_bootstrap.json).
- [Kiểm tra chạy lại phân tích](results/evidence/analysis_repeat.json),
  [chạy lại inference](results/reproducibility/inference_repeat.json),
  [test XML](results/evidence/tests.xml), [môi trường](results/evidence/environment.json).
- [Biểu đồ diện tích/giữ chữ](results/evidence/primary_tradeoff.png),
  [biểu đồ coverage/lỗi](results/evidence/risk_policy_tradeoff.png).
- [Ngoài MIDV-2020](results/external_midv2020/summary.json),
  [neural cùng ảnh](results/neural_baseline/summary.json),
  [partial-support](results/partial_support_v3/summary.json),
  [control post-hoc](results/posthoc_controls/summary.json).
