# G04.5 · Kiểm toán tương thích C2-37 với D4 đóng băng

Ngày 28/11/2026, từ main `76a0f9194724b7204a5e90fc5c1b2034d778d114`. **0/37 ca có cặp body–MRZ tương thích với D4 ở đúng trường và precision đã khóa.** Cả 37 ca trên 18 giấy tờ vẫn thuộc panel mô tả nguồn C2. Hai dòng MRZ trong annotation của cả 37 ca qua được bộ kiểm literal TD3 khi gọi đúng profile gốc của D4. Kiểm tra đó chỉ xác nhận cú pháp, ngày và các check digit mà policy thực sự kiểm. [Receipt G04.5](human_gate/receipts/g04_5_20261128/compatibility.json) · [Protocol C2-37](C2_37_ANALYSIS_PROTOCOL_VI.md)

## Phạm vi và provenance

Kiểm trực tiếp SHA-256 của queue 37 có thứ tự và tệp selection với aggregate đã niêm phong; đối chiếu digest của hai manifest và hash byte của 155 asset trong mỗi bản. Nối từng candidate với acquisition qua **cả physical ID và SHA-256 ảnh trước**, đối chiếu code template, hash khối annotation VIA, chỉ mục region, native key, hai dòng MRZ theo thứ tự, field alias, precision và hash ảnh mẹ trước/sau. Chỉ trích annotation từ ba template đã tuyển. Hash khối annotation ràng buộc bản local đã dùng; không chứng thực toàn bộ archive upstream. So hash policy và adapter với manifest D4 gốc. Audit không mở phiếu, không dùng OCR, inference hoặc reference mới. [Mã audit](oracle_reliability/g04_5_compatibility.py) · [Aggregate C2-37](human_gate/receipts/c2_37_20261123/aggregate.json) · [Manifest D4](execution/master_01/d4_development_20261117/controls_01/manifest.json)

| Template | Identifier, ca/ID | Ngày sinh, ca/ID | Ngày hết hạn, ca/ID | Tổng ca/ID |
|---|---:|---:|---:|---:|
| Azerbaijan | 3/3 | 5/5 | 4/4 | 12/7 |
| Latvia | 4/4 | 4/4 | 3/3 | 11/4 |
| Serbia | 4/4 | 5/5 | 5/5 | 14/7 |
| Toàn panel | 11/11 | 14/14 | 12/12 | 37/18 |

Một ID có thể đóng góp nhiều trường. Mỗi ô đếm ID duy nhất bên trong ô.

## Phân loại ở trường và precision đã khóa

| Phân loại kỹ thuật chính (mỗi ca một dòng phân loại) | Ca | ID | Căn cứ |
|---|---:|---:|---|
| UNSUPPORTED_SOURCE_SLOT | 11 | 11 | Key và kind của identifier có chữ ký D4 hợp lệ. Nhưng cả 11 literal lấy từ ô **số giấy tờ** của TD3 đều khớp native `number` và khác native `id_number` mà queue chỉ định. |
| UNSUPPORTED_PRECISION | 26 | 16 | `birth_date → dob` và `expiry_date → expiry_date` có body ngày/tháng/năm bốn chữ số. Cả hai arm chỉ nhận MRZ `date_yymmdd` cho hai key này. |
| UNSUPPORTED_LITERAL_PROFILE | 0 | 0 | Không có trường hợp bị xếp nhóm chính do lỗi literal TD3. Kiểm riêng tại precision gốc thành công 37/18. |
| AMBIGUOUS_MAPPING | 0 | 0 | Metadata đủ để xác định region và chẩn đoán hai blocker trên. Sự tương đương ngữ nghĩa trong ảnh vẫn chờ người đánh giá. |
| STRUCTURALLY_COMPATIBLE | 0 | 0 | Không có cặp nào đồng thời khớp ô literal, trường và precision đã khóa. |

**Pending human evidence** là trục riêng. Tại snapshot đã khóa, 37 ca/18 ID chờ căn cứ người cho semantic/source; 0 ca/0 ID đủ điều kiện khoa học. Audit không cập nhật số phiếu nhận sau snapshot. Một phán quyết của assessor có thể xác định nguồn nào thật sự còn đọc được; nó không tự thêm profile mới vào policy. [Snapshot qualification](human_gate/receipts/c2_37_20261123/aggregate.json) · [Registry ánh xạ trường](oracle_reliability/semantic_registry.json)

- **Identifier.** 7 ca/7 ID có body trùng chính xác phần optional data sau bỏ filler cuối; 4/4 khác. Frozen D4 kiểm checksum optional nhưng chỉ **trích giá trị identifier từ ô số giấy tờ**. Không thay body bằng `number`, không dùng optional data làm fallback. Nếu đưa nhầm giá trị cá nhân vào metadata khai báo, bất đồng asserted/checked có thể phản ánh lỗi ghép nguồn của adapter.
- **Ngày.** Chỉ để chẩn đoán, chiếu ngày đầy đủ *xuống* YYMMDD rồi so ô TD3 đúng trường: khớp 25 ca/16 ID, khác 1 ca/1 ID. Cả 26 vẫn ở nhóm unsupported. Ngay cả khi sáu số trùng, thế kỷ trong MRZ vẫn UNKNOWN. Giữ nguyên literal và precision mỗi nguồn. Không áp dụng pivot tuổi, năm cấp, đồng hồ hệ thống hoặc century của body để điền vào MRZ. Một chuẩn hóa dấu phân cách có thể giữ nguyên bốn chữ số năm nhưng không giải quyết khác biệt precision.

## Mutation C2 và điều kiện can thiệp D4

Tính lại tỷ lệ pixel polygon bị cắt/che từ quad trước và transform của từng ca. 32 ca/15 ID dùng `value_mask`, 5 ca/4 ID dùng `field_clip`. Cả 37/18 có **100% footprint vùng chính** bị tác động và **0% footprint của từng dòng MRZ** bị tác động. Sau căn chỉnh tọa độ, so trực tiếp RGB bên trong hai polygon MRZ trên crop đã ràng buộc hash: cả hai dòng giữ nguyên pixel ở 37/18. Nếu so hash của cả crop chữ nhật, chỉ 32/15 có cả hai crop trùng byte; 5/3 có ít nhất một crop khác byte. Các nhóm theo hash crop và theo operator là hai phép đếm riêng. Khả năng đọc và ngữ cảnh vẫn cần phiếu.

Vì vậy C2 tạo tình huống mất vùng chính và giữ vùng dự phòng theo hình học. Audit tìm thấy **0 ca có mutation đổi pixel bên trong dòng MRZ**. Điều kiện phân biệt hai arm D4 phát sinh khi asserted chấp nhận khai báo có profile phù hợp nhưng checked bác literal hoặc bác sự khớp giá trị. Một literal, mapping hoặc khai báo đã có vấn đề trước biến đổi vẫn có thể làm hai arm khác nhau. Không gán bất đồng đó cho tác động làm hỏng MRZ của C2. Không có kết quả arm thực trên panel. [Giới hạn cơ chế D4](D4_MECHANISM_BOUNDS_VI.md)

## Hai endpoint và hướng bàn giao

**Pointwise tier 1** là endpoint chính đã khóa. Sau các gate chung, D4 đánh giá output sau biến đổi so với reference có căn cứ cho frame sau. **Relation C2** còn yêu cầu main được hỗ trợ trước và bị loại sau, cùng backup tồn tại ở cả hai phía và giá trị đã phân giải bằng nhau. Một control có pointwise FAULT nhưng relation UNKNOWN khi chưa chứng minh transition. Cần giữ riêng output thiếu, UNKNOWN của oracle, eligibility và truth độc lập. 0 ca tương thích không phải là 37 quyết định UNKNOWN đã đo. Coverage, FAR, sensitivity và chênh lệch hai arm trên ca thật chưa có số đo. [Policy](oracle_reliability/policy.py) · [Adapter hai arm](oracle_reliability/mrz_ablation_v1.py)

- **G03.5 có thể chuẩn bị không cần phiếu.** Sau review G04.5, xây adapter đọc queue/manifest ở chế độ chỉ đọc, khóa thứ tự, nguồn, template, field, precision, cụm ID và lý do không tương thích; kiểm bằng fixture tráo field, tráo frame, sai checkpoint và thiếu literal. Luôn xuất dòng chảy tuyển đủ 37/18. Tách số có đủ cặp output, số được phê duyệt, số đủ tám điều kiện và số có truth. Giữ metric chưa tính khi thiếu frame đúng thẩm quyền. G03 v2 chỉ là fixture và cách diễn giải qualified frame vẫn cần quyết định có ngày. [Handoff G03](G03_V2_HANDOFF_20261124_VI.md)
- **G07.** Thiết kế preflight rồi mới có lệnh chạy riêng có gate. Gắn byte ảnh và pixel digest từng phía với reader/version, checkpoint, config, preprocessing, runtime, digest output và provenance. Cho phép dùng lại đúng input trùng byte trong cùng cấu hình đã xác minh, song vẫn giữ nguyên từng candidate và cụm ID. Thiếu binding, quyền hoặc gate thì dừng trước model. Preflight trước ghi 0/37 cặp exact, và file có sẵn không cấp quyền chạy. [Kiểm toán cache](C2_37_OCR_CACHE_PREFLIGHT_VI.md) · [Readiness](C2_37_RUNTIME_READINESS_VI.md)
- **Quyết định precision.** Tiếp tục mô tả nguồn với precision nguyên gốc theo protocol hiện hành. Nếu muốn hỏi câu khác về phép chiếu YYMMDD, hoặc khai thác identifier trong optional data theo template, cần amendment có ngày, khai báo đã thấy chẩn đoán metadata 25/1 và 7/4, khóa mapping, frame, endpoint, quy tắc missing/abstention và phiên bản comparator trước khi đọc phiếu hay output. Kiểm riêng bằng controls và review độc lập. Giữ phân tích đó tách với D4 đóng băng; audit này không sửa protocol.

## Tái kiểm và trạng thái

Trên máy organizer, từ gốc repo chạy `python -B -m research.evidence_contract.oracle_reliability.g04_5_compatibility` để tái tạo nội dung JSON tổng hợp trên stdout. CI công khai chỉ cần fixture tổng hợp. Kiểm có mục tiêu qua pytest trên ba module G04.5, D4 comparator và G03 v2: **177 tests và 12 subtests đạt**, gồm 13 test mới. Các control kiểm trường nguồn, hai thế kỷ cùng YYMMDD, sai lịch/checksum/profile, pixel ngoài polygon, hai arm với MRZ nguyên/hỏng và pointwise khác relation. [Tests G04.5](tests/test_g04_5_compatibility.py) · [Receipt tổng hợp](human_gate/receipts/g04_5_20261128/compatibility.json)

Giữ D10 theo hồ sơ hiện hành, GO_PREPARATORY_ONLY, NO_GO_SUPERIORITY, P5B INFEASIBLE và TASK 6B/7B BLOCKED. G04.5 dừng tại bàn giao kỹ thuật để review.
