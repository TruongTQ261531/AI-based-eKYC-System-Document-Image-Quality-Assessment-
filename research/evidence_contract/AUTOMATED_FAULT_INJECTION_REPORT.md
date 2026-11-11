# Control M1–M7 cho development

Chạy trên pipeline trong suốt với các ảnh do fixture tạo. Bộ tạo dùng lại generator và vùng che hard-pair. Xác minh pixel bằng vùng mực đã biết, không hỏi A/B3. Dùng lại scorer hard-pair để ghi bộ đếm chất lượng trường. Với lỗi JSON dùng kiểm object JSON độc lập và kiểm trùng khóa. Với attribution đối chiếu membership nguồn trong trace. Các vị trí vùng dựa trên inventory do tác giả tạo. Số liệu này không đo readability của người. [Execution JSON](execution/master_01/controlled_faults.json) · [Log](execution/master_01/faults_01.log)

| Họ | Control và can thiệp | A / B3 |
|---|---|---|
| M1 che body, còn backup | Output đúng so với router chỉ đọc body và bỏ trường | Cùng PASS ở control, cùng phát hiện ca bỏ trường |
| M2 che đủ nguồn | Từ chối đúng so với giữ nhầm giá trị cũ | Cùng phân biệt hai ca |
| M3 che A, theo dõi B | B giữ đúng, B bị mất do rule ghép trường, ca mất ngữ cảnh dù glyph B giữ | Cùng báo lỗi rule, cùng loại ca context invalid |
| M4 crop/rectification | Crop lỗi tại M2 giả lập làm mất nguồn B sau input hợp lệ và một crop no-op | Cùng báo khi B mất, cùng không báo no-op |
| M5 ánh xạ trường | Hoán nhầm giá trị giữa hai key vẫn tạo JSON hợp lệ | Cùng báo sai giá trị |
| M6 khai nguồn | Output đúng, trace mutant trỏ về body đã bị che | A/B3 không báo sai giá trị. Checker membership báo nguồn không hợp lệ |
| M7 JSON | Chuỗi gãy cú pháp và control chỉ đổi khoảng trắng | A/B3 chưa kết luận chuỗi gãy. Kiểm schema báo chuỗi gãy và chấp nhận đổi khoảng trắng |

14 ca gồm 4 negative controls, 1 invalid, 9 can thiệp đã đi qua nhánh thực thi. Trong 9, có 7 hiệu ứng lỗi quan sát và 2 tương đương **trên fixture này**. Valid-test rate là 13/14. Mẫu số mutation score là 7 lỗi kích hoạt quan sát được, hoặc 5 nếu giới hạn ở structured field. A và B3 có 5/7 trên các giao diện và 5/5 trên structured field. Coverage theo họ được ghi trong JSON. Chi phí code đoạn control cộng dồn 0,79 giây trên lượt thực thi, không gồm khởi động/import. Số lần gọi OCR/VLM là 0. 

Ca chèn chỉ kiểm cách đo. Không suy từ 5/5 rằng oracle phát hiện đủ lỗi sản phẩm hoặc rằng các kiểu mutant đại diện lỗi thực. Muốn dùng RQ2 cần corpus fault-family đa dạng, version quad hoặc bug–patch–revert, nhãn nguồn và baseline được cấp thông tin như nhau.
