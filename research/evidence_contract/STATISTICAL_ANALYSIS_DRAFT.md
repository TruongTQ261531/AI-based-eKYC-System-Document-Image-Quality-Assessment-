# Kế hoạch thống kê dự thảo · TASK 6A/7A

Giữ [RQ đã ghi](RESEARCH_QUESTIONS.md). IFV là nhãn chính cho natural output. Controlled mutants và lỗi tự nhiên có bảng riêng. Các threshold dưới đây là cấu hình dự thảo của phân tích và cần biện minh trước lock.

| Contrast | Estimand và cụm | Đối chứng chính | Điều kiện phát biểu |
|---|---|---|---|
| RQ1 độ tin cậy oracle | Chênh FAR trên ca hợp lệ không lỗi, chênh sensitivity trên ca hợp lệ có lỗi, chênh decision coverage trên tổng hai nhóm. Cụm physical ID và sensitivity theo component của duplicate | V3 đóng băng, V3 với gate chung, thêm B3 và A_flat để kiểm information parity | Hướng FAR giảm, với guard one-sided về sensitivity và coverage trên −5 điểm %. Báo test invalid và abstention riêng |
| RQ2 lỗi regression | Recall theo root-cause family có provenance, panel known-good cho FAR và coverage. Các view trong cùng lỗi không độc lập | Per-field version-pair checker cùng gate, B3/gated V3, phân tích raw và schema khi liên quan | Tăng recall trên lỗi xác minh. Guard coverage và FAR theo RQ cũ. Trace chỉ kết luận stage khi có activation/revert hoặc tác động do can thiệp được kiểm |
| RQ3 sinh test theo ngân sách | Số lỗi riêng đã xác minh theo prefix budget trong block paired. Cụm hoặc sensitivity theo ID và họ lỗi | Random theo box, validity-filtered, cùng annotation, quota và scorer | Tăng yield ở ngân sách đã khóa. Báo proposal bỏ, log runtime, người, cache và trùng |

## Điểm ước lượng và CI

- Pha pilot IFV tính precision, false negatives, FAR, decision coverage và sensitivity trên các ca đã chấm có thể phân xử. Bảng theo contract và ID dùng đúng cặp. Giữ INVALID, INCONCLUSIVE và UNREVIEWED riêng. Gold positive mà oracle chưa ra alarm là FN cho sensitivity. Với mẫu phân tầng hiện tại, `population_recall=null`. Một reviewer không tạo inter-rater agreement. Mọi mẫu số bằng 0 trả NA.
- Với panel đủ cụm, bootstrap theo ID ghép cặp. Lấy lại cùng các cụm cho cả hai checker, tính tỷ số từ tổng tử và mẫu mỗi lần, trả CI 95% percentile và lower bound one-sided. Hàm demo mặc định 10.000 lần, tối thiểu 20 cụm có đóng góp cho mẫu số **của mỗi phương pháp**. Báo số cụm từng phương pháp cạnh số cụm chung. Nếu hơn 5% resample bị mẫu số 0 thì không đưa CI. Ngưỡng 20 chỉ là guard kỹ thuật, không phải cỡ mẫu đủ lực.
- Sign-flip trên chênh theo cụm khi có paired denominator chung và giả định trao đổi được. Exact tới 16 cụm discordant, sau đó Monte Carlo có hiệu chỉnh +1. Dưới 8 cụm discordant giữ NA. Holm cho family 3 kiểm định đã định. Kiểm thiếu số liệu giữ slot multiplicity. Guards one-sided và tiêu chí effect/adequacy phải giữ nguyên khi khóa.
- Một bootstrap cho ca review thuận tiện hoặc partial không sửa verification bias. Chỉ tính weighted population sau khi kế hoạch lấy mẫu, xác suất, nonresponse và nhãn đủ chặt. Bản hiện tại không extrapolate từ 46 ca, không dùng p-value confirmatory. Raw OCR latency, cost chấm, annotation và triage tách mẫu số.

## Mô phỏng cỡ mẫu

Mô phỏng giả định mỗi cụm góp một cặp no-fault, 4.000 lần mỗi kịch bản, dùng worst-case alpha Holm 0,05/3. Ví dụ giả định FAR chênh −10 điểm % cho xác suất bác bỏ 0,498 ở 96 cụm và 0,861 ở 192 cụm. Với chênh −3 điểm % tại 192 cụm, chỉ 0,107. Các số này là giả định lập kế hoạch. Chưa mô hình hóa độ khó không đều, guard sensitivity/coverage, nhiều field trong ID, họ lỗi chéo hoặc thiếu reviewer. Không dùng 192 **view** lịch sử làm 192 cụm. [Kết quả mô phỏng](execution/master_01/sizing_illustration_v2.json)

Lần tạo artifact đầu không serialize được NumPy integer. Lượt hai chuyển kiểu trước khi ghi và có test regression. Giữ log lỗi và phần ghi dang dở riêng. [Log đầu](execution/master_01/prelock.log) · [Lượt đạt](execution/master_01/prelock_02.log)

Rà soát ngày 11/11/2026 bổ sung kiểm kiểu số đếm nguyên, hình dạng vector sign-flip, và điều kiện số cụm ở mỗi phía khi CI precision có mẫu số khác nhau. Phiếu pha 1 partial giữ toàn bộ frame đã chọn trong bảng, gồm các ca chưa mở được ở pha 2. Các kết quả lịch sử và mô phỏng đã lưu giữ nguyên. [Regression log](execution/master_01/continuation_20261111/regressions_01.log)
