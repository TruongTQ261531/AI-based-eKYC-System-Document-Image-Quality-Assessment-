# LoRA V1: đợt fine-tune và benchmark hoàn tất

Cập nhật2026-11-01. Không còn train/benchmark GPU đang chạy. Không chạy lại
training do chat bị ngắt: các model, test, audit và export đã hoàn tất.

## Kết quả thực tế

- Vintern938,193,024tham số; BF16 LoRA r8/alpha16,1,081,344tham số trainable.
  RTX3050 Laptop6GB, RAM16GB; không tạo venv, CUDA overlay riêng.
- Hai seed chính42/31415 và một đối chứng42,192optimizer steps mỗi lượt.
  GPU smoke20bước +resume10bước giống hệt;192tensor adapter thay đổi.
- Chọn seed42/step192 trên development trước test. Cả hai locks đã công bố
  tại10268e47bbb25a536f51d2aa7ac71753762f0d8b, xác nhận remote ở464a34e.
- Test120ảnh/24mock IDs: F1 strict OCR V4=.808989; Vintern gốc=.281095
  (parser phụ=.5583); LoRA42=.976313,LoRA31415=.976215; đối chứng=.886275.
  Seed42 đúng trọn106/120ảnh, có3key che kín (2giá trị không rỗng) vẫn xuất.
  Giữ lỗi thật; không gọi model an toàn tuyệt đối hoặc hết hallucination.
- Audit replay672hàng VLM chính+224đối chứng+400OCR,48nhóm lặp có3lần
  suy luận; không sai khác. Fresh-online72calls, vision luôn tính mới,
  không sai khác output cache. Panel lặp không phải test dataset độc lập.
- Final44Python +6frontend tests qua. Một cảnh báo TestClient deprecation
  còn giữ nguyên. Các lỗi trước/sửa lại ghi trong execution_notes.json.
-63artifact V4 và10source hash chính giữ nguyên; mentor runtime diff rỗng.
  Python OCR gốc vẫn2.14.1+cpu, không cài lại package toàn cục.

## Tài liệu và adapter

Đọc VLM_RESULTS_VI.md, VLM_PRIOR_ART_VI.md và VLM_REPRODUCE_VI.md.
Số/checksum đầy đủ ở research/results/vlm_lora_v1, gồm audit.json,
format_analysis.json,error_taxonomy.json,fresh_online.json và artifact_index.

Adapter suy luận đã xuất vào research/cache/vlm_lora_v1/export/seed_42.
adapter_model.safetensors=4,350,392bytes. Đọc vintern_adapter.json/README:
adapter thuộc language_model của full Vintern, vẫn cần weights gốc đúng
revision. Optimizer/RNG checkpoints ở seed_42/seed_31415/control riêng.
Weights/corpus/raw predictions không đưa Git.

## Web localhost

Web LoRA8002 đang chạy ở owned session30509,uvicorn PID12264.
Web OCR V4 dự phòng8001 ở session20203,PID19212. Bản mentor giữ riêng.
Nếu server đã tắt, từ thư mục gốc Ekyc chạy:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\versions\research-document-recovery\research\start-vlm-web.ps1
```

Mở http://127.0.0.1:8002/ trong trình duyệt máy tính. Script nhận ra server
đã chạy, tránh khởi động trùng. Web LoRA giữ model GPU trong RAM; dừng đúng
server này trước khi chạy một benchmark/training GPU mới.

Browser thật đã gọi model GPU: SPECIMEN train001 full5/5,field_clip4/4,
value_mask1/2 (bỏ sót full_name còn nhìn thấy). Đây là QA tích hợp, không
phải accuracy test. Không che lỗi bằng đổi ảnh mẫu hay hardcode kết quả.
Sửa thông tin hủy xác nhận; xóa bỏ ảnh/các trường; viewport390px không
tràn ngang,console0error/warning. Screenshot web_full.jpg và
web_mobile_mask.jpg cùng browser_validation.json được lưu. Chưa thử
camera vật lý; các camera tests dùng mock media/DOM. Không phê duyệt ID
hoặc tuyên bố liveness/PAD qua bản OCR này.

## Phạm vi và giới hạn

Corpus có720SPECIMEN với GT từng trường; model chính train480ảnh, không
train toàn bộ720ảnh hoặc21,050dòng nhãn chất lượng của full_dataset_original.
Tách mock IDs giữa roles,
cùng generator/hai bố cục/hai font;10nhóm field canonical. Calibration40ảnh
chưa dùng. Chưa có camera mới/human legibility labels/held-out-layout.

Đối chứng được chọn ở48bước:192presentations/192raster/91ID, khác mức
tiếp xúc của model chính768/480/96; báo cáo rõ, không coi là ablation
hoàn toàn khớp exposure. Khoảng2708s giữa control steps140/141 giữ nguyên
trong wall-time, chưa xác định nguyên nhân.

Không đổi source/model/scorer đã khóa sau test. Signature chính:
26dd9dd72db10e24413195c20541b45290f45e8835b52d553f8dfbe64cbd6f5c.
Fine-tuning/masking/routing có prior art; chưa đủ kết luận novelty CORE B.
Kết quả V1 không chứng minh mọi giấy tờ/camera thật hoặc mọi trường ngoài
schema. Không cần rerun V4, không sửa các artifact/manuscript V4 đã frozen.
