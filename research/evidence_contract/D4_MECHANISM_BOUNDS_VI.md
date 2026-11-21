# D4 · Chuyển trạng thái và giới hạn của giảm FAR

**Ở endpoint pointwise của v3, D4 có thể rút lại một cảnh báo bằng cách trả UNKNOWN. Khi checked và asserted đều đưa ra kết luận nhị phân, hai arm luôn đưa ra cùng kết luận.** Chứng minh áp dụng cho adapter đã ghim hash, cùng payload hợp lệ để gọi hàm, cùng tier 1 hoặc 2, cùng thẩm quyền và reader. Tần suất ngoài thực tế và độ chính xác của reference vẫn chưa biết. [Adapter](oracle_reliability/mrz_ablation_v1.py) · [Policy đóng băng](oracle_reliability/policy.py)

## Ma trận asserted → checked

Số trong ô là số ca đã quan sát ở **tier 1 / tier 2**, mỗi tier có 72 ca dựng sẵn. Ký hiệu × là bất khả trong phạm vi vừa nêu, có lập luận từ mã bên dưới.

| Asserted ↓ / Checked → | FAULT | NO_FAULT | UNKNOWN | INVALID_TEST |
|---|---:|---:|---:|---:|
| FAULT | 23 / 8 | × | 6 / 6 | × |
| NO_FAULT | × | 5 / 2 | 2 / 2 | × |
| UNKNOWN | × | × | 31 / 49 | × |
| INVALID_TEST | × | × | × | 5 / 5 |

Cả sáu chuyển tiếp mà code cho phép đều có ví dụ trong controls, nên ở mức **cặp trạng thái** không còn ô “có thể nhưng chưa thấy”. Ở mức tổ hợp field, template, loại mutation, hỗ trợ nhiều nguồn và truth, vẫn có đầu vào chưa quan sát. Không có ước lượng tần suất tự nhiên nào từ 8 ca lệch hay 16 lần tính theo tier. Ba phản ví dụ nguồn cùng sai được giữ nguyên. [Kết quả frozen](execution/master_01/d4_development_20261117/controls_01/control_results.json) · [Divergences](execution/master_01/d4_development_20261117/controls_01/divergences.json)

1. Hai arm dùng cùng code object `evaluate`. Các nhánh INVALID_TEST do binding hoặc mutation, từ chối reference, kiểm cấu trúc và thẩm quyền đều dùng cùng dữ liệu. Chúng chạy trước `resolve`. INVALID_TEST chỉ có thể đồng thời trên cả hai arm.
2. Hai resolver chỉ khác cách gọi TD3 tại một điểm. Cả hai đều đòi đúng profile và giá trị khai báo canonical hợp lệ. Ở nhánh checked, literal phải tự kiểm thành công **và bằng giá trị khai báo**. Dù literal chứa giá trị khác có vẻ đúng, resolver đưa nguồn vào danh sách unresolved. Nó không thay giá trị khai báo bằng literal.
3. Nếu có bất cứ nguồn unresolved nào, resolver không trả SUPPORTED hay REMOVED, kể cả khi một nguồn body khác có vẻ đủ dùng. Nếu checked phân giải được thì mỗi nguồn được checked chấp nhận cũng được asserted chấp nhận, với cùng giá trị, cùng tập nguồn và grade. Nguồn REMOVED được xử lý trước phép kiểm literal. Xung đột nguồn ở asserted có thể khiến cả hai UNKNOWN. Guard inventory C1 dựa trên các ID dùng chung. Với cùng `after` và tier, một kết luận nhị phân checked do đó buộc asserted có cùng kết luận.
4. Một literal bị từ chối có thể làm asserted FAULT → checked UNKNOWN hoặc asserted NO_FAULT → checked UNKNOWN, tùy output của reader. Chuyển FAULT thành NO_FAULT để sửa trực tiếp quyết định nhị phân đòi một adapter khác. Kết luận này chỉ cho endpoint pointwise. Relation còn kiểm trước/sau và C2, còn structure có trạng thái riêng. Một ngoại lệ phần mềm hoặc cặp output bị thiếu phải dừng theo v3.

## Hệ quả với ba estimand

Gọi D là số ca, C là coverage checked, F và N là số ca có nhãn lỗi và không lỗi. Gọi H là số ca **trong N** có asserted FAULT và checked UNKNOWN. Khi N > 0, giảm FAR Δ = H/N. Tỷ lệ bất đồng *về báo động trên N* cũng bằng H/N vì không có chiều ngược. Asserted NO_FAULT → checked UNKNOWN có thể thay đổi quyết định mà không đổi báo động. Coverage asserted trừ coverage checked bằng tỷ lệ của **cả hai** loại chuyển tiếp trong D.

- H ≤ D(1−C), nên Δ ≤ min(1, D(1−C)/N). Cận có thể siết thêm bằng số checked UNKNOWN thay vì mọi ca hoãn, hoặc đếm UNKNOWN thực sự trong N. Khi đầy đủ truth và prevalence π, N/D = 1−π. Khi truth thiếu, N/D = P(nonfault **và có nhãn**). Dùng 1−π cho mẫu số chỉ đúng dưới điều kiện bổ sung thích hợp, ví dụ truth đầy đủ. Khi N = 0, Δ không xác định.
- Nếu K ca lỗi có nhãn mất cảnh báo vì checked hoãn thì sensitivity checked = sensitivity asserted − K/F khi F > 0. Khi đó H + K ≤ D(1−C). D4 không thể tăng phát hiện lỗi thật qua quyết định đảo chiều trên panel ghép này. Mức cải thiện FAR phụ thuộc vào **ca nào** bị hoãn. Với C = 1, H = 0; với C = 99,9% và 80% ca là nonfault có nhãn, Δ ≤ 0,125 điểm phần trăm.
- Có phân bố **hỗn hợp** đúng cơ chế với C = 88%, sensitivity = 94%, Δ = 10 điểm. Ví dụ trên nonfault, 10% ca chuyển từ FAULT thành UNKNOWN, trên fault 1,5% ca chuyển như vậy. 20% ca là lỗi, nhãn sẵn có ngẫu nhiên ở 90%. Phần còn lại vào các ô đã chứng minh, với 1% INVALID_TEST chung. Mọi ô, xác suất và truth nằm trong aggregate. Khi phần lớn panel chứa literal thực sự bị hỏng ở chính nguồn đang được dùng, tỷ lệ này có thể hoàn toàn khác.
- Ở cực kia, nếu **tất cả** ca đã qua guard chung và tác động trúng MRZ SUPPORTED của trường sau biến đổi, literal hỏng/thiếu/mismatch làm resolver checked UNKNOWN trên mọi ca. Coverage và sensitivity có nhãn bằng 0 dù asserted vẫn có thể báo động. Tăng ID không thể vượt hai ngưỡng. Tỷ lệ can thiệp thực sự chạm nguồn đang được dùng trong panel dự kiến của v3 là UNKNOWN. Mixture thuận lợi không phải mặc định cho panel được làm giàu bằng lỗi literal.

[Kiểm thử adapter và các cận](tests/test_p5b.py) · [Protocol về panel can thiệp](B_PROTOCOL_V3_20261121.md) · [Kết quả mô phỏng P5B](P5B_STATISTICAL_CALIBRATION_VI.md)
