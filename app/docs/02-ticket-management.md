# Ticket Management

## 1. Tổng quan

Hệ thống quản lý ticket hỗ trợ khách hàng với các tính năng:
- Tạo ticket từ template (form builder linh hoạt)
- Vòng đời ticket đầy đủ (lifecycle)
- Bình luận (public + internal note)
- Lịch sử thay đổi (audit trail)
- Phân loại danh mục & template versioning
- SLA policy tự động
- Rate limiting (Redis)
- Thông báo real-time (Socket.IO + Email + Notification)

---

## 2. Database Schema

### Ticket (`tickets`)
| Cột | Kiểu | Mô tả |
|-----|------|--------|
| id_ticket | UUID, PK | ID ticket |
| title | String(255) | Tiêu đề |
| custom_fields | JSON | Trường tùy chỉnh theo template |
| status | String(50) | Trạng thái (default: "New") |
| severity | String(50) | Mức độ nghiêm trọng |
| resolution_note | Text | Ghi chú giải quyết |
| version | Integer | Optimistic locking |
| expired_date | DateTime | Ngày hết hạn SLA |
| id_employee | UUID, FK | Nhân viên được gán |
| id_customer | UUID, FK | Khách hàng tạo |
| id_template | UUID, FK | Template sử dụng |
| template_version | Integer | Phiên bản template |
| is_deleted / deleted_at | Boolean / DateTime | Soft delete |
| survey_sent | Boolean | Đã gửi khảo sát CSAT |
| resolved_at | DateTime | Thời điểm giải quyết |

### TicketCategory (`tickets_category`)
| Cột | Kiểu | Mô tả |
|-----|------|--------|
| id_category | UUID, PK | ID danh mục |
| name | String(100) | Tên |
| description | Text | Mô tả |
| is_active | Boolean | Đang hoạt động |
| id_department | UUID, FK | Phòng ban phụ trách |
| auto_assign | Boolean | Tự động phân công |

### TicketTemplate (`ticket_templates`)
| Cột | Kiểu | Mô tả |
|-----|------|--------|
| id_template | UUID, PK | ID template |
| version | Integer, PK | Phiên bản (composite PK) |
| name | String(100) | Tên |
| fields_config | JSON | Cấu hình form fields |
| id_author | UUID, FK | Người tạo |
| id_category | UUID, FK | Danh mục |
| is_active / is_deleted | Boolean | Trạng thái |

### TicketHistory (`ticket_history`)
| Cột | Kiểu | Mô tả |
|-----|------|--------|
| id_history | UUID, PK | ID |
| id_ticket | UUID, FK | Ticket |
| id_actor | UUID, FK | Người thực hiện |
| actor_type | String(20) | customer/employee/system |
| action | String(50) | Loại hành động |
| old_value / new_value | JSON | Giá trị cũ/mới |

### TicketComment (`ticket_comments`)
| Cột | Kiểu | Mô tả |
|-----|------|--------|
| id_comment | UUID, PK | ID |
| id_ticket | UUID, FK | Ticket |
| id_author | UUID, FK | Tác giả |
| author_type | String(20) | customer/employee |
| content | Text | Nội dung |
| is_internal | Boolean | Ghi chú nội bộ (chỉ employee thấy) |

---

## 3. API Endpoints

### Tickets (`/api/v1/tickets`)

| Method | Path | Quyền | Mô tả |
|--------|------|-------|--------|
| POST | `/tickets/from-template` | Customer | Tạo ticket từ template |
| GET | `/tickets/user` | Customer | Ticket của customer (không Closed) |
| GET | `/tickets/user/closed` | Customer | Ticket đã đóng |
| GET | `/tickets/unassigned` | Employee | Ticket chưa gán |
| GET | `/tickets/department/{dept_id}` | Employee | Ticket theo phòng ban |
| GET | `/tickets/employee-tickets` | Employee | Ticket được gán cho mình |
| GET | `/tickets/employee-tickets/closed` | Employee | Ticket đã đóng của mình |
| GET | `/tickets/all` | Employee | Tất cả ticket |
| GET | `/tickets/{ticket_id}` | User | Chi tiết ticket |
| PATCH | `/tickets/{ticket_id}/customer-update` | Customer | Cập nhật (chỉ khi New) |
| PATCH | `/tickets/{ticket_id}` | Employee | Cập nhật status/severity |
| DELETE | `/tickets/{ticket_id}` | Employee | Soft delete |
| POST | `/tickets/{ticket_id}/assign` | Employee | Gán nhân viên |
| POST | `/tickets/{ticket_id}/resolve` | Employee | Giải quyết |
| POST | `/tickets/{ticket_id}/close` | Customer | Đóng (từ Resolved) |
| POST | `/tickets/{ticket_id}/reopen` | Customer | Mở lại (từ Closed) |
| GET | `/tickets/manager/department/{dept_id}` | Manager | Xem ticket phòng ban |
| POST | `/tickets/manager/assign/{ticket_id}` | Manager | Gán ticket |

### History (`/api/v1/tickets/{ticket_id}/history`)

| Method | Path | Quyền | Mô tả |
|--------|------|-------|--------|
| GET | `/tickets/{ticket_id}/history` | User | Xem lịch sử ticket |

### Comments (`/api/v1/tickets/{ticket_id}/comments`)

| Method | Path | Quyền | Mô tả |
|--------|------|-------|--------|
| POST | `/tickets/{ticket_id}/comments` | User | Tạo comment |
| GET | `/tickets/{ticket_id}/comments` | User | Lấy comments |
| PATCH | `/tickets/{ticket_id}/comments/{id}` | Author | Sửa comment |
| DELETE | `/tickets/{ticket_id}/comments/{id}` | Author/Admin | Xóa comment |

### Categories (`/api/v1/ticket-categories`)

| Method | Path | Quyền | Mô tả |
|--------|------|-------|--------|
| GET | `/ticket-categories` | User | Danh sách (mặc định active) |
| POST | `/ticket-categories` | Employee | Tạo mới |
| GET | `/ticket-categories/{id}` | User | Chi tiết |
| GET | `/ticket-categories/{id}/templates` | User | Templates của category |
| PATCH | `/ticket-categories/{id}` | Employee | Cập nhật |
| DELETE | `/ticket-categories/{id}` | Admin | Xóa |

### Templates (`/api/v1/templates`)

| Method | Path | Quyền | Mô tả |
|--------|------|-------|--------|
| GET | `/templates` | User | Tất cả (latest version) |
| GET | `/templates/category/{id}` | User | Theo danh mục |
| GET | `/templates/{id}` | User | Chi tiết (có thể chỉ định version) |
| GET | `/templates/{id}/versions` | User | Tất cả versions |
| POST | `/templates` | Employee | Tạo mới |
| PATCH | `/templates/{id}` | Employee | Cập nhật (thay đổi fields → version mới) |
| DELETE | `/templates/{id}` | Admin | Soft delete |
| POST | `/templates/{id}/activate` | Admin | Kích hoạt lại |

---

## 4. Vòng đời Ticket (Lifecycle)

```
[Customer tạo từ template]
         │
         ▼
       NEW ──────────────────────────────┐
         │                                │
         │ (Employee assign)              │
         ▼                                │
    IN PROGRESS                           │
         │                                │
         ├── PENDING (chờ thông tin)      │
         ├── ON HOLD (tạm giữ)           │
         │                                │
         ▼                                │
     RESOLVED ◄───────────────────────────┘
         │
         │ (Customer close)
         ▼
      CLOSED
         │
         │ (Customer reopen + lý do)
         ▼
    IN PROGRESS (nếu có employee) / NEW (nếu chưa gán)
```

---

## 5. Service Layer

### TicketService
- **Tạo ticket**: Validate template active → rate limit (Redis) → tính expired_date từ SLA → tạo ticket → notify phòng ban
- **Customer update**: Chỉ khi status=New, validate custom_fields theo template version
- **Assign**: Gán nhân viên → email notification + Socket.IO broadcast
- **Resolve**: Validate transition → set resolved_at → trigger CSAT survey
- **Close**: Chỉ từ Resolved
- **Reopen**: Chỉ từ Closed, yêu cầu lý do

### TicketHistoryService
- Ghi log mọi thay đổi: tạo, đổi status, gán/bỏ gán, resolve, close, reopen
- Lưu old_value/new_value dạng JSON

### TicketCommentService
- Employee tạo được internal note
- Customer chỉ thấy non-internal comments
- Notification khi comment mới

### TicketTemplateService
- **Versioning**: Thay đổi fields_config → tạo version mới (version cũ deactivate)
- **19 loại field**: text, textarea, email, phone, number, url, date, time, datetime, select, select_multi, radio, checkbox, checkbox_group, file, file_multi, rating, rich_text, hidden, readonly, info

---

## 6. Tính năng bổ sung

- **Optimistic Locking**: `version_id_col` tránh conflict cập nhật đồng thời
- **Rate Limiting**: Redis-based, giới hạn số ticket tạo/thời gian
- **SLA tự động**: Tính expired_date theo severity + SLA policy, tính lại khi đổi severity
- **Bulk Operations**: Repository hỗ trợ update status, assign, delete hàng loạt
- **Chatbot Cache Invalidation**: Thay đổi category/template → invalidate chatbot cache
