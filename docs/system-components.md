# Tài liệu giải thích các thành phần hệ thống Customer Feedback System

## Mục lục
1. [Ticket Comment](#1-ticket-comment)
2. [Ticket History](#2-ticket-history)
3. [Audit Logs](#3-audit-logs)
4. [Customer Type](#4-customer-type)

---

## 1. Ticket Comment

### Mục đích
Cho phép **nhân viên (employee)** và **khách hàng (customer)** trao đổi, bình luận trên ticket để giải quyết vấn đề.

### Cấu trúc dữ liệu (`TicketComment` model)

| Field | Type | Mô tả |
|-------|------|--------|
| `id_comment` | UUID | Primary key |
| `id_ticket` | UUID | Foreign key đến ticket |
| `id_author` | UUID | ID của người viết comment |
| `author_type` | String | "employee" hoặc "customer" |
| `content` | Text | Nội dung bình luận |
| `is_internal` | Boolean | `True` = ghi chú nội bộ (chỉ employee thấy) |
| `created_at` | DateTime | Thời gian tạo |
| `updated_at` | DateTime | Thời gian sửa |

### Các chức năng chính (`TicketCommentService`)

#### 1.1. Tạo Comment (`create_comment`)
```python
def create_comment(ticket_id, data, author_id, author_type) -> TicketComment
```
- **Input**: ticket_id, nội dung comment, id người viết, loại người viết
- **Kiểm tra**:
  - Ticket tồn tại
  - Nếu `is_internal=True`, chỉ employee mới được tạo (customer không được tạo ghi chú nội bộ)
- **Side effect**: Gửi notification cho bên liên quan

#### 1.2. Lấy Comments (`get_comments`)
```python
def get_comments(ticket_id, is_employee=False) -> List[TicketComment]
```
- **Logic phân quyền xem**:
  - Employee: thấy **tất cả** comments (kể cả `is_internal=True`)
  - Customer: chỉ thấy comments có `is_internal=False`
- Trả về danh sách comments của ticket

#### 1.3. Cập nhật Comment (`update_comment`)
```python
def update_comment(comment_id, data, user_id) -> TicketComment
```
- **Ràng buộc**: Chỉ **author** (người tạo) mới được sửa comment của mình
- Không cho phép sửa `is_internal` sau khi tạo

#### 1.4. Xóa Comment (`delete_comment`)
```python
def delete_comment(comment_id, user_id, is_admin=False)
```
- **Ràng buộc**: 
  - Author có thể xóa comment của mình
  - Admin có thể xóa bất kỳ comment nào

### Logic Notification khi có Comment mới

| Người tạo | Người nhận notification |
|-----------|-------------------------|
| Customer | Employee được assign trên ticket |
| Employee | Customer sở hữu ticket |

```python
# Ví dụ: Customer comment → notify Employee
Notification(
    title="Bình luận mới từ khách hàng",
    content="Khách hàng bình luận trên ticket #xxx: nội dung...",
    notification_type="NEW_COMMENT",
    id_receiver=ticket.id_employee
)
```

### API Endpoints

| Method | Endpoint | Mô tả | Ai được phép |
|--------|----------|--------|--------------|
| `POST` | `/api/v1/tickets/{ticket_id}/comments` | Tạo comment | Employee, Customer |
| `GET` | `/api/v1/tickets/{ticket_id}/comments` | Lấy comments | Employee, Customer |
| `PATCH` | `/api/v1/tickets/{ticket_id}/comments/{comment_id}` | Sửa comment | Author (hoặc Admin) |
| `DELETE` | `/api/v1/tickets/{ticket_id}/comments/{comment_id}` | Xóa comment | Author (hoặc Admin) |

### Ví dụ sử dụng thực tế

1. **Customer hỏi về ticket**: Tạo comment thường (`is_internal=False`)
2. **Employee trả lời**: Tạo comment thường (`is_internal=False`)
3. **Employee ghi chú nội bộ**: Tạo comment với `is_internal=True` (VD: "Đã liên hệ kỹ thuật support")
4. **Customer không thấy**: Các ghi chú nội bộ của employee

---

## 2. Ticket History

### Mục đích
Ghi lại **toàn bộ lịch sử thay đổi** của một ticket, phục vụ:
- **Audit trail**: Theo dõi ai làm gì, khi nào
- **Transparency**: Customer và Employee có thể xem lại lịch sử ticket
- **Troubleshooting**: Debug khi có vấn đề xảy ra

### Cấu trúc dữ liệu (`TicketHistory` model)

| Field | Type | Mô tả |
|-------|------|--------|
| `id_history` | UUID | Primary key |
| `id_ticket` | UUID | Foreign key đến ticket |
| `id_actor` | UUID | ID người thực hiện |
| `actor_type` | String | "employee", "customer", "system" |
| `action` | Enum | Loại hành động |
| `old_value` | JSON | Giá trị trước thay đổi |
| `new_value` | JSON | Giá trị sau thay đổi |
| `note` | Text | Ghi chú bổ sung |
| `created_at` | DateTime | Thời gian thực hiện |

### Các loại Action được log

| Action | Mô tả | old_value | new_value |
|--------|--------|-----------|-----------|
| `CREATED` | Ticket được tạo | null | {title, description, severity, category} |
| `STATUS_CHANGED` | Thay đổi trạng thái | {status: "New"} | {status: "In Progress"} |
| `ASSIGNED` | Được phân công | {id_employee: null} | {id_employee: "..."} |
| `UNASSIGNED` | Bỏ phân công | {id_employee: "..."} | {id_employee: null} |
| `CATEGORY_CHANGED` | Đổi danh mục | {id_category: "..."} | {id_category: "..."} |
| `SEVERITY_CHANGED` | Đổi mức độ nghiêm trọng | {severity: "Low"} | {severity: "High"} |
| `RESOLVED` | Ticket được giải quyết | null | {status: "Resolved"} |
| `CLOSED` | Ticket được đóng | null | {status: "Closed"} |
| `REOPENED` | Ticket được mở lại | {status: "Closed"} | {status: "In Progress"} |

### Các phương thức log (`TicketHistoryService`)

| Method | Log khi nào |
|--------|--------------|
| `log_ticket_created()` | Tạo ticket mới |
| `log_status_change()` | Chuyển trạng thái |
| `log_assignment()` | Phân công/Bỏ phân công |
| `log_category_change()` | Đổi danh mục |
| `log_severity_change()` | Đổi mức độ |
| `log_resolution()` | Resolve ticket |
| `log_closure()` | Close ticket |
| `log_reopen()` | Reopen ticket |

### Ví dụ log entry

```json
{
  "id_history": "uuid-xxx",
  "id_ticket": "uuid-ticket-123",
  "actor_type": "employee",
  "actor_name": "Nguyễn Văn A",
  "action": "STATUS_CHANGED",
  "old_value": {"status": "New"},
  "new_value": {"status": "In Progress"},
  "note": null,
  "created_at": "2024-01-15T10:30:00Z"
}
```

### Được sử dụng khi nào

Trong `ticketService.py`:
```python
# Khi resolve ticket
history_service.log_resolution(ticket, resolution_note, actor_id, actor_type)

# Khi close ticket
history_service.log_closure(ticket, reason, actor_id, actor_type)

# Khi reopen ticket
history_service.log_reopen(ticket, reason, actor_id, actor_type)
```

---

## 3. Audit Logs

### Mục đích
Ghi lại **tất cả thay đổi trên toàn hệ thống** (system-wide), khác với Ticket History chỉ log trên ticket. Dùng cho:
- **Compliance**: Đáp ứng yêu cầu pháp lý, kiểm toán
- **Security Monitoring**: Theo dõi hành vi đáng nghi ngờ
- **Debugging**: Tra cứu khi có sự cố
- **User Activity Tracking**: Theo dõi hoạt động của user

### Cấu trúc dữ liệu (`AuditLog` model)

| Field | Type | Mô tả |
|-------|------|--------|
| `id_log` | UUID | Primary key |
| `log_type` | String(50) | Loại log (VD: "CHAT", "FAQ", "TICKET") |
| `action` | String(255) | Hành động cụ thể (VD: "MESSAGE_SENT", "CREATED") |
| `old_value` | Text | JSON data trước thay đổi |
| `new_value` | Text | JSON data sau thay đổi |
| `id_reference` | UUID | ID của entity bị thay đổi |
| `id_employee` | UUID | Ai thực hiện thay đổi (Foreign key đến employees) |
| `created_at` | DateTime | Thời gian thực hiện |

### Sự khác biệt với Ticket History

| Khía cạnh | Ticket History | Audit Log |
|-----------|----------------|-----------|
| **Phạm vi** | Chỉ ticket | Toàn hệ thống |
| **Đối tượng xem** | Customer, Employee | Chỉ Admin |
| **Dữ liệu** | Field changes của ticket | Tất cả CRUD operations |
| **Use case** | Xem lại ticket | Compliance, Security |

### API Endpoints

| Method | Endpoint | Mô tả | Ai được phép |
|--------|----------|--------|--------------|
| `GET` | `/api/v1/audit-logs` | Lấy tất cả logs (phân trang) | Admin |
| `GET` | `/api/v1/audit-logs/{reference_id}` | Lấy logs của một entity cụ thể | Admin |

### Ví dụ sử dụng

```python
# Trong chatService.py
self.audit_service.log_action(
    log_type="CHAT",
    action="MESSAGE_SENT",
    old_data=None,
    new_data={"message": "Xin chào, tôi cần hỗ trợ"},
    id_reference=chat_id,
    id_employee=employee_id
)

# Trong FAQ service
self.audit_service.log_action(
    log_type="FAQ",
    action="ARTICLE_PUBLISHED",
    old_data={"is_published": False},
    new_data={"is_published": True},
    id_reference=article_id,
    id_employee=admin_id
)
```

### Ví dụ log entry

```json
{
  "id_log": "uuid-xxx",
  "log_type": "CHAT",
  "action": "MESSAGE_SENT",
  "old_value": null,
  "new_value": "{\"message\": \"Xin chào\"}",
  "id_reference": "uuid-chat-123",
  "id_employee": "uuid-employee-456",
  "created_at": "2024-01-15T10:30:00Z"
}
```

---

## 4. Customer Type

### Mục đích
**Phân loại khách hàng** (customer) thành các nhóm khác nhau. Đây là bảng lookup/reference data đơn giản.

### Cấu trúc dữ liệu (`CustomerType` model)

| Field | Type | Mô tả |
|-------|------|--------|
| `type_name` | String(50) | **Primary Key** - Tên loại khách hàng |
| `description` | String(255) | Mô tả chi tiết |

### Mối quan hệ

```
┌─────────────────┐         ┌─────────────────┐
│  CustomerType   │ 1 ─── N │    Customer      │
│                 │         │                 │
│ - type_name (PK)│─────────►│ - customer_type  │
│ - description   │         │                 │
└─────────────────┘         └─────────────────┘
```

### Ví dụ dữ liệu

| type_name | description |
|-----------|-------------|
| "VIP" | Khách hàng VIP - ưu tiên cao nhất |
| "Regular" | Khách hàng thường |
| "Enterprise" | Khách hàng doanh nghiệp |
| "Guest" | Khách hàng chưa đăng ký |

### API Endpoints

| Method | Endpoint | Mô tả | Ai được phép |
|--------|----------|--------|--------------|
| `GET` | `/api/v1/customer-types` | Lấy tất cả loại khách hàng | Tất cả |
| `POST` | `/api/v1/customer-types` | Tạo loại khách hàng mới | Admin |
| `PUT` | `/api/v1/customer-types/{type_name}` | Cập nhật loại khách hàng | Admin |
| `DELETE` | `/api/v1/customer-types/{type_name}` | Xóa loại khách hàng | Admin |

### Các phương thức (`CustomerTypeService`)

| Method | Mô tả |
|--------|--------|
| `get_all()` | Lấy tất cả customer types |
| `get_by_name(type_name)` | Lấy một customer type theo tên |
| `create(data)` | Tạo customer type mới |
| `update(type_name, data)` | Cập nhật description |
| `delete(type_name)` | Xóa customer type |

### Vai trò trong hệ thống

**Hiện tại**: Chỉ là metadata đơn giản, chưa có logic nghiệp vụ phức tạp dựa trên customer type.

**Trong tương lai** có thể dùng để:
- **SLA khác nhau**: VIP customer có SLA 1 giờ, Regular có SLA 24 giờ
- **Priority Routing**: Ticket của VIP được ưu tiên xử lý trước
- **Auto-assignment**: VIP được assign cho senior employee
- **Reporting**: Báo cáo doanh thu/theo dõi theo từng customer type
- **Pricing/Discount**: Áp dụng chính sách giá khác nhau

---

## Tổng kết so sánh

| Thành phần | Phạm vi | Mục đích chính | Ai xem được |
|------------|---------|----------------|-------------|
| **Ticket Comment** | Ticket | Trao đổi giữa customer và employee | Customer (chỉ public), Employee (tất cả) |
| **Ticket History** | Ticket | Lịch sử thay đổi ticket | Customer, Employee |
| **Audit Log** | System-wide | Compliance, Security, Debugging | Admin only |
| **Customer Type** | Reference | Phân loại customer | Tất cả (chỉ xem) |
