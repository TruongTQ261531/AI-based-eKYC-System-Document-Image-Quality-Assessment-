# LoRA V1: checkpoint vận hành

Cập nhật2026-11-01,07:51UTC. Benchmark đang chạy; đọc các JSON trạng thái
trong cache để xem tiến độ hiện tại thay vì coi số ở chat là live.

## Đã hoàn tất

- Vintern revision b98f263eab246eb5269ade64edbdca8a887dc44d; weights/runtime
  checksum đúng; dùng Python có sẵn, CUDA overlay riêng, không sửa venv gốc.
- GPU smoke20bước +resume10bước byte-identical,192tensor LoRA thay đổi.
  Hai seed chính42/31415 và đối chứng42 đều train192optimizer steps.
- Dev80ảnh mỗi phương án, CPU OCR cũng80ảnh. Main chọn seed42/step192;
  đối chứng chọn step48 bằng quy tắc devloss đã định trước.
- Cả hai test locks công bố ở10268e47bbb25a536f51d2aa7ac71753762f0d8b;
  xác nhận remote trước test ghi ở pretest_publication.json (commit464a34e).
- VLM gốc test120ảnh +panel12ảnh ×2 đã xong, công bố ởdd589e8.
-44Python +6frontend tests đã qua; API tests dùng mock model, camera tests
  dùng mock media/DOM. Chưa kiểm thử camera vật lý.
-63artifact V4 không đổi; mentor runtime diff rỗng. Python gốc2.14.1+cpu.

## Tiến trình đang hoạt động

Supervisor `python -m research.vlm_final_workflow`, PID10060, unified exec
session52449. Trạng thái/log:

- research/cache/vlm_lora_v1/final_workflow.json
- research/cache/vlm_lora_v1/progress.json (main)
- research/cache/vlm_lora_v1/control/progress.json (control)
- research/cache/vlm_lora_v1/logs/final_*.txt

Supervisor tiếp tục main tests42/31415,control test, hai panel12case lặp cho
mỗi model,CPU baseline,fresh-online72calls,secondary parser,error taxonomy,
audit,report và adapter export. Mọi task GPU chạy nối tiếp bằng mutex.
Không khởi động train lại hoặc chạy hai supervisor cùng lúc. Cache lưu từng
ảnh; khi process thực sự đã dừng, đọc lỗi rồi có thể chạy lại supervisor để
tiếp tục phần chưa hoàn tất. Test đã công bố không còn là test mới chưa thấy.

Các source/signature chính đã frozen: vlm_data.py,vlm_runtime.py,
vlm_train.py,vlm_config.json,VLM_LORA_PROTOCOL.md,assets.json,dataset_card.json.
Signature26dd9dd72db10e24413195c20541b45290f45e8835b52d553f8dfbe64cbd6f5c.
Control source/protocol cũng frozen theo control/test_lock.json. Không đổi
scorer hoặc model sau khi đã thấy test. Các bổ sung sau khóa chỉ kiểm kê
exposure/integrity, tài liệu prior art và biểu đồ từ số đã công bố.

## Còn phải hoàn tất trước khi kết luận

1. Supervisor phải báo completed, đủ tất cả kết quả và replay audit.
2. `python -m research.vlm_figures`, xem ảnh biểu đồ thực tế.
3. Final44Python/6frontend checks sau sửa web/audit; lưu log/XML hiện hành.
4. Restart đúng server LoRA do phiên này mở (uvicorn PID24836,session81482,
   kiểm tra command trước khi dừng); chạy start-vlm-web.ps1 ở8002.
5. Browser chạy model thật trên SPECIMEN train full/field_clip/value_mask;
   kiểm tra sửa/xác nhận/xóa và viewport390px; lưu screenshot và
   results/vlm_lora_v1/browser_validation.json chỉ có số/checksum.
6. `python -m research.vlm_release`, kiểm toàn vẹn/public data và tạo index.
   Commit/push artifact công khai; cache/data/weights/raw output giữ private.

Lưu ý khoảng2708s giữa control steps140/141 được giữ nguyên trong log và
thời gian wall. Chưa biết nguyên nhân, không gọi đó là thời gian compute GPU.
Train LoRA này chỉ dùng720SPECIMEN, không phải toàn bộ MIDV/full_original.
Không có ảnh camera mới, không có GT legibility độc lập, không có bảo đảm
novelty/CORE B hoặc liveness. Đọc VLM_PRIOR_ART_VI.md và báo cáo V1 khi xong.
