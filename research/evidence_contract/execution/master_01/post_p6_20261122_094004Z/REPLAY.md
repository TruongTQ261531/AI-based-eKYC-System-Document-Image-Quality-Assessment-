# Tái lập biên bản sau P6

Mốc nguồn Git là `c99e467ddf403afed5bd520a0b69d22d277a38d0`. Cutoff Round 1 là 21/11/2026. Hồ sơ này được lập ngày 22/11/2026. Toàn bộ lệnh chạy từ gốc repo nghiên cứu trên máy organizer. Dùng môi trường Python của dự án với Pillow, NumPy, OpenCV, cryptography và pytest.

## Kiểm tra bản đã lưu

```powershell
$py = '..\..\.venv\Scripts\python.exe'
$pkg = 'research.evidence_contract'
$record = 'post_p6_20261122_094004Z'
$original = 'run_20261122094004'
& $py -X utf8 -B -m "$pkg.oracle_reliability.verify_post_p6" $original $record
```

Verifier đối chiếu snapshot, alias riêng, join, agreement, roster P2, 8 điều kiện, số ID duy nhất của từng trường và pixel của từng crop. Kết quả `VERIFIED` yêu cầu khớp cả hai biên bản pytest và SHA của log riêng. So sánh git với baseline dùng checkout của mốc này. Chạy trên checkout khác có chỉnh sửa receipt lịch sử sẽ dừng.

## Chạy mới, giữ nguyên bản trước

```powershell
$run = 'replay_' + [guid]::NewGuid().ToString('N')
$private = "research/evidence_contract/local/post_p6/$run"
$p2run = 'audit21_1795225290150'
& $py -X utf8 -B -m "$pkg.adjudication.post_p6_closure" $run
& $py -X utf8 -B -m "$pkg.oracle_reliability.post_p6_qualification" $run $p2run
& $py -X utf8 -B -m "$pkg.execution.master_01.$record.run_tests" $run
& $py -X utf8 -B -c "import json,sys,pathlib; p=pathlib.Path(sys.argv[1]); r=json.loads(pathlib.Path(sys.argv[2]).read_text(encoding='utf-8')); assert all(json.loads(f.read_text(encoding='utf-8'))==r[k] for f,k in [(p/'round.json','round1'),(p/'qualification/c2.json','c2')]); print('MATCH')" $private "research/evidence_contract/execution/master_01/$record/aggregate.json"
```

Cần sáu export gốc, các snapshot/join và gói organizer đã cấp, nguồn ảnh và metadata lịch sử trong `research/data`, bản `template_head.bin` đã dùng ở P2, lineage và inventory riêng khớp receipt feasibility_02, hai manifest riêng của P2. Hàm `inputs()` đối chiếu trực tiếp các hash. Archive local là phần đầu lưu annotation của tar. Các full frame sử dụng ảnh lịch sử có byte và pixel hash riêng. Thời gian chạy và hash log pytest có thể khác giữa các lần. Bảng `aggregate.json` gắn các hash đầu vào và hai đầu ra riêng. Muốn kiểm pixel từng crop cần giữ nguyên các tệp ảnh gốc.

Bản riêng `qualification/index.html` mở ngoại tuyến trên máy này. Mỗi candidate có đường dẫn ảnh đầy đủ, crop từng vùng và bản ghi tình trạng vùng nằm ngoài khung. Đối chiếu `qualification/evidence.json` để tra candidate, chỉ số region và polygon, ảnh/manifest cha con, nguồn metadata có chỉ số dòng zero-based, biến đổi, hash và lý do từng điều kiện. Hàng đợi riêng ở `organizer_queue.json`. Payload canonical với hai trường đang chờ phải được hoàn tất bằng authority và thời điểm ký thật, sau đó mới qua workflow ký hiện hành.

Tệp công khai gồm số đếm, hash, mã và hướng dẫn. D10 áp dụng cho việc sử dụng và phát hành từng artifact. Các nguồn gốc, ảnh, crop, câu trả lời, bảng đối chiếu, hồ sơ quyền và khóa được giữ trong phạm vi riêng.
