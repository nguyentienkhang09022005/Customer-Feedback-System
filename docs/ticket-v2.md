# Ticket V2 - Phân quyền Update và Template Versioning

## Tổng quan

Document này mô tả logic **V2** của hệ thống Ticket, tập trung vào:
1. **Phân quyền update**: Customer và Employee có quyền hạn khác nhau
2. **Template Versioning**: Đảm bảo tickets đang dùng template version cũ không bị ảnh hưởng khi template được nâng cấp

---

## Phân quyền Update Ticket

### Nguyên tắc

| Actor | Quyền update | Giới hạn |
|-------|--------------|----------|
| **Customer** | Update `title`, `custom_fields` | Chỉ khi `status = "New"` |
| **Employee** | Update `status`, `severity` | Không được sửa `title`, `custom_fields` |
| **Customer** | Close, Reopen ticket | Đã có sẵn |

### Luồng Customer Update

```
Customer gọi PATCH /api/v1/tickets/{ticket_id}/customer-update
    ↓
Kiểm tra ticket.status == "New"? → Không → Reject 400
    ↓
Kiểm tra ticket.id_customer == customer_id? → Không → Reject 403
    ↓
Validate custom_fields theo template version của ticket
    ↓
Update title và/hoặc custom_fields
```

### Luồng Employee Update

```
Employee gọi PATCH /api/v1/tickets/{ticket_id}
    ↓
Kiểm tra actor_type == "employee"
    ↓
Nếu có title hoặc custom_fields trong request → Reject 403
    ↓
Chỉ cho phép update status, severity
```

---

## Template Versioning

### Nguyên tắc

- **Composite Primary Key**: `(id_template, version)` - mỗi version là 1 row riêng biệt
- **Khi update `fields_config`**: Tạo row mới với version tăng lên 1, old version set `is_active = false`
- **Ticket lưu template_version**: Mỗi ticket lưu `id_template` và `template_version` để reference đúng version đã dùng

### Ví dụ

1. **Tạo template mới** → Version 1, `is_active = true`
2. **Cập nhật fields_config** → Version 2 được tạo, Version 1 set `is_active = false`
3. **Customer tạo ticket** → Dùng Version 2 (latest active)
4. **Cập nhật fields_config lần nữa** → Version 3 được tạo, Version 2 set `is_active = false`

### Isolation

- Tickets đang dùng Version 1 → Vẫn hoạt động bình thường, update không bị ảnh hưởng bởi Version 2, 3
- Tickets đang dùng Version 2 → Vẫn hoạt động bình thường, update không bị ảnh hưởng bởi Version 3
- Tickets đang dùng Version 3 → Dùng fields_config mới nhất

---

## Validate Custom Fields Theo Template Version

### Nguyên tắc

Khi customer update ticket:
- Lấy template version mà ticket đang dùng (`ticket.template_version`)
- Validate `custom_fields` theo `fields_config` của version đó
- KHÔNG dùng latest version của template

### Ví dụ

**Template v1** có fields:
```json
{
  "fields": [
    {"name": "full_name", "type": "text", "required": true},
    {"name": "phone", "type": "text", "required": false}
  ]
}
```

**Template v2** có fields:
```json
{
  "fields": [
    {"name": "full_name", "type": "text", "required": true},
    {"name": "phone", "type": "text", "required": false},
    {"name": "email", "type": "email", "required": true}
  ]
}
```

**Ticket A** dùng v1, **Ticket B** dùng v2:
- Customer update Ticket A → KHÔNG bắt buộc填 `email` (vì đang dùng v1)
- Customer update Ticket B → BẮT BUỘC填 `email` (vì đang dùng v2)

---

## API Endpoints Mới

### Customer Update

```
PATCH /api/v1/tickets/{ticket_id}/customer-update
Authorization: Customer token
Content-Type: application/json

Body:
{
  "title": "Tiêu đề mới",        // optional
  "custom_fields": {              // optional
    "full_name": "Nguyễn Văn B",
    "phone": "0909123456"
  }
}

Responses:
- 200: Success
- 400: "Chỉ được cập nhật khi ticket còn ở trạng thái New!"
- 403: "Bạn không có quyền cập nhật ticket này!"
- 400: "Thiếu field bắt buộc: {field_name}"
```

### Employee Update (sửa đổi)

```
PATCH /api/v1/tickets/{ticket_id}
Authorization: Employee token
Content-Type: application/json

Body:
{
  "status": "In Progress",        // allowed
  "severity": "High"              // allowed
}

Responses:
- 200: Success
- 403: "Employee chỉ được cập nhật trạng thái ticket!"
- 400: Invalid status transition
```

---

## Data Model Changes

### Ticket Schema (ticketSchema.py)

Thêm `TicketCustomerUpdate`:
```python
class TicketCustomerUpdate(BaseModel):
    title: Optional[str] = None
    custom_fields: Optional[dict] = None
```

### TicketService (ticketService.py)

Thêm methods:
```python
def update_ticket_customer(self, ticket_id, data: TicketCustomerUpdate, customer_id) -> Ticket:
    # 1. Validate ticket tồn tại và chưa bị xóa
    # 2. Validate status == "New"
    # 3. Validate customer sở hữu ticket
    # 4. Validate custom_fields theo template version
    # 5. Update title và/hoặc custom_fields

def _validate_custom_fields_by_template_version(self, custom_fields, id_template, template_version):
    # 1. Lấy template version
    # 2. Extract required fields từ fields_config
    # 3. Validate custom_fields chứa đủ required fields
```

Sửa `update_ticket()` thêm `actor_type` param:
```python
def update_ticket(self, ticket_id, data, actor_id=None, actor_type=None):
    # Nếu actor_type == "employee" và có title/custom_fields → Reject 403
```

---

## Flow Diagram

### Customer Update Flow

```
┌─────────────────────────────────────────────────────────────┐
│                 Customer Update Ticket                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ ticket_id có    │
                    │ tồn tại không? │
                    └────────┬────────┘
                             │ Không → 404
                             │ Có
                             ▼
                    ┌─────────────────┐
                    │ ticket đã bị    │
                    │ xóa chưa?      │
                    └────────┬────────┘
                             │ Rồi → 400
                             │ Chưa
                             ▼
                    ┌─────────────────┐
                    │ ticket.status   │
                    │ == "New" ?     │
                    └────────┬────────┘
                             │ Không → 400 "Chỉ được cập nhật..."
                             │ Có
                             ▼
                    ┌─────────────────┐
                    │ Customer sở    │
                    │ hữu ticket?    │
                    └────────┬────────┘
                             │ Không → 403
                             │ Có
                             ▼
              ┌──────────────────────────────┐
              │ validate custom_fields theo   │
              │ ticket.template_version      │
              └──────────────┬───────────────┘
                             │ Không đủ required → 400
                             │ Đủ
                             ▼
                    ┌─────────────────┐
                    │ Update title    │
                    │ và/hoặc         │
                    │ custom_fields   │
                    └────────┬────────┘
                             │
                             ▼
                          200 OK
```

### Employee Update Flow

```
┌─────────────────────────────────────────────────────────────┐
│                 Employee Update Ticket                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ ticket_id có    │
                    │ tồn tại không? │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Có title hoặc   │
                    │ custom_fields?  │
                    └────────┬────────┘
                             │ Có → 403 "Employee chỉ được..."
                             │ Không
                             ▼
                    ┌─────────────────┐
                    │ Validate status │
                    │ transition      │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Update status   │
                    │ và/hoặc severity│
                    └────────┬────────┘
                             │
                             ▼
                          200 OK
```

---

## Status Transition Matrix

| Current Status | Allowed Next Status (Employee) | Customer Can Update? |
|----------------|-------------------------------|---------------------|
| `New` | In Progress, Pending, On Hold | ✅ Yes |
| `In Progress` | Resolved, Pending, On Hold | ❌ No |
| `Pending` | In Progress, Resolved, On Hold | ❌ No |
| `On Hold` | In Progress, Resolved | ❌ No |
| `Resolved` | Closed | ❌ No (chỉ close/reopen) |
| `Closed` | Reopen | ❌ No (chỉ reopen) |

---

## Error Messages

| Code | Message | Giải thích |
|------|---------|------------|
| 400 | "Không tìm thấy ticket!" | Ticket không tồn tại |
| 400 | "Ticket đã bị xóa!" | Ticket đã soft delete |
| 400 | "Chỉ được cập nhật khi ticket còn ở trạng thái New!" | Customer update khi status != New |
| 403 | "Bạn không có quyền cập nhật ticket này!" | Customer không sở hữu ticket |
| 403 | "Employee chỉ được cập nhật trạng thái ticket!" | Employee cố sửa title/custom_fields |
| 400 | "Thiếu field bắt buộc: {field_name}" | custom_fields thiếu required field |
| 404 | "Template version không tồn tại!" | Template version đã bị xóa |
| 400 | "Không thể chuyển từ '{status}' sang '{new_status}'" | Invalid status transition |

---

## Example Scenarios

### Scenario 1: Customer update thành công

```
1. Customer tạo ticket từ template v1 (status = "New")
2. Customer gọi PATCH /tickets/{id}/customer-update với title = "Mới"
3. Hệ thống kiểm tra:
   - ticket.status == "New" ✅
   - ticket.id_customer == customer_id ✅
   - custom_fields valid theo template v1 ✅
4. Update thành công → 200 OK
```

### Scenario 2: Customer update thất bại - status không phải New

```
1. Ticket đang có status = "In Progress"
2. Customer gọi PATCH /tickets/{id}/customer-update
3. Hệ thống kiểm tra:
   - ticket.status == "New" ❌ → "Chỉ được cập nhật khi ticket còn ở trạng thái New!"
4. Return 400
```

### Scenario 3: Template nâng cấp, ticket cũ update bình thường

```
1. Template v1 có fields: [full_name, phone]
2. Ticket A được tạo từ v1 (template_version = 1)
3. Admin nâng cấp template → v2 thêm field: [full_name, phone, email]
4. Customer update Ticket A:
   - Hệ thống lấy template v1 (id_template, version=1)
   - Validate custom_fields theo v1 fields_config
   - KHÔNG bắt buộc填 email vì ticket đang dùng v1
   - Update thành công
```

### Scenario 4: Employee cố sửa title

```
1. Employee gọi PATCH /tickets/{id} với body: {"title": "New Title"}
2. Hệ thống kiểm tra actor_type == "employee"
3. Phát hiện có "title" trong request → Reject 403
4. Return: "Employee chỉ được cập nhật trạng thái ticket!"
```