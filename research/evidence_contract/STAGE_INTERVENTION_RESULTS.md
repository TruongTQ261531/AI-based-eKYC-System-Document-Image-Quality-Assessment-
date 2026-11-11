# Kết quả can thiệp M2 trên development

3 ID giả lập, 4 view mỗi ID. **10 lượt RapidOCR v4 trên CPU mới, 2 output cache lịch sử, 0 GPU**, 0 training. Replay đọc lại 12 output và tái tạo đúng hash kết quả `5960d28024879d5f54046ca4d9dbd21ffcb13b6a326d8af9773cda0e81944699` với 0 inference. Worker quan sát 33,66 giây wall, 46,19 giây CPU và khoảng 900 MiB RSS đỉnh lấy mẫu, gồm nạp, đo và chấm. [Execute](execution/master_01/ab_execute.json) · [Replay](execution/master_01/ab_replay.json) · [Receipt từng stage](execution/master_01/ab_stage_comparison.json)

| View | Đúng / field tham chiếu | Giá trị dự đoán | Exact-field micro F1 |
|---|---:|---:|---:|
| Bản dựng tác giả | 6/12 | 11 | 12/23 = 52,17% |
| Projective raw | 6/12 | 11 | 12/23 = 52,17% |
| Nắn với góc chuẩn | 6/12 | 11 | 12/23 = 52,17% |
| Nắn với crop sai | 2/12 | 3 | 4/15 = 26,67% |

Raw → nắn chuẩn không có trường chuyển đúng–sai hoặc sai–đúng. Nắn chuẩn → crop lỗi có 4 trường chuyển đúng–sai trên 2 ID, tất cả nằm ở trường mà nguồn khai báo đã bị cắt. M2 là điểm đổi hash đầu tiên cả ở nắn chuẩn và crop lỗi, nên hash một mình không phân biệt mất bằng chứng. F1 gộp giảm ở 2/3 ID với crop sai; per-field baseline chỉ ra đủ bốn trường, trace cho biết chúng thuộc vùng mất nguồn. Với một ID, F1 trên phần vùng còn tăng từ 0,60 lên 0,67 vì mẫu số đổi, trong khi F1 so input toàn thẻ giảm từ 0,60 xuống 0,50.

Ba trường đích crop đều mất nguồn theo hình học, nhưng **0/3 được reader đọc đúng trước crop**. Bốn chuyển đúng–sai là trường khác cũng bị ảnh hưởng. Đây là hạn chế trực tiếp cho claim causal trên trường đích. Không quan sát lỗi mới ở trường còn nguồn. Pilot chưa có bản dựng ảnh chụp camera, reader thứ hai, lỗi tự nhiên được kiểm, hoặc lỗi lịch sử có patch/revert.

Lần đầu xuất receipt hậu kiểm đọc sai tên khóa runtime trong payload, nên dừng ở bước đọc lại cache. Sau khi dùng parser `NativeOutput`, phân tích đi qua. Lần sửa này không gọi lại model. [Log lỗi đọc receipt](execution/master_01/ab_stage_analysis.log) · [Lượt chạy lại](execution/master_01/ab_stage_analysis_02.log)

Hoàn thiện đối chứng còn thiếu ngày 11/11/2026 trên trace đã lưu. Khi nhận cùng metadata nguồn, checker phẳng và giải thích theo graph trùng **24/24** cặp trường, gồm cả **4/4** trường đúng→sai. Cả stage-diff và trace nguồn chỉ ra M2 trên **3/3** crop intervention đã biết. Với warp đúng, hash stage cũng đổi, nên con số này chỉ xác nhận vị trí can thiệp do thí nghiệm tạo. Accuracy định vị root cause của lỗi tự nhiên giữ NA. Không có inference mới cho đối chiếu này. [Matched baselines](execution/master_01/continuation_20261111/stage_baselines.json)
