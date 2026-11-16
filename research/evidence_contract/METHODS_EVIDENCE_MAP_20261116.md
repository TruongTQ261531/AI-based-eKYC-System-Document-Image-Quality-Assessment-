# Evidence map phương pháp khắc phục — 16/11/2026

Đây là tìm kiếm có mục tiêu trên nguồn chính thức/paper gốc, không phải systematic
review hay tuyên bố đã tìm hết mọi phương pháp. Các cụm tìm gồm: metamorphic oracle
false alarm, information-matched baseline, document grounding, real faults versus
mutants, delta debugging, selective prediction, conformal calibration, combinatorial
testing, annotation quality, identity document benchmark và CFP EASE 2027. Ưu tiên
nguồn tác giả, proceedings, cơ quan chuẩn và official CFP. Chưa làm citation snowball
toàn bộ, đánh giá risk of bias cho từng paper, hoặc tái lập các hệ thống bên dưới.

| Họ phương pháp và nguồn gốc | Áp dụng vào vấn đề A | Quyết định và giới hạn |
|---|---|---|
| Oracle taxonomy — Barr et al., [TSE 2015](https://ieeexplore.ieee.org/document/6963470) | Phân biệt reference oracle, relation oracle, heuristic candidate và bug proof | Đã tách endpoint/provenance; không gọi heuristic là gold |
| MT có điều kiện — Segura et al., [TSE 2016](https://eprints.whiterose.ac.uk/id/eprint/110335/1/segura16-tse.pdf) | MR phải có applicability, không mặc định mọi mask/rotate là hợp lệ | Đã có validity, abstention và boundary probes; cần ngoài-renderer |
| Sinh/lọc MR — Ayerdi et al., [GenMorph](https://arxiv.org/html/2312.15302v3) | Tối ưu cả false alarms và missed faults, đánh giá trên known-good và fault controls | Union phát thêm FP nên không chọn làm mặc định. Không train/tune theo nhãn test |
| Functional coupling + amplification — Xu et al., [MR-Coupler, FSE 2026](https://arxiv.org/abs/2604.10126) | Dùng cấu trúc stage để sinh candidate, kiểm bằng amplification và patch witness | Ý tưởng cho generator tiếp theo, chưa triển khai MR-Coupler, không dùng số paper làm số project |
| MT cho LLM — Cho et al., [LLMorph](https://arxiv.org/html/2603.23611v1) | Tách task, relation, subject và output; relation violation vẫn cần triage | Tham khảo kiến trúc và replay. Không mặc định LLM làm judge độc lập của chính nó |
| Grounding vị trí — Perot et al., [LMDX, ACL 2024](https://aclanthology.org/2024.findings-acl.899/) | Gắn field vào pixel/source để tránh “đúng chuỗi nhưng sai nguồn” | Prototype reference binding đã có; grounding không tự chứng minh novel graph contribution |
| Differential testing — Pei et al., [DeepXplore](https://arxiv.org/abs/1705.06640) | Bất đồng reader ưu tiên triage, có thể tìm vùng hệ thống yếu | Chưa lấy majority làm gold; hai reader Rapid có quan hệ nên không là ba bằng chứng độc lập |
| Real fault versus mutation — Just et al., [FSE 2014](https://homes.cs.washington.edu/~mernst/pubs/mutation-effectiveness-fse2014-abstract.html) | Không thay lỗi thực bằng output tiêm khi claim root cause/discovery | Đã chạy 5 phiên bản mã và cô lập 2 lỗi lịch sử. Cần lỗi phát hiện tiến cứu ngoài hai family |
| Corpus bug tái lập — Widyasari et al., [BugsInPy, FSE 2020](https://ratnadiraw.github.io/assets/pdf/bugsinpy.pdf) | Lưu buggy/fixed revision, reproducer, environment và expected failure | Áp dụng cấu trúc artifact, chưa chạy benchmark BugsInPy và không giả định bug Python chung đại diện eKYC |
| Giảm input — Zeller & Hildebrandt, [TSE 2002](https://www.cs.purdue.edu/homes/xyzhang/fall07/Papers/delta-debugging.pdf) | Tạo witness nhỏ, dễ kiểm và tiết kiệm triage | Đã chạy whole-row ddmin: 3→1 và 4→2 dòng; precondition không đủ trả UNRESOLVED |
| Thiết kế tổ hợp — [NIST SP 800-142](https://csrc.nist.gov/pubs/sp/800/142/final) | Phủ tổ hợp source, label, locale, geometry, precision theo ngân sách | Panel nhỏ chạy factorial; covering array dành panel lớn. Coverage không chứng minh accuracy |
| Selective prediction — Geifman & El-Yaniv, [SelectiveNet, ICML 2019](https://proceedings.mlr.press/v97/geifman19a.html) | Báo coverage cùng error/risk, phân biệt abstention với PASS | Đã đo coverage; chưa triển khai SelectiveNet. Chỉ hạ alarm bằng abstain không đủ |
| Calibration/conformal — Angelopoulos & Bates, [tutorial](https://arxiv.org/abs/2107.07511) | Có thể đặt ngưỡng reject bằng tập calibration độc lập | Chưa dùng: không có tập calibration đủ và giả định exchangeability chưa được kiểm. Không bịa guarantee từ 3 ID |
| Annotation quality — Klie et al., [Computational Linguistics 2024](https://aclanthology.org/2024.cl-3.1/) | Quy trình, instruction, adjudication và agreement cần báo riêng | UI guard, blind packet, sealing và agreement tooling đã có. Kappa/alpha không thay validity hay independence |
| MRZ theo trường — [ICAO Doc 9303 Part 3](https://www.icao.int/publications/documents/9303_p3_cons_en.pdf), [Part 4](https://www.icao.int/publications/documents/9303_p4_cons_en.pdf) | Check digit có phạm vi; giữ YYMMDD, composite, semantic link; không “sửa” O/0 tùy tiện | Prototype còn bảo thủ, không claim triển khai đầy đủ ICAO. Cần controls trường không có checksum và xung đột precision |
| Dữ liệu ngoài renderer — Bulatov et al., [MIDV-2020](https://arxiv.org/abs/2107.00396) | Giấy tờ giả lập đa dạng, capture/video/scans; split ở document/template level | Đã khảo sát nguồn; chưa tải. Phải kiểm license, mapping và leakage trước inference. Video frame không là ID độc lập |
| Huấn luyện/fine-tune OCR hoặc quality model | Có thể sửa lỗi reader đã định vị và có nhãn training phù hợp | Chưa train thêm: lỗi hiện tại chủ yếu ở thiết kế oracle/reference và evidence. Muốn train cần freeze task, train/dev/test và ablation; không dùng feedback đánh giá làm training ngầm |
| Đổi claim/đổi phạm vi bài | Kết quả âm có điều kiện và methodological lessons có thể hữu ích | Chuẩn bị draft Emerging; chưa tự tuyên bố đủ tính mới hoặc được nhận. Research giữ gate |

Các ý tưởng chưa triển khai không được tính là tiến độ thực nghiệm hoàn tất. Kết
quả từ paper là động cơ phương pháp; mọi số đo project phải trỏ tới artifact của
project. Tìm kiếm thêm sẽ ưu tiên literature về generation validity, diagnostic
cost và information parity, vì đó là các claim có thể phân biệt A sau phân tích
hiện tại; không chạy vô hạn cùng một pilot để tìm kết quả có lợi.

Tiêu chuẩn đối chiếu thiết kế nghiên cứu: [ACM SIGSOFT Empirical Standards](https://www2.sigsoft.org/EmpiricalStandards/).
Tình trạng và tiêu chí đóng từng gap: [Readiness analysis](READINESS_ANALYSIS_20261116.md).
