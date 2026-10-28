# Kiểm tra chân dung qua camera — cơ chế cử động từ API v3.0.1

**Cập nhật API 3.1.0:** đã thêm PAD MiniFASNet ở từng frame và ảnh cuối.
Xem [OCR/PAD và kiểm thử mới](ocr_and_pad.md). Thông số 4 động tác/180 giây
vẫn giữ nguyên. Phần kiểm thử 79/10 cuối trang là lịch sử của v3.0.1,
trước khi thay OCR và bổ sung PAD.

Trước v3, web chỉ nhận một ảnh selfie để so với giấy tờ. Module 4 cũ đọc video
ở nhánh CLI nghiên cứu; web không gọi nhánh đó, nên kết quả ghi chưa kiểm tra
liveness. Từ v3, web bắt buộc thực hiện thử thách cử động do server quản lý trước
khi đối chiếu ảnh chân dung cuối.

## Các chức năng đã triển khai

| Chức năng | Cách xử lý và giới hạn |
|---|---|
| Một khuôn mặt trong ảnh | MediaPipe tối đa hai mặt; nhiều hơn một mặt làm thử thách thất bại. |
| Khung căn chỉnh | Kiểm tra mặt quá nhỏ/quá gần, thiếu trán/cằm/mép, lệch tâm; hướng dẫn ngay trên trang. |
| Chất lượng vùng mặt | Độ sáng, độ tương phản và Laplacian vùng mặt; chỉ các ngưỡng heuristic, chưa hiệu chỉnh theo từng camera. |
| Hướng đầu | Euler yaw/pitch/roll từ ma trận biến đổi của MediaPipe; hiệu chuẩn tương đối khi nhìn thẳng. Không phải góc đo bằng camera đã hiệu chuẩn. |
| Chớp mắt | Hai điểm số eyeBlink phải cùng cao rồi cùng thấp; cần chuỗi mở → nhắm → mở đúng thời gian. Nhắm một mắt không đạt. |
| Quay trái/phải | Cả hai động tác bắt buộc, giữ góc rồi trở về tư thế giữa; không tính một ảnh mặt nghiêng đơn lẻ. |
| Cúi đầu | Tăng pitch so với lúc căn chỉnh, giữ rồi trở lại. |
| Ánh nhìn | Vị trí mống mắt so với hai góc mắt, hiệu chuẩn lúc nhìn camera khi theo dõi được mắt. Chỉ hiển thị tham khảo; không bắt buộc trong 4 động tác và không chặn bước trở về giữa nếu chưa đọc rõ iris. |
| Hình học trên preview | Các điểm mắt, mống mắt, mũi, trán/cằm; yaw/pitch/roll, mắt nhắm và chỉ số chất lượng. Preview và overlay cùng được lật khi dùng camera trước; pixel gửi đi giữ nguyên hướng camera. |
| Cùng người trong thử thách | Lấy mẫu SFace cách nhau ít nhất 0,7 giây ở góc đầu vừa phải; kiểm tra tương đồng với mọi mẫu đã giữ. Tối đa giữ 12 embedding trên RAM. |
| Ảnh cuối cùng người | So ảnh chân dung độ phân giải gốc với các mẫu thử thách và ảnh giấy tờ. Nếu mẫu giữa các bước không nhất quán, trả lý do riêng. |
| Thứ tự và thời hạn | Server chọn ngẫu nhiên thứ tự 4 động tác, chỉ công bố động tác hiện tại; nonce thay mỗi frame, số thứ tự tăng. Dùng một hạn tổng 180 giây theo đồng hồ server; không có timeout riêng từng bước hoặc giới hạn 500 frame. |
| Chống dùng lại nguyên frame | Phát hiện hash pixel bị lặp, sai nonce/thứ tự; không coi đây là khả năng chống mọi video phát lại. |
| Chặn bỏ qua bước | `/api/selfie` trả HTTP 409 nếu chưa có thử thách đạt trên RAM hoặc kết quả quá 45 giây. Client không tự khai blink/yaw/đã đạt. |
| Hủy và riêng tư | Dừng, đổi camera, rời trang hoặc reset hủy tiến trình ở client; DELETE hủy challenge ở server. Không giữ ảnh/video ra tệp. Không lưu landmark hoặc embedding vào localStorage. |

4 động tác gồm chớp mắt, quay trái, quay phải và cúi đầu.
Mỗi động tác phải bắt đầu ở giữa và kết thúc ở giữa. Ngưỡng mặc định: quay đầu
14–40°, cúi 10–30°; trở về giữa khi yaw/pitch lệch dưới 10°; giữ tối thiểu
0,25 giây; mở mắt <0,28, nhắm cả hai >0,55, nhắm 0,08–1,8 giây. Tạm mất mặt
hoặc chất lượng không đạt được chờ tối đa 6 giây để điều chỉnh; nhiều mặt/đổi
identity vẫn bị chặn. Các ngưỡng cần được hiệu
chỉnh bằng dữ liệu camera thật, đặc biệt với kính và hình dạng mắt khác nhau.

## Luồng API và cách sử dụng

1. Chụp giấy tờ và xác nhận form như trước.
2. Mở camera trước. Bấm **Bắt đầu kiểm tra cử động**: đây là thao tác đồng ý gửi
   các khung hình để phân tích. Trình duyệt gửi từng JPEG (cạnh dài tối đa 960 px),
   chỉ có một yêu cầu đang xử lý; không upload video ghi sẵn.
3. Làm từng hướng dẫn. Trang hiển thị tiến độ trên tổng 4 và thời gian còn lại
   trong 180 giây. Khi timeout, hiển thị đã hết thời gian. Các lỗi khác hiển thị
   đã dừng và lý do riêng, không tiếp tục ghi còn thời gian như một lượt đang chạy.
4. Đạt thử thách thì nút **Chụp ảnh** xuất hiện. Chụp ảnh gốc, xem lại rồi xác nhận.
   Hiệu lực thử thách 45 giây; chụp lại bằng camera cần thực hiện thử thách mới.
5. Kết quả ghi các động tác đã đạt, tính nhất quán khuôn mặt và điểm đối chiếu.
   `identity_verified=false` vẫn được giữ vì hệ thống không tự phê duyệt eKYC.

| Endpoint mới | Ý nghĩa |
|---|---|
| POST `/api/liveness/start` | Cần form đã xác nhận và ID embedding. Khởi tạo challenge mới, tối đa 3 lần/phiên. |
| POST `/api/liveness/frame` | Multipart `image`, header `X-Session-Token`, `X-Liveness-Id`, `X-Frame-Token`, `X-Frame-Sequence`. Server tự đo từ pixel. |
| DELETE `/api/liveness` | Hủy challenge và embedding của challenge, giữ bước giấy tờ/form để thử lại. |

Frame giới hạn 750 KiB và 1,2 MP, request giới hạn trước multipart; dữ liệu ở RAM.
Ảnh chân dung cuối vẫn theo giới hạn 30 MB/32 MP hiện có. Các phiên được xóa
sau đối chiếu hoặc hết TTL. API dùng model `face_landmarker.task` đã có sẵn;
v3.1 bổ sung ONNXRuntime/VietOCR/einops trong môi trường có sẵn, không tạo project mới.

## Chức năng còn thiếu để đánh giá xác thực chống giả mạo

| Phần cần bổ sung/đánh giá | Tình trạng thực tế |
|---|---|
| PAD chuyên dụng trên ảnh/video | Từ v3.1 có MiniFASNetV2 + V1SE; chưa có tập bona fide/attack của camera mục tiêu để đo độ chính xác hoặc chứng minh chống mọi replay, mặt nạ/deepfake. |
| Camera giả và chèn luồng hình | Browser RGB/getUserMedia không chứng thực camera vật lý. Nonce/sequence ngăn dùng lại yêu cầu nhưng không chứng minh nguồn pixel. |
| Che mặt và kính phản chiếu | Có kiểm tra chất lượng và khả năng theo dõi mắt; chưa có classifier chuyên dụng cho khẩu trang, vật che mặt, phản chiếu trên kính. Không kết luận loại vật che từ landmark. |
| Ánh nhìn chính xác/gaze dọc | Mới có gaze ngang tương đối để tham khảo, không phải thử thách bắt buộc; chưa hiệu chỉnh eye tracker và chưa yêu cầu nhìn lên/xuống bằng mắt. |
| Kiểm thử người thật và tấn công | Chưa có lượt camera người thật trong kiểm thử tự động lần này. Cần đánh giá nhiều camera, ánh sáng, kính, hình dạng mắt, tốc độ chuyển động và tấn công thật. |
| Hiệu chỉnh ngưỡng nhận dạng | Ngưỡng SFace 0,363 vẫn là ngưỡng tham chiếu; chưa có ROC/FAR/FRR trên cặp ID/selfie của ứng dụng. |
| Đăng ký sinh trắc lâu dài | Luồng này xác minh trong một phiên; chưa lưu template chân dung dài hạn. Việc đăng ký/lưu trữ cần yêu cầu riêng về mục đích, đồng ý và bảo vệ dữ liệu. |

Dataset hiện tại là ảnh giấy tờ với nhãn Clean/Blur/Cropped/Dark/Distorted.
Nó không chứa chuỗi selfie người thật/tấn công đã gán nhãn để huấn luyện PAD.
Nên API báo `presentation_attack_detection=not_certified` và mô tả kết quả là
**đã hoàn thành thử thách cử động**, không tự nhận kết quả chống giả mạo đã được kiểm định.

## Bằng chứng kiểm thử

Kiểm tra cuối: **79 test Python và 10 test frontend qua**. Server localhost dùng
API `3.0.1`, `liveness_enabled=true`, thời hạn 180 giây và 4 động tác,
`presentation_attack_detection=not_certified`; trang đang phục vụ nút bắt đầu
kiểm tra cử động. Không thực hiện lượt camera người thật trong lần kiểm tra này.

- Unit/API: đo pose/iris, chuỗi đủ 4 động tác (kể cả iris không đọc được), không
  timeout ngầm sau 18 giây/500 frame, hết hạn đúng bộ đếm tổng, quay sai thứ tự, nhắm một mắt,
  mất mặt, nhiều mặt, đổi identity, frame lặp, nonce cũ, thử lại/hủy, timeout,
  giới hạn frame, gửi số đo giả từ client và chặn photo-only. Các lượt đạt trong
  test dùng **observation giả lập**, không được dùng như bằng chứng người thật.
- Frontend: quyền camera, ảnh gốc, chỉ gửi frame sau bấm bắt đầu, đúng nonce,
  chưa đạt thì không chụp selfie, preview/xác nhận sau khi đạt, thất bại/hủy.
- `python -m scripts.smoke_active_liveness`: dùng thật MobileNet/OCR/YuNet/SFace/
  MediaPipe; ảnh chân dung dataset đứng yên không đạt. Frame lặp bị chặn;
  thay đổi pixel nền trong 20 frame vẫn không hoàn thành động tác. Gửi ảnh cuối
  bị từ chối HTTP 409, phiên được xóa và không tạo tệp PII. Báo cáo
  `outputs/active_liveness_smoke.json`. Đây là smoke âm tính, không phải benchmark PAD.

Tài liệu chính thức sử dụng: [MediaPipe Face Landmarker Python](https://ai.google.dev/edge/mediapipe/solutions/vision/face_landmarker/python),
[MediaPipe blendshape definitions](https://github.com/google-ai-edge/mediapipe/blob/master/mediapipe/tasks/python/vision/face_landmarker.py).
Để thiết kế đánh giá PAD riêng, xem [NIST FATE PAD / NISTIR 8491](https://www.nist.gov/publications/face-analysis-technology-evaluation-fate-part-10-performance-passive-software-based).
