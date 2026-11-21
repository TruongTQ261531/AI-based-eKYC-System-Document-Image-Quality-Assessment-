# Tái lập audit P2 trên máy có dữ liệu nghiên cứu

Chạy PowerShell tại repository nghiên cứu. Bản chạy ngày 21/11 dùng Python và Pillow ở các phiên bản ghi trong aggregate.json. Cần có ảnh lịch sử trong research/data, metadata đi cùng, template_head.bin của MIDV-2020, cùng lineage.json và c2_candidates.json riêng khớp receipt feasibility_02. Không cần model, GPU hoặc phiếu khảo sát.

```powershell
$python = '..\..\.venv\Scripts\python.exe'
$module = 'research.evidence_contract.oracle_reliability'
$local = 'research/evidence_contract/local/p2_20261120'
$run = 'replay_' + [guid]::NewGuid().ToString('N')
& $python -B -X utf8 -m "$module.p2_audit" --run "inventory_$run" --dry-run
& $python -B -X utf8 -m "$module.p2_audit" --run $run
& $python -B -X utf8 -m "$module.verify_p2" "$local/$run"
& $python -B -X utf8 -m "$module.verify_d4" research/evidence_contract/execution/master_01/d4_development_20261117/controls_01
$tests = 'research/evidence_contract/tests'
& $python -B -X utf8 -m pytest -q -p no:cacheprovider "$tests/test_pixel_lineage_audit.py" "$tests/test_c2_evidence_audit.py" "$tests/test_semantic_lineage_c2.py" "$tests/test_verify_d4.py" --basetemp "$local/targeted_$run"
& $python -B -X utf8 -m pytest -q -p no:cacheprovider $tests --basetemp "$local/full_$run"
Get-FileHash "$local/$run/aggregate.json"
```

Đối chiếu hash aggregate với verification.json khi môi trường, code, dữ liệu và config trùng bản chạy. Nếu khác, đối chiếu từng digest trong aggregate trước khi diễn giải số đếm. Kiểm tra bảo toàn dùng hash byte của working tree Windows tại baseline, bao gồm quy ước xuống dòng của lần checkout.

## Phạm vi và quyền

Dữ liệu được đọc để kiểm tra kỹ thuật nội bộ theo yêu cầu của chủ dự án. Phạm vi pixel là ảnh raster trong research/data, gồm JPEG/MPO nhiều khung, gồm bộ dựng của dự án, MIDV-2020, MIDV-UP và các bản dẫn xuất đang lưu. Tệp nén, video, weights, thư mục reviewer, dữ liệu camera trực tiếp và tài sản ngoài workspace nằm ngoài khung kiểm kê. Phạm vi C2 là 1.100 cặp từ annotation template MIDV-2020. Giấy phép ở mức nhà cung cấp và việc sở hữu bản local chưa quyết định quyền tái phát hành từng artifact. D10 vẫn cần hồ sơ quyền theo phiên bản. Chỉ aggregate, mã và receipt được phát hành.

Duyệt tệp theo thứ tự ổn định, kiểm từng thành phần đường dẫn và reparse point. Tệp tối đa 64 MiB, tối đa 32 triệu pixel mỗi khung và tối đa 4 khung MPO. Từng khung được giải mã nối tiếp. Khung chính dùng cho các nhóm so sánh. Với từng khung phụ, bản ghi lưu chỉ số và hash nếu đọc được, hoặc loại lỗi nếu giải mã thất bại. Trạng thái `PARTIAL_AUXILIARY_FRAME_COVERAGE` cho biết tất cả khung chính đã được đọc nhưng còn thiếu khung phụ. Manifest metadata được đọc từng tệp với giới hạn 120 MB. Chỉ giữ các khóa phục vụ đối chiếu. Bộ nhớ cho index metadata và các nhóm tăng theo số mục kiểm kê. Bản chi tiết, đường dẫn, mã giấy tờ và thành phần từng nhóm chỉ lưu trong vùng local.

## Định nghĩa phép đo

- File trùng có cùng SHA-256 trên byte. Pixel trùng có cùng SHA-256 sau EXIF transpose, chuyển RGB 8 bit, thêm version, mode, chiều rộng và chiều cao vào đầu chuỗi byte. Bỏ alpha, không hiệu chỉnh màu theo ICC.
- dHash so 64 cặp pixel xám liền kề trên ảnh thu nhỏ 9×8. Khoảng cách Hamming tối đa 3 tạo cạnh. Mỗi nhóm là thành phần liên thông có ít nhất hai giá trị pixel hash khác nhau. Hai đầu của một chuỗi có thể xa nhau hơn 3 bit. Mẫu bố cục giống nhau có thể tạo dương tính giả. Phép cắt mạnh, xoay hoặc đổi nội dung có thể làm mất cạnh.
- Metadata gắn với ảnh khi đường dẫn và SHA file khớp. Một manifest tham chiếu ảnh của bộ khác được tính cho cả hai bộ có chứng cứ. Cross-role đếm mọi nhãn role khác nhau, gồm cả nhãn lịch sử đặc thù. Mục này cần đọc cùng role thực tế trước khi kết luận rò rỉ train/test.
- Physical ID được đếm theo mã ghi trong manifest. Template đếm cặp bộ dữ liệu–layout; capture đếm cặp ID–nhãn capture. Hai số này đo nhóm nhãn ghi nhận, có thể thiếu hoặc gộp nhiều lần chụp thật. Hash nguồn/cha khớp file xác minh liên kết byte được ghi nhận. Việc tái dựng chính xác phép crop/resize hoặc vùng chữ cần tham số và annotation bổ sung.
- Một cặp C2 cần bảy điều kiện nội dung/quyền và hai nguồn khác ID. PASS/FAIL/UNKNOWN được ghi cho từng điều kiện. Parser MRZ, trùng literal, một ảnh cùng physical ID hoặc một hash cha khớp là đầu mối điều tra. Để quyết định support cần gắn đúng vùng nguồn của trường trên ảnh trước và sau mutation.
