# C2-37 · Ảnh chụp trạng thái runtime ngày 24/11/2026

Bản kiểm chỉ đọc trên baseline `9e1a3a15be4b397a38c994136b3fe462257b5260`. Kết quả cache lịch sử đã có trong preflight. Mục mới của đợt này là tình trạng tệp và môi trường hiện tại trên máy organizer. [Preflight cache](C2_37_OCR_CACHE_PREFLIGHT_VI.md) · [Đánh giá ngày 24/11](C2_37_CACHE_AUDIT_EVALUATION_20261124_VI.md)

| Phạm vi | Trạng thái và bằng chứng |
|---|---|
| Full-frame C2-37 | `READY_FILES_PRESENT`. 18 ảnh before và 27 ảnh after trong mỗi workspace khớp SHA-256 của queue và manifest. Hai digest manifest khớp aggregate công khai. Chỉ đọc byte để băm. |
| Frozen RapidOCR | `READY_FILES_PRESENT` cho PP-OCRv4 và Latin PP-OCRv5 recognizer dùng detector/classifier v4, cả hai dùng RapidOCR ONNX 1.4.4 trên CPU, profile `rect2`, detector max 960, hai host threads. Preflight file/spec không tải model. Model digest, code digest và cấu hình khớp spec lịch sử của cả hai reader. Fingerprint runtime hiện tại khác đúng trường platform. |
| Frozen Vintern | `READY_FILES_PRESENT` cho Vintern-1B-v3_5 ở revision đã ghim, adapter `partial_42` tại step 320, profile `rect2`, seed 42, giới hạn 384 token, hai host threads. Đủ 18/18 tệp đã liệt kê. Hash manifest nền, adapter và cấu hình adapter khớp. Dùng kiểm byte trọng số nền và các tệp đi kèm đã ghi ở preflight 23/11. Chưa xác nhận fingerprint CUDA hiện hành của reader. |
| Máy organizer | Python 3.11.4. Metadata môi trường ghi PyTorch 2.7.1+cu126 và ONNX Runtime 1.24.4. NVIDIA-SMI thấy RTX 3050 Laptop GPU, 6.144 MiB VRAM, 4.745 MiB còn trống tại lúc đo, driver 591.66 báo hỗ trợ CUDA 13.1. CUDA 13.1 là mức driver báo, còn `cu126` là bản build của PyTorch. Số đo chỉ phản ánh trạng thái thiết bị. |

`MISSING_FILES` không ghi nhận trong các tệp đã kiểm theo các manifest trên. `PROVENANCE_UNCERTAIN` vẫn áp dụng cho liên kết runtime/weights theo từng output RapidOCR lịch sử của V2 r2/V3. Snapshot hiện tại chưa cung cấp cặp before/after và chưa kiểm khả năng chạy thực tế của Vintern.

**`NOT_AUTHORIZED_TO_RUN`** cho C2-37. D10 `REVIEW_ACCESS_PENDING`, `RETENTION_PENDING`, `RELEASE_PENDING`. Scientific gate `GO_PREPARATORY_ONLY`, `NO_GO_SUPERIORITY`, P5B `INFEASIBLE`, TASK 6B/7B `BLOCKED`. [D10 C2-37](C2_37_D10_VI.md)
