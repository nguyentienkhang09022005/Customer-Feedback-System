# Notification & Email

## 1. Tổng quan

- **In-app Notification**: Thông báo trong ứng dụng với realtime qua Socket.IO
- **Email Service**: Gửi email qua SMTP (Gmail / SendGrid) cho OTP, ticket events, CSAT survey

---

## 2. Database Schema

### Notification (`notification`)
| Cột | Kiểu | Mô tả |
|-----|------|--------|
| id_notification | UUID, PK | ID thông báo |
| title | String(255), NOT NULL | Tiêu đề |
| content | Text | Nội dung chi tiết |
| notification_type | String(50) | Loại (ticket_created, ticket_assigned...) |
| is_read | Boolean, default=False | Đã đọc |
| created_at | DateTime | Thời gian tạo |
| id_reference | UUID | ID tham chiếu (ticket_id) |
| id_receiver | UUID, FK→humans | Người nhận |

---

## 3. API Endpoints

| Method | Path | Quyền | Mô tả |
|--------|------|-------|--------|
| GET | `/api/v1/notifications` | User | Danh sách thông báo (lọc unread, phân trang) |
| PATCH | `/api/v1/notifications/{id}/read` | User | Đánh dấu đã đọc |

**Query params**: `is_unread_only` (bool), `skip` (int), `limit` (int, default=20)

---

## 4. Service Layer

### NotificationService
- `create_and_send(data)`: Tạo notification DB → emit realtime event qua Socket.IO (`new_notification` trên namespace `/chat`, room `user_{id_receiver}`)
- `get_my_notifications(user_id, is_unread_only, skip, limit)`: Lấy danh sách phân trang
- `mark_as_read(notification_id, user_id)`: Kiểm tra quyền sở hữu → đánh dấu đã đọc (404 nếu không tìm thấy, 403 nếu không phải người nhận)

### EmailService
- **Singleton pattern**: Chỉ 1 instance
- **2 provider**: Gmail SMTP (STARTTLS port 587) và SendGrid SMTP
- **Retry**: Tự động retry 3 lần khi disconnect
- **Connection pooling**: Giữ kết nối SMTP tái sử dụng

---

## 5. Các phương thức gửi email

| Method | Mục đích | Template |
|--------|----------|----------|
| `send_otp_email(to, otp_code)` | OTP xác minh đăng nhập | `otp_verification.html` |
| `send_password_reset_otp_email(to, otp_code)` | OTP đặt lại mật khẩu | `password_reset.html` |
| `send_ticket_notification(to, ticket_id, event_type, info)` | Thông báo sự kiện ticket | `ticket_notification.html` |
| `send_csat_survey(to, ticket_id, title, status, severity)` | Khảo sát hài lòng | `csat_survey.html` |

---

## 6. Ticket Event Types

| Event Type | Subject | Icon |
|------------|---------|------|
| `created` | "Ticket #X - Da tao moi" | 🎫 |
| `assigned` | "Ticket #X - Da duoc phan cong" | 📋 |
| `updated` | "Ticket #X - Da duoc cap nhat" | 🔄 |
| `resolved` | "Ticket #X - Da duoc giai quyet" | ✅ |
| `closed` | "Ticket #X - Da dong" | 🔒 |

---

## 7. CSAT Survey Flow

```
Ticket resolved → send_csat_survey() → Email đến khách hàng
  → Thông tin: ticket ID (8 ký tự), tiêu đề, trạng thái, severity
  → Thang đánh giá 1-5: 😞 😕 😐 🙂 😀
  → Khách hàng reply email với số điểm
```

---

## 8. Email Templates

Tất cả template sử dụng dark theme (GitHub-style, nền `#0d1117`):
- `otp_verification.html`: Mã OTP đăng ký
- `password_reset.html`: Mã OTP reset (hết hạn 5 phút)
- `ticket_notification.html`: Thông báo sự kiện ticket
- `csat_survey.html`: Khảo sát mức độ hài lòng

---

## 9. Cấu hình

```
SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD
SMTP_FROM_NAME, SMTP_USE_TLS
EMAIL_PROVIDER (gmail | sendgrid)
SENDGRID_API_KEY
```
