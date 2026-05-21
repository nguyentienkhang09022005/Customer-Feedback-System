# API Documentation - Customer Feedback System

## Tổng quan

Hệ thống có **164 API endpoints** được phân loại theo chức năng và phân quyền người dùng.

---

## 4 Role & Chức năng

### 1. ADMIN

| Module | API | Phương thức | Mô tả |
|--------|-----|-------------|-------|
| **Auth** | /auth/register | POST | Đăng ký tài khoản mới |
| | /auth/verify-otp | POST | Xác minh OTP để kích hoạt tài khoản |
| | /auth/login | POST | Đăng nhập |
| | /auth/refresh | POST | Làm mới access token |
| | /auth/logout | POST | Đăng xuất |
| | /auth/forgot-password | POST | Quên mật khẩu |
| | /auth/reset-password | POST | Đặt lại mật khẩu |
| **User** | /user/me | GET | Lấy thông tin cá nhân |
| | /user/me | PUT | Cập nhật thông tin cá nhân |
| | /user/change-password | POST | Đổi mật khẩu |
| | /user/avatar | POST | Upload avatar |
| **Customer** | /customers | GET | Lấy danh sách khách hàng |
| | /customers | POST | Tạo khách hàng |
| | /customers/{cus_id} | PATCH | Cập nhật khách hàng |
| | /customers/{cus_id} | DELETE | Xóa khách hàng |
| **Employee** | /employees | GET | Lấy danh sách nhân viên |
| | /employees | POST | Tạo nhân viên |
| | /employees/{emp_id} | GET | Lấy thông tin nhân viên |
| | /employees/{emp_id} | PATCH | Cập nhật nhân viên |
| | /employees/{emp_id} | DELETE | Xóa nhân viên |
| | /employees/department/{dept_id} | GET | Lấy NV theo phòng ban |
| | /employees/department/{dept_id}/members | GET | Lấy thành viên phòng ban |
| | /employees/workload/department/{dept_id} | GET | Xem workload phòng ban |
| | /employees/manager/{emp_id} | PATCH | Manager cập nhật NV |
| **Department** | /departments | GET | Lấy danh sách phòng ban |
| | /departments | POST | Tạo phòng ban |
| | /departments/{dept_id} | GET | Lấy thông tin phòng ban |
| | /departments/{dept_id} | PATCH | Cập nhật phòng ban |
| | /departments/{dept_id} | DELETE | Xóa phòng ban |
| **Ticket** | /tickets/all | GET | Xem tất cả ticket |
| | /tickets/unassigned | GET | Xem ticket chưa gán |
| | /tickets/department/{dept_id} | GET | Xem ticket theo phòng ban |
| | /tickets/employee-tickets | GET | Xem ticket của nhân viên |
| | /tickets/employee-tickets/closed | GET | Xem ticket đã đóng của nhân viên |
| | /tickets/{ticket_id} | GET | Xem chi tiết ticket |
| | /tickets/{ticket_id} | PATCH | Cập nhật ticket |
| | /tickets/{ticket_id} | DELETE | Xóa ticket |
| | /tickets/{ticket_id}/assign | POST | Gán ticket |
| | /tickets/{ticket_id}/resolve | POST | Giải quyết ticket |
| | /tickets/{ticket_id}/close | POST | Đóng ticket |
| | /tickets/{ticket_id}/reopen | POST | Mở lại ticket |
| | /tickets/manager/department/{dept_id} | GET | Manager xem ticket phòng ban |
| | /tickets/manager/assign/{ticket_id} | POST | Manager gán ticket |
| | /tickets/user | GET | Customer xem ticket của mình |
| | /tickets/user/closed | GET | Customer xem ticket đã đóng |
| | /tickets/{ticket_id}/customer-update | PATCH | Customer cập nhật ticket |
| | /tickets/from-template | POST | Tạo ticket từ template |
| **Ticket Comment** | /tickets/{ticket_id}/comments | GET | Lấy comments |
| | /tickets/{ticket_id}/comments | POST | Tạo comment |
| | /tickets/{ticket_id}/comments/{comment_id} | PATCH | Cập nhật comment |
| | /tickets/{ticket_id}/comments/{comment_id} | DELETE | Xóa comment |
| **Ticket History** | /tickets/{ticket_id}/history | GET | Xem lịch sử ticket |
| **Ticket Category** | /ticket-categories | GET | Lấy danh mục ticket |
| | /ticket-categories | POST | Tạo danh mục |
| | /ticket-categories/{cat_id} | GET | Lấy chi tiết danh mục |
| | /ticket-categories/{cat_id}/templates | GET | Lấy templates theo danh mục |
| | /ticket-categories/{cat_id} | PATCH | Cập nhật danh mục |
| | /ticket-categories/{cat_id} | DELETE | Xóa danh mục |
| **Template** | /templates | GET | Lấy danh sách template |
| | /templates | POST | Tạo template |
| | /templates/{template_id} | GET | Lấy chi tiết template |
| | /templates/{template_id}/versions | GET | Lấy các phiên bản template |
| | /templates/{template_id} | PATCH | Cập nhật template |
| | /templates/{template_id} | DELETE | Xóa template |
| | /templates/{template_id}/activate | POST | Kích hoạt template |
| **SLA** | /sla-policies | GET | Lấy danh sách SLA |
| | /sla-policies | POST | Tạo SLA policy |
| | /sla-policies/{policy_id} | PUT | Cập nhật SLA policy |
| | /sla-policies/{policy_id}/toggle | PATCH | Bật/Tắt SLA policy |
| **Role** | /roles | GET | Lấy danh sách vai trò |
| | /roles | POST | Tạo vai trò |
| | /roles/{role_name} | PUT | Cập nhật vai trò |
| | /roles/{role_name} | DELETE | Xóa vai trò |
| **Customer Type** | /customer-types | GET | Lấy loại khách hàng |
| | /customer-types | POST | Tạo loại khách hàng |
| | /customer-types/{type_name} | PUT | Cập nhật loại khách hàng |
| | /customer-types/{type_name} | DELETE | Xóa loại khách hàng |
| **FAQ** | /faqs | GET | Lấy danh sách FAQ |
| | /faqs | POST | Tạo FAQ |
| | /faqs/public | GET | Lấy FAQ công khai |
| | /faqs/private | GET | Lấy FAQ riêng tư |
| | /faqs/{article_id} | PATCH | Cập nhật FAQ |
| | /faqs/{article_id} | DELETE | Xóa FAQ |
| **Evaluate** | /evaluates | POST | Tạo đánh giá |
| | /evaluates/ticket/{ticket_id} | GET | Lấy đánh giá theo ticket |
| | /evaluates/{evaluate_id} | PATCH | Cập nhật đánh giá |
| | /evaluates/{evaluate_id} | DELETE | Xóa đánh giá |
| **Chat** | /chat/tickets/{ticket_id}/messages | GET | Lấy lịch sử chat |
| | /chat/tickets/{ticket_id}/read | PATCH | Đánh dấu đã đọc |
| | /chat/tickets/{ticket_id}/unread-count | GET | Đếm tin chưa đọc |
| | /chat/conversations | GET | Lấy danh sách cuộc trò chuyện |
| | /chat/tickets/{ticket_id}/messages/{message_id} | DELETE | Xóa tin nhắn |
| | /chat/tickets/{ticket_id}/messages/{message_id} | PUT | Cập nhật tin nhắn |
| **Chatbot** | /chatbot/message | POST | Gửi tin nhắn chatbot |
| | /chatbot/session | GET | Lấy phiên chat |
| | /chatbot/session | DELETE | Xóa phiên chat |
| **Appointment** | /appointments | POST | Tạo lịch hẹn |
| | /appointments/ticket/{ticket_id} | GET | Lấy lịch hẹn theo ticket |
| | /appointments/employee | GET | Lấy lịch hẹn của nhân viên |
| | /appointments/employee/pending | GET | Lấy lịch hẹn chờ xác nhận |
| | /appointments/{appointment_id} | GET | Lấy chi tiết lịch hẹn |
| | /appointments/{appointment_id}/accept | PATCH | Chấp nhận lịch hẹn |
| | /appointments/{appointment_id}/reject | PATCH | Từ chối lịch hẹn |
| | /appointments/{appointment_id}/cancel | PATCH | Hủy lịch hẹn |
| **Notification** | /notifications | GET | Lấy thông báo |
| | /notifications/{notification_id}/read | PATCH | Đánh dấu đã đọc |
| **Attachment** | /attachments/upload | POST | Upload file đính kèm |
| | /attachments/upload-multiple | POST | Upload nhiều file |
| | /attachments/{attachment_id} | GET | Lấy thông tin attachment |
| | /attachments/reference/{type}/{id} | GET | Lấy attachments theo reference |
| | /attachments/{attachment_id} | DELETE | Xóa attachment |
| | /attachments/cleanup | POST | Dọn dẹp orphan attachments |
| **Department Assignment** | /department-assignments | GET | Lấy tất cả phân bổ |
| | /department-assignments/employees/{emp_id} | GET | Lấy phân bổ của nhân viên |
| | /department-assignments/departments/{dept_id}/members | GET | Lấy thành viên phòng ban |
| | /department-assignments | POST | Gán nhân viên vào phòng ban |
| | /department-assignments/transfer | POST | Chuyển phòng ban |
| | /department-assignments/manager | POST | Chỉ định Manager |
| | /department-assignments | DELETE | Xóa khỏi phòng ban |

### 2. MANAGER

| Module | API | Phương thức | Mô tả |
|--------|-----|-------------|-------|
| **Ticket** | /tickets/manager/department/{dept_id} | GET | Xem ticket phòng ban mình |
| | /tickets/manager/assign/{ticket_id} | POST | Gán ticket cho nhân viên |
| **Employee** | /employees/workload/department/{dept_id} | GET | Xem workload team |
| | /employees/department/{dept_id}/members | GET | Xem thành viên phòng ban |
| | /employees/manager/{emp_id} | PATCH | Cập nhật nhân viên trong phòng ban |
| **Department Analytics** | /department/me/sentiment | GET | Xem sentiment phòng ban mình |
| | /department/me/sentiment/trends | GET | Xem xu hướng sentiment |
| | /department/{dept_id}/sentiment | GET | Xem sentiment phòng ban cụ thể |
| | /department/{dept_id}/sentiment/trends | GET | Xem xu hướng phòng ban |
| | /department/{dept_id}/sentiment/compare | GET | So sánh sentiment |
| **Ticket** | Xem các ticket của phòng ban, gán, giải quyết, đóng/mở lại |
| **Chat** | Tham gia chat trong ticket |
| **Appointment** | Xem, chấp nhận/từ chối lịch hẹn |
| **Notification** | Nhận thông báo |

### 3. EMPLOYEE

| Module | API | Phương thức | Mô tả |
|--------|-----|-------------|-------|
| **Ticket** | /tickets/unassigned | GET | Xem ticket chưa gán |
| | /tickets/department/{dept_id} | GET | Xem ticket theo phòng ban |
| | /tickets/employee-tickets | GET | Xem ticket được gán |
| | /tickets/employee-tickets/closed | GET | Xem ticket đã đóng |
| | /tickets/{ticket_id} | GET | Xem chi tiết ticket |
| | /tickets/{ticket_id} | PATCH | Cập nhật ticket |
| | /tickets/{ticket_id}/assign | POST | Gán ticket (Manager) |
| | /tickets/{ticket_id}/resolve | POST | Giải quyết ticket |
| | /tickets/{ticket_id}/close | POST | Đóng ticket |
| | /tickets/{ticket_id}/reopen | POST | Mở lại ticket |
| **Chat** | /chat/tickets/{ticket_id}/messages | GET | Xem chat |
| | /chat/tickets/{ticket_id}/read | PATCH | Đánh dấu đã đọc |
| | /chat/tickets/{ticket_id}/unread-count | GET | Đếm tin chưa đọc |
| | /chat/conversations | GET | Xem danh sách hội thoại |
| | /chat/tickets/{ticket_id}/messages/{message_id} | PUT | Sửa tin nhắn |
| | /chat/tickets/{ticket_id}/messages/{message_id} | DELETE | Xóa tin nhắn |
| **FAQ** | /faqs | GET | Xem FAQ |
| | /faqs/private | GET | Xem FAQ private |
| | /faqs/{article_id} | PATCH | Cập nhật FAQ |
| **Template** | /templates | GET | Xem templates |
| | /templates/category/{cat_id} | GET | Xem theo danh mục |
| | /templates/{template_id} | GET | Xem chi tiết template |
| | /templates/{template_id}/versions | GET | Xem các phiên bản |
| | /templates | POST | Tạo template |
| | /templates/{template_id} | PATCH | Cập nhật template |
| **Ticket Category** | /ticket-categories | GET | Xem danh mục |
| | /ticket-categories | POST | Tạo danh mục |
| | /ticket-categories/{cat_id} | GET | Xem chi tiết danh mục |
| | /ticket-categories/{cat_id}/templates | GET | Xem templates danh mục |
| | /ticket-categories/{cat_id} | PATCH | Cập nhật danh mục |
| **SLA** | /sla-policies | GET | Xem SLA policies |
| **Chatbot** | /chatbot/message | POST | Chat với chatbot |
| | /chatbot/session | GET | Xem phiên chat |
| | /chatbot/session | DELETE | Xóa phiên chat |
| **Notification** | /notifications | GET | Xem thông báo |
| | /notifications/{notification_id}/read | PATCH | Đánh dấu đã đọc |
| **Attachment** | /attachments/upload | POST | Upload file |
| | /attachments/upload-multiple | POST | Upload nhiều file |
| | /attachments/{attachment_id} | GET | Xem attachment |
| | /attachments/reference/{type}/{id} | GET | Xem danh sách attachments |
| | /attachments/{attachment_id} | DELETE | Xóa attachment |
| **Appointment** | /appointments/employee | GET | Xem lịch hẹn của mình |
| | /appointments/employee/pending | GET | Xem lịch hẹn chờ |
| | /appointments/{appointment_id} | GET | Xem chi tiết lịch hẹn |
| | /appointments/{appointment_id}/accept | PATCH | Chấp nhận lịch hẹn |
| | /appointments/{appointment_id}/reject | PATCH | Từ chối lịch hẹn |

### 4. CUSTOMER

| Module | API | Phương thức | Mô tả |
|--------|-----|-------------|-------|
| **Auth** | /auth/register | POST | Đăng ký |
| | /auth/verify-otp | POST | Xác minh OTP |
| | /auth/login | POST | Đăng nhập |
| | /auth/forgot-password | POST | Quên mật khẩu |
| | /auth/reset-password | POST | Đặt lại mật khẩu |
| | /otp/verify-registration | POST | Xác minh OTP đăng ký |
| **User** | /user/me | GET | Lấy thông tin |
| | /user/me | PUT | Cập nhật thông tin |
| | /user/change-password | POST | Đổi mật khẩu |
| | /user/avatar | POST | Upload avatar |
| **Ticket** | /tickets/from-template | POST | Tạo ticket từ template |
| | /tickets/user | GET | Xem ticket của mình |
| | /tickets/user/closed | GET | Xem ticket đã đóng |
| | /tickets/{ticket_id} | GET | Xem chi tiết ticket (chỉ ticket của mình) |
| | /tickets/{ticket_id}/customer-update | PATCH | Cập nhật ticket |
| | /tickets/{ticket_id}/close | POST | Đóng ticket |
| | /tickets/{ticket_id}/reopen | POST | Mở lại ticket |
| **Ticket Comment** | /tickets/{ticket_id}/comments | GET | Xem comments |
| | /tickets/{ticket_id}/comments | POST | Tạo comment |
| | /tickets/{ticket_id}/comments/{comment_id} | PATCH | Cập nhật comment (chỉ author) |
| | /tickets/{ticket_id}/comments/{comment_id} | DELETE | Xóa comment (chỉ author) |
| **Ticket History** | /tickets/{ticket_id}/history | GET | Xem lịch sử (chỉ ticket của mình) |
| **Evaluate** | /evaluates | POST | Đánh giá ticket |
| | /evaluates/ticket/{ticket_id} | GET | Xem đánh giá |
| | /evaluates/{evaluate_id} | PATCH | Cập nhật đánh giá |
| | /evaluates/{evaluate_id} | DELETE | Xóa đánh giá |
| **FAQ** | /faqs/public | GET | Xem FAQ công khai |
| **Chatbot** | /chatbot/message | POST | Chat với chatbot |
| | /chatbot/session | GET | Xem phiên chat |
| | /chatbot/session | DELETE | Xóa phiên chat |
| **Chat** | /chat/tickets/{ticket_id}/messages | GET | Xem tin nhắn chat |
| | /chat/tickets/{ticket_id}/read | PATCH | Đánh dấu đã đọc |
| | /chat/tickets/{ticket_id}/unread-count | GET | Đếm tin chưa đọc |
| | /chat/conversations | GET | Xem cuộc trò chuyện |
| **Appointment** | /appointments | POST | Tạo lịch hẹn |
| | /appointments/ticket/{ticket_id} | GET | Xem lịch hẹn theo ticket |
| | /appointments/{appointment_id} | GET | Xem chi tiết lịch hẹn |
| | /appointments/{appointment_id}/cancel | PATCH | Hủy lịch hẹn |
| **Notification** | /notifications | GET | Xem thông báo |
| | /notifications/{notification_id}/read | PATCH | Đánh dấu đã đọc |
| **Attachment** | /attachments/upload | POST | Upload file |
| | /attachments/upload-multiple | POST | Upload nhiều file |
| | /attachments/{attachment_id} | GET | Xem attachment |
| | /attachments/reference/{type}/{id} | GET | Xem danh sách attachments |
| | /attachments/{attachment_id} | DELETE | Xóa attachment |

---

## Public Endpoints (Không cần đăng nhập)

| API | Phương thức | Mô tả |
|-----|-------------|-------|
| /auth/register | POST | Đăng ký |
| /auth/verify-otp | POST | Xác minh OTP |
| /auth/login | POST | Đăng nhập |
| /auth/forgot-password | POST | Quên mật khẩu |
| /auth/reset-password | POST | Đặt lại mật khẩu |
| /otp/verify-registration | POST | Xác minh OTP đăng ký |
| /faqs/public | GET | Xem FAQ công khai |
| /customer-types | GET | Xem loại khách hàng |
| /constants/ticket-statuses | GET | Xem trạng thái ticket |
| /constants/membership-tiers | GET | Xem hạng khách hàng |
| /constants/severity-levels | GET | Xem mức độ nghiêm trọng |
| /constants/human-statuses | GET | Xem trạng thái người dùng |
| /constants/sentiment-labels | GET | Xem nhãn sentiment |
| /constants/system-limits | GET | Xem giới hạn hệ thống |

---

## Summary

- **Admin**: Toàn quyền hệ thống, quản lý user, department, ticket, báo cáo
- **Manager**: Quản lý phòng ban, gán ticket, xem báo cáo sentiment phòng ban
- **Employee**: Xử lý ticket được gán, chat với khách, quản lý FAQ/templates
- **Customer**: Tạo và quản lý ticket của mình, chat với chatbot, đánh giá