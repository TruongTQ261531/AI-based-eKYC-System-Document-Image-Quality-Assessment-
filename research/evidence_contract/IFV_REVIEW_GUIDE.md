# Trạng thái sau khi hoàn tất cả hai pha cá nhân

Ngày 15/11/2026 đã nhập và niêm phong đủ **46/46 ca pha 2**, sau pha 1
86/86 ô. Phần việc cá nhân hiện tại đã DONE. Không cần gửi lại file đã nhận.
[Kết quả](IFV_RESULTS_VI.md) · [Bước tiếp theo](NEXT_ACTIONS.md) ·
[Hậu kiểm và độ nhạy](execution/master_01/ifv_20261115/analysis.md)

Để replay, dùng `master.ifv_report --submission` với bản niêm phong:

`local/task55_output_review/d7598ae874d735869d2505c30ac9f7348691c2450af2a70d45666f8b3293c223/submissions/812605bbab3940be838ac9da07ed903c0098717ace789f703f080869dde3267d/output_observations.json`.

Không import lại vào cùng snapshot hoặc sửa phiếu khóa. Nếu có phân xử bổ sung,
lưu amendment/version mới và exposure thực tế; không coi cùng tác giả đã xem
output là một reviewer mù mới. Các hướng dẫn dưới đây là workflow đã hoàn tất.

## Hướng dẫn thu thập đã dùng ngày 14–15/11

Ngày 14/11/2026, export mới đã đạt **86/86 ô trên 31 ảnh** và được khóa nguyên
trạng. Pha 1 đã xong; phiếu bổ sung ngày 13/11 là lịch sử. Bước kế tiếp là đánh
giá **output đã ẩn danh**, tách khỏi việc chép chữ trên ảnh.

[Mở phiếu đối chiếu 46 ca](local/task55_output_review/d7598ae874d735869d2505c30ac9f7348691c2450af2a70d45666f8b3293c223/index.html)

Mở file `index.html` bằng trình duyệt trên máy, giữ nguyên cấu trúc thư mục.
Phiếu dùng 42 ca primary và 4 diagnostic đã chọn trước nhãn; thứ tự không hiện
tên reader hoặc phương pháp A/B3. Không cần khởi động hệ thống eKYC.

1. Xem ảnh gốc và ảnh biến đổi cùng ghi chép pha 1. Nguồn chữ và hai dòng MRZ
   được hiển thị nguyên văn. Bấm ảnh để xem kích thước gốc.
2. Chọn điều kiện phép thử, ghi lý do quan sát. Với trường cần che toàn bộ,
   chỉ xác nhận mọi nguồn đã bị xóa khi có đủ bằng chứng trên toàn ảnh.
   Chưa đủ bằng chứng thì chọn lựa chọn tương ứng.
3. Bấm **Ghi điều kiện và xem đầu ra**. Điều kiện được lưu trước khi hiện
   output và khóa cho ca đó. Sau đó đánh giá cả giá trị gốc lẫn giá trị biến đổi;
   nếu cho rằng sai/bỏ sót/điền khi thiếu nguồn thì ghi căn cứ cụ thể.
4. Bấm **Lưu đánh giá ca này**, rồi chuyển ca. Có thể chia nhiều buổi.
   **Sao lưu nháp JSON** giữ cả ca mới ghi điều kiện, chưa đánh giá output.
   Dùng **Nạp phiếu JSON đã xuất** để tiếp tục từ bản sao.
5. Khi đủ 46 ca, bấm **Xuất phiếu hoàn chỉnh** và gửi đường dẫn JSON. Nếu chủ
   động dừng sớm, **Xuất phần đã đánh giá** báo rõ số đã làm; các ca còn lại giữ
   chưa đánh giá. Bản nháp là bản sao để tiếp tục, không phải nhãn đã nộp.

Nếu trình duyệt không lưu nháp cục bộ, giữ bản sao JSON trước khi đóng trang.
Ghi riêng số phút thực làm nếu muốn phân tích chi phí; phiếu hiện không đo
active time. Không suy thời gian làm từ thời điểm export hoặc first reveal.

Pha 1 có 12 ghi chú nhất quán nguồn, được giữ nguyên. Cả 10 ca C2 hiện chưa
đạt đồng thời điều kiện đọc rõ và backup theo guard đã có. Pha 2 không yêu cầu
sửa lại phiếu khóa hoặc chép theo output; ca chưa chứng minh được giữ bất định.
[Chi tiết trạng thái](IFV_REVIEW_STATUS.md)

## Sau khi nhận JSON pha 2 thật

Chạy từ worktree nghiên cứu bằng venv hiện có. Thay đường dẫn submission bằng
file thật đã nhận. Không import bản nháp hay tạo câu trả lời thay người.

```powershell
$py = 'D:\laptrinhcuatao\Ekyc\.venv\Scripts\python.exe'
$snapshot = '00ff0a49d4df5a84c2d78511bcf2d9ed36e19945747a93c08d6788e3b9a9da79'
& $py -B -m research.evidence_contract.task55.ifv import-stage2 --snapshot $snapshot --submission '<JSON pha 2 đã xuất>'
& $py -B -m research.evidence_contract.master.ifv_report --submission '<bản output_observations.json đã niêm phong dưới local/>'
```

Importer in ra receipt và lưu bản niêm phong trong
`local/task55_output_review/<reviewer-hash>/submissions/<export-hash>/`.
Reporter nhận file `output_observations.json` tại đó, xác minh hash và analyst
join trước khi tính hai endpoint. Giữ riêng invalid, inconclusive, unreviewed,
độ phủ theo contract và ca không cảnh báo. Một người chấm hỗ trợ mô tả pilot;
độc lập, agreement và adjudication tiếp tục chưa xác nhận.

## Bảo toàn và nối lại

Snapshot hiện tại:
`00ff0a49d4df5a84c2d78511bcf2d9ed36e19945747a93c08d6788e3b9a9da79`.

Phiếu pha 2 đã phát hành được ràng buộc với snapshot này. Nếu cần xác minh/mở
lại bằng CLI, `open-stage2 --snapshot <SHA ở trên>` kiểm publication và trả lại
cùng đường dẫn, không tạo sample mới. Không sửa HTML, packet hoặc pha 1 tại chỗ;
một protocol mới phải có version, exposure và scope riêng.

[Receipt 14/11](execution/master_01/ifv_20261114/phase1_readiness.json) ·
[Receipt partial 13/11](execution/master_01/ifv_20261113/phase1_readiness.json) ·
[Roadmap](EASE2027_ROADMAP_VI.md)
