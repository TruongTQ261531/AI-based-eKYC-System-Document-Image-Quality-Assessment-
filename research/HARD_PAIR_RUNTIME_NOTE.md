# Điều chỉnh quản lý cache trước khi tiếp tục huấn luyện

Sau mốc đăng ký trước huấn luyện `1939a90552da758e8cf951aaee3ac22a9fdae506`,
lượt hard42 đã có checkpoint hoàn tất tại bước80. Bộ đếm reserved sau đó lên
khoảng9.27GiB, trong khi nvidia-smi ghi GPU6GiB gần đầy và RAM trống dưới1GiB.
Không quan sát OOM hoặc gradient/loss không hữu hạn. Đã dừng có kiểm soát worker,
giữ checkpoint80, stdout và mọi events chưa checkpoint; supervisor ghi failed
vì worker bị dừng, không phải vì một kết quả OCR bị loại.

Điều chỉnh vận hành: chỉ child process của thí nghiệm nhận
`PYTORCH_CUDA_ALLOC_CONF=garbage_collection_threshold:0.6`. Không đổi package,
weights gốc, dữ liệu, loss, seed, thứ tự lấy mẫu, learning rate, tổng bước hoặc
checkpoint lựa chọn. Hợp đồng phương pháp không thay. Tham số quản lý cache
này được mô tả trong [tài liệu CUDA của PyTorch](https://docs.pytorch.org/docs/2.7/notes/cuda.html).
Không suy ra tổng VRAM vật lý từ bộ đếm reserved, hoặc tuyên bố ưu thế tốc độ.

Trước khi tiếp tục: chạy riêng một bước81 từ cùng checkpoint80 với cấu hình
cache gốc và cấu hình thu hồi cache. Hai bước là chẩn đoán ngoài ngân sách
primary, không phải hai run mới hoặc kết quả benchmark. So mọi tensor LoRA,
optimizer và RNG; chỉ tiếp tục tự động nếu khớp. Bằng chứng nằm trong
`results/hard_pairs_v1/runtime_amendment.json`. Parity một bước chỉ kiểm chứng
phạm vi đó, không chứng minh mọi chuỗi cập nhật có cùng số học.

Khi resume, các update chưa checkpoint sau80 được ghi giữ trong bản sao,
rồi phát lại từ optimizer/RNG tại80. Primary vẫn kết thúc ở320 update và1280
lượt ảnh hiệu dụng. Phải báo riêng số update đã thực hiện rồi phát lại, thay
vì đếm chúng thành thêm dữ liệu độc lập. Timers/peak memory trước điều chỉnh
được giữ; không trừ hoặc sửa để làm đẹp kết quả.
