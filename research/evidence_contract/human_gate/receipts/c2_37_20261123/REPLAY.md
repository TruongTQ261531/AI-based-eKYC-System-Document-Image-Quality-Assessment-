# Tái lập C2-37 trên máy organizer

Từ gốc repo nghiên cứu, dùng môi trường đã kiểm và cache gốc C2-45. Chạy các lệnh dưới với tên mới. Không cần truy cập mạng. Giữ nguyên master, protocol và các receipt lịch sử.

~~~powershell
$py = '..\..\.venv\Scripts\python.exe'
$pkg = 'research.evidence_contract.human_gate'
& $py -X utf8 -B -m "$pkg.verify" human_20261122144027Z
$run = 'replay37_' + [guid]::NewGuid().ToString('N')
& $py -X utf8 -B -m "$pkg.prepare37" $run
& $py -X utf8 -B -m "$pkg.verify37" $run
$local = "research/evidence_contract/local/human_gate/$run"
$public = 'research/evidence_contract/human_gate/receipts/c2_37_20261123'
foreach ($f in 'aggregate.json','verification.json') {
    if ((Get-FileHash "$local/$f").Hash -ne (Get-FileHash "$public/$f").Hash) { throw "Mismatch $f" }
}
~~~

selection.json lưu riêng đủ 18 ID giữ, 6 ID loại và 8 candidate loại. Queue giữ nguyên thứ tự và nội dung từng item. Hai manifest riêng cho biết hash mỗi tệp, còn aggregate công khai chỉ chứa số đếm và hash nhóm. Mỗi index.html có 37 form, tham chiếu đúng 155 ảnh trong thư mục assets/. Kiểm độc lập so từng section và script với master, phân loại lại theo acquisition + VIA + readme và xác minh từng byte. Để phát lại master dùng [hướng dẫn 45](../human_20261122144027Z/REPLAY.md).

Kiểm thử Python theo danh sách TARGETS trong human_gate/tests_receipt.py cộng test_c2_37_verify, sau đó toàn bộ research/evidence_contract/tests. Kiểm thêm năm tệp test_*.cjs bằng node --test --test-isolation=none. [Receipt kiểm thử và phát lại](validation.json) · [Protocol](../../../C2_37_ANALYSIS_PROTOCOL_VI.md) · [Hồ sơ D10](../../../C2_37_D10_VI.md). Trạng thái chỉ là PREPARED_TECHNICAL_37.
