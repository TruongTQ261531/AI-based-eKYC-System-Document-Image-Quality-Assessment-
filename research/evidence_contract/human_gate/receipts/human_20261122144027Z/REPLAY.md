# Tái lập C2-45 trên máy organizer

Checkout của mốc này dùng baseline `81557747d9f1a3467b0f6bdb0dad6f60805a9fe4` và private run Post-P6 đã xác minh. Cần giữ nguyên sáu export, ba view, queue và coherence detail, ảnh/crop, `template_head.bin`, lineage, inventory, manifest P2 và hai văn bản license/readme MIDV-2020 đã cache. Chạy từ gốc repo nghiên cứu. Bản kiểm hiện hành là snapshot lúc chưa có authority hoặc phiếu C2 thật.

```powershell
$py = '..\..\.venv\Scripts\python.exe'
$pkg = 'research.evidence_contract.human_gate'
$original = 'human_20261122144027Z'
& $py -X utf8 -B -m "$pkg.verify" $original
& $py -X utf8 -B -m "$pkg.state_matrix" $original
$run = 'replay_' + [guid]::NewGuid().ToString('N')
& $py -X utf8 -B -m "$pkg.prepare" $run
& $py -X utf8 -B -m "$pkg.tests_receipt" $run
& $py -X utf8 -B -m "$pkg.state_matrix" $run
& $py -X utf8 -B -m "$pkg.verify" $run
$local = "research/evidence_contract/local/human_gate/$run"
$public = "research/evidence_contract/human_gate/receipts/$original"
(Get-FileHash "$local/aggregate.json").Hash -eq (Get-FileHash "$public/aggregate.json").Hash
(Get-FileHash "$local/matrix_receipt.json").Hash -eq (Get-FileHash "$public/matrix_receipt.json").Hash
```

Hash của log và thời gian pytest thay đổi khi chạy mới. Mỗi run cần khoảng 1 GiB cho hai workspace. `queue.json` và `candidate_state.json` chỉ dành cho organizer. Mở `R02/index.html` hoặc `R03/index.html` cục bộ để kiểm tra. Chuẩn bị gói không cấp quyền gửi.

Với phiếu thật sau khi D10 đã cho phép, chạy `& $py -X utf8 -B -m "$pkg.review" $original R02 $privateObservation` (hoặc R03). Công cụ in receipt nội dung. Organizer lưu nguyên byte phiếu và receipt riêng. Đối chiếu ID candidate và hash của item với queue đã khóa. Khi có journal thật, thêm `--journal $privateJournal` chứa `candidates` và `events`, cùng `--assignment $ownerSignedRoster` nếu cần nối authority ID khác mã assessor. Một journal xác thực cần cấu hình production và checkpoint của chủ dự án. [Bàn giao ký và phân xử](../../../C2_45_ADJUDICATION_READINESS_VI.md)

Trước đồng bộ, chạy `& $py -X utf8 -B -m "$pkg.release_scan" $original` sau khi stage đúng các đường dẫn mới. Receipt ghi digest nội dung thêm trong diff từ baseline. Chỉ dùng đối chiếu receipt này tại commit phát hành tương ứng. Giữ các lần chạy sau và mọi hồ sơ có chữ ký trong run riêng.
