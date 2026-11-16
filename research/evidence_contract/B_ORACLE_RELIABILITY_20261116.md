# B mới: Oracle Reliability & Abstention — kết quả development

Ngày 16/11/2026. **P0 audit, P1 policy v2 và P2 evaluation/replay đã hoàn tất.**
B mới kiểm độ tin cậy của bộ quyết định đúng/sai và khả năng từ chối kết luận
khi thiếu căn cứ. Đây không phải B propagation cũ hoặc baseline B3.
`NO_GO_SUPERIORITY` vẫn giữ nguyên; không mở TASK 6B/7B.

Đã đọc toàn bộ handoff và 21 tài liệu nguồn, lưu hash trong
[intake](execution/master_01/oracle_reliability_20261116/p0_intake.json).
[Kế hoạch development](execution/master_01/oracle_reliability_20261116/development_plan.json)
được ghi trước lượt chạy; không gọi đây là preregistration cho dữ liệu mới.
P3 có kế hoạch vòng review còn mở; P4 có [protocol dự thảo](B_PROSPECTIVE_PROTOCOL_DRAFT.md)
và kiểm feasibility dữ liệu. P5 mới có [claim ledger riêng](paper/B_CLAIM_TO_EVIDENCE_20261116.md),
chưa viết/compile một paper B mới.

## Thay đổi đã thực hiện

[Policy v2](oracle_reliability/policy.py) ở namespace mới; frozen A, A_flat, B3
và prototype v1 không thay đổi. Ba kênh `pointwise`, `relation`, `structure`
trả riêng `FAULT`, `NO_FAULT`, `UNKNOWN`, `INVALID_TEST`, `STRUCTURAL_ERROR`.
`FAULT` là quyết định của oracle, chưa chứng minh lỗi phần mềm hay nguyên nhân.

| Phần | Hành vi v2 và giới hạn |
|---|---|
| Binding / trust | Kiểm hash nội dung, pixel trước/sau, field, mutation, schema, provenance; chặn bool dạng chuỗi và nguồn trùng. Reference constructed chỉ dùng cho output injected. External reference phải được duyệt đúng ID phiên bản; danh sách duyệt thực hiện đang rỗng |
| Inventory | Nguồn mâu thuẫn hoặc chưa rõ làm kết luận UNKNOWN. Inventory partial có thể hỗ trợ một nguồn đã biết, không đủ chứng minh toàn bộ nguồn đã mất |
| C1 | Kết luận mất toàn bộ cần inventory đầy đủ và cùng danh sách source ID trước/sau; bỏ record khỏi inventory không được tính là đã che nguồn |
| C2 | Nguồn chính phải có trước và bị loại sau; backup khác nguồn chính phải được hỗ trợ ở cả hai ảnh và cùng giá trị semantic. Nguồn mới xuất hiện sau mutation không được coi là backup còn sống |
| C3 / C4 | Giữ riêng kết luận trường và quan hệ. Original sai hoặc không kiểm được không đủ căn cứ cho quan hệ; wrong→correct không bị gọi là lỗi quan hệ. C4 chỉ hỗ trợ identity/translate_pad trong phiên bản này |
| Typed values | NFC/casefold/space cho text; ID giữ phân biệt O/0; full date và YYMMDD khác precision. `000229` chưa biết century nên UNKNOWN |
| MRZ TD3 | Tính lại checksum 7/3/1 từ hai dòng literal và đối chiếu đúng field/value. Chỉ hỗ trợ số hộ chiếu thông thường, DOB và expiry ở độ chính xác YYMMDD; không dùng checksum để xác nhận tên hoặc suy ra century |
| Structure | Dùng cờ usable của normalizer đã đóng băng. Không gọi đây là bộ kiểm JSON nghiêm ngặt độc lập hoặc nhãn semantic từ con người |

MRZ triển khai một tập con bảo thủ theo [ICAO Part 3, §4.8–4.9](https://www.icao.int/sites/default/files/publications/DocSeries/9303_p3_cons_en.pdf)
và [Part 4, §4.2.4](https://www.icao.int/sites/default/files/publications/DocSeries/9303_p4_cons_en.pdf).
Không hỗ trợ TD1/TD2, số hộ chiếu mở rộng hoặc mọi cách viết hợp lệ của chuẩn;
trường hợp ngoài phạm vi trả UNKNOWN. Checksum không chứng minh tài liệu thật,
source inventory đúng hay người nhập reference trung thực.

## Kết quả có thể kiểm lại

[Run cuối `run_02`](execution/master_01/oracle_reliability_20261116/run_02/results.json)
có **58 control logic do tác giả dựng, 0 ảnh, 0 physical ID, 1 cặp hash pixel
tượng trưng**. Tập này kiểm logic, không ước lượng tần suất lỗi trong thực tế.
25 ca có constructed truth pointwise; 13 ca có constructed truth relation.
Các ca còn lại vẫn nằm trong tổng 58 với truth chưa xác định/không áp dụng;
không được cộng vào số quyết định đúng. Xem từng ca trong
[bảng expected/actual/truth](execution/master_01/oracle_reliability_20261116/run_02/expected_vs_actual.md).

Tier 1 nhận nguồn đủ điều kiện; tier 2 yêu cầu hai source được khai cùng giá trị
hoặc MRZ literal qua kiểm, hoặc inventory bị loại đầy đủ. Hai source được khai
không đồng nghĩa hai bằng chứng độc lập. Đây là hai mức policy được chọn thủ công,
không phải confidence đã calibration hay đường risk–coverage đã học.

| Endpoint / policy | TP / FP / FN / TN theo phát alarm | Coverage có truth | Coverage toàn bộ | Risk trong quyết định có truth | Lỗi bị abstain |
|---|---:|---:|---:|---:|---:|
| Pointwise, tier 1 | 19 / 2 / 0 / 4 | 25/25 | 25/58 | 2/25 = 8% | 0 |
| Pointwise, tier 2 | 5 / 1 / 14 / 5 | 7/25 | 7/58 | 1/7 ≈ 14,29% | 14 |
| Relation, tier 1 | 11 / 0 / 0 / 2 | 13/13 | 13/58 | 0/13 | 0 |
| Relation, tier 2 | 4 / 0 / 7 / 2 | 4/13 | 4/58 | 0/4 | 7 |

FN trong bảng alarm gồm lỗi không được báo do abstain. TN trong bảng đó chỉ có
nghĩa không phát alarm trên ca không lỗi, không có nghĩa đã quyết định NO_FAULT.
JSON công bố thêm `decided_confusion` để tách hai cách tính.
Risk = số quyết định sai / số quyết định có truth; mẫu số 0 phải là NA.

**Kết quả âm:** hai nguồn cùng mang tham chiếu sai vẫn qua tier 2 và gây FP.
Giảm alarm không tự cải thiện độ tin cậy: tier 2 mất 14/19 lỗi pointwise và risk
điều kiện còn tăng trong tập dựng này. Ca shared wrong reference một nguồn
cũng giữ lại, nên tier 1 có hai FP. Expected policy output và task truth là hai
cột riêng: khớp expected không có nghĩa oracle đúng.

Flat được cấp cùng input, reference, validator và guard, đạt parity toàn bộ
58 ca ở cả hai tier/ba endpoint. Đây là kiểm baseline cùng thông tin trong
thiết kế chia sẻ guard; không phải hai bộ xác minh truth độc lập hoặc chứng minh
graph ưu việt. Không gộp control với mẫu inference để tăng cỡ mẫu.

Run đầu có 57 ca được giữ nguyên kèm source snapshot. Sau khi xem run đầu,
đã thêm ca hai nguồn cùng sai trong [amendment 02](execution/master_01/oracle_reliability_20261116/control_amendment_02.json)
và chạy lại thành run_02; báo rõ đây là bổ sung development hậu kiểm.
Không thay kết quả run_01 hoặc che lượt test thất bại ban đầu do đếm nhầm số
hoán vị (356 thay vì 368), được ghi trong `development_failures.json`.

Bốn projection chẩn đoán v1→v2 còn chỉ ra các guard khác nhau: C2 chưa loại
nguồn chính, source UNKNOWN, checksum literal sai nhưng metadata khai đúng,
và ngày `000229`. Đây là counterexample logic do dựng, không phải bốn lỗi
model tự nhiên mới phát hiện. Quyết định hai phiên bản có trong control JSON.

## Replay pilot lịch sử, giữ nguyên nhãn

Đã kiểm **93 cached outputs**, replay **46 ca**, gồm **42 primary / 3 ID** và
4 diagnostic. Nhãn pha 2 vẫn của một tác giả, chưa phân xử; R02 mới có pha 1.
Các số dưới đây là primary/original, chưa phải independent gold.

| Endpoint / phương pháp | TP / FP / FN / TN alarm | Coverage có nhãn | Risk trong quyết định có nhãn | Alarm: tổng / chưa kết luận |
|---|---:|---:|---:|---:|
| Pointwise A = A_flat | 2 / 0 / 5 / 19 | 18/26 | 0/18 | 14 / 12 |
| Pointwise B3 | 7 / 3 / 0 / 16 | 26/26 | 3/26 | 26 / 16 |
| Pointwise B reference gate | 0 / 0 / 7 / 19 | 0/26 | NA | 0 / 0 |
| Relation A = A_flat | 2 / 0 / 0 / 19 | 18/21 | 0/18 | 14 / 12 |
| Relation B3 | 2 / 3 / 0 / 16 | 21/21 | 3/21 | 26 / 21 |
| Relation B reference gate | 0 / 0 / 2 / 19 | 0/21 | NA | 0 / 0 |

B gate nhận reference=None vì chưa có external reference được duyệt: abstain
toàn bộ field/relation là kiểm trust boundary, **không phải bằng chứng B tốt hơn**.
A risk 0/18 vẫn bỏ sót 5/7 lỗi; không diễn giải riêng một chỉ số.

Panel withholding literal flags giữ riêng: pointwise A 2/0/4/14, B3 6/0/0/14;
relation cả hai 2/0/0/14. B3 vẫn có 20/26 alarm pointwise và 24/26 alarm relation
chưa kết luận trong panel này. B3 không còn FP có nhãn ở sensitivity không có
nghĩa đã được adjudicate. B0/B2, contract, từng cluster ẩn danh, diagnostic và
các lý do abstain đều có trong aggregate JSON; không chọn riêng lát thuận lợi.

## Kiểm chứng và khả năng tái lập

**336 tests + 6 subtests PASS** trong bộ Evidence Contract cuối cùng; 80 cấu hình
source/inventory và 368 hoán vị được kiểm trong một invariant test, không phải
368 ảnh độc lập. Không chạy lại JavaScript vì không sửa UI. Các lần chạy test
lặp để kiểm regression không được cộng thành bằng chứng mới.

[Verifier stdlib](oracle_reliability/verify.py) tái tính **492 nhóm metric từ
823 contingency cells**, kiểm hash và parity/expected/control→cell consistency.
Nó độc lập với hàm reporter, không xác minh truth do người chấm và không chạy
policy. [Organizer replay](execution/master_01/oracle_reliability_20261116/run_02/organizer_replay.json)
chạy lại policy và private joins, khớp records/cells/report. Hai mức kiểm này
không thay thế đánh giá semantic độc lập.

Trong root repo:

```powershell
python -X utf8 -B research/evidence_contract/oracle_reliability/verify.py research/evidence_contract/execution/master_01/oracle_reliability_20261116/run_02
```

[Gói arithmetic replay](execution/master_01/oracle_reliability_20261116/aggregate_replay_02.zip)
chỉ gồm aggregate, control tượng trưng và verifier. Giải nén rồi chạy
`python -B verify.py run_02`; không cần model/ảnh/phiếu riêng tư.
Replay đầy đủ policy + nhãn cần repo và dữ liệu private organizer; runner
`python -m research.evidence_contract.oracle_reliability.run --destination ...`
chỉ chấp nhận một thư mục mới trong checkpoint, không ghi đè lượt cũ.

**0 inference mới, 0 training, 0 phiếu người mới, 0 external approval.**
[Receipt bảo toàn](execution/master_01/oracle_reliability_20261116/preservation_after.json)
đối chiếu 2.685 tài sản từ trước lượt; các ZIP đã phát, raw review, frozen code
và receipts lịch sử giữ nguyên. Private rows và ảnh không nằm trong gói public.

## Gap tiếp theo và quyết định

Đã kiểm metadata MIDV-2020 thực trên máy: 1.000 annotation rows ở mỗi header,
photo chỉ có doc_quad/face; template có 16.194 regions nhưng chưa phải reference
về khả năng đọc/nguồn backup sau mutation. Năm manifest lịch sử cho thấy ít nhất
**148 instance đã dùng, bao phủ cả 10 loại giấy tờ**. Không tuyên bố các instance
còn lại chưa có exposure. [Feasibility receipt](execution/master_01/oracle_reliability_20261116/midv_metadata_feasibility.json).
License provider đã được tìm và kiểm tại nguồn chính thức; xem
[evidence notes](execution/master_01/oracle_reliability_20261116/SOURCES_AND_FEASIBILITY.md).

Công việc tiếp là độc lập hóa reference, xác minh C2/semantic key, khóa design
và sizing cho cohort mới, hoàn thiện paper với claim hẹp. Thêm seed hoặc train
OCR không sửa được reference sai và coverage thấp của oracle. Protocol mới
chưa có approval, sample size, budget hoặc scientific GO; chưa sẵn sàng nộp EASE.
