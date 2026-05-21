"""
FAQ Seed Script - Direct SQL
Run: python seed_faq_data.py
"""
import sys
import os
import uuid
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.db.session import SessionLocal, engine


# Sample FAQ data
FAQ_DATA = [
    # Quản lý tài khoản
    {
        "title": "Làm sao đổi mật khẩu?",
        "content": """Để đổi mật khẩu, bạn cần thực hiện các bước sau:

1. Đăng nhập vào tài khoản của bạn
2. Di chuyển đến phần "Cài đặt" trong menu profile
3. Chọn "Bảo mật" → "Đổi mật khẩu"
4. Nhập mật khẩu hiện tại và mật khẩu mới
5. Xác nhận mật khẩu mới một lần nữa
6. Nhấn "Lưu" để cập nhật

Lưu ý: Mật khẩu mới phải có ít nhất 8 ký tự, bao gồm chữ hoa, chữ thường và số.""",
        "category": "Quản lý tài khoản",
        "view_count": 1234,
        "is_published": True,
    },
    {
        "title": "Tôi quên mật khẩu thì làm sao?",
        "content": """Nếu bạn quên mật khẩu, hãy làm theo các bước:

1. Tại trang đăng nhập, nhấn vào "Quên mật khẩu"
2. Nhập email đã đăng ký với tài khoản
3. Hệ thống sẽ gửi một email chứa link để reset mật khẩu
4. Nhấn vào link trong email và làm theo hướng dẫn
5. Đặt mật khẩu mới cho tài khoản

Nếu không nhận được email, hãy kiểm tra thư mục Spam hoặc liên hệ hotline 1800 0000.""",
        "category": "Quản lý tài khoản",
        "view_count": 2156,
        "is_published": True,
    },
    {
        "title": "Tôi có thể cập nhật thông tin cá nhân không?",
        "content": """Có, bạn có thể cập nhật thông tin cá nhân bất cứ lúc nào:

1. Đăng nhập vào tài khoản
2. Di chuyển đến "Thông tin cá nhân" trong phần profile
3. Cập nhật các thông tin sau:
   - Họ và tên
   - Số điện thoại
   - Email (cần xác thực nếu thay đổi)
   - Địa chỉ

<b>Lưu ý:</b>
- Email không thể thay đổi nếu đã được xác minh
- Số điện thoại cần xác thực qua OTP khi thay đổi lần đầu
- Các thay đổi sẽ có hiệu lực ngay lập tức

Nếu cần thay đổi email đã xác minh, vui lòng liên hệ hotline.""",
        "category": "Quản lý tài khoản",
        "view_count": 543,
        "is_published": True,
    },
    {
        "title": "Làm sao để xác thực email mới?",
        "content": """Sau khi đăng ký hoặc thay đổi email mới, bạn cần xác thực:

1. Kiểm tra hộp thư email đã đăng ký
2. Tìm email từ support@obsidian.vn với tiêu đề "Xác thực email của bạn"
3. Nhấn vào link trong email (link có hiệu lực trong 24 giờ)
4. Trang xác thực sẽ mở ra, xác nhận thành công

<b>Nếu không nhận được email:</b>
- Kiểm tra thư mục Spam/Junk
- Thử gửi lại email xác thực trong phần Cài đặt
- Email xác thực có thể mất 2-5 phút để đến

Liên hệ hotline 1800 0000 nếu vấn đề vẫn tiếp tục.""",
        "category": "Quản lý tài khoản",
        "view_count": 892,
        "is_published": True,
    },
    {
        "title": "Cách đăng ký tài khoản mới?",
        "content": """Để đăng ký tài khoản mới, bạn thực hiện:

1. Truy cập trang đăng ký tại obsidian.vn/dang-ky
2. Điền thông tin bắt buộc:
   - Họ và tên đầy đủ
   - Email (sẽ được dùng để đăng nhập)
   - Số điện thoại
   - Mật khẩu (tối thiểu 8 ký tự)
3. Đồng ý với Điều khoản sử dụng và Chính sách bảo mật
4. Nhấn "Đăng ký"

Sau khi đăng ký thành công, bạn sẽ nhận được email xác thực. Vui lòng xác thực email trong vòng 24 giờ.

<b>Đã có tài khoản?</b> Nếu công ty của bạn đã có tài khoản, hãy liên hệ quản trị viên để được cấp quyền truy cập.""",
        "category": "Quản lý tài khoản",
        "view_count": 1567,
        "is_published": True,
    },
    {
        "title": "Tài khoản của tôi có bị khóa không và làm sao mở lại?",
        "content": """Tài khoản có thể bị khóa vì các lý do:

<b>Tự động khóa:</b>
- Nhập sai mật khẩu 5 lần liên tiếp
- Tài khoản không hoạt động trong 90 ngày

<b>Khóa thủ công:</b>
- Vi phạm điều khoản sử dụng
- Yêu cầu từ quản trị viên công ty

<b>Cách mở khóa:</b>
1. Truy cập trang đăng nhập
2. Nhấn "Quên mật khẩu" để reset (nếu bị khóa vì sai mật khẩu)
3. Hoặc liên hệ hotline 1800 0000 để được hỗ trợ mở khóa

<b>Lưu ý:</b> Hotline làm việc Thứ 2 - Thứ 6, 08:00 - 18:00.""",
        "category": "Quản lý tài khoản",
        "view_count": 654,
        "is_published": True,
    },

    # Thanh toán
    {
        "title": "Cách thanh toán qua chuyển khoản ngân hàng?",
        "content": """Bạn có thể thanh toán qua chuyển khoản ngân hàng như sau:

<b>Thông tin tài khoản:</b>
- Vietcombank: 1234567890 - Công ty TNHH Obsidian
- VietinBank: 0987654321 - Công ty TNHH Obsidian
- MB Bank: 8888888888 - Công ty TNHH Obsidian

<b>Các bước thực hiện:</b>
1. Chuyển khoản với số tiền tương ứng với dịch vụ bạn đã đăng ký
2. Ghi chú nội dung: [Mã tài khoản] - [Tên dịch vụ]
3. Sau khi chuyển, gửi slip qua email: payments@obsidian.vn
4. Chúng tôi sẽ xác nhận trong vòng 24 giờ làm việc

Thanh toán sẽ được kích hoạt sau khi xác nhận thành công. Hóa đơn sẽ được gửi qua email đã đăng ký.""",
        "category": "Thanh toán",
        "view_count": 856,
        "is_published": True,
    },
    {
        "title": "Làm sao để hủy đăng ký dịch vụ?",
        "content": """Để hủy đăng ký dịch vụ, bạn có thể:

1. Đăng nhập vào tài khoản
2. Di chuyển đến "Quản lý dịch vụ" trong phần cài đặt
3. Chọn dịch vụ muốn hủy
4. Nhấn "Hủy đăng ký" và xác nhận

<b>Lưu ý quan trọng:</b>
- Việc hủy sẽ có hiệu lực vào cuối kỳ thanh toán hiện tại
- Không hoàn tiền cho thời gian còn lại trong kỳ
- Mọi dữ liệu sẽ được lưu trữ trong 30 ngày trước khi xóa vĩnh viễn
- Bạn vẫn có thể truy cập dữ liệu trong thời gian lưu trữ

Nếu cần hỗ trợ thêm, vui lòng liên hệ hotline 1800 0000.""",
        "category": "Thanh toán",
        "view_count": 432,
        "is_published": True,
    },
    {
        "title": "Tôi có được hoàn tiền không?",
        "content": """Chính sách hoàn tiền của chúng tôi:

<b>Hoàn tiền đầy đủ (trong 7 ngày đầu):</b>
- Nếu dịch vụ không hoạt động đúng như mô tả
- Nếu bạn hủy trước khi kỳ thanh toán bắt đầu

<b>Hoàn tiền theo tỷ lệ:</b>
- Hoàn tiền theo tỷ lệ ngày sử dụng còn lại (không áp dụng cho các gói đã giảm giá)

<b>Không hoàn tiền:</b>
- Sau 7 ngày sử dụng dịch vụ
- Đối với các gói khuyến mãi đặc biệt
- Phí setup ban đầu (nếu có)

<b>Cách yêu cầu hoàn tiền:</b>
1. Gửi yêu cầu qua email: billing@obsidian.vn
2. Hoặc gọi hotline 1800 0000
3. Yêu cầu sẽ được xử lý trong 3-5 ngày làm việc

Điều khoản chi tiết xem tại: obsidian.vn/chinh-sach-thanh-toan""",
        "category": "Thanh toán",
        "view_count": 387,
        "is_published": True,
    },
    {
        "title": "Chu kỳ thanh toán và hóa đơn như thế nào?",
        "content": """Thông tin chu kỳ thanh toán:

<b>Các gói dịch vụ:</b>
- <b>Gói Tháng:</b> Thanh toán hàng tháng, gia hạn tự động
- <b>Gói Năm:</b> Thanh toán hàng năm, tiết kiệm 20%

<b>Ngày thanh toán:</b>
- Ngày thanh toán cố định theo ngày đăng ký ban đầu
- Nhắc nhở sẽ được gửi 7 ngày trước khi đến hạn

<b>Hóa đơn:</b>
- Hóa đơn sẽ được gửi qua email trong vòng 24 giờ sau khi thanh toán
- Bạn có thể tải hóa đơn tại phần "Quản lý thanh toán"
- Hóa đơn điện tử có giá trị pháp lý

<b>Phương thức thanh toán:</b>
- Chuyển khoản ngân hàng
- Thẻ tín dụng/ghi nợ (sắp ra mắt)
- Ví điện tử (sắp ra mắt)""",
        "category": "Thanh toán",
        "view_count": 234,
        "is_published": True,
    },
    {
        "title": "Làm sao để nâng cấp hoặc hạ cấp gói dịch vụ?",
        "content": """Để thay đổi gói dịch vụ:

<b>Nâng cấp gói:</b>
1. Đăng nhập vào tài khoản
2. Di chuyển đến "Quản lý dịch vụ"
3. Chọn "Thay đổi gói dịch vụ"
4. Chọn gói mới phù hợp
5. Xác nhận thanh toán (phí chênh lệch sẽ được tính theo tỷ lệ)

<b>Hạ cấp gói:</b>
1. Đăng nhập vào tài khoản
2. Di chuyển đến "Quản lý dịch vụ"
3. Chọn "Hạ cấp gói"
4. Chọn gói mới và xác nhận

<b>Lưu ý:</b>
- Nâng cấp có hiệu lực ngay lập tức
- Hạ cấp có hiệu lực vào cuối kỳ thanh toán hiện tại
- Các tính năng đặc biệt của gói cao cấp sẽ bị vô hiệu hóa khi hạ cấp

Liên hệ hotline 1800 0000 nếu cần hỗ trợ.""",
        "category": "Thanh toán",
        "view_count": 298,
        "is_published": True,
    },

    # Kỹ thuật
    {
        "title": "Lỗi kết nối khi đăng nhập?",
        "content": """Nếu bạn gặp lỗi kết nối khi đăng nhập, hãy thử:

<b>Các bước xử lý:</b>
1. Kiểm tra kết nối internet của bạn
2. Thử đăng nhập lại sau 30 giây
3. Xóa cache trình duyệt: Settings → Privacy → Clear browsing data
4. Thử sử dụng trình duyệt khác (Chrome, Firefox, Edge)

<b>Nếu vẫn không được:</b>
- Kiểm tra xem tài khoản có bị khóa không
- Đảm bảo bạn đang sử dụng email đúng đã đăng ký
- Thử đăng nhập ở chế độ ẩn danh/private window

Chúng tôi làm việc 24/7 để hỗ trợ bạn. Nếu vấn đề vẫn tiếp tục, vui lòng gửi ticket với mô tả chi tiết lỗi.""",
        "category": "Kỹ thuật",
        "view_count": 423,
        "is_published": True,
    },
    {
        "title": "Trang web không tải được hoặc bị treo",
        "content": """Nếu trang web không tải được hoặc bị treo:

<b>Các bước khắc phục:</b>
1. <b>F5 hoặc Ctrl+R</b> - Tải lại trang
2. <b>Ctrl+Shift+R</b> - Tải lại không dùng cache
3. Xóa cache trình duyệt (Ctrl+Shift+Delete)
4. Kiểm tra đường truyền internet
5. Thử sử dụng mạng khác (VD: điện thoại di động)

<b>Kiểm tra trạng thái hệ thống:</b>
- Truy cập obsidian.vn/status để xem trạng thái hệ thống
- Theo dõi các bảo trì định kỳ

<b>Nếu vấn đề vẫn tiếp tục:</b>
- Gửi ticket kèm ảnh chụp màn hình lỗi
- Note thời gian xảy ra lỗi
- Thông tin trình duyệt và hệ điều hành đang sử dụng

Chúng tôi sẽ phản hồi trong vòng 4 giờ làm việc.""",
        "category": "Kỹ thuật",
        "view_count": 312,
        "is_published": True,
    },
    {
        "title": "Tôi không nhận được email thông báo",
        "content": """Nếu không nhận được email thông báo:

<b>Kiểm tra các bước sau:</b>
1. Kiểm tra thư mục Spam/Junk/Quảng cáo
2. Thêm support@obsidian.vn vào danh sách người gửi đáng tin cậy
3. Kiểm tra cài đặt thông báo trong profile
4. Xác nhận email đã được xác thực

<b>Các email nên nhận được:</b>
- Email xác thực khi đăng ký
- Thông báo tạo ticket thành công
- Cập nhật trạng thái ticket
- Nhắc nhở thanh toán sắp đến hạn
- Thông báo phản hồi từ nhân viên hỗ trợ

<b>Nếu vẫn không nhận được:</b>
- Kiểm tra bộ lọc email công ty (nếu dùng email doanh nghiệp)
- Liên hệ hotline 1800 0000 để được hỗ trợ cập nhật email

<b>Thay đổi email nhận thông báo:</b>
Vào Cài đặt → Thông báo → Cập nhật email nhận thông báo""",
        "category": "Kỹ thuật",
        "view_count": 567,
        "is_published": True,
    },
    {
        "title": "File đính kèm không tải được",
        "content": """Nếu file đính kèm không tải được:

<b>Kiểm tra định dạng file:</b>
- Các định dạng được hỗ trợ: PDF, DOC, DOCX, XLS, XLSX, PNG, JPG, JPEG, GIF
- Kích thước tối đa: 10MB mỗi file

<b>Giải pháp:</b>
1. Đảm bảo kết nối internet ổn định
2. Thử tải lại file (F5)
3. Xóa cache trình duyệt trước khi tải
4. Thử sử dụng trình duyệt khác

<b>Nếu file vẫn không tải được:</b>
- File có thể đã bị xóa hoặc hết hạn (sau 30 ngày)
- Gửi ticket yêu cầu gửi lại file

<b>Lưu ý:</b>
- Không tải được file có thể do firewall công ty chặn
- Thử tải ở nhà hoặc kết nối di động""",
        "category": "Kỹ thuật",
        "view_count": 198,
        "is_published": True,
    },
    {
        "title": "Lỗi 500 Internal Server Error",
        "content": """Lỗi 500 là lỗi từ phía máy chủ, không phải do bạn gây ra.

<b>Các bước xử lý:</b>
1. Đợi 1-2 phút và thử tải lại trang
2. Kiểm tra trạng thái hệ thống tại obsidian.vn/status
3. Nếu có bảo trì đã thông báo, vui lòng đợi đến khi hoàn tất

<b>Khi nào liên hệ hỗ trợ:</b>
- Lỗi kéo dài hơn 30 phút
- Bạn đang thực hiện thao tác quan trọng (gửi ticket, thanh toán)
- Gặp lỗi nhiều lần trong ngày

<b>Thông tin cần cung cấp khi gửi ticket:</b>
- Mã lỗi hiển thị (nếu có)
- Thời gian xảy ra lỗi
- Các bước để tái hiện lỗi
- Ảnh chụp màn hình lỗi

Chúng tôi xin lỗi về sự bất tiện này!""",
        "category": "Kỹ thuật",
        "view_count": 276,
        "is_published": True,
    },
    {
        "title": "App di động bị lag hoặc crash",
        "content": """Nếu app di động bị lag hoặc crash:

<b>Đối với iOS:</b>
1. Cập nhật app lên phiên bản mới nhất từ App Store
2. Khởi động lại iPhone/iPad
3. Xóa app và cài đặt lại
4. Kiểm tra bộ nhớ trong: Cài đặt → Bộ nhớ → Dung lượng

<b>Đối với Android:</b>
1. Cập nhật app từ Google Play
2. Khởi động lại thiết bị
3. Xóa cache app: Cài đặt → Ứng dụng → Obsidian → Xóa cache
4. Gỡ cài đặt và cài lại app

<b>Yêu cầu hệ thống tối thiểu:</b>
- iOS 14.0 trở lên
- Android 8.0 (API 26) trở lên

<b>Nếu vấn đề vẫn tiếp tục:</b>
- Gửi feedback từ trong app (Cài đặt → Phản hồi)
- Bao gồm mô tả thiết bị và phiên bản hệ điều hành""",
        "category": "Kỹ thuật",
        "view_count": 145,
        "is_published": True,
    },

    # Hướng dẫn sử dụng
    {
        "title": "Làm sao để tạo ticket hỗ trợ?",
        "content": """Để tạo ticket hỗ trợ, bạn cần:

1. <b>Đăng nhập</b> vào tài khoản của bạn
2. Di chuyển đến phần "Tạo yêu cầu hỗ trợ"
3. Điền đầy đủ thông tin:
   - Chủ đề: Mô tả ngắn gọn vấn đề của bạn
   - Mô tả chi tiết: Nêu rõ vấn đề bạn đang gặp
   - Độ ưu tiên: Thấp / Trung bình / Cao / Khẩn cấp
   - Danh mục: Chọn danh mục phù hợp với vấn đề
4. Nhấn "Gửi yêu cầu"

Sau khi gửi, bạn sẽ nhận được email xác nhận và mã ticket để theo dõi. Thời gian phản hồi tùy thuộc vào độ ưu tiên đã chọn.

<b>Mẹo:</b> Cung cấp càng nhiều thông tin chi tiết càng tốt để nhân viên hỗ trợ nhanh chóng giải quyết vấn đề.""",
        "category": "Hướng dẫn sử dụng",
        "view_count": 987,
        "is_published": True,
    },
    {
        "title": "Cách theo dõi trạng thái ticket?",
        "content": """Để theo dõi trạng thái ticket của bạn:

<b>Xem danh sách ticket:</b>
1. Đăng nhập vào tài khoản
2. Di chuyển đến "Lịch sử ticket" hoặc "Ticket của tôi"
3. Bạn sẽ thấy danh sách tất cả ticket đã tạo

<b>Các trạng thái ticket:</b>
- <b>Đã gửi:</b> Ticket đã được gửi thành công
- <b>Đang xử lý:</b> Nhân viên đang xem xét
- <b>Đã phản hồi:</b> Có phản hồi mới từ nhân viên
- <b>Đã giải quyết:</b> Vấn đề đã được xử lý xong
- <b>Đóng:</b> Ticket đã được đóng lại

<b>Nhận thông báo:</b>
- Bật thông báo email trong Cài đặt → Thông báo
- Bật thông báo app (nếu dùng app di động)

<b>Theo dõi nhanh:</b>
- Mỗi ticket có một mã riêng (VD: HD-2024-00001)
- Bạn có thể dùng mã này để tìm kiếm nhanh""",
        "category": "Hướng dẫn sử dụng",
        "view_count": 654,
        "is_published": True,
    },
    {
        "title": "Làm sao để đánh giá chất lượng hỗ trợ?",
        "content": """Sau khi ticket được giải quyết, bạn có thể đánh giá:

<b>Cách đánh giá:</b>
1. Nhận email thông báo "Ticket đã được giải quyết"
2. Click vào link đánh giá trong email
3. Hoặc đăng nhập → Lịch sử ticket → Chọn ticket → Đánh giá

<b>Tiêu chí đánh giá:</b>
- Chất lượng phản hồi (1-5 sao)
- Thời gian xử lý (1-5 sao)
- Thái độ nhân viên (1-5 sao)
- Mức độ hài lòng tổng thể (1-5 sao)
- Bình luận thêm (tùy chọn)

<b>Tại sao đánh giá quan trọng:</b>
- Giúp chúng tôi cải thiện dịch vụ
- Nhân viên được đánh giá dựa trên phản hồi của bạn
- Đánh giá 5 sao giúp chúng tôi phục vụ tốt hơn

<b>Đánh giá ẩn danh:</b>
- Phản hồi của bạn có thể được ẩn danh
- Thông tin cá nhân sẽ không bị tiết lộ""",
        "category": "Hướng dẫn sử dụng",
        "view_count": 234,
        "is_published": True,
    },
    {
        "title": "Tôi có thể tạo ticket thay cho đồng nghiệp không?",
        "content": """Có, bạn có thể tạo ticket thay cho đồng nghiệp:

<b>Với quyền Quản trị viên:</b>
1. Đăng nhập vào tài khoản quản trị
2. Di chuyển đến "Quản lý ticket"
3. Chọn "Tạo ticket mới"
4. Chọn người dùng thay mặt từ danh sách

<b>Với quyền Nhân viên:</b>
1. Tạo ticket mới
2. Ở phần "Người yêu cầu", chọn đồng nghiệp từ danh sách
3. Điền thông tin và gửi

<b>Lưu ý:</b>
- Bạn cần có quyền thích hợp để tạo ticket thay
- Ticket sẽ hiển thị tên người tạo và người yêu cầu
- Đồng nghiệp sẽ nhận email thông báo
- Theo mặc định, chỉ người tạo và người được chỉ định mới thấy ticket

Liên hệ quản trị viên công ty nếu bạn cần được cấp quyền này.""",
        "category": "Hướng dẫn sử dụng",
        "view_count": 187,
        "is_published": True,
    },
    {
        "title": "Cách sử dụng template ticket?",
        "content": """Sử dụng template giúp tạo ticket nhanh hơn:

<b>Chọn template:</b>
1. Khi tạo ticket mới, click "Chọn template"
2. Danh sách template sẽ hiển thị
3. Chọn template phù hợp với vấn đề của bạn

<b>Các template có sẵn:</b>
- <b>Lỗi kỹ thuật:</b> Báo cáo lỗi hệ thống hoặc ứng dụng
- <b>Yêu cầu tính năng mới:</b> Đề xuất cải tiến hoặc tính năng mới
- <b>Hỗ trợ thanh toán:</b> Các vấn đề liên quan đến thanh toán
- <b>Tư vấn sản phẩm:</b> Hỏi về tính năng và cách sử dụng
- <b>Bảo mật:</b> Báo cáo vấn đề bảo mật nghiêm trọng

<b>Tùy chỉnh template:</b>
- Quản trị viên có thể tạo template tùy chỉnh cho công ty
- Template tùy chỉnh sẽ hiển thị riêng trong danh sách

Template giúp tiết kiệm thời gian và đảm bảo thông tin đầy đủ.""",
        "category": "Hướng dẫn sử dụng",
        "view_count": 156,
        "is_published": True,
    },
    {
        "title": "Cách phân loại độ ưu tiên ticket?",
        "content": """Hướng dẫn chọn độ ưu tiên phù hợp:

<b>🟢 Thấp (Low)</b>
- Câu hỏi chung, không gấp
- Thời gian phản hồi: 24-72 giờ
- Ví dụ: Hướng dẫn sử dụng tính năng cơ bản

<b>🟡 Trung bình (Medium)</b>
- Vấn đề ảnh hưởng đến công việc nhưng có thể tạm chờ
- Thời gian phản hồi: 8-24 giờ
- Ví dụ: Lỗi một tính năng không quan trọng

<b>🟠 Cao (High)</b>
- Vấn đề nghiêm trọng, ảnh hưởng nhiều người dùng
- Thời gian phản hồi: 4-8 giờ
- Ví dụ: Không thể đăng nhập, lỗi thanh toán

<b>🔴 Khẩn cấp (Critical)</b>
- Hệ thống ngừng hoạt động hoàn toàn
- Thời gian phản hồi: 1-4 giờ
- Ví dụ: Không thể truy cập dữ liệu, breach bảo mật

<b>Lưu ý quan trọng:</b>
- Không lạm dụng độ Khẩn cấp
- Độ ưu tiên được duyệt bởi nhân viên hỗ trợ
- Sai độ ưu tiên có thể bị điều chỉnh""",
        "category": "Hướng dẫn sử dụng",
        "view_count": 298,
        "is_published": True,
    },

    # Chính sách
    {
        "title": "Chính sách SLA là gì và hoạt động như thế nào?",
        "content": """<b>SLA (Service Level Agreement)</b> là cam kết về thời gian xử lý của chúng tôi:

<b>Các mức độ ưu tiên:</b>

🔴 <b>Khẩn cấp (Critical)</b>
- Thời gian phản hồi: 1 giờ
- Thời gian giải quyết: 4 giờ
- Hỗ trợ: 24/7

🟠 <b>Cao (High)</b>
- Thời gian phản hồi: 4 giờ
- Thời gian giải quyết: 24 giờ
- Hỗ trợ: Thứ 2 - Thứ 6, 8:00 - 18:00

🟡 <b>Trung bình (Medium)</b>
- Thời gian phản hồi: 8 giờ
- Thời gian giải quyết: 48 giờ
- Hỗ trợ: Thứ 2 - Thứ 6, 8:00 - 18:00

🟢 <b>Thấp (Low)</b>
- Thời gian phản hồi: 24 giờ
- Thời gian giải quyết: 72 giờ
- Hỗ trợ: Thứ 2 - Thứ 6, 8:00 - 18:00

<b>Lưu ý:</b>
- SLA được tính trong giờ làm việc và không tính ngày nghỉ, ngày lễ
- Thời gian có thể kéo dài nếu cần thông tin bổ sung từ bạn
- SLA không áp dụng cho các vấn đề nằm ngoài tầm kiểm soát của chúng tôi""",
        "category": "Chính sách",
        "view_count": 654,
        "is_published": True,
    },
    {
        "title": "Chính sách bảo mật dữ liệu",
        "content": """Chúng tôi cam kết bảo vệ dữ liệu của bạn:

<b>Cam kết của chúng tôi:</b>
- Mã hóa dữ liệu khi truyền tải và lưu trữ (TLS 1.3)
- Lưu trữ dữ liệu tại trung tâm dữ liệu đạt chuẩn ISO 27001
- Giới hạn quyền truy cập chỉ cho nhân viên được ủy quyền
- Thực hiện audit bảo mật định kỳ

<b>Quyền của bạn:</b>
- Quyền truy cập dữ liệu cá nhân
- Quyền yêu cầu xóa dữ liệu
- Quyền xuất dữ liệu ra file
- Quyền phản đối việc xử lý dữ liệu

<b>Thời gian lưu trữ:</b>
- Dữ liệu tài khoản: Lưu trữ khi tài khoản hoạt động + 30 ngày sau khi xóa
- Dữ liệu ticket: 5 năm theo quy định pháp luật
- Log truy cập: 90 ngày

<b>Liên hệ:</b>
- Email bảo mật: security@obsidian.vn
- Báo cáo lỗ hổng bảo mật: security@obsidian.vn

Xem chi tiết tại: obsidian.vn/chinh-sach-bao-mat""",
        "category": "Chính sách",
        "view_count": 423,
        "is_published": True,
    },
    {
        "title": "Điều khoản sử dụng dịch vụ",
        "content": """Điều khoản sử dụng dịch vụ Obsidian HelpDesk:

<b>1. Chấp nhận điều khoản</b>
Bằng việc sử dụng dịch vụ, bạn đồng ý tuân thủ các điều khoản này.

<b>2. Tài khoản người dùng</b>
- Bạn chịu trách nhiệm bảo mật thông tin đăng nhập
- Bạn phải từ 18 tuổi trở lên để sử dụng dịch vụ
- Một người dùng chỉ được tạo một tài khoản

<b>3. Sử dụng hợp pháp</b>
- Không sử dụng dịch vụ cho mục đích bất hợp pháp
- Không cố gắng truy cập trái phép vào hệ thống
- Không spam hoặc gửi yêu cầu không hợp lệ

<b>4. Giới hạn trách nhiệm</b>
- Chúng tôi không chịu trách nhiệm về thiệt hại gián tiếp
- Thời gian downtime được thông báo trước nếu có bảo trì

<b>5. Thay đổi điều khoản</b>
- Chúng tôi có quyền thay đổi điều khoản với thông báo trước 30 ngày
- Tiếp tục sử dụng sau thay đổi đồng nghĩa chấp nhận điều khoản mới

Xem đầy đủ tại: obsidian.vn/dieu-khoan-su-dung""",
        "category": "Chính sách",
        "view_count": 312,
        "is_published": True,
    },
    {
        "title": "Chính sách riêng tư",
        "content": """Chính sách riêng tư của Obsidian HelpDesk:

<b>Thông tin chúng tôi thu thập:</b>
- Thông tin đăng ký: tên, email, số điện thoại
- Thông tin sử dụng: log truy cập, ticket đã tạo
- Thiết bị: IP, trình duyệt, hệ điều hành

<b>Mục đích sử dụng:</b>
- Cung cấp và cải thiện dịch vụ
- Gửi thông báo liên quan đến tài khoản
- Hỗ trợ khách hàng
- Bảo mật và ngăn chặn lạm dụng

<b>Chia sẻ thông tin:</b>
- Không bán hoặc chia sẻ thông tin cá nhân cho bên thứ ba
- Chia sẻ chỉ khi được yêu cầu bởi pháp luật
- Nhà cung cấp dịch vụ (hosting, email) có thể truy cập theo hợp đồng

<b>Cookie:</b>
- Sử dụng cookie cần thiết cho chức năng đăng nhập
- Cookie phân tích ẩn danh để cải thiện dịch vụ
- Bạn có thể tắt cookie trong trình duyệt nhưng một số tính năng có thể bị ảnh hưởng

Xem chi tiết: obsidian.vn/chinh-sach-rieng-tu""",
        "category": "Chính sách",
        "view_count": 287,
        "is_published": True,
    },
    {
        "title": " Cam kết hỗ trợ 24/7",
        "content": """Dịch vụ hỗ trợ của chúng tôi:

<b>Kênh hỗ trợ:</b>
- <b>Hotline:</b> 1800 0000 (miễn phí cuộc gọi)
- <b>Email:</b> support@obsidian.vn
- <b>Tickets:</b> qua hệ thống trực tuyến
- <b>Chat:</b> cửa sổ chat trên website (08:00 - 22:00)

<b>Giờ làm việc:</b>
- <b>Hỗ trợ cơ bản:</b> 24/7 cho tất cả khách hàng
- <b>Hỗ trợ kỹ thuật chuyên sâu:</b> Thứ 2 - Thứ 6, 8:00 - 18:00
- <b>Hỗ trợ tại chỗ:</b> Theo thỏa thuận với khách hàng gói Enterprise

<b>Đội ngũ hỗ trợ:</b>
- Đội ngũ Tier 1: Xử lý các câu hỏi và vấn đề thông thường
- Đội ngũ Tier 2: Xử lý các vấn đề kỹ thuật phức tạp
- Đội ngũ chuyên gia: Hỗ trợ các vấn đề nghiêm trọng

<b>Ngôn ngữ hỗ trợ:</b>
- Tiếng Việt (mặc định)
- Tiếng Anh

<b>cam kết của chúng tôi:</b>
- Phản hồi trong vòng 1 giờ cho các vấn đề Khẩn cấp
- Giải quyết 90% ticket trong thời gian SLA cam kết""",
        "category": "Chính sách",
        "view_count": 456,
        "is_published": True,
    },

    # Bắt đầu sử dụng
    {
        "title": "Làm sao để bắt đầu sử dụng Obsidian HelpDesk?",
        "content": """Hướng dẫn bắt đầu nhanh:

<b>Bước 1: Đăng ký tài khoản</b>
1. Truy cập obsidian.vn/dang-ky
2. Điền thông tin và xác thực email
3. Đăng nhập lần đầu

<b>Bước 2: Làm quen với giao diện</b>
1. Xem tour giới thiệu khi đăng nhập lần đầu
2. Tham khảo FAQ này để hiểu các tính năng
3. Liên hệ hotline 1800 0000 nếu cần hỗ trợ

<b>Bước 3: Tạo ticket đầu tiên</b>
1. Click nút "Tạo yêu cầu hỗ trợ"
2. Chọn danh mục phù hợp
3. Mô tả vấn đề của bạn chi tiết nhất có thể
4. Gửi và chờ phản hồi

<b>Bước 4: Theo dõi ticket</b>
1. Vào "Lịch sử ticket" để xem tất cả ticket đã tạo
2. Bật thông báo email để cập nhật kịp thời
3. Đánh giá chất lượng hỗ trợ sau khi ticket được giải quyết

<b>Tài liệu hướng dẫn:</b>
- Video hướng dẫn: obsidian.vn/huong-dan
- API documentation: obsidian.vn/docs/api
- Knowledge base: obsidian.vn/kb""",
        "category": "Bắt đầu",
        "view_count": 876,
        "is_published": True,
    },
    {
        "title": "Tính năng nổi bật của Obsidian HelpDesk",
        "content": """Các tính năng chính của Obsidian HelpDesk:

<b>🎫 Quản lý Ticket</b>
- Tạo ticket nhanh chóng với template có sẵn
- Theo dõi trạng thái real-time
- Đính kèm file và hình ảnh
- Phân loại theo danh mục và độ ưu tiên

<b>⚡ Tự động hóa</b>
- Phân bổ ticket tự động theo danh mục
- Cảnh báo khi SLA sắp hết hạn
- Email tự động khi có cập nhật
- Dashboard theo dõi hiệu suất

<b>📊 Báo cáo & Phân tích</b>
- Báo cáo thời gian phản hồi
- Phân tích xu hướng ticket
- Đánh giá chất lượng dịch vụ
- Xuất báo cáo theo định dạng

<b>🔒 Bảo mật</b>
- Mã hóa dữ liệu đầu cuối
- Phân quyền người dùng chi tiết
- Audit log theo dõi hoạt động
- Backup tự động hàng ngày

<b>🔗 Tích hợp</b>
- API RESTful đầy đủ
- Webhook cho các sự kiện
- Tích hợp với email, Slack, Jira
- Import dữ liệu từ các hệ thống khác

<b>📱 Đa nền tảng</b>
- Giao diện web responsive
- Ứng dụng di động iOS & Android
- Hỗ trợ đa ngôn ngữ""",
        "category": "Bắt đầu",
        "view_count": 567,
        "is_published": True,
    },
    {
        "title": "So sánh các gói dịch vụ",
        "content": """Bảng so sánh các gói dịch vụ:

| Tính năng | Starter | Professional | Enterprise |
|-----------|---------|--------------|------------|
| <b>Người dùng</b> | 5 | 25 | Unlimited |
| <b>Ticket/tháng</b> | 100 | 1,000 | Unlimited |
| <b>Storage</b> | 5GB | 50GB | Unlimited |
| <b>Email hỗ trợ</b> | ✓ | ✓ | ✓ |
| <b>Hotline hỗ trợ</b> | - | ✓ | ✓ |
| <b>SLA</b> | 24h | 4h | 1h |
| <b>Custom domain</b> | - | ✓ | ✓ |
| <b>API access</b> | - | ✓ | ✓ |
| <b>SSO</b> | - | - | ✓ |
| <b>Audit log</b> | - | - | ✓ |
| <b>Hỗ trợ tại chỗ</b> | - | - | ✓ |

<b>Starter (Miễn phí):</b>
- Dành cho đội nhóm nhỏ, bắt đầu tìm hiểu
- Đủ cho nhu cầu cơ bản

<b>Professional ($29/tháng):</b>
- Dành cho doanh nghiệp vừa
- Tất cả tính năng cần thiết

<b>Enterprise (Liên hệ):</b>
- Cho doanh nghiệp lớn
- Tùy chỉnh theo nhu cầu
- Hỗ trợ ưu tiên và onboarding

Xem chi tiết: obsidian.vn/bang-gia""",
        "category": "Bắt đầu",
        "view_count": 432,
        "is_published": True,
    },
]

CATEGORIES = [
    ("Quản lý tài khoản", "Danh mục hỗ trợ quản lý tài khoản người dùng"),
    ("Thanh toán", "Danh mục liên quan đến thanh toán và hóa đơn"),
    ("Kỹ thuật", "Danh mục hỗ trợ kỹ thuật và xử lý lỗi"),
    ("Hướng dẫn sử dụng", "Danh mục hướng dẫn sử dụng hệ thống"),
    ("Chính sách", "Danh mục về chính sách và điều khoản dịch vụ"),
    ("Bắt đầu", "Danh mục hướng dẫn bắt đầu sử dụng"),
]


def seed_faq():
    db = SessionLocal()
    try:
        # Get existing departments to link categories
        result = db.execute(text("SELECT id_department FROM departments LIMIT 1"))
        dept_row = result.fetchone()
        if not dept_row:
            print("No department found. Please create a department first.")
            return
        dept_id = str(dept_row[0])

        # Create categories if not exist
        category_ids = {}
        for cat_name, cat_desc in CATEGORIES:
            result = db.execute(
                text("SELECT id_category FROM tickets_category WHERE name = :name"),
                {"name": cat_name}
            )
            row = result.fetchone()
            if row:
                category_ids[cat_name] = str(row[0])
                print(f"Category exists: {cat_name}")
            else:
                cat_id = str(uuid.uuid4())
                db.execute(
                    text("""INSERT INTO tickets_category (id_category, name, description, id_department, is_active, is_deleted, created_at, updated_at)
                       VALUES (:id, :name, :desc, :dept_id, true, false, :now, :now)"""),
                    {"id": cat_id, "name": cat_name, "desc": cat_desc, "dept_id": dept_id, "now": datetime.utcnow()}
                )
                category_ids[cat_name] = cat_id
                print(f"Created category: {cat_name}")

        db.commit()

        # Get first employee for author_id
        result = db.execute(text("SELECT id_employee FROM employees LIMIT 1"))
        author_row = result.fetchone()
        author_id = str(author_row[0]) if author_row else None

        # Create FAQ articles
        created = 0
        for faq_data in FAQ_DATA:
            category_name = faq_data["category"]
            category_id = category_ids.get(category_name)

            if not category_id:
                print(f"Skipping: no category '{category_name}'")
                continue

            # Check if exists
            result = db.execute(
                text("SELECT id_article FROM faq_articles WHERE title = :title"),
                {"title": faq_data["title"]}
            )
            if result.fetchone():
                print(f"FAQ already exists: {faq_data['title']}")
                continue

            faq_id = str(uuid.uuid4())
            db.execute(
                text("""INSERT INTO faq_articles
                   (id_article, title, content, view_count, is_published, id_category, id_author, created_at, updated_at)
                   VALUES (:id, :title, :content, :view_count, :is_published, :id_category, :id_author, :now, :now)"""),
                {
                    "id": faq_id,
                    "title": faq_data["title"],
                    "content": faq_data["content"],
                    "view_count": faq_data.get("view_count", 0),
                    "is_published": faq_data.get("is_published", True),
                    "id_category": category_id,
                    "id_author": author_id,
                    "now": datetime.utcnow(),
                }
            )
            created += 1
            print(f"Created FAQ: {faq_data['title']}")

        db.commit()
        print(f"\n✅ Successfully created {created} FAQ articles!")

    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("Starting FAQ seed...\n")
    seed_faq()
    print("\nDone!")