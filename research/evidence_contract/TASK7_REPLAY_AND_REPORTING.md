# TASK 7A · Tooling đã thử trên development

| Mục | Dùng lại / hoàn thiện | Bằng chứng |
|---|---|---|
| Cache, resume, hash, budget | Dùng Runner TASK 4. Bắt buộc kết quả cũ có cache key và event hoàn tất khớp. Pilot stage dùng log mới, cap 12 và chỉ OCR CPU. Replay không có model loader | [Log replay](execution/master_01/ab_replay.log) · [Tests Python](execution/master_01/master_python_02.log) |
| Score replay | Dùng lại 132 dòng TASK 5 đã audit cho ablation. Pilot stage replay cùng output digest, đối chiếu native payload và input với chuỗi log | [Ablation](execution/master_01/method_decision_replay.json) · [Receipts](execution/master_01/ab_stage_comparison.json) |
| Metrics trên nhãn thật | Import hai pha hiện có. Report mới kiểm snapshot, receipt, provenance và analyst join. Tách pointwise với relation, tính bảng theo field contract và paired ID. Giữ NA khi chưa có phiếu | [Mã report](master/ifv_report.py) · [Trạng thái](execution/master_01/ifv_waiting.json) |
| Thống kê | Paired ratio cluster bootstrap, sign-flip, Holm dùng lại `fc_statistics`, mô phỏng sizing riêng. Kiểm zero denominator và trùng cluster với fixture | [SAP draft](STATISTICAL_ANALYSIS_DRAFT.md) · [Tests Python](execution/master_01/master_python_02.log) |
| Phân loại lỗi | C1 unsupported scope-qualified, C2/C3/C4 omission hoặc sai giá trị, invalid phép thử, absence chưa chứng minh, output JSON lỗi, attribution lỗi, nguyên nhân chưa đủ chứng cứ. Model behavior, lỗi seeded và lỗi phần mềm verified là các lớp dữ liệu riêng | [Coverage](CONTRACT_COVERAGE_MATRIX.md) · [Mutation](AUTOMATED_FAULT_INJECTION_REPORT.md) |
| Thời gian | Giữ actual calls riêng với replay. Lưu wall/CPU/RSS, latency theo view và timing audit checker đã có. Phút công review chưa đo | [Pilot](STAGE_INTERVENTION_RESULTS.md) |

Sau khi có một JSON pha 2 thật và import bằng `task55.ifv import-stage2`, chạy từ worktree bằng Python venv hiện có:

```powershell
$py = 'D:\laptrinhcuatao\Ekyc\.venv\Scripts\python.exe'
& $py -B -m research.evidence_contract.master.ifv_report --submission '<đường dẫn tới bản output_observations.json đã niêm phong trong local/>'
```

Pha 1/2 dùng [hướng dẫn đã có](IFV_REVIEW_GUIDE.md). Trạng thái hiện tại WAITING_FOR_HUMAN_REVIEW, 0 phiếu. Đã test đọc/lưu/xuất/nạp pha 1 và che đầu ra pha 2 qua event fixture JavaScript. Trình duyệt thật chưa xác minh vì preview localhost timeout và cửa sổ Edge không được cấp quyền điều khiển trong thời gian chờ. Không dùng fixture UI làm nhãn người. TASK 7B vẫn phụ thuộc GO và lock mới.

Ngày 11/11/2026, reporter đã được sửa để giữ các ca được chọn nhưng thiếu quan sát pha 1 trong nhóm UNREVIEWED, thay vì chỉ tổng hợp các ca có trong gói pha 2. Mã reviewer, snapshot và số ca phải khớp receipt trước khi join. CI trả cả số cụm theo từng phương pháp và giữ NA nếu một phía thiếu cụm cho mẫu số.

Score verification hiện kiểm lại digest của nội dung stage, bên cạnh việc so execute/replay. Hash cấu hình reader được lấy trực tiếp từ ReaderSpec. Receipt mới ghi hash đúng của 12 output cũ. Các giá trị F1 và verdict lịch sử không thay đổi. 28 regression checks liên quan đã chạy qua. [Tests](execution/master_01/continuation_20261111/regressions_01.log) · [Stage binding đã kiểm](execution/master_01/continuation_20261111/stage_bindings.json)
