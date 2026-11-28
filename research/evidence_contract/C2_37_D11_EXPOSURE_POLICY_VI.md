# Quyết định D11 cho C2-37 · 28/11/2026

Chủ dự án xác nhận chính sách trong trao đổi ngày 28/11/2026.
Trạng thái `OWNER_POLICY_ACCEPTED`. Hồ sơ này áp dụng cho
`C2_37_PROPOSED`, run `c2_37_20261123`, gồm 37 ca trên 18 giấy tờ.
[Protocol C2-37 đã khóa](C2_37_ANALYSIS_PROTOCOL_VI.md)

## Chính sách áp dụng

- Giữ nguyên các khai báo exposure và toàn bộ hồ sơ lịch sử. `EXPOSED`
  được dùng cho development hoặc mô tả phù hợp. `EXPOSURE_UNKNOWN` là
  tình trạng chưa xác định và không được tính là unseen.
- Ghi exposure theo từng candidate, nguồn, thời điểm trước/sau, physical ID
  và điều kiện trong protocol, gồm template, trường, mutation và precision.
  Ghi căn cứ kèm đúng phạm vi mà căn cứ đó hỗ trợ.
- Giữ nguyên thành viên của panel và bản gốc của phiếu. Kết quả bất lợi,
  mức đồng thuận thấp và prior exposure không phải căn cứ để chỉnh hay bỏ
  phiếu. Khi có quyền sử dụng, ghi trạng thái và mẫu số của từng strata,
  kể cả trường hợp thiếu chứng cứ.
- Tuyên bố về khả năng tổng quát hóa độc lập cần có bằng chứng phù hợp.
  Kết quả từ C2-37 phục vụ mô tả trên panel lịch sử.

## Cách ghi nhận và kết quả xác minh

Khi đối chiếu phiếu đã được cấp quyền sử dụng, giữ mã khai báo gốc ở cấp
người chấm và ca. Bảng dưới quy định cách đọc khi lập bảng tổng hợp.

| Mã khai báo trong phiếu | Trạng thái dùng khi tổng hợp |
|---|---|
| `PREVIOUSLY_SEEN` | `EXPOSED` theo khai báo của người chấm cho ca |
| `NO_KNOWN_EXPOSURE` | `EXPOSURE_UNKNOWN` |
| `UNCERTAIN` hoặc thiếu khai báo | `EXPOSURE_UNKNOWN`, giữ riêng lý do thiếu khi có |

Đã đối chiếu từng ca với queue niêm phong và hồ sơ lineage có hash. Cả
**18/18 physical ID** có bằng chứng xuất hiện trong nghiên cứu trước đây.
Đã ghi đủ **37 ca** và **148 bản ghi nguồn theo thời điểm**, gồm nguồn chính
và nguồn dự phòng ở hai phía. Trong đó 5 bản ghi thiếu crop nhưng vẫn có liên
kết với ảnh đầy đủ. Trạng thái exposure trực tiếp ở cấp ca và từng nguồn
trước/sau hiện là `EXPOSURE_UNKNOWN` trong phép đối chiếu này. Chứng cứ cấp
physical ID chỉ xác nhận lịch sử ở cấp giấy tờ. Nhật ký nguồn và ID được lưu
private. [Biên nhận xác minh](human_gate/receipts/c2_37_20261123/d11_owner_policy_20261128.json)

Phiếu R03 vẫn ở `CONTENT_VALIDATED_ONLY`. Kiểm tra lần này xác minh rằng
schema có trường khai báo exposure. Việc đối chiếu khai báo thực tế còn
chờ quyền sử dụng và thẩm quyền tương ứng. [Hồ sơ D10](C2_37_D10_VI.md)
· [Biên nhận R03](human_gate/receipts/c2_37_20261123/r03_return_20261128.json)

Trên máy organizer, chạy `python -B -m research.evidence_contract.human_gate.exposure37`
từ gốc repository để tái lập số đếm và digest của sổ exposure. Đối chiếu các
trường kỹ thuật với biên nhận. [Mã đối chiếu](human_gate/exposure37.py)
