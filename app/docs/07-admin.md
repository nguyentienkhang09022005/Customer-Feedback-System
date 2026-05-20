# Admin Management

## 1. Tổng quan

Module Admin cung cấp chức năng quản trị hệ thống (yêu cầu quyền Admin):
- Quản lý người dùng (status, reset password)
- Quản lý ticket hàng loạt (bulk operations)
- Quản lý tag/nhãn
- Cấu hình hệ thống
- Báo cáo workload
- Quy tắc leo thang (escalation rules)
- Ghi nhật ký kiểm toán (audit log)

---

## 2. Database Schema

### Tag (`tags`)
| Cột | Kiểu | Mô tả |
|-----|------|--------|
| id_tag | String(36), PK | UUID |
| name | String(100), UNIQUE | Tên tag |
| color | String(7) | Mã màu hex (default "#000000") |
| description | Text | Mô tả |

Quan hệ many-to-many với Ticket qua bảng `ticket_tags`.

### SystemSettings (`system_settings`)
| Cột | Kiểu | Mô tả |
|-----|------|--------|
| id | String(36), PK | "default" |
| company_name | String(255) | Tên công ty |
| company_logo | String(500) | URL logo |
| support_email | String(255) | Email hỗ trợ |
| support_phone | String(50) | SĐT hỗ trợ |
| maintenance_mode | Boolean | Chế độ bảo trì |
| allow_customer_registration | Boolean | Cho phép đăng ký |
| default_customer_type | String(50) | Loại KH mặc định |

### EscalationRule (`escalation_rules`)
| Cột | Kiểu | Mô tả |
|-----|------|--------|
| id | String(36), PK | UUID |
| name | String(255) | Tên quy tắc |
| priority | String(50) | Mức ưu tiên |
| condition_type | String(50) | time_elapsed / priority / category |
| condition_value | String(255) | VD: "4h", "high", "billing" |
| action_type | String(50) | reassign / notify / escalate |
| action_target | String(255) | department_id / email / manager_id |
| is_active | Boolean | Kích hoạt |

---

## 3. API Endpoints

### User Management (`/api/v1/admin/users`)

| Method | Path | Mô tả |
|--------|------|--------|
| POST | `/admin/users/status` | Cập nhật trạng thái user |
| POST | `/admin/users/reset-password` | Reset mật khẩu user |

### Ticket Bulk (`/api/v1/admin/tickets`)

| Method | Path | Mô tả |
|--------|------|--------|
| POST | `/admin/tickets/bulk-status` | Cập nhật status hàng loạt |
| POST | `/admin/tickets/bulk-assign` | Gán nhân viên hàng loạt |
| POST | `/admin/tickets/bulk-delete` | Xóa hàng loạt |

### Tags (`/api/v1/admin/tags`)

| Method | Path | Mô tả |
|--------|------|--------|
| GET | `/admin/tags` | Tất cả tags |
| POST | `/admin/tags` | Tạo tag |
| GET | `/admin/tags/{id}` | Chi tiết tag |
| PUT | `/admin/tags/{id}` | Cập nhật tag |
| DELETE | `/admin/tags/{id}` | Xóa tag |

### Settings (`/api/v1/admin/settings`)

| Method | Path | Mô tả |
|--------|------|--------|
| GET | `/admin/settings` | Lấy cấu hình |
| PUT | `/admin/settings` | Cập nhật cấu hình |

### Reports (`/api/v1/admin/reports`)

| Method | Path | Mô tả |
|--------|------|--------|
| GET | `/admin/reports/workload` | Workload toàn hệ thống |
| GET | `/admin/reports/workload/departments` | Workload theo phòng ban |

### Escalation Rules (`/api/v1/admin/escalation-rules`)

| Method | Path | Mô tả |
|--------|------|--------|
| GET | `/admin/escalation-rules` | Tất cả quy tắc |
| POST | `/admin/escalation-rules` | Tạo quy tắc |
| GET | `/admin/escalation-rules/{id}` | Chi tiết |
| PUT | `/admin/escalation-rules/{id}` | Cập nhật |
| DELETE | `/admin/escalation-rules/{id}` | Xóa |
| PATCH | `/admin/escalation-rules/{id}/toggle` | Bật/tắt |

### Audit Logs (`/api/v1/audit-logs`)

| Method | Path | Mô tả |
|--------|------|--------|
| GET | `/audit-logs` | Danh sách log (phân trang, lọc log_type) |
| GET | `/audit-logs/export` | Xuất CSV |
| GET | `/audit-logs/{reference_id}` | Log theo entity ID |

---

## 4. Service Layer

### UserAdminService
- `update_user_status`: Validate status → tìm user (employee/customer) → cập nhật
- `reset_password`: Validate min 6 ký tự → hash → cập nhật

### BulkTicketService
- `bulk_update_status`: Validate status hợp lệ → cập nhật hàng loạt
- `bulk_assign`: Gán danh sách ticket cho 1 employee
- `bulk_delete`: Xóa hàng loạt
- Trả về số lượng đã xử lý

### TagService
- CRUD với validation tên không trùng
- Partial update (exclude_unset)

### SystemSettingsService
- Singleton (ID="default"), tự tạo nếu chưa tồn tại
- Partial update

### EscalationRuleService
- CRUD + toggle (đảo is_active)
- `get_active_rules`: Chỉ lấy rules đang kích hoạt

### WorkloadReportService
- `get_system_wide_workload`: Mỗi NV → open_tickets, max_capacity, utilization_percent, csat_score
- `get_department_summary`: Mỗi dept (active) → members, total_capacity, total_load, utilization

### AuditLogService
- `log_action`: Ghi log_type, action, old_data/new_data, id_reference, id_employee
- `get_all_logs`: Phân trang, lọc log_type, sắp xếp mới nhất
- `export_to_csv`: Xuất list[dict]

---

## 5. Escalation Rules

### Cấu hình
- **condition_type**: time_elapsed, priority, category
- **action_type**: reassign, notify, escalate

### Xử lý tự động (EscalationService)
- `escalate_to_manager`: Tìm manager dept → gửi notification
- `auto_escalate_overdue_tickets`: Chạy định kỳ, tìm ticket quá hạn (status: New, In Progress, Pending, On Hold) → escalate lên manager

---

## 6. Workload Reports

### Toàn hệ thống
```json
{
  "employees": [
    {"id", "name", "department", "job_title", "open_tickets", "max_capacity", "utilization_percent", "csat_score"}
  ],
  "summary": {"total_employees", "total_open_tickets", "system_utilization_percent"}
}
```

### Theo phòng ban
```json
{
  "departments": [
    {"id", "name", "member_count", "total_capacity", "total_load", "utilization_percent"}
  ]
}
```
