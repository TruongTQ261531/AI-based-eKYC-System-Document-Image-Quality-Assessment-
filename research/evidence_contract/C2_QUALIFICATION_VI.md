# C2 sau P6 · Kiểm chứng ảnh và vùng nguồn ngày 22/11/2026

**Đã tìm được bằng chứng trước/sau cho 110/110 candidate thuộc 40 giấy tờ. Trong đó, 45 candidate thuộc 24 giấy tờ có ít nhất một biến đổi che hoặc cắt hết polygon trường chính trong khi giữ nguyên cả hai polygon MRZ. Số candidate đủ tám điều kiện C2 vẫn là 0.** Cả 45 trường hợp cần người đánh giá kiểm tra khả năng đọc và quan hệ ngữ nghĩa. Hồ sơ thực nghiệm giữ `GO_PREPARATORY_ONLY` và `NO_GO_SUPERIORITY`. [Aggregate và hash đầu vào](execution/master_01/post_p6_20261122_094004Z/aggregate.json)

## Phạm vi và mẫu số

Inventory P2 có SHA-256 nội dung `088ab3bf7cb21ecfb44eb2ba8f0335648c2d64f64a1ec6106c8e897c4d1782c8`. Có 1.100 candidate trên 400 ID, gồm 300 trường số giấy tờ, 400 ngày sinh và 400 ngày hết hạn. Tại mốc P2, số bản ghi trước/sau khớp chính xác là 0. Lượt này tái dựng quan hệ từ dữ liệu riêng cho toàn bộ nhóm ưu tiên đầu tiên. Nhóm 96/35 và 894/325 giữ trạng thái đã ghi ở P2. [Biên bản P2](execution/master_01/p2_20261120/verification.json)

| Trường | Candidate / ID có cặp ảnh và vùng khớp | Có biến đổi chạm trường chính | Có biến đổi phủ hết trường chính và giữ cả hai vùng MRZ | Đủ tám điều kiện |
|---|---:|---:|---:|---:|
| id_number | 30 / 30 | 19 | 11 | 0 |
| dob | 40 / 40 | 37 | 18 | 0 |
| expiry_date | 40 / 40 | 31 | 16 | 0 |
| **Tất cả** | **110 / 40** | **87 trên 37 ID** | **45 trên 24 ID** | **0/110 candidate, 0/40 ID** |

Mỗi trường xuất hiện tối đa một lần trên mỗi ID trong nhóm này. Một ID có thể xuất hiện ở nhiều dòng. Có 23 candidate mà các biến đổi đã tái dựng đều không chạm polygon trường chính. Trong 87 trường hợp có tác động, 42 trường hợp vẫn thiếu biến đổi đáp ứng đồng thời tiêu chí hình học phủ hết vùng chính và giữ cả hai vùng dự phòng. Không dùng tập 45 để ước lượng tỷ lệ thành công trên dân số hoặc chọn cohort.

## Cách xác minh

1. Kiểm byte của receipt, lineage, inventory riêng, hai manifest P2, bộ metadata ảnh và phần đầu tar MIDV-2020 chứa annotation template. Dựng lại inventory và so từng candidate. Nối bằng physical ID, hash ảnh gốc và source ID bản địa. Kiểm file và pixel RGB sau hiệu chỉnh EXIF của 433 đường dẫn ảnh. Cả 433 khớp kho P2.
2. Tìm đúng trường body và hai dòng MRZ trong annotation VIA. Với template có kích thước đã lưu, dựng phép chiếu từ bốn góc tài liệu vào ảnh. Với nguồn chỉ lưu tọa độ từng trường, khớp alias và literal của annotation rồi kiểm một homography trên tất cả các vùng có đối chiếu. Sai số tối đa cho mỗi tọa độ là 0,2 pixel. Loại các vùng gốc nằm ngoài khung. Đây là kiểm nhất quán hình học của các bản ghi chung nguồn cung cấp.
3. Với ảnh dẫn xuất, kiểm hash cha, ID, byte ảnh con và biến đổi thuộc nhóm crop/mask. Tái tạo đúng toàn bộ pixel RGB ảnh con từ cha và tọa độ crop hoặc mask lịch sử. Với ảnh recovery, thử decoder OpenCV mà pipeline gốc sử dụng khi cần. Thu được 203 liên kết theo hash cha và đường dẫn ảnh con. Một ảnh hoặc liên kết có thể phục vụ nhiều trường.
4. Tính phần polygon chính bị cắt/che và phần bị ảnh hưởng lớn nhất của hai dòng MRZ. Lưu mọi lựa chọn khớp. Khi có nhiều lựa chọn, ảnh đại diện ưu tiên phủ hết trường chính và giữ nguyên hai dòng MRZ. Lần lượt ưu tiên tác động một phần với MRZ còn nguyên, độ phủ vùng chính, mức giữ MRZ và thứ tự bản ghi. Quy tắc phục vụ đọc hồ sơ nội bộ.
5. Lưu tập HTML ngoại tuyến trong vùng riêng. Mỗi ca có hai liên kết ảnh đầy đủ, danh tính nguồn, tọa độ và hash trong manifest. Có 646 crop lưu được trong 660 vị trí trước/sau của ba vùng. Còn 14 vị trí hoàn toàn ngoài khung sau crop, có lý do và polygon đã dịch. Verifier đối chiếu pixel của 646 crop với ảnh và tính lại phần diện tích bị ảnh hưởng. [Hướng dẫn tái lập](execution/master_01/post_p6_20261122_094004Z/REPLAY.md)

## Tám điều kiện

PASS cần bằng chứng khẳng định điều kiện. FAIL ghi điều kiện hiện không đạt. UNKNOWN giữ phần cần quan sát hoặc quyết định bổ sung. Đủ điều kiện đưa vào C2 đòi hỏi tám PASS trên cùng candidate, cùng bằng chứng.

| Điều kiện | PASS | FAIL | UNKNOWN | Căn cứ |
|---|---:|---:|---:|---|
| primary_supported_before | 0 | 0 | 110 | Chờ xác nhận vùng chính đọc được trước biến đổi |
| primary_removed_after | 0 | 0 | 110 | Đã đo tác động hình học, còn chờ kết luận nội dung sau biến đổi |
| backup_supported_before | 0 | 0 | 110 | Chưa có quan sát được duyệt về khả năng đọc hai dòng MRZ trước biến đổi |
| backup_supported_after | 0 | 0 | 110 | Chưa có quan sát được duyệt về khả năng đọc hai dòng MRZ sau biến đổi |
| semantic_equality_approved | 0 | 0 | 110 | Mapping phát triển và kết quả cơ học chưa có quyết định của người có thẩm quyền |
| provenance_verified | 110 | 0 | 0 | Gắn được đúng ảnh, ID, hai nguồn, phép biến đổi và tọa độ trước/sau |
| reference_approved | 0 | 110 | 0 | Registry production có 0 authority và 0 reference được duyệt. Quyền D10 còn thiếu |
| distinct_sources | 110 | 0 | 0 | Vùng chữ body và hai dòng MRZ có định danh tách biệt trong template |

Cả 110 có kết quả cơ học `LITERAL_OR_PRECISION_DIFFERENCE`. Trên toàn inventory, P2 ghi 1.097 kết quả này và 3 MRZ ngoài định dạng được hỗ trợ. Chưa xác lập lỗi annotation. Registry phát triển giữ riêng số giấy tờ thông thường, alias chưa rõ, chữ O và số 0, ngày đầy đủ và YYMMDD. TD3 kiểm lại checksum trên dòng gốc. Thế kỷ chưa được xác nhận giữ chưa biết.

## Quyết định chuyển nhóm

| Nhóm | Công việc tiếp theo | Điều kiện chuyển bước |
|---|---|---|
| 45 candidate / 24 ID có hình học phù hợp | Kiểm quyền sử dụng theo phiên bản, bốn quan sát khả năng đọc, căn cứ ngữ nghĩa và độ chính xác của trường. R02 và R03 khai exposure và đề xuất riêng cho từng candidate. | Chỉ trình candidate có căn cứ cho người phân xử đã định danh. Quyết định có lý do, hash, chữ ký. Chủ dự án phê duyệt riêng với D10 trước khi đếm đủ điều kiện. |
| 65 candidate còn lại trong nhóm 110 | Tìm một biến đổi lịch sử bổ sung có thể tái tạo chính xác, phủ hết vùng chính và bảo toàn hai vùng dự phòng. | Giữ hồ sơ với lý do hiện tại nếu không có ảnh/biến đổi mới đáp ứng điều kiện. |
| 96 candidate / 35 ID có ảnh, thiếu cha đã gắn | Có thể làm kiểm kê nguồn nội bộ. Cần tìm ảnh cha có hash, metadata biến đổi và hệ tọa độ cho từng ID trước khi dựng gói. | Hoãn mở rộng. Chỉ chuyển từng candidate khi có ít nhất một cặp tái dựng được và hai nguồn được định vị. |
| 894 candidate / 325 ID chỉ có metadata | Trước hết cần tìm ảnh gốc lịch sử khớp ID/hash và căn cứ quyền. Sau đó mới tìm ảnh biến đổi và mapping. | Chưa khả thi cho đánh giá vùng với đầu vào hiện có. Dừng ở metadata cho tới khi có ảnh đủ căn cứ. |

Khả năng kiểm tra bằng chứng C2 trên máy organizer đã tăng. Khả năng đọc, tương đương ngữ nghĩa, tính độc lập, quyền sử dụng và sức mạnh thống kê vẫn có các điều kiện riêng. Kết luận P5B `INFEASIBLE` tiếp tục áp dụng cho thiết kế đã mô phỏng. TASK 6B và TASK 7B vẫn đóng. [Biên bản Round 1](ROUND1_CLOSURE_20261122_VI.md) · [Biên bản kiểm chứng](execution/master_01/post_p6_20261122_094004Z/verification.json)
