# eKYC → EASE 2027: tiến độ sau lượt đánh giá cá nhân

Cập nhật 16/11/2026, Asia/Bangkok. Đây là lịch làm việc đề xuất từ trạng thái
đã kiểm; ngày nội bộ là mục tiêu, phụ thuộc người đánh giá và dữ liệu thực nhận.
Không tính phần trăm hoàn thành chung vì phạm vi thực nghiệm chưa khóa.

**Phiếu không chặn toàn project.** [Luồng kỹ thuật độc lập](INDEPENDENT_WORK_STATUS.md)
ghi công việc đã tiếp tục khi chờ pha 2: kiểm backend/camera, sửa tách trường,
smoke model thật và kiểm điều kiện huấn luyện. Cần phân biệt tiến độ ứng dụng
với phần bằng chứng phải chờ người đánh giá.

## Kết quả đã hoàn tất

Pha 1 cá nhân: **31 ảnh, 86/86 mục đủ schema**, đã nhập và khóa nguyên trạng.
Một tác giả dự án có hai phiên bản export, không phải hai reviewer độc lập.
Pha 2 đã hoàn tất và nhập đủ **46 ca: 42 primary + 4 diagnostic**, gồm ca có
và không có cảnh báo. Đã sửa đường dẫn và kiểm hash 92 liên kết ảnh. Công cụ cho
phép sao lưu nháp, xuất hoàn chỉnh hoặc xuất phần đã làm với thông báo rõ.
[Receipt](execution/master_01/ifv_20261114/phase1_readiness.json)

Phần development trước đây đã có cache, baseline, controls, can thiệp M2–M3,
replay và nháp ACM. Lượt này không chạy inference hay training mới.
Ngày 15/11 đã niêm phong, replay báo cáo hai endpoint và kiểm độ nhạy. Có
26/42 nhãn pointwise và 21/42 relation; các mục cá nhân đều đã làm xong.
CI, agreement, cost và chuẩn độc lập tiếp tục thiếu; chưa có GO hoặc lock mới.
[Kết quả](IFV_RESULTS_VI.md) · [Protocol prospective](POST_IFV_PROTOCOL_DRAFT.md)

Ngày 16/11 đã replay ba hướng A exploratory trên lịch cũ, tách field/relation,
đồng thời hoàn thiện gói review offline R02/R03 và công cụ agreement. A_change
tăng TP pointwise 2→4/7 trong panel tác giả; A_dual đạt 7/7 bằng kênh B3 cũ.
Đây là development sau pilot, chưa phải tăng hiệu quả được xác nhận độc lập.
[Kết quả và giới hạn](A_DEVELOPMENT_20261116.md). Hai ZIP đã sẵn sàng gửi riêng;
**0 reviewer ngoài thực nhận**, không tính package thành người đã chấm.
[Cách gửi/nhận JSON](REVIEWER_HANDOFF_VI.md). Mỗi mốc hoàn tất phải commit/push
và kiểm remote HEAD theo [chính sách GitHub](../../PROJECT_SYNC_POLICY.md).

Trong lúc người dùng gửi phiếu, đã hoàn thành thêm
[reference controls](REFERENCE_CONTROLS_20261116.md): 252 lượt injected, khử trùng
còn 131 so sánh/13 cặp pixel. Tìm được counterexample của union và shared-reference
failure; prototype reference-bound xử lý được controls nhưng baseline nhận cùng
reference cũng tương đương ở field. Đây là tiến độ P1 không phụ thuộc feedback,
không tăng số lỗi model thật hoặc reviewer.

## Đóng góp phù hợp hội nghị

Đề xuất giữ câu hỏi chính: **tiền điều kiện về nguồn và cách xử lý bất định
ảnh hưởng thế nào đến độ tin cậy của test oracle cho pipeline trích xuất
giấy tờ bằng AI?** eKYC cung cấp ngữ cảnh và pipeline cụ thể. Kết quả phải giúp
kỹ sư quyết định khi nào một cảnh báo kiểm thử có căn cứ và khi nào cần từ chối
kết luận. Phần identity matching/PAD/liveness chưa thuộc endpoint đã đo.

Đối chiếu CFP ngày 15/11: phạm vi liên quan gồm Software Testing, Software
Engineering for AI, Software Quality và phương pháp đánh giá thực nghiệm.
Research Papers nhận bài tối đa 10 trang nội dung + 2 trang chỉ tài liệu tham
khảo, review ẩn danh. Hạn abstract **15/01/2027**, full paper **22/01/2027**,
đều AoE. [CFP Research Papers](https://conf.researchr.org/track/ease-2027/ease-2027-papers)

Đây là đánh giá mức phù hợp do dự án đề xuất, không phải cam kết được nhận.
Claim phải theo bằng chứng: A_flat đã trùng A trên 120/120 verdict development;
chưa chứng minh cấu trúc graph tạo thêm hiệu quả. Giữ so sánh ngang thông tin
với A_flat, B3 có gate, V3, B0 và B2; không dùng baseline yếu để tạo cải thiện.
[Claim ledger](paper/CLAIM_TO_EVIDENCE.md) · [Gate](REVISED_GO_NO_GO.md)

## Các mốc và người phụ trách

| Mốc nội bộ | Phụ trách | Đầu việc và đầu ra cần có | Dependency / tiêu chí qua mốc |
|---|---|---|---|
| 14/11 — DONE | Công cụ/analyst | Khóa pha 1; phát hành pha 2; kiểm ảnh, bảo toàn, cập nhật bản thảo và kế hoạch | 86/86; 46/46; không đổi quan sát hay cache |
| 15/11 — DONE sớm | Tác giả | Hoàn tất cả 46 ca đối chiếu và gửi export | Đã nhận và khóa; không còn chờ phiếu hiện tại |
| 15/11 — DONE sớm | Công cụ/analyst | Import/replay; counts hai endpoint; source gates, all-alarm accounting và sensitivity | 26/42 pointwise, 21/42 relation; 17 cờ/15 primary; 0 UNREVIEWED. Bảng chính không đổi |
| 16/11 — DONE development tooling | Công cụ/analyst | Ba ứng viên A exploratory, replay toàn lịch cũ, ZIP R02/R03, guard lựa chọn và công cụ agreement | 0 inference/training mới; A_dual field=B3; chưa có phiếu ngoài, superiority NO-GO |
| 16/11 — DONE reference controls | Công cụ/analyst | Prototype schema/typed policy/trust binding và 252 injected executions; verifier stdlib; kiểm hồi quy 245 Python + 6 subtests/15 JS | 131 comparisons khác nhau, 13 cặp pixel; fixture truth và inventory chia sẻ renderer, chưa là external ground truth |
| 16–20/11 | Công cụ/analyst + tác giả | Hoàn thiện reference schema/policy và thiết kế panel oracle validity/coverage; [protocol](POST_IFV_PROTOCOL_DRAFT.md) đã có | Tooling đã có một phần; reference approval, sizing/budget và panel mới còn pending |
| 16–27/11 | Tác giả tổ chức nguồn lực | Gửi ZIP riêng cho hai người ngoài; thu pha 1→seal→pha 2, đo agreement trước phân xử; chuẩn độc lập phù hợp endpoint | Tối thiểu thêm 1 để bắt đầu so, khuyến nghị thêm 2. Không có số người bảo đảm đúng; không yêu cầu tác giả làm lại 46 ca |
| 28–30/11 | Tác giả + phân tích | Quyết định GO mới cho claim cụ thể sau prep/reference/adequacy | Pilot hiện giữ NO-GO superiority: A_flat trùng A, sensitivity/coverage A thấp hơn, FAR không vững qua sensitivity |
| 01–07/12, nếu GO | Công cụ/analyst + nguồn dữ liệu | Thực hiện 6B từ prep 6A: manifest mới, nguồn quyền dùng, kiểm tách ID/content/pixel/lineage, nhãn và lock | Đủ số cụm theo sizing/effect đã chốt; protocol, code, reader, seed, exclusions và inference budget được ghim |
| 08–20/12, nếu lock hợp lệ | Công cụ/analyst | 7B: thực nghiệm theo manifest; log append-only, replay, thống kê và kiểm sensitivity | Không sửa protocol theo output. Khóa không đạt thì không chạy confirmatory |
| 21/12–03/01 | Tác giả + công cụ | Viết kết quả/threats, đối chiếu mọi claim; build PDF, kiểm trang/hình/bảng; gói tái lập ẩn danh | Kết quả thật có provenance. Có compiler và kiểm layout; quyền phát hành và ẩn danh được rà |
| 04–10/01 | Tác giả | Rà soát readiness; quyết định Research hay phương án track khác | Đủ bằng chứng và artifact; quyết định dựa maturity, không chỉ theo hạn |
| 11–14/01 | Tác giả | Chốt abstract, thông tin đăng ký bài và kiểm CFP lần cuối | Mục tiêu nội bộ trước hạn abstract chính thức 15/01 AoE |
| 15–21/01 | Tác giả | Chốt manuscript và supplement để nộp | Mục tiêu nội bộ trước hạn paper chính thức 22/01 AoE. Chưa có thao tác nộp trong lượt này |

AoE là UTC−12; tại Asia/Bangkok, 23:59 ngày 15/01 tương ứng **18:59 ngày
16/01/2027**, và 23:59 ngày 22/01 tương ứng **18:59 ngày 23/01/2027**.
Dùng mục tiêu nội bộ sớm hơn để tránh phụ thuộc giờ cuối.

## Những điểm phải giải quyết trước khi mở rộng thực nghiệm

1. **Giới hạn C2.** Từ quan sát đã khóa, 0/10 ca C2 đạt đồng thời điều kiện đọc
   rõ và backup theo guard hiện có. Có 12 quan sát mang ghi chú nhất quán nguồn.
   Không sửa nguồn/MRZ bằng tham chiếu tác giả hoặc output. Giữ pilot và báo
   inconclusive/invalid; nếu cần panel mới thì tạo protocol/version và exposure
   riêng. Không lựa chọn lại ca thuận lợi trong sample cũ.
2. **Một người đánh giá.** Kết quả mô tả có ích cho pilot nhưng chưa là độc lập
   hay agreement. Gói đã có theo [handoff](REVIEWER_HANDOFF_VI.md); cần người thực
   và kiểm exposure, không dùng hai phiên bản của một người. Nếu không có nguồn lực thứ hai, thu hẹp claim và báo rõ giới
   hạn; không gắn nhãn confirmatory cho development đã xem.
3. **Số cụm và fault provenance.** Ba ID primary không cho phép coi nhiều field,
   reader hoặc view là mẫu độc lập. Dùng sizing theo ID/family và kế hoạch đã
   chốt trước output. Claim regression/localization cần lỗi có nguồn gốc
   version/patch/revert phù hợp; can thiệp crop và synthetic controls báo riêng.
4. **Chi phí và PDF.** Timestamp reveal/export không phải active review time.
   Nếu chưa đo thì để NA. Bản ACM còn cần compiler và QA PDF trước khi xác nhận
   trang/format; kiểm source không thay được kiểm layout.

## Nếu đến mốc quyết định vẫn NO-GO

Giữ Research Papers là mục tiêu nhưng chưa hứa nộp. Hướng khả thi khi bằng
chứng còn ở mức pilot là bài phương pháp hoặc kết quả bước đầu có claim hẹp.
Short Papers and Emerging Results cho phép tối đa **6 trang tổng cộng**, hạn
abstract **22/02**, paper **01/03/2027**, AoE.
[CFP Short/Emerging](https://conf.researchr.org/track/ease-2027/ease-2027-short-papers-and-emerging-results)

RENE phù hợp nếu nghiên cứu chặt chẽ làm rõ giới hạn, baseline đơn giản hoặc
độ tái lập; pilot nhỏ không có ý nghĩa thống kê chưa đủ để gọi kết quả âm.
Hạn abstract **22/02**, paper **01/03/2027**, AoE; tối đa **10+2 trang**.
[CFP RENE](https://conf.researchr.org/track/ease-2027/ease-2027-reproducibility-and-negative-results)

Chưa quyết định chuyển track. Nhánh A+B giữ exploratory. Phần đánh giá cá
nhân của bạn ở cả hai pha được ghi nhận DONE. Việc còn cần nguồn lực con
người là reference độc lập phù hợp claim; không tiếp tục chờ phiếu đã nhận.
