# Tính độc lập của oracle

| Thành phần | Đường chấm và nguy cơ chung | Bằng chứng độc lập cần có |
|---|---|---|
| Giá trị và precision | A đi qua `oracle.evaluate` và `contracts.evaluate`. B3 có wrapper riêng nhưng dùng cùng `contracts.assessment` cho trường còn nguồn. Cùng canonicalization và date precision. A_flat gọi B3 trực tiếp rồi thêm tiền điều kiện. Không có threshold confidence để giải thích kết quả | Chữ người đọc thực sự quan sát, kiểm nghĩa trường, đối chiếu output ẩn danh sau khi khóa pha 1 |
| Availability và semantic link | A/B3 dùng chung after graph và ValidationReport. Cùng `Field.state` và `supported_sources`. Một vùng chưa được annotate có thể còn chữ. MRZ có glyph không bảo đảm đúng checksum hay đúng nghĩa | Xem cả ảnh, ghi vị trí nguồn chưa khai báo, ghi khả năng đọc riêng. Kiểm checksum trên dòng người đọc chép khi dùng TD3 |
| Quan hệ biến đổi | B3 gắn kết luận với ảnh sau. A yêu cầu ảnh gốc đúng cho C3/C4. 42 lượt bất định của A đều từ điều kiện này. Điểm khác biệt về scope, không phải 42 nhãn GT độc lập | Hai endpoint pointwise và relation dùng cùng bằng chứng. Kiểm nguồn B và ngữ cảnh trên cả cặp ảnh |
| B3 legacy | V3 dùng mã visibility/score riêng và logic OR đã có. Adapter vẫn nhận cùng inventory do tác giả tạo. Gated V3 chia sẻ gate | So với V3 có cùng gate và A_flat, ghi cả lỗi cùng bỏ sót và ca chưa kết luận |
| Truy vết và gốc lỗi | Reader cache và binding được kiểm hash. Hai phương pháp chấm đầu ra đã chuẩn hóa nên không thể gán sai số cho reader, crop, rectifier hay parser chỉ từ sai field | Giữ nhóm hành vi, version quad cùng pixel và chứng cứ activation hoặc patch/revert trước khi gán lỗi phần mềm |

[Matcher dùng chung](contracts.py#L94) · [Oracle A](oracle.py#L166) · [Checker B3 và ablation](task5/baselines.py#L117) · [Scorer V3](../v3_metrics.py#L39)

Một control trong bộ test thay kết quả của `contracts.assessment` thành luôn “correct” trong bộ nhớ, rồi dùng cùng cặp ảnh và output B cố ý sai. Cả A và B3 chuyển từ cảnh báo sang PASS. Chữ và ngữ cảnh B được đối chiếu pixel theo fixture, còn giá trị sai được ấn định trước từ control. Kết quả cho thấy sự đồng thuận có thể che lỗi trong dependency dùng chung. Control chỉ kiểm thử tester. Không có thay đổi trên file matcher, model hay production. [Control results](execution/task55_recovery/controlled_results.json)

Một điểm cần phân biệt trong đặc tả. TASK 3 trả INCONCLUSIVE khi scope nguồn không đủ chứng minh. Wrapper TASK 4 có nhánh triage trả CANDIDATE_VIOLATION khi mọi nguồn **đã khai báo** bị xóa và output vẫn khẳng định giá trị, kể cả khi scope chưa đầy đủ. Đây là khác biệt giữa trạng thái tiền điều kiện và báo động sàng lọc. IFV giữ trạng thái chưa đủ chứng cứ trừ khi có xác minh độc lập; nếu chứng minh nguồn hợp lệ còn tồn tại thì đánh giá quan hệ C1 là invalid và báo riêng cảnh báo trên ca invalid. [Nhánh triage](oracle.py#L226) · [IFV](INDEPENDENT_ORACLE_REVIEW.md)

## Đối chiếu prior work

- GenMorph đã đặt bài toán sinh và lọc quan hệ metamorphic theo false positive và false negative, có bước kiểm candidate bằng dữ liệu thực thi. Dùng mutation hoặc đo lỗi oracle tự thân không tạo novelty. Điểm có thể kiểm chứng ở đây là tính hợp lệ của quan hệ khi chữ nhìn thấy, nguồn thay thế và ngữ cảnh semantic thay đổi. [GenMorph, mục III và VII](https://arxiv.org/html/2312.15302v3)
- VeriOCRBench đã dùng visual evidence để kiểm task còn thực hiện được, audit bởi nhóm người của dự án và đo hành vi từ chối. Kiểm bằng chứng khả kiến và tỷ lệ bỏ sót do từ chối đã có tiền lệ. IFV ở đây đánh giá **tester và lỗi của pipeline**, với baseline và nguồn lỗi tách riêng. [VeriOCRBench, mục 3 và phụ lục D.2](https://arxiv.org/html/2609.00232v1)
- LMDX liên kết output với vùng OCR để đo extraction/localization. Một source ID hoặc bbox trong graph là hạ tầng có tiền lệ. Giá trị nghiên cứu cần được đo ở nguồn không đầy đủ, báo động trên phép biến đổi không hợp lệ hoặc triage liên stage có chứng cứ. [LMDX, phương pháp và đánh giá](https://aclanthology.org/2024.findings-acl.899.pdf)

Blindness chỉ được kiểm ở artifact. Người chấm có thể nhận ra ảnh đã thấy, phép che hoặc nội dung lặp. Phiếu ghi exposure; reviewer code tự khai chưa chứng minh người độc lập. Kết quả một người chỉ là đối chiếu pilot chưa adjudicate. [Trạng thái IFV](IFV_REVIEW_STATUS.md)
