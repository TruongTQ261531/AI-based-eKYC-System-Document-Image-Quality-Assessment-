# Phân tích độ nhạy đăng ký trước khi mở test

Kiểm tra nguồn tác giả của24 ảnh chụp mới phát hiện11 trường hợp có MRZ,
10 trường hợp được parser TD3 nhận; một trường hợp có hai chuỗi tác giả dài
43/44 ký tự. Không tự thêm filler hoặc sửa transcript bằng dự đoán của model.
Các giá trị và pixel nguyên gốc được giữ. Chỉ số định danh công khai của mẫu
giấy tờ trong corpus là `midv2020/aze_passport/53`; đây không phải số giấy tờ
hoặc tên người được công bố từ OCR.

Hợp đồng chính vẫn là các vùng thân thẻ/bản lặp/TD3 được liên kết tường minh.
Vì MRZ chưa được liên kết ở mẫu đó, output ngoài hợp đồng không đủ để kết luận
thông tin thật sự biến mất hoặc model hallucinate. Kết quả chính vẫn giữ đủ
48 ID/192 ca, và báo riêng giới hạn này.

Trước bất kỳ suy luận test mới nào, đăng ký thêm độ nhạy: giữ nguyên output và
scorer, bỏ đúng ID có MRZ tác giả không nhận được khỏi bản phân tích bổ sung,
còn47 ID/188 ca. Dùng cùng bootstrap ghép cặp theo ID và phân tầng nguồn; giữ cả
kết quả toàn bộ và kết quả bổ sung, bất kể hướng cải thiện. Đây là kiểm tra
phụ thuộc vào độ bao phủ nhãn, không phải lọc ca model đọc sai hay thay tiêu chí
chính. Không phát sinh thêm lượt model từ phân tích này.

Nhãn người và việc mọi nguồn encoded đều được hỗ trợ vẫn chưa có. Các giới hạn
này không được thay bằng nhãn do model tự gán. Không sửa giao thức/mẫu train,
weights hoặc checkpoint để phản ứng với quan sát test. Bằng chứng đăng ký được
ghi trong `results/hard_pairs_v1/analysis_plan.json` và `analysis_publication.json`.
