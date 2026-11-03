# Kết quả cải thiện hai nhóm lỗi bằng cặp che/giữ

Ứng viên **hard_42** được chọn bằng development và **không đạt cổng thay model**. Quyết định này đã khóa trước test. Hai seed và mọi kết quả trái chiều đều có trong bảng dưới; kiểm tra tính toàn vẹn đã vượt qua không đồng nghĩa phương pháp mới có hiệu quả tốt hơn.

Thực nghiệm mới sau R2/V3. Hai LoRA mới bắt đầu từ cùng Vintern gốc, đối chiếu hai checkpoint source-supervised có cùng seed/ngân sách. Không so F1 tuyệt đối giữa hai test khác nhau để gọi là cải thiện. Test mới và mọi kết quả âm được giữ.

## Dữ liệu và can thiệp

640 slot train trên128 mẫu giấy tờ; chỉ64 slot của32 ID đã chọn trước được thay bằng cặp ảnh che tất cả nguồn khai báo của A/giữ B và đảo chiều.29 ID ảnh chụp,3 ID giả lập. Không đổi ID/slot exposure,320 update,1280 lượt ảnh, prompt, rect2,384 token, rank8/alpha16, optimizer hoặc checkpoint cuối. Đối chứng là hai adapter uniform-source V3 đã có; không tính chúng thành hai run huấn luyện mới.

Development96 ca trên24 ID; test192 ca trên48 ID mới (24 ảnh MIDV chưa dùng và24 giấy tờ giả lập mới). Test có 179 raster khác nhau theo SHA256; 0 nhóm raster trùng giữa các ID. Giữ các raster trùng/fallback, không coi số lượt đọc là số giấy tờ độc lập. Có 6 fallback dev và 12 fallback test vì không có cặp che/giữ nguyên vẹn gần nhau. Chúng dùng value_mask và vẫn nằm trong kết quả tổng.

Camera EXIF test: {'iPhone XS Max': 20, 'SM-G973F': 4}. Đây là ảnh giấy tờ mẫu công khai, không phải bộ camera mới tự thu thập hoặc người dùng thật. Hai font/layout giả lập mới tương quan với nhau; không quy tác động riêng cho font. Transcript/vị trí lấy từ tác giả/generator; khả năng đọc được vẫn là proxy hình học, chưa có nhãn người độc lập.

## Kết quả trên cùng test mới

| Model | F1 dev | F1 test | Key mất nguồn vẫn xuất | Bỏ sót lân cận | Sai lân cận | Recall lân cận | Thành công cặp |
|---|---:|---:|---:|---:|---:|---:|---:|
| uniform_42 | 0.5243 | 0.5785 | 149 | 78 | 104 | 0.5094 | 10/36 |
| hard_42 | 0.5188 | 0.5899 | 165 | 64 | 107 | 0.5391 | 9/36 |
| uniform_31415 | 0.5223 | 0.5839 | 136 | 73 | 101 | 0.5310 | 10/36 |
| hard_31415 | 0.5034 | 0.5918 | 153 | 71 | 99 | 0.5418 | 7/36 |

Cùng mẫu số cho cả bốn model: 391 trường mất tất cả nguồn khai báo và 371 trường lân cận có nguồn nguyên vẹn. Các số là lượt trường trên nhiều view của48 giấy tờ, không phải số người. “Mất nguồn” được tính theo hợp đồng nhãn hình học; nguồn chưa được parser nhận không được coi là bằng chứng chắc chắn về hallucination.

## So sánh ghép cặp theo seed

| So sánh | ΔF1 test | CI95% theo ID | CI95% nối ID trùng raster |
|---|---:|---|---|
| hard_42 − uniform_42 | +0.0113 | [-0.015030, +0.034945] | [-0.015030, +0.034945] |
| hard_31415 − uniform_31415 | +0.0079 | [-0.023093, +0.039600] | [-0.023093, +0.039600] |

| So sánh | ΔRecall lân cận | CI95% | ΔSố output mất nguồn | CI95% |
|---|---:|---|---:|---|
| hard_42 − uniform_42 | +0.0296 | [-0.018869, +0.073879] | +16 | [-6.00, +45.00] |
| hard_31415 − uniform_31415 | +0.0108 | [-0.048472, +0.071438] | +17 | [-19.00, +54.00] |

Recall lân cận tăng là chiều mong muốn; số output mất nguồn giảm là chiều mong muốn. CI lấy từ cùng resample ID đã đăng ký, không từ coi từng trường là mẫu độc lập. CI theo dữ liệu trong từng seed không thay thế đánh giá biến thiên qua nhiều seed.

Bootstrap10000 lần, seed20261104, phân tầng nguồn. Phân tích chính dùng48 cụm ID; phân tích độ nhạy dùng48 cụm nối ID có raster trùng. Các trường và nhiều view của một giấy tờ không được coi là các ID độc lập. Trong36 cặp test hợp lệ có24 ảnh chụp và12 ảnh giả lập bố cục hàng.12 ảnh giả lập bố cục cột thưa dùng fallback; không kết luận hiệu quả cặp riêng trên bố cục/font đó.

## Độ nhạy với một nguồn MRZ chưa nhận được

Một mẫu ảnh mới có transcript MRZ tác giả dài43/44 ký tự. Parser TD3 không nhận nó; ngoài hợp đồng không đồng nghĩa thông tin thật sự vắng. Phân tích phụ đã đăng ký trước test giữ nguyên output và chỉ loại ID này, còn47 ID/188 ca. Kết quả chính vẫn giữ đủ192 ca; không có lượt model mới hoặc sửa transcript dựa trên dự đoán.

| So sánh | ΔF1 trên47 ID | CI95% |
|---|---:|---|
| hard_42 − uniform_42 | +0.0106 | [-0.015843, +0.035443] |
| hard_31415 − uniform_31415 | +0.0060 | [-0.025384, +0.038996] |

Xem [ghi chú độ bao phủ](HARD_PAIR_COVERAGE_NOTE.md). Không thay kết luận chính bằng một tập con tốt hơn.

## Các nguồn và kiểu ảnh

| Model | Nguồn | View | F1 | Bỏ sót lân cận | Key mất nguồn vẫn xuất |
|---|---|---|---:|---:|---:|
| uniform_42 | authored | full | 0.9917 | 0 | 0 |
| uniform_42 | authored | field_clip | 0.5862 | 1 | 29 |
| uniform_42 | authored | value_mask | 0.8600 | 5 | 3 |
| uniform_42 | authored | pair_mask | 0.9024 | 1 | 7 |
| uniform_42 | midv2020 | full | 0.5917 | 0 | 0 |
| uniform_42 | midv2020 | field_clip | 0.2154 | 31 | 36 |
| uniform_42 | midv2020 | value_mask | 0.3364 | 17 | 55 |
| uniform_42 | midv2020 | pair_mask | 0.5429 | 23 | 19 |
| hard_42 | authored | full | 0.9917 | 0 | 0 |
| hard_42 | authored | field_clip | 0.5965 | 1 | 27 |
| hard_42 | authored | value_mask | 0.9216 | 3 | 2 |
| hard_42 | authored | pair_mask | 0.9268 | 2 | 6 |
| hard_42 | midv2020 | full | 0.6187 | 0 | 0 |
| hard_42 | midv2020 | field_clip | 0.1978 | 31 | 50 |
| hard_42 | midv2020 | value_mask | 0.3609 | 10 | 60 |
| hard_42 | midv2020 | pair_mask | 0.5537 | 17 | 20 |
| uniform_31415 | authored | full | 0.9917 | 0 | 0 |
| uniform_31415 | authored | field_clip | 0.7907 | 1 | 9 |
| uniform_31415 | authored | value_mask | 0.8654 | 3 | 4 |
| uniform_31415 | authored | pair_mask | 0.8589 | 2 | 8 |
| uniform_31415 | midv2020 | full | 0.5775 | 0 | 0 |
| uniform_31415 | midv2020 | field_clip | 0.1931 | 32 | 43 |
| uniform_31415 | midv2020 | value_mask | 0.3614 | 8 | 55 |
| uniform_31415 | midv2020 | pair_mask | 0.5545 | 27 | 17 |
| hard_31415 | authored | full | 0.9917 | 0 | 0 |
| hard_31415 | authored | field_clip | 0.5965 | 1 | 27 |
| hard_31415 | authored | value_mask | 0.9231 | 3 | 2 |
| hard_31415 | authored | pair_mask | 0.9222 | 2 | 7 |
| hard_31415 | midv2020 | full | 0.6005 | 0 | 0 |
| hard_31415 | midv2020 | field_clip | 0.1825 | 35 | 44 |
| hard_31415 | midv2020 | value_mask | 0.3746 | 12 | 53 |
| hard_31415 | midv2020 | pair_mask | 0.5673 | 18 | 20 |

## Định dạng và ngân sách đọc

| Model | JSON hợp lệ | Chạm384 token |
|---|---:|---:|
| uniform_42 | 187/192 | 1 |
| hard_42 | 188/192 | 0 |
| uniform_31415 | 185/192 | 3 |
| hard_31415 | 183/192 | 1 |

Giữ mọi ca lỗi JSON và chạm ngân sách trong kết quả tổng; không bỏ hoặc chạy lại với prompt tốt hơn. Chạm384 token là bộ đếm sinh, không tự chứng minh đáp án bị cắt. Chỉ số trường phải được đọc cùng chỉ số định dạng và thành công cặp.

## Ngân sách hiệu dụng và bộ đếm bộ nhớ

| Run | Trạng thái | Update | Lượt ảnh | Token loss | Max allocated/reserved GiB |
|---|---|---:|---:|---:|---|
| uniform_42 | đối chứng đã có | 320 | 1280 | 75088 | 2.801 / 9.195 |
| hard_42 | huấn luyện mới | 320 | 1280 | 79974 | 2.802 / 9.270 |
| uniform_31415 | đối chứng đã có | 320 | 1280 | 75088 | 2.802 / 11.953 |
| hard_31415 | huấn luyện mới | 320 | 1280 | 79974 | 2.802 / 8.369 |

Khớp ID/lượt ảnh và số update không đồng nghĩa khớp số token, thời gian hoặc FLOPs. Đối chứng là các run lịch sử; chính sách cache/tài nguyên đã thay đổi như ghi chú runtime. Token và update trong bảng lấy từ log canonical của320 bước hiệu dụng; các update phải tính lại và chẩn đoán được kê riêng bên dưới. Cột bộ nhớ là max trên các event giữ lại, không chứng minh ưu thế bộ nhớ hoặc tốc độ huấn luyện.

Đã replay 1152 hàng điểm từ output nguyên văn; 1008 lượt sinh mới từ feature cache và 144 output development cũ được tái chấm. Thêm16 lượt từ pixel trên8 ảnh/4 ID: 0 hash khác với test. p50/p95 đầu cuối mẫu lặp: 18.14/36.08s. Các timer feature-cache và pixel-level có phạm vi khác nhau; không tuyên bố ưu thế tốc độ. VRAM allocated/reserved là bộ đếm PyTorch, không phải tổng VRAM vật lý.

## Sự cố tài nguyên và kiểm tra resume

Lượt hard42 được dừng có kiểm soát sau khi đã lưu checkpoint80 do cache gây áp lực bộ nhớ. Có 43 update sau checkpoint được ghi nhận rồi phát lại; không cộng chúng vào ngân sách hiệu dụng320 hoặc coi là dữ liệu độc lập. Hai bước chẩn đoán ngoài primary từ cùng checkpoint80 kiểm tra cache gốc và cache thu hồi: mọi192 tensor LoRA, optimizer và RNG khớp, sai khác tối đa0. Cấu hình cache đã được công bố trước resume; không đổi input/loss/seed/ngân sách. Parity một bước không chứng minh mọi chuỗi cập nhật tương đương. Đối chiếu thêm 43 event scalar được phát lại cũng khớp; đây không phải so mọi tensor sau từng bước. Peak/timer trước thay đổi vẫn giữ nguyên. Xem [ghi chú runtime](HARD_PAIR_RUNTIME_NOTE.md).

## Quyết định và giới hạn

Ứng viên hard chọn bằng development: **hard_42**; cổng promotion: **False**. Quyết định được công bố trước test. Web cũ được khôi phục sau thực nghiệm; không đổi model dựa trên test. Muốn đưa ứng viên mới vào web phải giữ quyết định development và hoàn tất kiểm thử phục vụ riêng.

Can thiệp này đồng thời thay crop bằng đầy đủ ngữ cảnh và thay chính sách mask ở64 slot; không tách riêng lợi ích hard selection, cặp đối nghịch hoặc số token đáp án. Chỉ một backbone nhỏ, hai seed; điều kiện sáng/che là giả lập trên giấy tờ mẫu. Chưa có nhãn legibility độc lập, kiểm thử camera người dùng hoặc chứng nhận chống giả. Không kết luận đạt CORE B, SOTA hoặc xác minh danh tính từ các kết quả này.

Khóa trước huấn luyện: `1939a90552da758e8cf951aaee3ac22a9fdae506`. Khóa trước test: `f27ecb68b47483279caae29f9ba9894c57326878`. Bảo toàn101 file V1,63 file V4 và hợp đồng R2/V3. Ảnh, nhãn riêng, output OCR nguyên văn và weights mới không đưa lên Git.

Bằng chứng: [audit](results/hard_pairs_v1/audit.json), [CI](results/hard_pairs_v1/paired_intervals.json), [protocol](HARD_PAIR_PROTOCOL.md), [runbook](HARD_PAIR_RUNBOOK.md), [đối chiếu nghiên cứu và giới hạn novelty](HARD_PAIR_RELATED_WORK.md).
