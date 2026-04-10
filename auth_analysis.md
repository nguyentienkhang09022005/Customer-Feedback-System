# Authentication & Logout Analysis Report

## Tổng quan kiến trúc

Hệ thống authen sử dụng JWT token với cơ chế blacklist lưu trong Redis.

## Các file chính

| File | Mô tả |
|------|-------|
| `app/api/v1/auth.py` | API endpoints (login, logout, register, verify-otp, refresh, etc.) |
| `app/services/authService.py` | Business logic xác thực, tạo token, đổi mật khẩu |
| `app/services/tokenBlacklistService.py` | Quản lý blacklist token trong Redis |
| `app/core/security.py` | Tạo & verify JWT token |
| `app/api/dependencies.py` | Dependency injection cho `get_current_user` |

---

## 1. LOGIN (Hoạt động ✅)

**Flow:**
1. `POST /auth/login` với `username` + `password`
2. `AuthService.authenticate_user()` kiểm tra:
   - User tồn tại theo username
   - Password hash match
   - User status = ACTIVE
3. `AuthService.create_tokens()` tạo:
   - Access token (15 phút mặc định)
   - Refresh token (7 ngày mặc định)
4. Trả về `TokenResponse` chứa cả 2 token

**Code đang hoạt động đúng.**

---

## 2. LOGOUT (Hoạt động ✅)

**Flow:**
1. `POST /auth/logout` yêu cầu Bearer token
2. `get_current_user` verify token và kiểm tra blacklist
3. Nếu token chưa bị blacklist:
   - Lấy `jti` và `exp` từ token
   - Tính `expires_in = exp - now`
   - Gọi `TokenBlacklistService.blacklist_access_token(jti, user_id, expires_in)`
4. Token được lưu vào Redis với key `blacklist:access:<jti>` và TTL = thời gian còn lại

**Chi tiết `TokenBlacklistService.blacklist_access_token()`:**
```python
key = f"blacklist:access:{jti}"
redis_service.set_with_expiry(key, "1", expires_in)  # Lưu "1" với TTL
redis_service.add_to_set(user_key, jti)  # Track theo user để logout all devices
```

**Code đang hoạt động đúng.**

---

## 3. Token Verification khi request có token (Hoạt động ✅)

**Trong `get_current_user()` (`app/api/dependencies.py`):**

1. **Bước 1:** Decode token không verify (unsafe) để lấy `jti`
   ```python
   payload_unsafe = decode_token_unsafe(token)
   jti = payload_unsafe.get("jti")
   ```

2. **Bước 2:** Kiểm tra blacklist TRƯỚC khi verify đầy đủ
   ```python
   if TokenBlacklistService.is_access_token_blacklisted(jti):
       raise HTTPException(status_code=401, detail="Token has been revoked!")
   ```

3. **Bước 3:** Verify token đầy đủ
   ```python
   payload = verify_token(token, "access")
   ```

4. **Bước 4:** Lấy user từ database
   ```python
   user = repo.get_by_id(user_id_str)
   ```

**Thứ tự này TỐI ƯU** vì:
- Kiểm tra blacklist trước (Redis lookup nhanh)
- Tránh verify token đã biết là invalid

---

## 4. REFRESH TOKEN (Hoạt động ✅)

**Flow:**
1. `POST /auth/refresh` với `refresh_token`
2. Verify refresh token
3. Tạo access token + refresh token MỚI
4. Blacklist refresh token CŨ (sau khi tạo token mới thành công)

**Code đang hoạt động đúng.**

---

## 5. Đăng ký & OTP (Hoạt động ✅)

**Flow:**
1. `POST /auth/register` → Lưu data + gửi OTP (5 phút hiệu lực)
2. `POST /auth/verify-otp` → Verify OTP → Tạo Customer + trả token
3. `POST /auth/forgot-password` → Gửi OTP reset password
4. `POST /auth/reset-password` → Verify OTP + đổi password

---

## 6. Phát hiện vấn đề tiềm ẩn

### ⚠️ Issue 1: Redis phải được bật
`TokenBlacklistService` phụ thuộc hoàn toàn vào Redis:
- Nếu `REDIS_ENABLED=false` hoặc Redis không kết nối → `is_connected()` trả `False`
- Khi đó `blacklist_access_token()` trả `False` (log warning nhưng KHÔNG raise exception)
- Token vẫn được coi là "logout thành công" về mặt API response
- **Nhưng token thực tế KHÔNG bị blacklist** → User vẫn có thể dùng token cũ!

**Khuyến nghị:** Thêm check ở logout endpoint để đảm bảo blacklist thực sự xảy ra:
```python
success = TokenBlacklistService.blacklist_access_token(jti, user_id, expires_in)
if not success:
    # Log warning or raise exception
    pass
```

### ⚠️ Issue 2: Refresh token KHÔNG bị blacklist khi logout
Khi logout (`POST /auth/logout`):
- Chỉ blacklist **access token**
- Refresh token VẪN CÒN HẠN → User có thể dùng refresh token để lấy access token mới

**Khuyến nghị:** Cần blacklist cả refresh token khi logout.

---

## Kết luận

| Chức năng | Trạng thái |
|-----------|------------|
| Login | ✅ Hoạt động |
| Logout (access token) | ✅ Hoạt động |
| Token verification | ✅ Hoạt động |
| Refresh token | ✅ Hoạt động |
| Register + OTP | ✅ Hoạt động |
| Forgot password | ✅ Hoạt động |

---

## Kết quả Test thực tế

### Test Redis Connection

```
Redis enabled: True
Host: localhost:6379
Is connected: True ✅
```

**Lưu ý:** Redis có password trong `.env` là `REDIS_PASSWORD=123` nhưng Redis thực tế **không có password**. Nếu Redis yêu cầu password, app sẽ không kết nối được.

### Test Blacklist Flow

```
Token JTI: 2230156b-6366-4ddc-8684-bca79d4d94d9
Blacklist result: True ✅
Token is blacklisted: True ✅
```

---

## Xác nhận 2 vấn đề tiềm ẩn

### ⚠️ Issue 1: Không kiểm tra kết quả blacklist

**Thực tế:**
```python
# Trong /logout endpoint
TokenBlacklistService.blacklist_access_token(jti, user_id, expires_in)
return {"message": "Đăng xuất thành công!"}
```

**Vấn đề:** `blacklist_access_token()` trả `False` khi Redis lỗi, nhưng code KHÔNG kiểm tra giá trị trả về. User vẫn nhận "Đăng xuất thành công" dù token không bị blacklist.

**✅ ĐÃ SỬA:**
- Kiểm tra return value của `blacklist_access_token()`
- Nếu `False`, raise `HTTP 500` với message "Không thể đăng xuất. Vui lòng thử lại!"

### ⚠️ Issue 2: Refresh token không bị blacklist khi logout

**Test thực tế:**
```
Refresh token JTI: 0f4406ae-d683-45d4-99e3-a7a6ddc9d927
Refresh token is NOT blacklisted when calling /logout endpoint
User can still use refresh_token to get new access token!
```

**Vấn đề:** Khi logout, chỉ access token bị blacklist. Refresh token vẫn còn hiệu lực 7 ngày → User có thể dùng `/auth/refresh` để lấy access token mới.

**✅ ĐÃ SỬA:**
- Thêm `LogoutRequest` schema với optional `refresh_token`
- Nếu `refresh_token` được gửi kèm, tự động blacklist luôn refresh token

---

## Các thay đổi đã thực hiện

### 1. `app/schemas/authSchema.py`
```python
class LogoutRequest(BaseModel):
    refresh_token: Optional[str] = None
```

### 2. `app/api/v1/auth.py`
- Import thêm `LogoutRequest`
- Thêm `request: LogoutRequest = None` parameter
- Kiểm tra return value của `blacklist_access_token()`, raise 500 nếu thất bại
- Nếu `request.refresh_token` được gửi, blacklist luôn refresh token

### Test sau khi fix:
```
Access token blacklisted: True
Refresh token blacklisted: True
Access token blacklisted (check): True
Refresh token blacklisted (check): True
```

---

## Test logout

```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "test", "password": "test123"}'

# Logout (dùng access token từ login)
curl -X POST http://localhost:8000/api/v1/auth/logout \
  -H "Authorization: Bearer <access_token>"

# Gọi API khác với cùng access token (sẽ bị 401)
curl http://localhost:8000/api/v1/tickets \
  -H "Authorization: Bearer <access_token>"
```
