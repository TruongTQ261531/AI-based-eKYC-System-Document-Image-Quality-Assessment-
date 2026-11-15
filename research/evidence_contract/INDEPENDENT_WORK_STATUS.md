# Việc tiếp tục độc lập với phiếu đối chiếu

Mốc không cần JSON feedback tiếp theo ngày 16/11 đã hoàn tất:
[reference controls và prototype kiểm tham chiếu](REFERENCE_CONTROLS_20261116.md).
Đã chạy 252 injected executions, khử trùng còn 131 so sánh/13 cặp pixel; có
counterexamples của union và reference sai dùng chung. 245 Python + 6 subtests,
15 JavaScript qua. Các ca tổng hợp không được cộng vào lỗi model thật hay nhãn người.

Cập nhật 16/11/2026, Asia/Bangkok. **Review cá nhân đã hoàn tất cả hai pha**;
đã nhập 46 ca và xuất [kết quả](IFV_RESULTS_VI.md). Không còn chờ phiếu hiện
tại. Reference độc lập và adequacy vẫn là dependency của confirmatory. Công
cụ, hồi quy ứng dụng và chuẩn bị artifact tiếp tục theo đầu vào riêng.

Ngày 16/11 đã làm thêm [các biến thể A và replay](A_DEVELOPMENT_20261116.md),
[gói reviewer offline/công cụ agreement](REVIEWER_HANDOFF_VI.md), cùng
[bản lưu mã sửa ứng dụng](../../engineering/application_20261114/README.md).
Đó là công việc thực hiện được khi chưa có người ngoài trả phiếu; không phải
inference/training mới hoặc đánh giá độc lập mới. Các số kiểm backend/model
bên dưới là kết quả ngày 14/11, không được tính thành lượt chạy mới ngày 16/11.

## Đã làm trong lượt tiếp tục này

| Phần | Kết quả thực tế | Phạm vi bằng chứng |
|---|---|---|
| Backend/API và dataset | 113 tests qua, gồm integrity manifest 21.050 ảnh và tách ID train/val/test | Kiểm phần mềm và metadata; không phải độ chính xác eKYC |
| Giao diện camera | 15 tests qua | DOM/media/network giả lập, bao gồm chuyển bước và chặn bỏ qua liveness |
| Tách trường OCR | Sửa hai lỗi trong bản ứng dụng: ghép hai tên mâu thuẫn và bỏ giá trị tùy chỉnh một ký tự | Code trước sửa được lưu; 12 ca token tổng hợp: 8 đạt trước, 12 đạt sau. Bốn ca hồi quy thuộc hai loại lỗi |
| Model thật | Hai luồng thẻ học sinh/bằng lái tổng hợp đều trả review, có bộ trường tương ứng | Có inference thật; ảnh được tạo trên RAM. Không có selfie hoặc ảnh giấy tờ thật mới |
| Bảo toàn | 16 tài sản model giữ nguyên hash; parser trong worktree nghiên cứu không thay đổi | Không thay subjects của nghiên cứu đã khóa hoặc sửa câu trả lời người |

Code ứng dụng được sửa tại `D:/laptrinhcuatao/Ekyc/ekyc/document_fields.py`,
tests tại `D:/laptrinhcuatao/Ekyc/tests/test_document_fields.py` và script mới
`D:/laptrinhcuatao/Ekyc/scripts/audit_field_extraction.py`.
Đây là nhánh công việc ứng dụng độc lập. Chưa chuyển patch vào reader nghiên
cứu; nếu đánh giá version mới sau này cần đăng ký version/hash và protocol mới.

[Receipt tổng hợp](execution/master_01/independent_20261114/completion_manifest.json)
ghi hash, kết quả kiểm và đường dẫn artifact. Mọi kết quả này nằm ngoài primary
IFV. Không biến synthetic expected values thành nhãn người hay gắn một sửa lỗi
mới thành historical fault pool có phân xử độc lập.

## Vì sao chưa mở thêm lượt huấn luyện

Module 1 đã có một lượt fine-tune classifier 7 epoch; checkpoint đang dùng
được chọn từ validation. Backbone khởi tạo có exposure chưa biết. Các reader
chính của nghiên cứu là subjects đóng băng; đổi weights sẽ đổi phân bố lỗi
của phép so sánh, không thay được tham chiếu độc lập.

Manifest ứng dụng hiện có nhãn Clean/Blur/Cropped/Dark/Distorted. Rà các file
JSON/XML/TXT/CSV/YAML dưới `full_dataset_original` không tìm thấy annotation
góc, mask hay transcript tương ứng. Không có nghĩa mọi nguồn dữ liệu khác
đều thiếu annotation, nhưng bộ TIFF cục bộ này chưa đủ cơ sở để mở huấn luyện
segmentation/OCR mới. Đọc nhãn chất lượng như nhãn định vị sẽ sai mục tiêu.

Huấn luyện tiếp là một nhánh độc lập có thể mở khi chốt được target, training
labels, split theo ID, validation selection, ngân sách và version riêng. Phiếu
IFV không phải dependency kỹ thuật của nhánh đó. Hiện chưa có cơ sở để chạy
thêm một lượt chỉ nhằm sử dụng GPU.

## Những phần còn lại và dependency thực sự

| Việc | Có phụ thuộc phiếu hiện tại? | Đầu vào / bước tiếp |
|---|---|---|
| Kiểm hồi quy và sửa bug ứng dụng | Không | Tiếp tục khi có thay đổi hoặc ca lỗi mới; các sửa của lượt này đã qua bộ kiểm đầy đủ |
| Kiểm tải, đo thời gian từng stage, profiling | Không | Chốt workload/budget riêng và đo trên bản ứng dụng. Hai thời gian smoke không đủ suy tải đồng thời |
| Nâng định vị/segmentation Module 2 | Không | Cần nhãn vùng/góc phù hợp và giao thức development. Có thể chuẩn bị công cụ nhập/audit nhãn trước model training |
| Huấn luyện OCR/quality mới | Không | Cần target và dataset đúng nhãn; giữ checkpoint ứng viên tách khỏi bản dùng và subject nghiên cứu |
| Chuẩn bị PDF/gói tái lập | Không | Source/gói replay đã có; PDF còn thiếu compiler và kiểm layout. Quyền phát hành và ẩn danh phải được rà trước release |
| Precision/FAR/sensitivity của oracle | Đã có pilot 15/11 | Đã nhập và replay; giữ original/sensitivity riêng, chưa phải nhãn độc lập hoặc inference quần thể |
| Tuyên bố độc lập và confirmatory | Chưa chỉ cần phiếu | Cần chuẩn độc lập, claim/adequacy/GO mới và dữ liệu/lock mới |

Không lặp huấn luyện hay chạy lại một nghiên cứu đã hoàn tất để tạo thêm số
lượt. Lịch nghiên cứu hiện tại vẫn ở [roadmap](EASE2027_ROADMAP_VI.md); bảng
này làm rõ các luồng kỹ thuật có thể tiến song song và phần nào thực sự phải chờ.
