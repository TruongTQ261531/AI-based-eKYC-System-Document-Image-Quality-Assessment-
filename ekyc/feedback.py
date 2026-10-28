"""Customer-facing, evidence-scoped diagnosis; no invented OCR or identity data."""
MESSAGES = {
    'too_dark': ('Ảnh có dấu hiệu quá tối', 'Chi tiết trên ảnh chưa đủ sáng để đọc.',
                 ['Di chuyển đến nơi có ánh sáng đều, chiếu sáng mặt trước giấy tờ.', 'Tránh để bóng tay hoặc điện thoại phủ lên giấy tờ; không bật flash chiếu thẳng.']),
    'blur': ('Ảnh có dấu hiệu bị mờ', 'Mô hình và phép đo độ nét cùng cho thấy ảnh thiếu chi tiết.',
             ['Lau sạch ống kính, giữ điện thoại đứng yên và chờ camera lấy nét.', 'Đưa giấy tờ gần hơn vừa đủ để đọc được chữ, nhưng giữ cả bốn góc trong ảnh.']),
    'no_detail': ('Ảnh chưa có đủ chi tiết', 'Ảnh gần như đồng màu, không đủ nét chữ và đường biên để xử lý.',
                  ['Kiểm tra ống kính không bị che và giấy tờ nằm trước camera.', 'Chờ camera lấy nét, điều chỉnh ánh sáng rồi chụp lại.']),
    'low_resolution': ('Ảnh có độ phân giải quá thấp', 'Kích thước ảnh chưa đủ để kiểm tra giấy tờ.',
                       ['Dùng camera chính, không dùng ảnh thu nhỏ hoặc zoom số.', 'Mở lại camera và chụp ở độ phân giải cao hơn.']),
    'suspected_blur': ('Mô hình nghi ngờ ảnh mờ', 'Chưa đủ bằng chứng để kết luận ảnh bị mờ; hệ thống tiếp tục kiểm tra giấy tờ.', []),
    'suspected_dark': ('Mô hình nghi ngờ thiếu sáng', 'Chưa đủ bằng chứng để kết luận ảnh quá tối; hệ thống tiếp tục kiểm tra giấy tờ.', []),
    'suspected_cropped': ('Mô hình nghi ngờ thiếu góc', 'Dự đoán này chưa được xác nhận. Hệ thống sẽ kiểm tra đường biên giấy tờ.', []),
    'suspected_distorted': ('Mô hình nghi ngờ lệch phối cảnh', 'Hệ thống sẽ thử nắn phối cảnh trước khi quyết định cần chụp lại.', []),
    'quality_uncertain': ('Chất lượng chưa chắc chắn', 'Mô hình chưa đủ chắc chắn; hệ thống tiếp tục kiểm tra biên giấy tờ và OCR.', []),
    'document_corners_not_found': ('Chưa xác định được đủ biên giấy tờ', 'Chưa thể nắn ảnh; không thể khẳng định giấy tờ bị cắt góc chỉ từ kết quả này.',
        ['Lùi camera một chút để cả bốn góc đều nằm trong ảnh, có khoảng trống quanh thẻ.', 'Đặt giấy tờ trên nền tương phản, không để ngón tay che mép và giữ camera song song mặt giấy tờ.']),
    'id_face_unavailable': ('Chưa tách được ảnh chân dung để đối chiếu', 'Bộ tìm khuôn mặt chưa xác định được vùng chân dung đủ tin cậy. Điều này không có nghĩa giấy tờ không hợp lệ hoặc không có trong dataset; cũng có thể do giới hạn của mô hình.',
        ['Chụp mặt giấy tờ có ảnh chân dung, tránh để ánh sáng phản chiếu lên vùng ảnh.', 'Đưa giấy tờ gần hơn, giữ toàn bộ thẻ trong khung và không để người khác xuất hiện cạnh thẻ.']),
    'id_face_ambiguous': ('Chưa xác định được chân dung chính', 'Phát hiện nhiều vùng khuôn mặt nhưng chưa xác nhận được chúng là cùng một người. Thông tin OCR vẫn có thể xem và sửa.',
        ['Chỉ đặt một giấy tờ trong ảnh, không để người khác xuất hiện cạnh thẻ.', 'Chụp rõ ảnh chân dung chính và vùng ảnh bảo an, tránh lóa. Nếu vẫn lỗi, mô hình có thể chưa xử lý tốt mẫu giấy tờ này.']),
    'ocr_unreadable': ('Chưa đọc được chữ trên giấy tờ', 'OCR không đọc được dòng nào đủ tin cậy; chưa thể điền thông tin.',
        ['Đưa giấy tờ gần hơn để chữ đủ lớn; giữ máy yên và chờ lấy nét.', 'Tránh lóa trên vùng chữ và dùng ánh sáng đều. Nếu vẫn lỗi, OCR hiện có có thể chưa hỗ trợ tốt ngôn ngữ giấy tờ.']),
    'selfie_face_unavailable': ('Chưa nhận diện được một khuôn mặt rõ nét', 'Cần đúng một khuôn mặt trong ảnh selfie.',
        ['Nhìn thẳng vào camera, đưa toàn bộ khuôn mặt vào khung.', 'Bỏ vật che mặt, tránh ngược sáng và đảm bảo không có người thứ hai trong ảnh.']),
    'face_mismatch': ('Khuôn mặt chưa khớp', 'Điểm đối chiếu dưới ngưỡng mô hình; kết quả này không khẳng định hai người khác nhau.',
        ['Dùng giấy tờ của người đang chụp selfie, nhìn thẳng và chiếu sáng đều khuôn mặt.', 'Bắt đầu lại để chụp ảnh chân dung giấy tờ và selfie rõ hơn.']),
    'selfie_identity_changed': ('Khuôn mặt giữa các bước chưa nhất quán', 'Ảnh chân dung cuối và các mẫu trong thử thách có điểm tương đồng dưới ngưỡng. Hệ thống chưa thể xác nhận chúng thuộc cùng một người.',
        ['Giữ cùng một người trong toàn bộ lượt kiểm tra và ảnh chụp cuối.', 'Giữ ánh sáng đều, nhìn thẳng khi chụp ảnh cuối và bắt đầu lại thử thách.']),
}


def issue(code, *, suspected=False):
    title, detail, instructions = MESSAGES[code]
    return dict(code=code, title=title, detail=detail, instructions=instructions,
                severity='warning' if suspected else 'error',
                certainty='suspected' if suspected else 'observed_processing_failure')


def retake(reason, quality=None):
    issues = quality.get('issues', []) if reason == 'quality_rejected' and quality else [issue(reason)]
    return dict(status='retake', reason=reason, quality=quality, issues=issues,
                message='Vui lòng điều chỉnh theo hướng dẫn rồi chụp lại.')
