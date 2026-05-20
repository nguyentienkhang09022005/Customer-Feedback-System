# Authentication & Authorization

## 1. Tổng quan

Hệ thống xác thực và phân quyền sử dụng:
- **JWT** (access token + refresh token) với JTI để hỗ trợ blacklist
- **OTP qua email** (6 chữ số, hiệu lực 5 phút) cho đăng ký và quên mật khẩu
- **Redis** lưu OTP và token blacklist
- **bcrypt** hash mật khẩu
- **RBAC**: Admin, Manager, Employee, Customer

---

## 2. Database Schema

### Bảng `roles`
| Cột | Kiểu | Mô tả |
|-----|------|--------|
| role_name | String(50), PK | Tên role |
| description | String(255) | Mô tả |

### Bảng `humans` (Base - Polymorphic)
| Cột | Kiểu | Mô tả |
|-----|------|--------|
| id | UUID, PK | ID chính |
| first_name / last_name | String(50) | Họ tên |
| email | String(100), unique | Email |
| phone | String(20) | SĐT |
| address | String(255) | Địa chỉ |
| username | String(50), unique | Tên đăng nhập |
| password_hash | String(255) | Mật khẩu đã hash |
| status | String(20) | Active/Pending |
| avatar | String(255) | URL avatar |
| type | String(50) | Discriminator (employee/customer) |
| created_at / updated_at | DateTime | Timestamps |

### Bảng `employees` (kế thừa `humans`)
| Cột | Kiểu | Mô tả |
|-----|------|--------|
| id_employee | UUID, PK | ID nhân viên |
| id_department | UUID, FK→departments | Phòng ban |
| employee_code | String(20), unique | Mã NV (VD: NV25001) |
| job_title | String(50) | Chức danh |
| max_ticket_capacity | Integer, default=5 | Số ticket tối đa |
| csat_score | Float, default=0.0 | Điểm CSAT |
| hire_date | Date | Ngày vào làm |
| role_name | String(50), FK→roles | Role phân quyền |

### Bảng `customers` (kế thừa `humans`)
| Cột | Kiểu | Mô tả |
|-----|------|--------|
| id_customer | UUID, PK | ID khách hàng |
| customer_code | String(20), unique | Mã KH (VD: KH25001) |
| membership_tier | String(20), default="Starter" | Hạng thành viên |
| timezone | String(50) | Múi giờ |
| customer_type | String(50), FK→customer_type | Loại KH |

---

## 3. API Endpoints

### Authentication (`/api/v1/auth`)

| Method | Path | Auth | Mô tả |
|--------|------|------|--------|
| POST | `/auth/register` | ❌ | Đăng ký khách hàng (gửi OTP) |
| POST | `/auth/verify-otp` | ❌ | Xác thực OTP & kích hoạt tài khoản |
| POST | `/auth/forgot-password` | ❌ | Gửi OTP quên mật khẩu |
| POST | `/auth/reset-password` | ❌ | Đặt lại mật khẩu bằng OTP |
| POST | `/auth/login` | ❌ | Đăng nhập |
| POST | `/auth/refresh` | ❌ | Làm mới token |
| POST | `/auth/logout` | ✅ | Đăng xuất (blacklist token) |

### OTP (`/api/v1/otp`)

| Method | Path | Auth | Mô tả |
|--------|------|------|--------|
| POST | `/otp/verify-registration` | ❌ | Xác thực OTP đăng ký (endpoint thay thế) |

### Roles (`/api/v1/roles`)

| Method | Path | Auth | Mô tả |
|--------|------|------|--------|
| GET | `/roles` | Employee | Lấy danh sách roles |
| POST | `/roles` | Admin | Tạo role mới |
| PUT | `/roles/{role_name}` | Admin | Cập nhật role |
| DELETE | `/roles/{role_name}` | Admin | Xóa role |

---

## 4. Luồng xác thực

### Đăng ký
```
POST /auth/register → Kiểm tra trùng → Tạo Customer (PENDING) → Gửi OTP email
POST /auth/verify-otp → Verify OTP → ACTIVE → Trả TokenResponse
```

### Đăng nhập
```
POST /auth/login → Verify password → Kiểm tra ACTIVE → Tạo tokens → Preload chatbot cache
```

### Quên mật khẩu
```
POST /auth/forgot-password → Luôn trả success (chống enumeration) → Gửi OTP nếu email tồn tại
POST /auth/reset-password → Verify OTP (type=password_reset) → Cập nhật password
```

---

## 5. Token Management

### JWT Payload
```json
{
  "sub": "user_uuid",
  "jti": "unique_token_id",
  "email": "user@email.com",
  "user_type": "employee|customer",
  "role": "Admin|Manager|Customer",
  "exp": 1234567890,
  "type": "access|refresh"
}
```

### Blacklist (Redis)
- `blacklist:access:{jti}` - access token bị thu hồi
- `blacklist:refresh:{jti}` - refresh token bị thu hồi
- `blacklist:user:{user_id}:access` - set chứa tất cả JTI access của user
- TTL = thời gian còn lại của token

### Refresh Flow
```
POST /auth/refresh → Decode old token → Verify → Tạo token mới → Blacklist old refresh (rotation)
```

### Logout Flow
```
POST /auth/logout → Blacklist access token → Blacklist refresh token → Invalidate chatbot cache
```

---

## 6. OTP Flow

| Bước | Chi tiết |
|------|----------|
| Sinh OTP | 6 chữ số ngẫu nhiên |
| Lưu Redis | Key: `otp:{email}`, Value: `{otp, data, type}`, TTL: 300s |
| Gửi email | Qua emailService |
| Verify | So sánh OTP + kiểm tra type phù hợp |
| Xóa | One-time use - xóa sau khi verify |

**Phân biệt type**: `verification` (đăng ký) vs `password_reset` (quên MK) → không dùng lẫn.

---

## 7. Phân quyền (RBAC)

| Dependency | Yêu cầu | Dùng cho |
|------------|----------|----------|
| `get_current_user` | Token hợp lệ | Mọi endpoint cần auth |
| `get_current_customer` | type=customer | Endpoint dành cho KH |
| `get_current_employee` | type=employee | Endpoint nội bộ |
| `get_current_manager` | role ∈ {Admin, Manager} | Quản lý |
| `get_current_admin` | role=Admin | Quản trị hệ thống |

---

## 8. Service Layer

### AuthService
- `register_customer`: Kiểm tra trùng → tạo Customer PENDING → sinh mã KH → gửi OTP
- `verify_otp_and_activate`: Verify OTP → chuyển ACTIVE
- `authenticate_user`: Tìm user → verify bcrypt → kiểm tra ACTIVE
- `create_tokens`: Tạo cặp access + refresh token
- `change_password`: Verify mật khẩu cũ → hash mới → lưu
- `initiate_forgot_password`: Luôn trả success (chống enumeration)
- `reset_password_with_otp`: Verify OTP type=password_reset → cập nhật hash

### OTPService
- Lưu trữ trên Redis, TTL 5 phút
- Phân biệt type verification/password_reset
- One-time use (xóa sau verify)

### TokenBlacklistService
- Blacklist theo JTI trên Redis
- Hỗ trợ blacklist all tokens của user (logout all devices)
- Tự dọn khi token hết hạn (TTL)
