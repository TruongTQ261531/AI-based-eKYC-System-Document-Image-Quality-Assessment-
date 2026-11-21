# P6.1 · Tái sử dụng ảnh và lineage của checkpoint

**Kết luận: 24/24 nhóm P2 được xác nhận tái sử dụng giữa các collection. Cả 24 xuất hiện trong chuỗi huấn luyện của từng adapter trong 12 adapter LoRA đã kiểm. Số nhóm được xác nhận đi qua cả train và evaluation của cùng checkpoint trong các phép đối chiếu đã định là 0.** Thành phần pretraining của các reader và mô hình hình học bên ngoài vẫn là `UNKNOWN_LINEAGE` với cả 24 nhóm. Giữ `GO_PREPARATORY_ONLY` và `NO_GO_SUPERIORITY`. [Aggregate và liên kết từng checkpoint với evaluation](execution/master_01/p6_integrity_20261121/aggregate.json)

## Nhóm nào đã được dùng ở đâu?

| Split Recovery V4 | Nhóm exact pixel | Vai trò đối với selector V4 | Kết quả đối chiếu với checkpoint LoRA |
|---|---:|---|---|
| Test | 10 | Ngoài ID và pixel của tập fit và calibration | Cả 10 vào train của từng adapter. V4 đánh giá bằng RapidOCR. |
| Development | 8 | ID và ảnh thuộc tập fit của selector | Cả 8 vào train của từng adapter. Điểm dev của selector là trong tập phát triển. |
| Calibration | 6 | Dùng đặt ngưỡng review của selector | Cả 6 vào train của từng adapter. Một nhóm cũng xuất hiện trên panel legacy và online. |

24 nhóm là **24 physical ID** đã ghi, tất cả thuộc nguồn MIDV dẫn xuất của V4. Verifier đã đọc lại 144 tệp thành viên, so SHA-256 của byte và tính lại SHA-256 trên RGB sau chuẩn hóa hướng EXIF, có cả kích thước trong tiền tố hash. Mọi nhóm có ít nhất một liên kết tới byte của tệp cha. Quan hệ cha, cùng ID, gần trùng theo dHash và trùng chính xác pixel được giữ riêng. Đồng nhất physical ID chỉ dựa trên metadata có ràng buộc trong các manifest đã xét. [P2](P2_AUDIT_VI.md) · [Kiểm chứng độc lập](execution/master_01/p6_integrity_20261121/verification.json)

## Quy tắc và mẫu số

| Trạng thái cho câu hỏi chính trên 24 nhóm | Nhóm | Quy tắc |
|---|---:|---|
| `CONFIRMED_SAME_CHECKPOINT_OVERLAP` | 0 | Cần thành viên train có bằng chứng, pixel đánh giá khớp, output thực trên split và hash checkpoint trùng. |
| `RECORDED_CROSS_COLLECTION_REUSE` | 24 | Pixel và chuỗi train khớp, reader thực của V4 khác các adapter đã đối chiếu. |
| `NO_OVERLAP_VERIFIED` | 0 | Chỉ dùng cho một checkpoint và frame cụ thể khi danh sách train đầy đủ cho phép loại trừ thành viên đã đánh giá. |
| `UNKNOWN_LINEAGE` | 0 | Ở cấp kết luận chính, cả 24 đã có bằng chứng dương cho reuse. Với câu hỏi riêng “đã vào pretraining của reader ngoài hay chưa?”, **24/24 UNKNOWN**. |
| `OUT_OF_SCOPE` | 0 | Không nhóm P2 nào bị loại. Các probe phát triển V2 nằm ngoài câu hỏi về reader của phép đo chính V4. |

Kết quả âm có phạm vi hẹp hơn. Trong 540 ca V4, 40 ID development, 30 calibration và 80 test tách nhau theo mã ID và pixel trong snapshot P2. Danh sách ID fit của cả hai selector khớp đúng tập development. Trong 44 bảng development/test của các adapter nội bộ, số nhóm trong 24 ứng viên xuất hiện ở phần evaluation bằng 0, kể cả khi tra theo mã physical ID đã ghi. Các phép kiểm này không xác lập tính độc lập với corpus bên ngoài hoặc với các benchmark chưa được nối.

## Checkpoint, version và thời gian

| Họ | Bằng chứng đã đọc | Kết luận |
|---|---|---|
| Recovery V4 | Manifest và chữ ký run, SHA mã nguồn, SHA detector/recognizer, SHA selector lock, manifest 540 ảnh, 24 receipt pass 1 cùng journal và seal từng receipt | Engine thực là `rapid_v4` và `rapid_latin_v5`. Hai engine chia sẻ detector PP-OCRv4. Đã kiểm FastViT-SA24 và LCNet100 ở vai trò hình học. |
| Selector downstream | Artifact selector, chữ ký inference chung, danh sách ID fit của từng reader, code fit development và chọn ngưỡng calibration | Đây là thành phần học nội bộ. 8 nhóm đi vào fit theo thiết kế, 6 đi vào calibration. 10 nhóm test tách khỏi cả hai split. |
| VLM V2 / V2-R2 | Manifest hai phiên bản, hồ sơ probe V2, card và hash samples R2, logs control/partial cho seed 42 và 31415 | Bốn adapter R2 tại step 320. R2 ghi hash thứ tự ID/slot và hash toàn bộ dataset. Việc nối đến file dùng slot duy nhất trong dataset đã seal. |
| Source-visibility, hard-pairs, fair-controls | 2 adapter source, 2 hard, 4 random/repeat. Hash adapter, config, training state, signature, cursor, 320 sự kiện và thứ tự raster/ID/slot | Mỗi run có 1.280 lượt trình ảnh. 24 nhóm đóng góp 48 lượt/run. Các alias uniform/hard tái dùng đúng trọng số ở study sau được nối theo digest. |
| Vintern gốc và V1 nhập lại | Vintern-1B-v3_5 theo revision đã khóa, hash tệp trọng số, adapter V1 seed 42 step 192 và checkpoint đã chọn | Kiểm 8 bảng evaluation bổ sung của original/V1 trong R2 và source-visibility. Không nhóm mục tiêu nào nằm trong các bảng này. Tập fit nội bộ của V1 không có 24 pixel mục tiêu. Corpus pretraining nền vẫn thiếu membership. |
| Legacy / online | Manifest CRAFT, EasyOCR, VietOCR, trọng số thực, các hàng legacy và trace có seal selector | Có **1 nhóm calibration** ở cả hai panel, gồm 6 trace online. Đây không phải 6 giấy tờ mới. Panel legacy chỉ có 24 ảnh. |

Lượt inference chính của V4 diễn ra **30/10/2026, 16:12:15–17:59:59 UTC**. Sự kiện train của 12 run nằm từ **01/11/2026 12:16:52 đến 03/11/2026 10:50:28 UTC**. Thứ tự này củng cố liên kết từ hash và engine. Manifest phân biệt thời gian sự kiện, thời gian commit chứa phiên bản sau cùng và mtime của bản sao cục bộ. Mtime có thể đổi khi sao chép. [Manifest nguồn và phiên bản Git](execution/master_01/p6_integrity_20261121/manifest.json)

## Ảnh hưởng tới benchmark

Các số V4 cũ vẫn là kết quả lịch sử của hai reader đã ghi, gồm kết quả âm của cascade so với completion. Các study LoRA sau này đã dùng 10 pixel thuộc test V4 để huấn luyện. Nếu đem một trong 12 adapter đó đo lại trên test V4 cũ, 10 nhóm này sẽ là **dữ liệu đã dùng để fit**. Không có phép đo như vậy trong 24 receipt V4 đã kiểm. Kết quả benchmark nội bộ của adapter phải được diễn giải trên split riêng của nó. P6 không đo chênh lệch accuracy do exposure và không sửa các con số trước đây.

Muốn so sánh checkpoint mới trong tương lai, cần một amendment riêng ấn định hash đầy đủ của base, adapter và selector, đối chiếu membership train theo ID/pixel/cha trước khi khóa test, nêu rõ giới hạn pretraining ngoài và quyền của từng phiên bản dữ liệu. Hiện chỉ tiếp tục mô tả D4 trên bằng chứng đã có. [Ma trận claim](P6_CLAIM_TO_EVIDENCE_MATRIX.md) · [Lệnh chạy lại và giới hạn](execution/master_01/p6_integrity_20261121/REPLAY.md)
