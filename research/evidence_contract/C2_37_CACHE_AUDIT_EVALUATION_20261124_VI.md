# C2-37 OCR cache — Đánh giá độc lập trên các bằng chứng công khai · 24/11/2026

**Phạm vi kiểm tra:** hai commit mới `8ab565712022f30bc98d8db0d46cfb1dc96e618b` và `d3c1d1ff5faaa92c555c9f5b76237afe7cc1928a`. Cả hai chỉ sửa `C2_37_OCR_CACHE_PREFLIGHT_VI.md`, không cung cấp bản ghi OCR raw hoặc verifier máy-local mới trong GitHub. Phân tích dưới đây đối chiếu nội dung/diff công khai; **không** tuyên bố đã độc lập băm lại input/output/chữ ký từ các private artifact.

## 1. Kết luận

- C2-37: **0/37 candidate, 0/18 ID** có cặp before/after đã xác minh với **cùng** reader/checkpoint/config trong những cache đã rà soát. `CACHE_AVAILABLE_PARTIAL` là kết luận phù hợp; không suy ra mô hình thất bại hoặc đã có C2 endpoint.
- Phân nhóm hợp qua reader: `AFTER_ONLY=19`, `BEFORE_ONLY=2`, `NEITHER=16`, `BOTH=0`. Tổng = 37. Các con số gộp **không** chứng minh có một reader đơn lẻ bao phủ 21 ca.
- `13/45` ảnh full-frame phân biệt được xác minh đầu ra ở ít nhất một cấu hình; `45=18 original+27 derived`, `13/45≈28,9%`. 155 asset/gói còn gồm 110 crop; đừng nhầm ảnh/crop với output OCR hoặc candidate độc lập.
- 172 dòng cache đã xác minh theo báo cáo gồm 112 Vintern và 60 E2E policy rows. Trong Vintern có 12 bản ghi tái sử dụng nối được với record gốc; E2E v1/v2 12+48 dòng quy về 4+16 khóa lịch sử theo UID/repeat/reader/raster. **Không** tính 172 như 172 suy luận độc lập, sample size, approved reference hoặc paired comparison.
- RapidOCR v4/Latin v5: một số byte ảnh after và output digest đã đối chiếu, nhưng ràng buộc runtime/weights **theo từng output** chưa đủ; giữ 19 AMBIGUOUS ở mỗi cấu hình, không nhập vào nhóm exact bound. Có 22 bản ghi V2 r2 và 66 V3 được báo kiểm, nhưng nhiều V3 dùng chung raw OCR; không nhân số ca.

## 2. Đánh giá từng commit

**8ab5657 — đạt mục đích preflight.** Đã kiểm queue/aggregate private so receipt public, đọc các nguồn cache được chỉ định, đưa ra phân loại theo reader và chỉ rõ không có pair. Điểm mạnh: byte hash/model signature chặt và không bịa kết quả. Điểm chưa đủ: kết luận phụ thuộc dữ liệu local; tài liệu public là báo cáo, không phải một phép xác minh độc lập có thể chạy chỉ với GitHub.

**d3c1d1f — bổ sung cần thiết.** Nêu rõ hai tập SHA ảnh before/after rời nhau, mapping UID E2E, model/checkpoint/code/config locks và output digest, đồng thời tách reused records khỏi nguồn. Điều này cải thiện traceability nhưng **không** thay đổi `0/37`, không sửa code/reader, không thêm model calls và không xóa blocker.

## 3. Tác động thực nghiệm và định hướng

1. Không thể dùng cache hiện có để ước lượng FAR/sensitivity/coverage trên cặp before/after C2-37 theo protocol; truth độc lập và reference được duyệt vẫn bằng 0.
2. Không thể gộp after Vintern và before EasyOCR/VietOCR thành cùng một paired arm; cùng image SHA không đồng nghĩa cùng decoder/profile/checkpoint.
3. Không mở inference mới lúc này: `D10_REVIEW_ACCESS_PENDING`, Round1 production authority và scientific `GO_PREPARATORY_ONLY/NO_GO_SUPERIORITY` vẫn phải được giải quyết.
4. Từ GitHub, ChatGPT có thể viết fixture-only paired analysis, missing-data flow, sample/cluster accounting, manuscript limitations và claim-to-evidence updates mà không sử dụng Codex.
5. Việc bổ sung 8 ca Hy Lạp **không** giải quyết bản chất cache đang thiếu cặp và không nên được kích hoạt vì muốn tăng cỡ mẫu sau khi thấy kết quả.

## 4. Tác vụ local cực nhỏ nếu còn 2% Codex (tùy chọn, không bắt buộc)

Chỉ làm **read-only runtime availability snapshot**: xác nhận máy có thể nhìn thấy 18 original và 27 derived của C2-37 theo `queue.json` và SHA-256 đã ghim; GPU/device/driver bằng lệnh status đơn giản (nếu có); sự hiện diện và danh tính file của **frozen reader/checkpoint/config** dự kiến dùng trong protocol (chỉ từ manifest đã biết). **Không** khởi tạo model, không infer, không train, không scan toàn disk, không thay quyền/protocol, không chạy full tests. Đầu ra local có thể liệt kê các artifact; bản GitHub chỉ có số đếm và trạng thái tổng hợp, thiếu cặp/missing prerequisites; nếu repo đã có đủ bằng chứng này thì báo `ALREADY_DOCUMENTED` và dừng ngay.

Ưu tiên **GPT-6 Luna · Low · Standard** nếu model đó xuất hiện trong Codex, vì task là kiểm tồn tại/hash và tổng hợp ngắn; dự phòng **GPT-6.2 Sol · Low**. Model/cấu hình không bảo đảm mức tiêu hao cụ thể; 2% có thể không đủ một lượt dài. Tránh Astra, subagents, ultrafast, refactor, training và các tác vụ không cần local.

## 5. Trạng thái sau đánh giá

`PREPARED_TECHNICAL_37` giữ nguyên; `REVIEW_ACCESS_PENDING`, `RETENTION_PENDING`, `RELEASE_PENDING`; 0/37 approved reference; `GO_PREPARATORY_ONLY`, `NO_GO_SUPERIORITY`, P5B `INFEASIBLE`, TASK 6B/7B `BLOCKED`. Đây là milestone **diagnostic**: đã giảm bất định về dữ liệu/cache nhưng chưa tăng số ca phân tích khoa học hợp lệ.
