# R02: tiếp nhận pha 1 và chuẩn bị pha 2

Cập nhật 16/11/2026. Đã nhận **một người ngoài dự án**, hoàn tất **31 ảnh,
86/86 mục pha 1**. Tính cả tác giả, hiện có hai người đã nộp pha 1; pha 2 vẫn
chỉ có phiếu của tác giả. **R02 pha 2 đã chuẩn bị, chưa được chấm; R03 chưa nộp.**

## Phiếu gốc và đính chính vai trò

JSON R02 khai `project_author`. Người tổ chức xác nhận người này không tham gia
xây dựng project, đã chọn nhầm vai trò. Phiếu gốc và snapshot nhập giữ nguyên;
[đính chính riêng](execution/master_01/reviewer_intake_20261116_r02/role_correction.json)
ghi vai trò sử dụng khi báo cáo là `external_reviewer`, nguồn là xác nhận của
người tổ chức. Không thay câu trả lời, không tự cấp chứng nhận độc lập.

Người chấm khai chưa xem output và cả 86 mục khai chưa tiếp xúc trước. Đây là
tự khai, chưa được xác minh bên ngoài. Phiếu tác giả cũng khai `none`; việc tác
giả tham gia phát triển vẫn là giới hạn, không được biến thành đánh giá mù chỉ
dựa vào trường metadata đó.

- SHA256 byte export gốc: `1d324ae5aefd6478137c0bf98218899c7728f02ca702f6dc492a8d79fcbc99b7`.
- Snapshot nội dung: `b25d59d918c7cd0ba01702bc0c16b3c19acd973245ab2c7ebe83352dcbeb074b`.
- Packet: `e0819a7806fbc8d799b4a241f5d4ea58c55f96d014de2246f1bc1ed5e5650103`.

Mã người chấm, packet, ảnh và trường khớp. Export không có package job ID nên
không thể chứng minh chính xác phiên bản ZIP đã dùng chỉ từ JSON. Không suy ra
việc đã đọc hướng dẫn v2 từ packet ID vốn dùng chung giữa các phiên bản.
[Receipt tiếp nhận](execution/master_01/reviewer_intake_20261116_r02/intake.json).

## Đồng thuận trước phân xử: tác giả và R02

| Tiêu chí | Trùng / mẫu số | Tỷ lệ | Cohen κ | Nominal α |
|---|---:|---:|---:|---:|
| Mức nhìn thấy (`availability`) | 78/86 | 90,70% | 0,7421 | 0,7429 |
| Mức đọc được (`readability`) | 78/86 | 90,70% | 0,7421 | 0,7431 |
| Xác nhận đúng trường (`semantic_key_confirmed`) | 67/86 | 77,91% | 0,0239 | −0,0182 |
| Bản chép trên tập cả hai cùng đọc được và xác nhận đúng trường | 65/65 | 100% | — | — |

Bản chép được so sau NFC, bỏ khác biệt hoa/thường và khoảng trắng; **O và 0
vẫn khác nhau**. 65/65 là tập con có điều kiện, không phải toàn bộ 86 mục hoặc
độ chính xác so với truth. Không báo CI hoặc suy rộng: các trường/view lặp trên
cùng giấy tờ; primary chỉ có ba ID. Agreement không chứng minh ai đúng.

Có **21/86 mục** bất đồng ít nhất một trong ba tiêu chí phân loại. Riêng semantic
key có 19 bất đồng: tác giả `yes`/R02 `no` 15, tác giả `no`/R02 `yes` 3,
tác giả `yes`/R02 `uncertain` 1. Tác giả chọn `yes` 82/86, R02 chọn `yes` 69/86;
phân bố lệch khiến tỷ lệ trùng 77,91% vẫn đi cùng κ gần 0. Không dùng tỷ lệ trùng
chung để tuyên bố độ tin cậy đã đủ. Cần kiểm cách hiểu câu hỏi, ánh xạ nguồn vào
đúng trường và các ca không đọc được sau khi khóa các đánh giá độc lập.

Bảng bất đồng từng mục, transcript và ghi chú chỉ lưu riêng cho organizer dưới
`local/master_01/reviewer_intake_20261116_r02/disagreements.json`. Không gửi bảng
này hoặc đáp án tác giả cho R02/R03 trước khi họ hoàn tất. Chưa phân xử mục nào.
[Agreement nguyên trạng metadata](execution/master_01/reviewer_intake_20261116_r02/phase1_agreement_raw_roles.json)
vẫn ghi hai role `project_author`; đọc cùng đính chính riêng phía trên.
[Bảng đếm chéo](execution/master_01/reviewer_intake_20261116_r02/phase1_contingencies.json).

## Gói gửi tiếp cho đúng R02

File riêng: `local/reviewer_exports/r02_20261116/reviewer_R02_phase2.zip`.
**46 ca = 42 primary + 4 diagnostic**, dùng **30 file ảnh khác nhau**, 35 file
trong ZIP, 673.385 byte. Đây là ca đối chiếu, không phải 46 ảnh mới. Pha 1 có
31 ảnh; chỉ 30 ảnh được sử dụng trong các cặp đã chọn của pha 2.

SHA256 ZIP: `7c36d6440af67bfbed06e8ca35f060df4c4feebcbbbfd5412edde52a14b0ac0d`.
Snapshot pha 1 của chính R02 được khóa trước khi tạo packet output. Gói chỉ có
quan sát của R02 và output đã ẩn reader/phương pháp, không có đáp án tác giả,
phiếu người khác hoặc analyst join. Raw role trong seal giữ nguyên theo export;
đính chính không phá binding cũ. Không cần gửi project hoặc Python/model.

Gửi ZIP cho R02, giải nén toàn bộ, mở `index.html`, ghi điều kiện trước khi mở
output, lưu và xuất JSON khi đủ 46 ca; gửi lại JSON cho organizer. Đây là gói
riêng của R02; R03 phải hoàn tất pha 1 của mình trước khi nhận gói pha 2 riêng.
Receipt package có `actual_new_reviewers=0` vì tạo gói không phải nhận phiếu
pha 2; số người đã nộp pha 1 được ghi trong receipt intake riêng.
[Receipt gói](execution/master_01/reviewer_intake_20261116_r02/phase2_package_receipt.json).

## Kiểm chứng và ảnh hưởng tới kết luận

23 kiểm thử hiện có về agreement, đóng gói và niêm phong/guard IFV đều qua.
Verifier đọc riêng dữ liệu local đã kiểm 92 liên kết quan sát, 92 output từ cache,
tất cả file ZIP/manifest/ảnh và replay chính xác báo cáo pha 2 cũ của tác giả.
**2.493 tài sản lịch sử** giữ nguyên sau intake, gồm 460 tài sản readiness.

Trước intake, năm file archive ứng dụng có byte xuống dòng CRLF khác receipt LF.
Đã xác nhận Git blob và nội dung quy về LF khớp đúng SHA lịch sử, khôi phục byte
gốc, thêm `.gitattributes` giữ byte source archive và manifest khi checkout.
Không thay logic parser, frozen reader, A/baseline hoặc receipt lịch sử.

Chạy lại trên máy organizer có dữ liệu riêng:

```powershell
python -B -m research.evidence_contract.master.reviewer_intake_verify
```

[Kiểm chứng](execution/master_01/reviewer_intake_20261116_r02/verification.json) ·
[23 tests](execution/master_01/reviewer_intake_20261116_r02/targeted_tests.log).
Verifier không cung cấp raw data trong repository công khai và không tự tạo
annotation hoặc nhãn gold. Lượt này có 0 inference/training mới, 0 đáp án sửa.

**NO_GO_SUPERIORITY giữ nguyên.** Đã có agreement pha 1 thực, nhưng chưa có
đánh giá output của người ngoài, chưa phân xử reference, chưa tăng đa dạng ID
hoặc chứng minh A vượt baseline. Các bảng TP/FP/FN/TN và PDF cũ vẫn là kết quả
pilot tác giả, không gộp R02 vào chúng. Bước tiếp theo: nhận pha 2 R02, nhận pha
1 rồi cấp pha 2 R03, đo agreement theo cùng frozen sample trước phân xử và ghi
biên bản ca còn bất đồng. Công việc adequacy/novelty/dữ liệu tiếp tục song song.
