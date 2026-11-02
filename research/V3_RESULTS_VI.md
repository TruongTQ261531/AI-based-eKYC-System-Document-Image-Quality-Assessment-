# V3: kết quả xét nguồn thông tin còn nhìn thấy

Đã hoàn thành hai lượt LoRA bổ sung với cùng pixel và ngân sách R2, benchmark tám model VLM và sáu cấu hình hậu xử lý OCR CPU. Kết quả là thực nghiệm trên giấy tờ mẫu, không phải chứng nhận eKYC hoặc bảo đảm được nhận CORE B.

## Vấn đề và can thiệp có kiểm soát

Một giá trị trên hộ chiếu có thể xuất hiện ở ô thân thẻ, bản phiên âm và MRZ. Che một ô không đồng nghĩa mất thông tin. V3 tạo nhãn theo OR giữa các nguồn, AND giữa các dòng thành phần; ngày tháng chỉ dùng độ đầy đủ thực sự được in. MRZ chỉ có YYMMDD không cho phép tự bịa thêm thế kỷ. Các vùng và văn bản gốc do tác giả MIDV cung cấp; đây vẫn là proxy hình học, chưa có nhãn legibility độc lập của người đọc.

- Giữ nguyên toàn bộ 1496 dòng ảnh R2, cùng hash và thứ tự. Train128 ID/640 slot ở nhánh partial,320 bước ×4 tích lũy =1280 lượt ảnh, hai seed42/31415.
- Hai model source-aware được khởi tạo lại từ Vintern gốc, không tiếp tục adapter R2. So với R2 partial cùng seed, chỉ target giám sát thay đổi.
- Thay đổi 22 target trong toàn bộ bảng train hai nhánh; 17 trường hợp test có target khác; bổ sung 83 key còn có nguồn hỗ trợ trong ảnh test.
- Test48 ID/144 ảnh:24 SPECIMEN mới và24 giấy tờ mẫu chụp bằng điện thoại;14 nguồn Samsung không có trong train, 8 ID của hai loại fin_id/lva_passport giữ riêng khỏi train. Các giới hạn camera/ID và pretraining như R2 vẫn còn.
- Cả hai khóa được kiểm tra remote tại [ca31e89](https://github.com/TruongTQ261531/AI-based-eKYC-System-Document-Image-Quality-Assessment-/commit/ca31e894a7945c02d0eea17a9614c1e0587562a4) trước test.
- Sáu output R2 được chấm lại trên cùng pixel, không gọi đó là sáu thí nghiệm suy luận độc lập mới. Báo cáo R2 theo hợp đồng cũ vẫn được giữ nguyên.

## Test dưới hợp đồng nguồn V3

| Phương án | F1 mọi nguồn | F1 đủ độ chính xác ngày | F1 ảnh dựng | F1 ảnh chụp | Bỏ sót | Sai giá trị | Key ngoài nhãn |
|---|---:|---:|---:|---:|---:|---:|---:|
| Vintern gốc | 0.1757 | 0.1757 | 0.1772 | 0.1744 | 52 | 374 | 1602 |
| V1 chuyển tác vụ | 0.3413 | 0.3413 | 0.7073 | 0.1748 | 427 | 76 | 112 |
| R2 complete42 | 0.3644 | 0.3644 | 0.4521 | 0.3189 | 95 | 292 | 350 |
| R2 body-partial42 | 0.3786 | 0.3786 | 0.5000 | 0.3133 | 175 | 241 | 216 |
| R2 complete31415 | 0.3670 | 0.3670 | 0.4404 | 0.3282 | 116 | 277 | 327 |
| R2 body-partial31415 | 0.3978 | 0.3978 | 0.5276 | 0.3309 | 148 | 248 | 222 |
| V3 source-partial42 | 0.3947 | 0.3947 | 0.5091 | 0.3340 | 162 | 238 | 227 |
| V3 source-partial31415 | 0.4063 | 0.4063 | 0.5161 | 0.3502 | 140 | 244 | 243 |
| rapid_latin_v5/body | 0.1916 | 0.1916 | 0.5000 | 0.0000 | 582 | 25 | 1 |
| rapid_latin_v5/mrz_checks | 0.2256 | 0.2180 | 0.5000 | 0.0602 | 567 | 25 | 1 |
| rapid_latin_v5/mrz_format | 0.2256 | 0.2180 | 0.5000 | 0.0602 | 567 | 25 | 1 |
| rapid_v4/body | 0.1938 | 0.1938 | 0.4860 | 0.0000 | 560 | 44 | 1 |
| rapid_v4/mrz_checks | 0.2834 | 0.2621 | 0.4860 | 0.1597 | 518 | 44 | 1 |
| rapid_v4/mrz_format | 0.2834 | 0.2621 | 0.4860 | 0.1597 | 518 | 44 | 1 |

Cột độ chính xác ngày chỉ chấp nhận mức năm đầy đủ nhất còn được thể hiện trong các nguồn khai báo. Ngày hai chữ số năm vẫn là một quan sát hợp lệ, nhưng không được đánh đồng với ngày có năm bốn chữ số. “Ngoài nhãn” luôn tương đối với tập nguồn khai báo, không chứng minh mọi giá trị là bịa hoặc mọi nguồn ngoài hợp đồng đều không tồn tại.

## Ngân sách và chi phí huấn luyện

| Nhánh | Seed | Bước | Lượt ảnh | Token tính loss | Token đầu vào + đáp án | Giây vòng tối ưu | GPU allocated tối đa (GiB) |
|---|---:|---:|---:|---:|---:|---:|---:|
| control | 42 | 320 | 1280 | 95920 | 1016240 | 901.2 | 2.802 |
| partial | 42 | 320 | 1280 | 73564 | 993884 | 901.8 | 2.801 |
| source | 42 | 320 | 1280 | 75088 | 995408 | 1094.5 | 2.801 |
| control | 31415 | 320 | 1280 | 95920 | 1016240 | 905.9 | 2.802 |
| partial | 31415 | 320 | 1280 | 73564 | 993884 | 1070.6 | 2.802 |
| source | 31415 | 320 | 1280 | 75088 | 995408 | 1135.2 | 2.802 |

Ngân sách được khớp theo bước và lượt ảnh; số token giám sát thay đổi theo target và được công khai ở trên. Thời gian vòng tối ưu không bao gồm mọi bước nạp model/chuẩn bị dữ liệu. GPU allocated là bộ đếm PyTorch, không phải toàn bộ VRAM của hệ thống. Bộ đếm reserved trên Windows/WDDM không được gọi là lượng VRAM vật lý đã dùng.

## Thời gian và proxy yêu cầu chụp lại

| Phương án | Đường đo | p50 (s) | p95 (s) | Output rỗng hoặc JSON lỗi |
|---|---|---:|---:|---:|
| Vintern gốc | VLM GPU, đọc feature cache | 21.53 | 30.46 | 3.5% |
| V1 chuyển tác vụ | VLM GPU, đọc feature cache | 5.23 | 17.70 | 31.9% |
| R2 complete42 | VLM GPU, đọc feature cache | 14.03 | 30.20 | 2.8% |
| R2 body-partial42 | VLM GPU, đọc feature cache | 13.75 | 27.20 | 3.5% |
| R2 complete31415 | VLM GPU, đọc feature cache | 14.79 | 30.39 | 5.6% |
| R2 body-partial31415 | VLM GPU, đọc feature cache | 13.36 | 20.00 | 4.9% |
| V3 source-partial42 | VLM GPU, đọc feature cache | 9.94 | 18.98 | 4.9% |
| V3 source-partial31415 | VLM GPU, đọc feature cache | 10.02 | 18.14 | 3.5% |
| rapid_latin_v5/body | OCR CPU, xử lý ảnh + hậu xử lý | 1.71 | 4.17 | 73.6% |
| rapid_latin_v5/mrz_checks | OCR CPU, xử lý ảnh + hậu xử lý | 1.71 | 4.17 | 71.5% |
| rapid_latin_v5/mrz_format | OCR CPU, xử lý ảnh + hậu xử lý | 1.71 | 4.17 | 71.5% |
| rapid_v4/body | OCR CPU, xử lý ảnh + hậu xử lý | 2.14 | 5.45 | 72.2% |
| rapid_v4/mrz_checks | OCR CPU, xử lý ảnh + hậu xử lý | 2.14 | 5.45 | 68.1% |
| rapid_v4/mrz_format | OCR CPU, xử lý ảnh + hậu xử lý | 2.14 | 5.45 | 68.1% |

Các dòng GPU dùng cache chưa phải độ trễ camera đầu cuối. Phép lặp ảnh mới của model được chọn được báo bên dưới; nạp model nguội được đo riêng với thời gian suy luận khi chạy web. CPU và GPU không phải đối chiếu tốc độ trên phần cứng tương đương. Một số lượt CPU chạy song song công việc GPU; không dùng bảng này để tuyên bố thắng tuyệt đối về tốc độ. Output rỗng/JSON lỗi chỉ là proxy, không phải tỷ lệ khách hàng chụp lại được quan sát, cũng không phải quyết định eKYC.

## So sánh đúng cặp và khoảng tin cậy

| So sánh | ΔF1 | CI95% theo ID |
|---|---:|---:|
| source_42 − partial_42 | +0.0160 | [-0.0000, +0.0322] |
| source_31415 − partial_31415 | +0.0085 | [-0.0168, +0.0339] |
| source_42 − control_42 | +0.0303 | [+0.0029, +0.0589] |
| source_42 − v1 | +0.0534 | [+0.0125, +0.0985] |

Bootstrap10000 lần theo48 cụm ID, phân tầng24+24 nguồn; hai seed được báo riêng. Đây không phải CI bao phủ mọi biến động training hay camera ngoài mẫu.

## Phân tích mô tả ảnh hưởng của hợp đồng nhãn

Phân tích sau thực nghiệm, không dùng chọn model. Giữ nguyên từng output để chấm theo hai hợp đồng; không phát sinh suy luận mới.
Tổng trường tham chiếu test: thân thẻ 599, nhiều nguồn 682. Nguồn hỗ trợ cho key bổ sung: {'MRZ': 82, 'body': 1}.

| Model | F1 thân thẻ | F1 nhiều nguồn | Ngoài nhãn cũ → đúng theo nguồn | Mới được tính nhưng model bỏ sót |
|---|---:|---:|---:|---:|
| Vintern gốc | 0.1696 | 0.1757 | 9 | 15 |
| V1 chuyển tác vụ | 0.3685 | 0.3413 | 1 | 64 |
| R2 complete42 | 0.3737 | 0.3644 | 5 | 16 |
| R2 body-partial42 | 0.3949 | 0.3786 | 2 | 25 |
| R2 complete31415 | 0.3753 | 0.3670 | 4 | 24 |
| R2 body-partial31415 | 0.4044 | 0.3978 | 6 | 19 |
| V3 source-partial42 | 0.4012 | 0.3947 | 7 | 20 |
| V3 source-partial31415 | 0.4003 | 0.4063 | 15 | 6 |

## Kiểm chứng và ứng dụng local

- Phát lại 3024 hàng kết quả nguồn từ output nguyên văn. Số hàng chấm lại và ba hậu xử lý dùng chung OCR không được tính thành số lần suy luận độc lập.
- Audit R2 đã đối chiếu mọi feature vision dùng trong nghiên cứu với trích xuất mới từ pixel, cùng các file/weights/checkpoint và budget. V3 dùng đúng các pixel/feature này.
- Hai lượt OCR CPU độc lập khớp nguyên văn ở 432 cặp output. Mỗi nhóm ba hậu xử lý V3 vẫn dùng chung một lần OCR, được đếm riêng với số cấu hình chấm điểm.
- Model được chọn từ development: **partial_42**; cổng khuyến nghị: **False**. Nếu model source-aware không tốt hơn, không gọi nó là model thắng chỉ vì là phiên bản mới.
- Lặp thêm16 lần suy luận ảnh mới trên8 ảnh/4 ID: sai khác 0; p50=10.12s, p95=16.81s. Thời gian này có xử lý ảnh/vision, khác đọc feature cache.
- Không tự gán thế kỷ; chữ số kiểm tra MRZ không chứng minh giấy tờ thật. Không phê duyệt danh tính, không đánh giá liveness ở trang OCR nghiên cứu.
- Camera thật của người dùng chưa được dùng làm benchmark. Nhãn sửa bằng tay trên web được phân biệt với kết quả OCR và chỉ tồn tại trên trình duyệt.

Đã chuẩn bị [trang đánh giá độc lập](http://127.0.0.1:8003/review) với 48 ảnh, mỗi ID một view. Hiện chưa nhận được nhãn của người; kiểm thử giao diện bằng câu trả lời giả không tính là annotation. Xem V3_HUMAN_REVIEW.md; phần bổ sung không đổi tham chiếu chính đã khóa.

## Đóng góp có thể viết và giới hạn

Có thể viết về sai lệch đánh giá khi dùng một ô làm toàn bộ bằng chứng, nhãn theo nhiều nguồn/thành phần và độ chính xác ngày, và phép thử LoRA ít tham số được kiểm soát pixel/ngân sách. Chỉ kết quả thực nghiệm mới quyết định can thiệp có hiệu quả.
Không nhận OR/AND, MRZ fusion hoặc LoRA là phát minh đầu tiên. Cần đối chiếu với [KIE-HVQA](https://arxiv.org/abs/2506.20168), [nghiên cứu redundancy trong OCR](https://arxiv.org/abs/2508.14557), [BoundingDocs](https://flore.unifi.it/retrieve/271bfa4d-4b12-4bd3-8ec1-a5f64ce8ca0b/s10032-025-00563-5.pdf) và [ICAO Doc9303 Part4](https://www.icao.int/sites/default/files/publications/DocSeries/9303_p4_cons_en.pdf).
CORE B chưa thể khẳng định chỉ nhờ fine-tune/đổi nhãn. Còn thiếu tập ảnh Việt Nam mới tự chụp có phép, nhãn legibility độc lập, nhiều camera/ID và backbone hơn. Hợp đồng nguồn chỉ gồm các vùng tác giả và TD3 đã khai báo, không bao phủ mọi thông tin suy ra từ mã quốc gia/QR/đặc điểm khuôn mặt. Chưa có kiểm chứng người thật hoặc chống giả.


## Baseline bổ sung: điền trường thiếu từ MRZ hợp lệ

Đăng ký sau khi xem development, trước mọi suy luận test. Tám phép ghép dùng output VLM đã có và cùng OCR CPU rapid_v4; không phải tám model mới hay tám lượt suy luận VLM độc lập. Không ghi đè giá trị, sửa ký tự hoặc suy đoán thế kỷ. Checksum không chứng minh giấy tờ thật. Thời gian ghép cache là tổng bộ đếm thành phần, chưa phải độ trễ một request đầu cuối.

| VLM thành phần | F1 gốc | F1 ghép | Bỏ sót gốc → ghép | Ngoài nhãn gốc → ghép |
|---|---:|---:|---:|---:|
| Vintern gốc | 0.1757 | 0.1757 | 52 → 52 | 1602 → 1602 |
| V1 chuyển tác vụ | 0.3413 | 0.3859 | 427 → 398 | 112 → 112 |
| R2 complete42 | 0.3644 | 0.3784 | 95 → 81 | 350 → 350 |
| R2 body-partial42 | 0.3786 | 0.3890 | 175 → 166 | 216 → 216 |
| R2 complete31415 | 0.3670 | 0.3742 | 116 → 109 | 327 → 327 |
| R2 body-partial31415 | 0.3978 | 0.4099 | 148 → 137 | 222 → 222 |
| V3 source-partial42 | 0.3947 | 0.4092 | 162 → 149 | 227 → 227 |
| V3 source-partial31415 | 0.4063 | 0.4106 | 140 → 136 | 243 → 243 |

Chọn thành phần từ development: partial_42; bật ghép trên web: **False**. Chỉ bật khi F1 development tăng và số key ngoài nhãn không tăng; không dùng test để đổi quyết định. Đã phát lại 1728 phép ghép; thêm 0 lần gọi ảnh mới cho hybrid. Nếu development không có lợi ích, web giữ VLM đơn và không chạy thêm hybrid chỉ để tăng số lần kiểm thử.


## Chẩn đoán riêng các trường có thêm nguồn hỗ trợ

Đây là phân tích mô tả bổ sung, không dùng chọn model hoặc thay kết quả tổng thể. Chỉ xét key vắng trong hợp đồng thân thẻ nhưng có nguồn khai báo còn hiện trong V3. Các key/ảnh cùng giấy tờ không phải các mẫu độc lập; không coi số trường là số người hoặc ID.

| Model | Trường bổ sung | Đúng | Sai giá trị | Bỏ sót | Recall tập con |
|---|---:|---:|---:|---:|---:|
| Vintern gốc | 83 | 9 | 59 | 15 | 0.1084 |
| V1 chuyển tác vụ | 83 | 1 | 18 | 64 | 0.0120 |
| R2 complete42 | 83 | 5 | 62 | 16 | 0.0602 |
| R2 body-partial42 | 83 | 2 | 56 | 25 | 0.0241 |
| R2 complete31415 | 83 | 4 | 55 | 24 | 0.0482 |
| R2 body-partial31415 | 83 | 6 | 58 | 19 | 0.0723 |
| V3 source-partial42 | 83 | 7 | 56 | 20 | 0.0843 |
| V3 source-partial31415 | 83 | 15 | 62 | 6 | 0.1807 |

Can thiệp target chỉ thay đổi 22/640 slot train của nhánh partial; phải xem cả hiệu quả ở trường bổ sung lẫn đánh đổi trên các trường khác. Kết quả tốt ở tập con không tự chứng minh model tốt hơn trên toàn bộ test.

## Ngân sách sinh văn bản

Tất cả model VLM dùng cùng giới hạn 384 token mới. Cờ chạm giới hạn cho biết đã dùng hết ngân sách; không tự chứng minh model bịa thông tin hoặc biết nguyên nhân output sai. Không đổi giới hạn sau khi mở test.

| Model | Lượt test | Chạm giới hạn | Trung vị token sinh |
|---|---:|---:|---:|
| Vintern gốc | 144 | 5 | 195.5 |
| V1 chuyển tác vụ | 144 | 0 | 29.0 |
| R2 complete42 | 144 | 1 | 67.5 |
| R2 body-partial42 | 144 | 0 | 61.0 |
| R2 complete31415 | 144 | 2 | 65.0 |
| R2 body-partial31415 | 144 | 1 | 63.0 |
| V3 source-partial42 | 144 | 1 | 64.0 |
| V3 source-partial31415 | 144 | 0 | 63.0 |

## Tương tác giữa hợp đồng nhãn và mức cải thiện được đo

Phân tích thăm dò bổ sung trên đúng output đã có: so chênh lệch F1 partial − control dưới hai hợp đồng. Giá trị thay đổi = chênh lệch theo nguồn − chênh lệch theo thân thẻ. Không dùng kết quả này để chọn model hay thay giả thuyết chính. Bootstrap ghép cặp 10000 lần theo 48 cụm giấy tờ, phân tầng nguồn, seed 20261103; CI thăm dò chưa chỉnh đa so sánh. Đây là khác biệt hợp đồng tác vụ, không phải chứng minh mọi bộ nhãn trước đó sai.

| Seed | Gain theo thân thẻ | Gain theo nguồn | Thay đổi gain | CI95% thay đổi |
|---|---:|---:|---:|---:|
| 42 | +0.0212 | +0.0142 | -0.0069 | [-0.0145, -0.0003] |
| 31415 | +0.0291 | +0.0308 | +0.0017 | [-0.0055, +0.0102] |

## Gián đoạn nguồn điện và độ nhạy thời gian

Windows ghi nhận sleep do pin lúc 09:25:46 UTC và thức lại 14:45:48 UTC ngày 2026-11-02. Một lượt V1 đang sinh văn bản bị tính cả thời gian ngủ. Output, hash, số đo thời gian gốc và mọi hàng độ chính xác được giữ nguyên. Bảng sau là phân tích thời gian bổ sung sau khi phát hiện sự cố, chỉ bỏ đúng lượt có nhật ký sleep khỏi thống kê độ trễ; không bỏ các lượt OCR khó hoặc sai. Nguồn điện/chế độ GPU không được kiểm soát xuyên suốt; các con số này không thiết lập ưu thế tốc độ.

| Model | Số lượt | Lượt sleep | p50/p95 gốc (s) | p50/p95 bỏ lượt sleep (s) |
|---|---:|---:|---:|---:|
| Vintern gốc | 144 | 0 | 21.53/30.46 | 21.53/30.46 |
| V1 chuyển tác vụ | 144 | 1 | 5.23/17.70 | 5.21/17.09 |
| R2 complete42 | 144 | 0 | 14.03/30.20 | 14.03/30.20 |
| R2 body-partial42 | 144 | 0 | 13.75/27.20 | 13.75/27.20 |
| R2 complete31415 | 144 | 0 | 14.79/30.39 | 14.79/30.39 |
| R2 body-partial31415 | 144 | 0 | 13.36/20.00 | 13.36/20.00 |
| V3 source-partial42 | 144 | 0 | 9.94/18.98 | 9.94/18.98 |
| V3 source-partial31415 | 144 | 0 | 10.02/18.14 | 10.02/18.14 |
| rapid_latin_v5/body | 144 | 0 | 1.71/4.17 | 1.71/4.17 |
| rapid_latin_v5/mrz_checks | 144 | 0 | 1.71/4.17 | 1.71/4.17 |
| rapid_latin_v5/mrz_format | 144 | 0 | 1.71/4.17 | 1.71/4.17 |
| rapid_v4/body | 144 | 0 | 2.14/5.45 | 2.14/5.45 |
| rapid_v4/mrz_checks | 144 | 0 | 2.14/5.45 | 2.14/5.45 |
| rapid_v4/mrz_format | 144 | 0 | 2.14/5.45 | 2.14/5.45 |

Kiểm tra gọi lại riêng lượt bị gián đoạn còn chờ; chưa được coi là đã qua.