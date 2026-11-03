# Mục 4: đối chứng khớp ngân sách và test mới

Trong bốn so sánh chính, 0/4 ủng hộ hard cao hơn và 0/4 ủng hộ hard thấp hơn theo cả p Holm < 0,05 và CI 98,75% đã đăng ký. Chưa đủ bằng chứng phân biệt hard với random/repeat trên bộ test này. So với uniform (đối chứng phụ), ΔF1 theo hai seed là 42: -0.01376, 31415: +0.00835.

Đã hoàn tất vòng đối chứng và audit. Đây là kiểm chứng một giả thuyết về cách chọn/che dữ liệu; hoàn tất mục4 không đồng nghĩa đã cải thiện model hoặc đạt CORE B. Các phương án và checkpoint cuối được khóa trước test; không chọn model triển khai bằng kết quả test.

## Những gì được so sánh

Tám adapter: bốn phương án × hai seed42/31415. Uniform V3 và hard HP là bốn checkpoint lịch sử được giữ nguyên. Random và repeat là bốn LoRA mới từ cùng Vintern gốc, không warm-start từ một adapter khác. Mỗi arm có128 ID,640 slot theo cùng thứ tự,320 update,1280 lượt ảnh, accumulation4, rank8/alpha16, cùng prompt17 khóa tùy chọn, rect2 và ngân sách sinh384 token.

Random dùng cùng thuật toán tạo cặp, nhưng chọn ID theo nguồn/bố cục và ngân sách token đã khớp. Repeat dùng cùng32 ID như hard, lặp một hướng che ở cả hai slot thay vì A/B. Loss hiện học từng ảnh độc lập; đây là đối chứng độ đa dạng hướng che, không phải bỏ một pair loss.

Đã xét đầy đủ16800 tổ hợp: 45 tổ hợp khớp token, mức khác biệt tối đa là5 ID, có10 tổ hợp đạt mức này. Chọn bằng reservoir sampling với seed cố định. Đây là số tổ hợp dữ liệu, không phải số lần chạy model. Random trùng27/32 ID chọn che với hard. Vì hỗ trợ dữ liệu hạn chế, không diễn giải thành phép thử rộng giữa hai tập32 ID hoàn toàn khác nhau.

Ba phương án chính hard/random/repeat khớp tổng token đáp án. Uniform cũ có ít token hơn và là đối chứng phụ cho toàn bộ can thiệp. Không tuyên bố khớp FLOPs, thời gian hoặc số token trong từng update.

| Arm | Token đáp án mỗi seed | Slot đổi pixel | ID đổi pixel | Pixel train khác nhau |
|---|---:|---:|---:|---:|
| uniform | 75088 | 0 | 0 | xem manifest |
| hard | 79974 | 64 | 32 | 640 |
| random | 79974 | 63 | 32 | 640 |
| repeat | 79974 | 64 | 32 | 608 |

640 slot không đồng nghĩa640 ảnh độc lập: repeat cố ý lặp pixel. Random gán lại64 slot nhưng có một ảnh bằng pixel với ô gốc, nên số đổi pixel được báo riêng. Bản chuẩn bị đầu và lượt tìm mức6 ID không thành công được giữ trong cache; điều chỉnh lựa chọn xảy ra trước mọi update mới. Xem [training design](results/fair_controls_v1/training_design.json), [exposure](results/fair_controls_v1/exposure_audit.json) và [nhật ký điều chỉnh chuẩn bị](results/fair_controls_v1/preparation_revision.json).

## Tập kiểm chứng và tính độc lập

Test mới192 view trên48 ID giấy tờ mẫu:24 ảnh MIDV từ các member16/17/18 đã chọn bằng metadata và24 mẫu giả lập mới. Có180 pixel raster khác nhau, 0 nhóm pixel trùng giữa các ID. Có12 fallback pair_mask giữ trong kết quả tổng. Không trùng ID, pixel đã giải mã hoặc fingerprint đáp án đầy đủ với các vai trò cũ được kiểm kê.

EXIF ảnh mới: {'iPhone XS Max': 10, 'SM-G973F': 14}. Đây là ảnh mẫu từ nguồn công khai và generator, không phải ảnh camera tự thu thập mới, người dùng thật hoặc kiểm chứng tách người tự nhiên. Giữ generator/font/layout cũ, thay nội dung/ID; không nhận đóng góp font/layout mới. Legibility vẫn là proxy hình học, chưa có đánh giá người độc lập.

## Kết quả trên cùng192 view mới

| Model | F1 dev | F1 test | Output mất nguồn | Bỏ sót lân cận | Sai lân cận | Recall lân cận | Cặp thành công |
|---|---:|---:|---:|---:|---:|---:|---:|
| uniform_42 | 0.5243 | 0.6007 | 108 | 78 | 85 | 0.5275 | 11/36 |
| hard_42 | 0.5188 | 0.5869 | 131 | 59 | 104 | 0.5275 | 12/36 |
| random_42 | 0.5154 | 0.5795 | 125 | 63 | 108 | 0.5043 | 12/36 |
| repeat_42 | 0.5299 | 0.5831 | 129 | 53 | 108 | 0.5333 | 12/36 |
| uniform_31415 | 0.5223 | 0.5736 | 108 | 64 | 106 | 0.5072 | 10/36 |
| hard_31415 | 0.5034 | 0.5820 | 126 | 51 | 111 | 0.5304 | 10/36 |
| random_31415 | 0.5048 | 0.5731 | 135 | 72 | 100 | 0.5014 | 9/36 |
| repeat_31415 | 0.5130 | 0.5726 | 135 | 53 | 110 | 0.5275 | 11/36 |

Mẫu số chung: 381 lượt trường mất nguồn khai báo, 345 lượt trường lân cận có nguồn body nguyên vẹn. Các số là lượt trường trên nhiều view, không phải số người. Nguồn chưa được parser nhận không tự chứng minh hallucination.

## Bốn so sánh chính đã đăng ký

| So sánh | ΔF1 | CI95% | CI98,75% | p hoán vị | p Holm | Nhận định có điều kiện |
|---|---:|---|---|---:|---:|---|
| hard_42 − random_42 | +0.0075 | [-0.00937, +0.02830] | [-0.01276, +0.03433] | 0.52995 | 1.00000 | chưa phân biệt rõ |
| hard_42 − repeat_42 | +0.0038 | [-0.00679, +0.01403] | [-0.00986, +0.01692] | 0.49015 | 1.00000 | chưa phân biệt rõ |
| hard_31415 − random_31415 | +0.0089 | [-0.00656, +0.02459] | [-0.01032, +0.02927] | 0.30067 | 1.00000 | chưa phân biệt rõ |
| hard_31415 − repeat_31415 | +0.0093 | [-0.00579, +0.02510] | [-0.00940, +0.02990] | 0.28037 | 1.00000 | chưa phân biệt rõ |

Bootstrap10000 lần phân tầng nguồn, lấy ID làm cụm; CI98,75% Bonferroni cho bốn so sánh chính. Hoán vị10000 lần đổi nhãn hai model cho toàn bộ view của từng ID, p=(extreme+1)/10001; Holm trên bốn p chính. Giả định exchangeability và hai seed là giới hạn. Các kiểm định theo ID có điều kiện trên model/template/camera cố định, không chứng minh ưu thế trên quần thể seed hoặc camera mới. Chỉ số lỗi phụ không được dùng chọn một test subset thuận lợi.

Độ nhạy nối ID có pixel trùng dùng48 cụm, từ48 ID. Kiểm kê MRZ trước test có0 ID ngoài phần source parser nhận; phân tích độ nhạy giữ cùng output và chỉ loại các ID đã định trước. Kết quả chính luôn giữ192 view.

Xem [thống kê chính và phụ](results/fair_controls_v1/paired_statistics.json), [cụm pixel](results/fair_controls_v1/pixel_cluster_sensitivity.json), [độ bao phủ nguồn](results/fair_controls_v1/source_coverage_sensitivity.json), [các lát nguồn/view/device/layout](results/fair_controls_v1/slices.json).

## Định dạng và kiểm tra từ pixel

| Model | JSON hợp lệ | Chạm384 token | Fresh khác test | Pixel panel p50/p95 giây |
|---|---:|---:|---:|---|
| uniform_42 | 187/192 | 2 | 0/8 | 13.59/16.30 |
| hard_42 | 188/192 | 4 | 0/8 | 14.66/18.61 |
| random_42 | 187/192 | 3 | 0/8 | 14.54/18.34 |
| repeat_42 | 190/192 | 2 | 0/8 | 14.87/18.38 |
| uniform_31415 | 190/192 | 2 | 0/8 | 13.41/18.81 |
| hard_31415 | 189/192 | 0 | 0/8 | 14.19/18.52 |
| random_31415 | 185/192 | 2 | 0/8 | 14.73/18.05 |
| repeat_31415 | 189/192 | 0 | 0/8 | 14.48/18.39 |

Fresh dùng bốn input trên hai ID, mỗi model đọc lại hai lần:64 lượt. Đây là kiểm tra nhất quán và panel thời gian nhỏ, không phải64 ID hoặc benchmark tốc độ CPU/SOTA. Giữ cả lỗi JSON và chạm ngân sách; không chạy lại với prompt tốt hơn sau khi xem test.

## Bằng chứng và giới hạn còn lại

Đã replay2304 hàng điểm: 1920 lượt sinh mới và384 output development cũ được tái chấm; thêm64 lượt từ pixel và10 lượt probe development. Có0 fresh hash khác test. Các số lượt sinh văn bản không gộp với lượt chạy encoder ảnh. Đã chạy lại encoder trên 984 đầu vào để đối chiếu đặc trưng; nguồn đặc trưng tham chiếu: {'current_cache': 925, 'historical_cache': 5, 'computed_during_audit': 54}. Có thêm 54 lượt encoder để tạo tham chiếu còn thiếu cache. Rescoring, tổ hợp dữ liệu, bootstrap và hoán vị chỉ là tính toán lại, không sinh thêm output OCR. Xem [audit encoder và cache](results/fair_controls_v1/feature_audit.json).

Bảo toàn101 file V1, 63 file V4, 53 file HP và hợp đồng R2/V3. Khóa trước train: `bfd017688f09c6c1c544a8b3d667e7433fe66937`; trước test: `167d8560a920b6fc500d7310dcd8e453c91f12ce`. Checkpoint cuối của cả tám model đã kiểm tra tensor/optimizer/order/token/hash trước test và xác nhận lại sau test.

Backup update phải tính lại trong vòng mới: []. Log/checkpoint gián đoạn nếu có được giữ, không cộng replay vào320 bước hiệu dụng hoặc gọi là run độc lập. Cấu hình tài nguyên của các run lịch sử khác nhau; số token bằng nhau không chứng minh thời gian/FLOPs bằng nhau.

Đối chứng chọn ca chỉ khác tối đa năm ID dưới điều kiện hiện có; power hạn chế. Đối chứng repeat vẫn thay đổi phân bố trường/token theo từng slot. Uniform không khớp token và chỉ là đối chứng phụ; V1 không bị biến thành đối chứng nhân quả cùng ngân sách. Chưa có người gán nhãn legibility, ảnh mới tự thu thập hoặc chứng nhận PAD. Không tự thay model web hoặc khẳng định đủ đóng góp CORE B. Mục2 sau đây phải chọn cấu hình trên development và dùng test mới để xác nhận nếu đã dùng kết quả này để điều chỉnh phương pháp.

Bằng chứng: [audit](results/fair_controls_v1/audit.json), [preflight](results/fair_controls_v1/preflight.json), [inventory checkpoint](results/fair_controls_v1/training_state_inventory.json), [protocol](FAIR_CONTROLS_PROTOCOL.md), [runbook](FAIR_CONTROLS_RUNBOOK.md).

## Gián đoạn ghi tiến độ

Một stage development dừng vì Windows từ chối atomic replace file progress. Bốn model đã huấn luyện và56 output đã lưu được giữ nguyên; chúng được kiểm tra hash sau khi tiếp tục. Đổi reader sang delete-sharing và retry metadata với cùng payload, không sửa dữ liệu/model/phép chấm hoặc huấn luyện lại.56 output cache không bị tính thành56 lượt OCR mới. Log lỗi gốc được giữ; xem [ghi chú I/O](FAIR_CONTROLS_IO_NOTE.md) và [record phục hồi](results/fair_controls_v1/io_recovery.json).

## Kiểm thử phần mềm và localhost

304 kiểm tra Python, 1496 subtest và48 kiểm tra hành vi giao diện đã qua. Bộ chính có4 bài cần overlay; đã chạy riêng và đều qua. Có1 cảnh báo trong log, không cài dependency mới.

Đã xác nhận eKYC8000 ready/API3.2.0 và web nghiên cứu8003 ready, vẫn dùngpartial_42. Health của8003 thuộc nghiên cứu V3 cũ, không dùng để đếm run FC. Các kiểm thử là mô phỏng/HTTP, không phải kiểm chứng camera người dùng thật. Xem [bằng chứng/hash log](results/fair_controls_v1/software_verification.json).
