# Bàn giao P0–P4 ngày 21/11/2026

Nhánh làm việc là `main`. Baseline cho lần đối chiếu này là `dd2e109bf1e2f7b8190dbd1efa0d527865b1207f`. Tên “audit P2” trong báo cáo trước bao gồm cả P1 (ảnh) và P2 (C2) của checklist này.

| Mục | Trạng thái theo tiêu chí nghiệm thu | Phạm vi bằng chứng |
|---|---|---|
| P0 | Hoàn tất baseline kỹ thuật và replay | Ghim SHA-256 của policy, adapter, verifier, các tệp D4 và biên bản trước. Chạy lại 72 controls ở 2 tier và 46 ca lịch sử. Manifest ghi commit, kết quả full regression, digest log và các trường thời gian loại khỏi so sánh. [Baseline và biên bản mới](execution/master_01/checklist_20261121/baseline_replay.json) |
| P1 | Hoàn tất kiểm kê trong kho raster được phép | 5.428/5.428 khung chính; 1.159 nhóm trùng file, 1.241 nhóm trùng pixel và 362 nhóm ứng viên gần trùng. 24 mã giấy tờ có nhiều vai trò và 200 mã xuất hiện ở nhiều bộ. 876 tệp thiếu mã giấy tờ, 12/24 khung phụ chưa giải mã được. Chỉ mục nhóm gắn với manifest lineage riêng bằng hash. [Tổng hợp và UNKNOWN](P2_AUDIT_VI.md) |
| P2 | Hoàn tất phân loại, 0/1.100 cặp đủ điều kiện | Trên 400 mã: hai định danh vùng khác nhau ở mọi cặp. Chưa có phê duyệt reference nào; quan sát vùng trước/sau, semantic equality và provenance chưa đủ. Bảng 8 điều kiện có cả ba cột PASS/FAIL/UNKNOWN và danh sách blocker theo loại. [Kết quả C2](execution/master_01/p2_20261120/aggregate.json) |
| P3 | Hoàn tất **đặc tả thiết kế** v3 | Chủ dự án chọn coverage ≥80%, all-fault sensitivity ≥80%, giảm FAR tuyệt đối >5 điểm phần trăm và trần nguồn lực. Protocol xác định hai arm, endpoint, mẫu số, cụm, quy tắc quyết định và dừng. [Protocol v3](B_PROTOCOL_V3_20261121.md) |
| P4 | Hoàn tất đối chiếu tài liệu và tái lập cho các claim hiện tại | Sáu nghiên cứu gốc trong năm nhóm đối chiếu. Bảy claim v3 có baseline, giới hạn và cách kiểm. Có mã phân tích trên artifact công khai và replay đầy đủ tại máy có dữ liệu. [Ledger, threats và nguồn](paper/B_EVIDENCE_V3_20261121.md) |

## Tái lập

Từ gốc repository nghiên cứu, dùng Python của dự án. Phép kiểm công khai kiểm hash các tệp được ghi trong baseline, đối chiếu kết quả D4, tính lại bảng đồng thuận R02/R03 và kiểm mẫu số C2.

~~~powershell
$python = '..\..\.venv\Scripts\python.exe'
$module = 'research.evidence_contract.execution.master_01.checklist_20261121'
& $python -X utf8 -B -m "$module.public_analysis"
~~~

Full regression tại mốc này đạt 597 kiểm thử Python và 6 subtest. Bộ giao diện người chấm đạt 15/15 kiểm thử trên Node 24.22.3. Có thể chạy lại phần giao diện bằng PowerShell:

~~~powershell
$files = (Get-ChildItem research/evidence_contract/tests/test_*.cjs).FullName
node --test --test-isolation=none @files
~~~

Máy có quyền đọc dữ liệu lịch sử có thể chạy lệnh dưới. Chọn thư mục P2 riêng có aggregate SHA-256 khớp [biên bản P2](execution/master_01/p2_20261120/verification.json). Lệnh tìm theo hash, ghi sang thư mục mới, rồi xuất biên bản và chỉ mục thành viên của nhóm file/pixel/near-duplicate trong `local`. Chỉ số từng thành viên tham chiếu thứ tự hàng của manifest lineage đã khóa. Phiếu và ảnh ở máy. Full regression dùng schema và dữ liệu riêng có sẵn trong môi trường dự án.

~~~powershell
$ec = 'research/evidence_contract'
$expected = (Get-Content -Raw "$ec/execution/master_01/p2_20261120/verification.json" | ConvertFrom-Json).aggregate_sha256
$match = Get-ChildItem "$ec/local/p2_20261120" -Directory | Where-Object {
    $aggregate = Join-Path $_.FullName 'aggregate.json'
    (Test-Path -LiteralPath $aggregate) -and ((Get-FileHash -LiteralPath $aggregate).Hash -eq $expected)
} | Select-Object -First 1
if (-not $match) { throw 'Thiếu bản chạy P2 riêng khớp hash' }
$out = "$ec/local/checklist_" + [guid]::NewGuid().ToString('N')
& $python -X utf8 -B -m "$module.replay" $match.FullName $out
~~~

Lượt đối chiếu ban đầu phát hiện một trường thời gian dùng hậu tố `_ns_shared`. Bản replay cuối liệt kê chính xác bảy trường thời gian thay đổi giữa các lượt. So sánh giữ nguyên số lần gọi, trạng thái, lý do, mặt nạ can thiệp và hash đầu vào; với 46 ca lịch sử còn đối chiếu nội dung hàng riêng sau khi kiểm digest gốc. Log regression và số đo thời gian có thể khác giữa các máy.

## Điều còn mở

Cả ba người chấm đã hoàn thành hai pha. Round 1 còn chờ cutoff, người có thẩm quyền và quy trình phân xử (D1–D3). Quyền cho từng artifact, quy tắc exposure và phạm vi claim (D10–D12), một cohort đủ điều kiện và kiểm tính khả thi thống kê vẫn cần trước scientific lock. Ngân sách prospective được phép dùng hiện tại bằng 0. Chưa có ước lượng FAR hoặc superiority trên cohort mới.
