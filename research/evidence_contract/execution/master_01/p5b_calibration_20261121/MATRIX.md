# P5B · Ma trận theo giả định

Đơn vị là %. Khoảng trong ngoặc là Wilson 95% theo từng điểm. P(đạt) và P(thiếu) dùng mọi cohort làm mẫu số. Độ phủ chỉ tính trên cohort xuất cả ba cận. C/S/Δ là coverage quyết định, độ nhạy trên lỗi có nhãn và giảm FAR. P(đạt) là power khi cả ba estimand đạt ngưỡng, là sai số loại I khi có null đúng, và không xác định về hiệu quả khi thiếu toàn bộ truth.

## calibration

800 cohort cho mỗi hàng và phương pháp, cùng đầu vào theo cặp.

| Scenario | Phương pháp | P(đạt cả ba) [95% MC] | P(thiếu) | Xuất cận | Độ phủ C / S / Δ | Độ phủ đồng thời |
|---|---|---:|---:|---:|---:|---:|
| mixed_50 | v3 percentile | 1.5 [0.9, 2.6] | 95.5 | 36/800 | 80.6 / 94.4 / 97.2 | 72.2 |
| mixed_50 | Cluster t | 1.2 [0.7, 2.3] | 95.5 | 36/800 | 77.8 / 83.3 / 97.2 | 61.1 |
| mixed_50 | Hoeffding | 0.0 [0.0, 0.5] | 95.2 | 38/800 | 100.0 / 100.0 / 100.0 | 100.0 |
| mixed_100 | v3 percentile | 69.4 [66.1, 72.5] | 2.4 | 781/800 | 92.8 / 88.2 / 96.4 | 78.7 |
| mixed_100 | Cluster t | 65.2 [61.9, 68.5] | 2.4 | 781/800 | 91.7 / 85.8 / 97.4 | 76.7 |
| mixed_100 | Hoeffding | 0.0 [0.0, 0.5] | 0.1 | 799/800 | 100.0 / 100.0 / 100.0 | 100.0 |
| mixed_150 | v3 percentile | 89.9 [87.6, 91.8] | 0.2 | 798/800 | 92.0 / 85.2 / 97.0 | 75.8 |
| mixed_150 | Cluster t | 89.1 [86.8, 91.1] | 0.2 | 798/800 | 91.1 / 83.3 / 97.4 | 73.9 |
| mixed_150 | Hoeffding | 0.0 [0.0, 0.5] | 0.0 | 800/800 | 100.0 / 100.0 / 100.0 | 100.0 |
| mixed_200 | v3 percentile | 97.2 [95.9, 98.2] | 0.1 | 799/800 | 94.2 / 86.9 / 96.7 | 79.5 |
| mixed_200 | Cluster t | 96.9 [95.4, 97.9] | 0.1 | 799/800 | 93.0 / 85.6 / 97.1 | 77.7 |
| mixed_200 | Hoeffding | 0.0 [0.0, 0.5] | 0.0 | 800/800 | 100.0 / 100.0 / 100.0 | 100.0 |
| null_far | v3 percentile | 2.5 [1.6, 3.8] | 0.0 | 800/800 | 94.0 / 86.5 / 97.5 | 79.5 |
| null_far | Cluster t | 1.8 [1.0, 2.9] | 0.0 | 800/800 | 93.0 / 85.0 / 98.2 | 78.0 |
| null_far | Hoeffding | 0.0 [0.0, 0.5] | 0.0 | 800/800 | 100.0 / 100.0 / 100.0 | 100.0 |
| null_sensitivity | v3 percentile | 6.8 [5.2, 8.7] | 0.0 | 800/800 | 93.4 / 93.0 / 96.1 | 83.4 |
| null_sensitivity | Cluster t | 7.0 [5.4, 9.0] | 0.0 | 800/800 | 92.9 / 92.8 / 96.8 | 83.2 |
| null_sensitivity | Hoeffding | 0.0 [0.0, 0.5] | 0.0 | 800/800 | 100.0 / 100.0 / 100.0 | 100.0 |
| null_coverage | v3 percentile | 5.1 [3.8, 6.9] | 0.0 | 800/800 | 93.9 / 86.5 / 96.8 | 78.9 |
| null_coverage | Cluster t | 4.9 [3.6, 6.6] | 0.0 | 800/800 | 94.0 / 85.5 / 97.6 | 79.1 |
| null_coverage | Hoeffding | 0.0 [0.0, 0.5] | 0.0 | 800/800 | 100.0 / 100.0 / 100.0 | 100.0 |
| null_joint | v3 percentile | 0.0 [0.0, 0.5] | 0.0 | 800/800 | 92.1 / 91.8 / 97.2 | 81.9 |
| null_joint | Cluster t | 0.0 [0.0, 0.5] | 0.0 | 800/800 | 92.1 / 91.9 / 97.9 | 82.6 |
| null_joint | Hoeffding | 0.0 [0.0, 0.5] | 0.0 | 800/800 | 100.0 / 100.0 / 100.0 | 100.0 |
| unequal | v3 percentile | 87.8 [85.3, 89.8] | 1.0 | 792/800 | 93.2 / 87.4 / 97.0 | 79.2 |
| unequal | Cluster t | 87.0 [84.5, 89.2] | 1.0 | 792/800 | 92.9 / 85.9 / 97.7 | 77.9 |
| unequal | Hoeffding | 0.0 [0.0, 0.5] | 0.0 | 800/800 | 100.0 / 100.0 / 100.0 | 100.0 |
| rare | v3 percentile | 0.0 [0.0, 0.5] | 100.0 | 0/800 | NA / NA / NA | NA |
| rare | Cluster t | 0.0 [0.0, 0.5] | 100.0 | 0/800 | NA / NA / NA | NA |
| rare | Hoeffding | 0.0 [0.0, 0.5] | 100.0 | 0/800 | NA / NA / NA | NA |
| prevalent | v3 percentile | 96.5 [95.0, 97.6] | 0.0 | 800/800 | 93.8 / 88.4 / 97.1 | 80.9 |
| prevalent | Cluster t | 95.6 [94.0, 96.8] | 0.0 | 800/800 | 93.5 / 87.4 / 97.8 | 80.2 |
| prevalent | Hoeffding | 0.0 [0.0, 0.5] | 0.0 | 800/800 | 100.0 / 100.0 / 100.0 | 100.0 |
| missing_mcar | v3 percentile | 78.1 [75.1, 80.9] | 1.0 | 792/800 | 94.7 / 89.0 / 97.1 | 81.8 |
| missing_mcar | Cluster t | 76.8 [73.7, 79.5] | 1.0 | 792/800 | 93.8 / 87.1 / 97.6 | 79.7 |
| missing_mcar | Hoeffding | 0.0 [0.0, 0.5] | 0.0 | 800/800 | 100.0 / 100.0 / 100.0 | 100.0 |
| missing_mnar | v3 percentile | 63.5 [60.1, 66.8] | 28.1 | 575/800 | 93.4 / 100.0 / 96.5 | 89.9 |
| missing_mnar | Cluster t | 61.8 [58.3, 65.1] | 28.1 | 575/800 | 92.5 / 100.0 / 97.0 | 89.6 |
| missing_mnar | Hoeffding | 0.0 [0.0, 0.5] | 0.0 | 800/800 | 100.0 / 100.0 / 100.0 | 100.0 |
| dependent | v3 percentile | 72.8 [69.6, 75.7] | 2.6 | 779/800 | 94.9 / 84.2 / 96.7 | 77.0 |
| dependent | Cluster t | 69.2 [66.0, 72.3] | 2.6 | 779/800 | 94.4 / 84.1 / 97.2 | 76.8 |
| dependent | Hoeffding | 0.0 [0.0, 0.5] | 0.0 | 800/800 | 100.0 / 100.0 / 100.0 | 100.0 |
| template | v3 percentile | 55.5 [52.0, 58.9] | 0.8 | 794/800 | 76.8 / 66.8 / 85.1 | 42.2 |
| template | Cluster t | 7.5 [5.9, 9.5] | 75.0 | 200/800 | 81.5 / 76.5 / 100.0 | 64.0 |
| template | Hoeffding | 0.0 [0.0, 0.5] | 75.0 | 200/800 | 100.0 / 100.0 / 100.0 | 100.0 |
| sparse | v3 percentile | 0.0 [0.0, 0.5] | 6.1 | 751/800 | 94.5 / 88.5 / 98.5 | 83.1 |
| sparse | Cluster t | 0.0 [0.0, 0.5] | 6.1 | 751/800 | 93.5 / 87.6 / 99.3 | 82.2 |
| sparse | Hoeffding | 0.0 [0.0, 0.5] | 0.0 | 800/800 | 100.0 / 100.0 / 100.0 | 100.0 |
| invalid_heavy | v3 percentile | 51.4 [47.9, 54.8] | 0.0 | 800/800 | 92.6 / 86.4 / 95.4 | 76.2 |
| invalid_heavy | Cluster t | 50.8 [47.3, 54.2] | 0.0 | 800/800 | 92.0 / 85.8 / 96.2 | 75.9 |
| invalid_heavy | Hoeffding | 0.0 [0.0, 0.5] | 0.0 | 800/800 | 100.0 / 100.0 / 100.0 | 100.0 |
| active_panel | v3 percentile | 0.0 [0.0, 0.5] | 100.0 | 0/800 | NA / NA / NA | NA |
| active_panel | Cluster t | 0.0 [0.0, 0.5] | 100.0 | 0/800 | NA / NA / NA | NA |
| active_panel | Hoeffding | 0.0 [0.0, 0.5] | 0.0 | 800/800 | 100.0 / 100.0 / 100.0 | 100.0 |
| stress_bidirectional | v3 percentile | 59.5 [56.1, 62.8] | 0.1 | 799/800 | 93.5 / 86.0 / 95.2 | 78.1 |
| stress_bidirectional | Cluster t | 59.5 [56.1, 62.8] | 0.1 | 799/800 | 92.4 / 84.2 / 95.4 | 75.5 |
| stress_bidirectional | Hoeffding | 0.0 [0.0, 0.5] | 0.0 | 800/800 | 100.0 / 100.0 / 100.0 | 100.0 |
| stress_full | v3 percentile | 0.0 [0.0, 0.5] | 100.0 | 0/800 | NA / NA / NA | NA |
| stress_full | Cluster t | 0.0 [0.0, 0.5] | 100.0 | 0/800 | NA / NA / NA | NA |
| stress_full | Hoeffding | 0.0 [0.0, 0.5] | 0.0 | 800/800 | 100.0 / 100.0 / 100.0 | 100.0 |
| stress_near | v3 percentile | 43.9 [40.5, 47.3] | 50.4 | 397/800 | 100.0 / 83.6 / 95.5 | 79.8 |
| stress_near | Cluster t | 43.8 [40.4, 47.2] | 50.4 | 397/800 | 100.0 / 83.1 / 96.0 | 79.8 |
| stress_near | Hoeffding | 0.0 [0.0, 0.5] | 0.0 | 800/800 | 100.0 / 100.0 / 100.0 | 100.0 |
| stress_template_null | v3 percentile | 14.2 [12.0, 16.8] | 0.0 | 800/800 | 75.2 / 70.9 / 79.6 | 43.6 |
| stress_template_null | Cluster t | 0.5 [0.2, 1.3] | 95.6 | 35/800 | 77.1 / 80.0 / 97.1 | 60.0 |
| stress_template_null | Hoeffding | 0.0 [0.0, 0.5] | 95.6 | 35/800 | 100.0 / 100.0 / 100.0 | 100.0 |
| no_truth | v3 percentile | 0.0 [0.0, 0.5] | 100.0 | 0/800 | NA / NA / NA | NA |
| no_truth | Cluster t | 0.0 [0.0, 0.5] | 100.0 | 0/800 | NA / NA / NA | NA |
| no_truth | Hoeffding | 0.0 [0.0, 0.5] | 100.0 | 0/800 | NA / NA / NA | NA |
| impossible_mixed | Loại trước mô phỏng | — | — | — | — | — |

### Báo đạt sai ở các biên

| Null | Phương pháp | Sai số biên [95% MC] | Sai số đồng thời [95% MC] |
|---|---|---:|---:|
| null_coverage | v3 percentile | 6.1 [4.7, 8.0] | 5.1 [3.8, 6.9] |
| null_coverage | Cluster t | 5.9 [4.4, 7.7] | 4.9 [3.6, 6.6] |
| null_coverage | Hoeffding | 0.0 [0.0, 0.5] | 0.0 [0.0, 0.5] |
| null_sensitivity | v3 percentile | 7.0 [5.4, 9.0] | 6.8 [5.2, 8.7] |
| null_sensitivity | Cluster t | 7.2 [5.7, 9.3] | 7.0 [5.4, 9.0] |
| null_sensitivity | Hoeffding | 0.0 [0.0, 0.5] | 0.0 [0.0, 0.5] |
| null_far | v3 percentile | 2.5 [1.6, 3.8] | 2.5 [1.6, 3.8] |
| null_far | Cluster t | 1.8 [1.0, 2.9] | 1.8 [1.0, 2.9] |
| null_far | Hoeffding | 0.0 [0.0, 0.5] | 0.0 [0.0, 0.5] |
| null_joint | v3 percentile | 7.9 [6.2, 9.9] / 8.2 [6.5, 10.4] / 2.8 [1.8, 4.1] | 0.0 [0.0, 0.5] |
| null_joint | Cluster t | 7.9 [6.2, 9.9] / 8.1 [6.4, 10.2] / 2.1 [1.3, 3.4] | 0.0 [0.0, 0.5] |
| null_joint | Hoeffding | 0.0 [0.0, 0.5] / 0.0 [0.0, 0.5] / 0.0 [0.0, 0.5] | 0.0 [0.0, 0.5] |
| stress_template_null | v3 percentile | 29.1 [26.1, 32.4] | 14.2 [12.0, 16.8] |
| stress_template_null | Cluster t | 0.9 [0.4, 1.8] | 0.5 [0.2, 1.3] |
| stress_template_null | Hoeffding | 0.0 [0.0, 0.5] | 0.0 [0.0, 0.5] |

## held_out

1600 cohort cho mỗi hàng và phương pháp, cùng đầu vào theo cặp.

| Scenario | Phương pháp | P(đạt cả ba) [95% MC] | P(thiếu) | Xuất cận | Độ phủ C / S / Δ | Độ phủ đồng thời |
|---|---|---:|---:|---:|---:|---:|
| mixed_50 | v3 percentile | 2.4 [1.7, 3.2] | 94.2 | 92/1600 | 91.3 / 89.1 / 96.7 | 79.3 |
| mixed_50 | Cluster t | 1.8 [1.3, 2.6] | 94.2 | 92/1600 | 90.2 / 85.9 / 96.7 | 75.0 |
| mixed_50 | Hoeffding | 0.0 [0.0, 0.2] | 93.8 | 100/1600 | 100.0 / 100.0 / 100.0 | 100.0 |
| mixed_100 | v3 percentile | 70.3 [68.0, 72.5] | 2.1 | 1567/1600 | 93.4 / 87.5 / 97.1 | 79.5 |
| mixed_100 | Cluster t | 67.6 [65.2, 69.8] | 2.1 | 1567/1600 | 92.1 / 85.8 / 97.6 | 77.3 |
| mixed_100 | Hoeffding | 0.0 [0.0, 0.2] | 0.0 | 1600/1600 | 100.0 / 100.0 / 100.0 | 100.0 |
| mixed_150 | v3 percentile | 90.0 [88.4, 91.4] | 0.4 | 1593/1600 | 93.4 / 85.6 / 96.9 | 77.8 |
| mixed_150 | Cluster t | 89.2 [87.6, 90.6] | 0.4 | 1593/1600 | 92.8 / 84.3 / 97.6 | 76.8 |
| mixed_150 | Hoeffding | 0.0 [0.0, 0.2] | 0.0 | 1600/1600 | 100.0 / 100.0 / 100.0 | 100.0 |
| mixed_200 | v3 percentile | 97.1 [96.1, 97.8] | 0.1 | 1599/1600 | 94.9 / 86.4 / 97.1 | 79.7 |
| mixed_200 | Cluster t | 96.5 [95.5, 97.3] | 0.1 | 1599/1600 | 94.2 / 85.4 / 97.8 | 78.9 |
| mixed_200 | Hoeffding | 0.0 [0.0, 0.2] | 0.0 | 1600/1600 | 100.0 / 100.0 / 100.0 | 100.0 |
| null_far | v3 percentile | 2.9 [2.2, 3.9] | 0.1 | 1599/1600 | 93.1 / 88.9 / 97.0 | 80.7 |
| null_far | Cluster t | 1.9 [1.4, 2.7] | 0.1 | 1599/1600 | 92.4 / 87.7 / 98.0 | 80.1 |
| null_far | Hoeffding | 0.0 [0.0, 0.2] | 0.0 | 1600/1600 | 100.0 / 100.0 / 100.0 | 100.0 |
| null_sensitivity | v3 percentile | 9.2 [7.9, 10.7] | 0.0 | 1600/1600 | 93.4 / 90.7 / 96.9 | 81.9 |
| null_sensitivity | Cluster t | 9.2 [7.9, 10.8] | 0.0 | 1600/1600 | 92.9 / 90.5 / 97.4 | 81.7 |
| null_sensitivity | Hoeffding | 0.0 [0.0, 0.2] | 0.0 | 1600/1600 | 100.0 / 100.0 / 100.0 | 100.0 |
| null_coverage | v3 percentile | 5.6 [4.5, 6.8] | 0.4 | 1594/1600 | 93.8 / 85.6 / 96.4 | 77.2 |
| null_coverage | Cluster t | 5.4 [4.4, 6.7] | 0.4 | 1594/1600 | 94.0 / 84.9 / 96.9 | 77.2 |
| null_coverage | Hoeffding | 0.0 [0.0, 0.2] | 0.0 | 1600/1600 | 100.0 / 100.0 / 100.0 | 100.0 |
| null_joint | v3 percentile | 0.0 [0.0, 0.2] | 0.0 | 1600/1600 | 94.8 / 93.4 / 96.6 | 85.6 |
| null_joint | Cluster t | 0.0 [0.0, 0.2] | 0.0 | 1600/1600 | 95.4 / 93.1 / 97.4 | 86.6 |
| null_joint | Hoeffding | 0.0 [0.0, 0.2] | 0.0 | 1600/1600 | 100.0 / 100.0 / 100.0 | 100.0 |
| unequal | v3 percentile | 87.1 [85.4, 88.7] | 0.7 | 1589/1600 | 94.7 / 87.4 / 96.6 | 80.1 |
| unequal | Cluster t | 85.8 [84.0, 87.4] | 0.7 | 1589/1600 | 94.3 / 85.8 / 97.3 | 79.0 |
| unequal | Hoeffding | 0.0 [0.0, 0.2] | 0.0 | 1600/1600 | 100.0 / 100.0 / 100.0 | 100.0 |
| rare | v3 percentile | 0.0 [0.0, 0.2] | 100.0 | 0/1600 | NA / NA / NA | NA |
| rare | Cluster t | 0.0 [0.0, 0.2] | 100.0 | 0/1600 | NA / NA / NA | NA |
| rare | Hoeffding | 0.0 [0.0, 0.2] | 100.0 | 0/1600 | NA / NA / NA | NA |
| prevalent | v3 percentile | 96.0 [94.9, 96.9] | 0.0 | 1600/1600 | 93.8 / 87.2 / 95.3 | 78.4 |
| prevalent | Cluster t | 94.4 [93.1, 95.4] | 0.0 | 1600/1600 | 93.1 / 86.4 / 95.8 | 77.4 |
| prevalent | Hoeffding | 0.0 [0.0, 0.2] | 0.0 | 1600/1600 | 100.0 / 100.0 / 100.0 | 100.0 |
| missing_mcar | v3 percentile | 80.1 [78.0, 81.9] | 1.9 | 1569/1600 | 93.5 / 87.1 / 96.9 | 79.2 |
| missing_mcar | Cluster t | 78.1 [76.0, 80.1] | 1.9 | 1569/1600 | 92.8 / 85.7 / 97.5 | 77.8 |
| missing_mcar | Hoeffding | 0.0 [0.0, 0.2] | 0.0 | 1600/1600 | 100.0 / 100.0 / 100.0 | 100.0 |
| missing_mnar | v3 percentile | 65.2 [62.9, 67.5] | 25.9 | 1186/1600 | 95.0 / 100.0 / 96.1 | 91.1 |
| missing_mnar | Cluster t | 63.4 [61.0, 65.8] | 25.9 | 1186/1600 | 93.8 / 100.0 / 96.8 | 90.6 |
| missing_mnar | Hoeffding | 0.0 [0.0, 0.2] | 0.0 | 1600/1600 | 100.0 / 100.0 / 100.0 | 100.0 |
| dependent | v3 percentile | 74.7 [72.5, 76.8] | 1.3 | 1579/1600 | 93.9 / 81.7 / 96.4 | 74.1 |
| dependent | Cluster t | 72.1 [69.9, 74.3] | 1.3 | 1579/1600 | 92.9 / 81.1 / 97.0 | 73.1 |
| dependent | Hoeffding | 0.0 [0.0, 0.2] | 0.0 | 1600/1600 | 100.0 / 100.0 / 100.0 | 100.0 |
| template | v3 percentile | 54.6 [52.2, 57.1] | 1.1 | 1582/1600 | 76.2 / 64.7 / 86.7 | 42.1 |
| template | Cluster t | 7.1 [6.0, 8.5] | 76.9 | 370/1600 | 81.1 / 72.4 / 99.2 | 58.9 |
| template | Hoeffding | 0.0 [0.0, 0.2] | 76.6 | 374/1600 | 100.0 / 100.0 / 100.0 | 100.0 |
| sparse | v3 percentile | 0.0 [0.0, 0.2] | 5.2 | 1517/1600 | 93.7 / 85.8 / 98.9 | 79.6 |
| sparse | Cluster t | 0.0 [0.0, 0.2] | 5.2 | 1517/1600 | 92.9 / 84.6 / 99.5 | 78.0 |
| sparse | Hoeffding | 0.0 [0.0, 0.2] | 0.0 | 1600/1600 | 100.0 / 100.0 / 100.0 | 100.0 |
| invalid_heavy | v3 percentile | 49.4 [47.0, 51.9] | 0.0 | 1600/1600 | 94.2 / 89.2 / 96.3 | 81.4 |
| invalid_heavy | Cluster t | 49.4 [46.9, 51.8] | 0.0 | 1600/1600 | 93.3 / 88.2 / 97.0 | 80.3 |
| invalid_heavy | Hoeffding | 0.0 [0.0, 0.2] | 0.0 | 1600/1600 | 100.0 / 100.0 / 100.0 | 100.0 |
| active_panel | v3 percentile | 0.0 [0.0, 0.2] | 100.0 | 0/1600 | NA / NA / NA | NA |
| active_panel | Cluster t | 0.0 [0.0, 0.2] | 100.0 | 0/1600 | NA / NA / NA | NA |
| active_panel | Hoeffding | 0.0 [0.0, 0.2] | 0.0 | 1600/1600 | 100.0 / 100.0 / 100.0 | 100.0 |
| stress_bidirectional | v3 percentile | 62.9 [60.5, 65.2] | 0.1 | 1599/1600 | 93.4 / 87.2 / 94.9 | 77.9 |
| stress_bidirectional | Cluster t | 62.3 [59.9, 64.7] | 0.1 | 1599/1600 | 92.4 / 86.1 / 95.1 | 76.2 |
| stress_bidirectional | Hoeffding | 0.0 [0.0, 0.2] | 0.0 | 1600/1600 | 100.0 / 100.0 / 100.0 | 100.0 |
| stress_full | v3 percentile | 0.0 [0.0, 0.2] | 100.0 | 0/1600 | NA / NA / NA | NA |
| stress_full | Cluster t | 0.0 [0.0, 0.2] | 100.0 | 0/1600 | NA / NA / NA | NA |
| stress_full | Hoeffding | 0.0 [0.0, 0.2] | 0.0 | 1600/1600 | 100.0 / 100.0 / 100.0 | 100.0 |
| stress_near | v3 percentile | 43.9 [41.5, 46.4] | 50.7 | 789/1600 | 100.0 / 88.8 / 95.6 | 84.8 |
| stress_near | Cluster t | 43.5 [41.1, 45.9] | 50.7 | 789/1600 | 100.0 / 87.1 / 95.9 | 83.4 |
| stress_near | Hoeffding | 0.0 [0.0, 0.2] | 0.0 | 1600/1600 | 100.0 / 100.0 / 100.0 | 100.0 |
| stress_template_null | v3 percentile | 13.7 [12.1, 15.5] | 0.0 | 1600/1600 | 75.9 / 70.6 / 81.0 | 44.6 |
| stress_template_null | Cluster t | 0.4 [0.2, 0.8] | 95.4 | 73/1600 | 83.6 / 74.0 / 100.0 | 61.6 |
| stress_template_null | Hoeffding | 0.0 [0.0, 0.2] | 95.4 | 73/1600 | 100.0 / 100.0 / 100.0 | 100.0 |
| no_truth | v3 percentile | 0.0 [0.0, 0.2] | 100.0 | 0/1600 | NA / NA / NA | NA |
| no_truth | Cluster t | 0.0 [0.0, 0.2] | 100.0 | 0/1600 | NA / NA / NA | NA |
| no_truth | Hoeffding | 0.0 [0.0, 0.2] | 100.0 | 0/1600 | NA / NA / NA | NA |
| impossible_mixed | Loại trước mô phỏng | — | — | — | — | — |

### Báo đạt sai ở các biên

| Null | Phương pháp | Sai số biên [95% MC] | Sai số đồng thời [95% MC] |
|---|---|---:|---:|
| null_coverage | v3 percentile | 6.2 [5.1, 7.5] | 5.6 [4.5, 6.8] |
| null_coverage | Cluster t | 6.0 [4.9, 7.3] | 5.4 [4.4, 6.7] |
| null_coverage | Hoeffding | 0.0 [0.0, 0.2] | 0.0 [0.0, 0.2] |
| null_sensitivity | v3 percentile | 9.3 [8.0, 10.8] | 9.2 [7.9, 10.7] |
| null_sensitivity | Cluster t | 9.5 [8.2, 11.0] | 9.2 [7.9, 10.8] |
| null_sensitivity | Hoeffding | 0.0 [0.0, 0.2] | 0.0 [0.0, 0.2] |
| null_far | v3 percentile | 3.0 [2.3, 4.0] | 2.9 [2.2, 3.9] |
| null_far | Cluster t | 2.0 [1.4, 2.8] | 1.9 [1.4, 2.7] |
| null_far | Hoeffding | 0.0 [0.0, 0.2] | 0.0 [0.0, 0.2] |
| null_joint | v3 percentile | 5.2 [4.2, 6.4] / 6.6 [5.5, 7.9] / 3.4 [2.6, 4.4] | 0.0 [0.0, 0.2] |
| null_joint | Cluster t | 4.6 [3.6, 5.7] / 6.9 [5.7, 8.2] / 2.6 [1.9, 3.5] | 0.0 [0.0, 0.2] |
| null_joint | Hoeffding | 0.0 [0.0, 0.2] / 0.0 [0.0, 0.2] / 0.0 [0.0, 0.2] | 0.0 [0.0, 0.2] |
| stress_template_null | v3 percentile | 29.4 [27.2, 31.7] | 13.7 [12.1, 15.5] |
| stress_template_null | Cluster t | 1.2 [0.8, 1.8] | 0.4 [0.2, 0.8] |
| stress_template_null | Hoeffding | 0.0 [0.0, 0.2] | 0.0 [0.0, 0.2] |
