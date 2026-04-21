# Appointment - Đặt lịch hẹn tư vấn

## Tổng quan

Chức năng **Appointment** cho phép khách hàng đặt lịch hẹn tư vấn trực tiếp với nhân viên đang đảm nhận ticket. Điều này giúp:

- Khách hàng chủ động sắp xếp thời gian để được hỗ trợ
- Nhân viên có thể từ chối nếu không phù hợp và giải thích lý do
- Quản lý lịch hẹn hiệu quả

---

## Database Schema

### Bảng `appointments`

| Column | Type | Mô tả |
|--------|------|-------|
| `id_appointment` | UUID | Primary key |
| `id_ticket` | UUID | Foreign key → tickets |
| `id_customer` | UUID | Foreign key → customers |
| `id_employee` | UUID | Foreign key → employees |
| `scheduled_at` | DateTime | Thời gian hẹn (phải > thời gian hiện tại) |
| `reason` | Text | Lý do/yêu cầu tư vấn |
| `status` | String(20) | Trạng thái: pending, accepted, rejected, cancelled, completed |
| `rejection_reason` | Text | Lý do từ chối (nullable) |
| `created_at` | DateTime | Thời gian tạo |
| `updated_at` | DateTime | Thời gian cập nhật cuối |

---

## Trạng thái Appointment

| Status | Mô tả | Actor có thể chuyển |
|--------|-------|---------------------|
| `pending` | Đang chờ xác nhận | Employee: accept/reject, Customer: cancel |
| `accepted` | Đã được chấp nhận | Customer: cancel |
| `rejected` | Bị từ chối | Không chuyển tiếp được |
| `cancelled` | Đã hủy | Không chuyển tiếp được |
| `completed` | Đã hoàn thành | Không chuyển tiếp được |

---

## API Endpoints

### 1. Tạo lịch hẹn

```
POST /api/v1/appointments
Authorization: Customer token
Content-Type: application/json

Body:
{
  "id_ticket": "uuid",
  "scheduled_at": "2026-04-22T14:00:00",
  "reason": "Tôi cần được tư vấn về..."
}

Responses:
- 201: Đặt lịch hẹn thành công
- 400: Ticket không có nhân viên đảm nhận
- 400: Ticket đã resolved/closed
- 400: Đã có lịch hẹn đang chờ
- 400: Thời gian hẹn phải lớn hơn hiện tại
- 403: Không có quyền đặt lịch cho ticket này
- 404: Không tìm thấy ticket
```

### 2. Lấy lịch hẹn theo ticket

```
GET /api/v1/appointments/ticket/{ticket_id}
Authorization: Customer/Employee token

Response:
- 200: Danh sách lịch hẹn của ticket
```

### 3. Lấy lịch hẹn của Employee

```
GET /api/v1/appointments/employee
Authorization: Employee token

Response:
- 200: Danh sách tất cả lịch hẹn của employee
```

### 4. Lấy lịch hẹn đang chờ của Employee

```
GET /api/v1/appointments/employee/pending
Authorization: Employee token

Response:
- 200: Danh sách lịch hẹn đang ở trạng thái pending
```

### 5. Lấy chi tiết lịch hẹn

```
GET /api/v1/appointments/{appointment_id}
Authorization: Customer/Employee token

Response:
- 200: Chi tiết lịch hẹn
- 403: Không có quyền xem
- 404: Không tìm thấy
```

### 6. Chấp nhận lịch hẹn

```
PATCH /api/v1/appointments/{appointment_id}/accept
Authorization: Employee token

Body: (empty or {})

Responses:
- 200: Chấp nhận thành công
- 400: Lịch hẹn không ở trạng thái pending
- 403: Không phải employee phụ trách
- 404: Không tìm thấy
```

### 7. Từ chối lịch hẹn

```
PATCH /api/v1/appointments/{appointment_id}/reject
Authorization: Employee token
Content-Type: application/json

Body:
{
  "rejection_reason": "Tôi không thể vào thời gian đó vì..."
}

Responses:
- 200: Từ chối thành công
- 400: Phải cung cấp lý do từ chối
- 400: Lịch hẹn không ở trạng thái pending
- 403: Không phải employee phụ trách
- 404: Không tìm thấy
```

### 8. Hủy lịch hẹn

```
PATCH /api/v1/appointments/{appointment_id}/cancel
Authorization: Customer token
Content-Type: application/json

Body: (empty or {})

Responses:
- 200: Hủy thành công
- 400: Không thể hủy ở trạng thái hiện tại
- 403: Không phải khách hàng tạo
- 404: Không tìm thấy
```

---

## Luồng nghiệp vụ

### Luồng 1: Customer đặt lịch hẹn thành công

```
Customer tạo ticket
    ↓
Employee được assign vào ticket
    ↓
Ticket status vẫn là "New" / "In Progress" / ...
    ↓
Customer gọi POST /appointments
    ↓
Hệ thống validate:
  - Ticket tồn tại? ✅
  - Ticket chưa resolved/closed? ✅
  - Customer sở hữu ticket? ✅
  - Ticket có employee assign? ✅
  - Thời gian hẹn > hiện tại? ✅
  - Chưa có lịch hẹn pending? ✅
    ↓
Tạo appointment với status = "pending"
    ↓
Gửi notification cho employee
    ↓
Return 201 với appointment data
```

### Luồng 2: Employee chấp nhận lịch hẹn

```
Employee nhận notification có lịch hẹn mới
    ↓
Employee gọi GET /appointments/employee/pending
    ↓
Employee xem chi tiết và quyết định accept
    ↓
Employee gọi PATCH /appointments/{id}/accept
    ↓
Status chuyển thành "accepted"
    ↓
Gửi notification cho customer
```

### Luồng 3: Employee từ chối lịch hẹn

```
Employee nhận notification có lịch hẹn mới
    ↓
Employee gọi PATCH /appointments/{id}/reject
Body: {"rejection_reason": "Tôi có cuộc họp vào lúc đó..."}
    ↓
Hệ thống validate:
  - rejection_reason không rỗng? ✅
  - Status là "pending"? ✅
    ↓
Status chuyển thành "rejected"
Lưu rejection_reason
    ↓
Gửi notification cho customer với lý do từ chối
```

### Luồng 4: Customer hủy lịch hẹn

```
Customer muốn hủy lịch hẹn
    ↓
Customer gọi PATCH /appointments/{id}/cancel
    ↓
Hệ thống validate:
  - Customer sở hữu appointment? ✅
  - Status là "pending" hoặc "accepted"? ✅
    ↓
Status chuyển thành "cancelled"
    ↓
Gửi notification cho employee
```

---

## Business Rules

1. **Điều kiện tạo appointment:**
   - Ticket phải tồn tại và chưa bị xóa
   - Ticket phải có `id_employee` (đã được assign)
   - Ticket status không được là `Resolved` hoặc `Closed`
   - Chỉ customer sở hữu ticket mới được tạo
   - Thời gian hẹn phải lớn hơn thời gian hiện tại
   - Mỗi ticket chỉ có tối đa 1 lịch hẹn ở trạng thái `pending`

2. **Điều kiện accept/reject:**
   - Chỉ employee được assign mới có quyền accept/reject
   - Chỉ áp dụng khi status là `pending`

3. **Điều kiện cancel:**
   - Customer có thể hủy lịch hẹn do mình tạo
   - Employee có thể hủy lịch hẹn được assign cho mình
   - Chỉ áp dụng khi status là `pending` hoặc `accepted`

4. **Rejection reason:**
   - BẮT BUỘC khi từ chối lịch hẹn
   - Được lưu lại để customer hiểu lý do

---

## Files structure

```
app/
├── models/
│   └── appointment.py          # Model + AppointmentStatus constants
├── schemas/
│   └── appointmentSchema.py    # Pydantic schemas (Create, Out, Accept, Reject, Cancel)
├── repositories/
│   └── appointmentRepository.py # CRUD operations
├── services/
│   └── appointmentService.py   # Business logic + notifications
└── api/
    └── v1/
        └── appointments.py     # API endpoints

migrations/
└── versions/
    └── a2e3c91d4bd8_create_appointments_table.py  # Migration file
```

---

## Notifications

Khi có sự kiện appointment, hệ thống tự động gửi notification:

| Event | Người nhận | Loại notification |
|-------|-----------|-------------------|
| Tạo lịch hẹn | Employee | `APPOINTMENT_REQUEST` |
| Chấp nhận lịch hẹn | Customer | `APPOINTMENT_ACCEPTED` |
| Từ chối lịch hẹn | Customer | `APPOINTMENT_REJECTED` |
| Hủy lịch hẹn | Employee | `APPOINTMENT_CANCELLED` |

---

## Error Messages

| Code | Message | Giải thích |
|------|---------|------------|
| 400 | "Thời gian hẹn phải lớn hơn thời gian hiện tại!" | `scheduled_at` <= now |
| 400 | "Vui lòng cung cấp lý do/yêu cầu tư vấn!" | `reason` empty |
| 400 | "Ticket chưa có nhân viên đảm nhận..." | Ticket chưa được assign |
| 400 | "Ticket đã được giải quyết hoặc đóng..." | Ticket resolved/closed |
| 400 | "Đã có lịch hẹn đang chờ xử lý..." | Ticket có pending appointment |
| 400 | "Vui lòng cung cấp lý do từ chối!" | rejection_reason empty |
| 403 | "Bạn không có quyền..." | Không phải owner/assignee |
| 404 | "Không tìm thấy..." | Không tìm thấy ticket/appointment |