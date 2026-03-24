# Ticket System Documentation

## Overview

Hệ thống Ticket cho phép customers tạo tickets với categories, employees có thể xem và assign tickets theo department, và tính năng auto-assignment với load balancing.

---

## Database Schema

### TicketCategory Table (Modified)

| Column | Type | Description |
|--------|------|-------------|
| `id_category` | UUID | Primary key |
| `name` | String(100) | Tên category |
| `description` | Text | Mô tả |
| `is_active` | Boolean | Category có đang hoạt động không |
| `department` | String(50) | Department mà category này thuộc về |
| `auto_assign` | Boolean | Tự động assign ticket cho employee (default: TRUE) |
| `created_at` | DateTime | Thời gian tạo |

### Ticket Table (Existing)

| Column | Type | Description |
|--------|------|-------------|
| `id_ticket` | UUID | Primary key |
| `title` | String(255) | Tiêu đề ticket |
| `description` | Text | Nội dung |
| `status` | String(50) | Trạng thái: "New", "In Progress", "Pending", "On Hold", "Resolved", "Closed", "Cancelled" |
| `severity` | String(50) | Mức độ: "Low", "Medium", "High", "Critical" |
| `id_category` | UUID | Foreign key → TicketCategory |
| `id_employee` | UUID | Foreign key → Employee (nullable - chưa assign thì NULL) |
| `id_customer` | UUID | Foreign key → Customer |
| `created_at` | DateTime | Thời gian tạo |
| `updated_at` | DateTime | Thời gian cập nhật cuối |

---

## API Endpoints

### Ticket Management

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/api/v1/tickets` | Customer | Tạo ticket mới |
| `GET` | `/api/v1/tickets` | Any | Lấy danh sách tất cả tickets |
| `GET` | `/api/v1/tickets/{id}` | Any | Lấy ticket theo ID |
| `PATCH` | `/api/v1/tickets/{id}` | Employee | Cập nhật ticket |
| `DELETE` | `/api/v1/tickets/{id}` | Employee | Xóa ticket |

### Ticket Assignment

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/api/v1/tickets/unassigned` | Employee | Lấy tickets chưa được assign |
| `GET` | `/api/v1/tickets/department/{dept}` | Employee | Lấy tickets theo department |
| `GET` | `/api/v1/tickets/my-tickets` | Employee | Lấy tickets của employee hiện tại |
| `POST` | `/api/v1/tickets/assign` | Employee | Manual assign ticket cho employee |

### Ticket Category Management

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/api/v1/ticket-categories` | Employee | Lấy danh sách categories |
| `POST` | `/api/v1/ticket-categories` | Employee | Tạo category mới |
| `PATCH` | `/api/v1/ticket-categories/{id}` | Employee | Cập nhật category |
| `DELETE` | `/api/v1/ticket-categories/{id}` | Employee | Xóa category |

---

## Auto-Assignment Logic

### Khi nào Auto-Assignment xảy ra?

1. **Khi tạo ticket mới** - `POST /api/v1/tickets`
2. **Khi cập nhật ticket và đổi category** - `PATCH /api/v1/tickets/{id}` với `id_category` thay đổi

### Luồng xử lý

```
Customer tạo ticket (chọn category)
    │
    ▼
Service kiểm tra:
1. Category có tồn tại và is_active = True?
    │
    ├── Không → Error: "Không tìm thấy danh mục" hoặc "Danh mục không hoạt động"
    │
    └── Có → Tiếp tục
    │
    ▼
2. Category có auto_assign = True?
    │
    ├── FALSE → Ticket giữ nguyên:
    │           - status = "New"
    │           - id_employee = NULL
    │           → Ticket cần được manual assign
    │
    └── TRUE → Gọi LoadBalancer để tìm best employee
        │
        ▼
    LoadBalancer.get_best_employee_for_department(department)
        │
        ▼
    Thuật toán Load Balancing:
    1. Lấy tất cả ACTIVE employees trong department đó
    2. Sắp xếp theo csat_score giảm dần
    3. Với mỗi employee, đếm active tickets hiện tại
       (status: New, In Progress, Pending, On Hold)
    4. Chọn employee đầu tiên có:
       - current_ticket_count < max_ticket_capacity
       - highest csat_score
    5. Nếu không có employee nào có capacity → return NULL
        │
        ▼
    Có employee được chọn?
        │
        ├── Có → Assign:
        │       - id_employee = employee.id
        │       - status = "In Progress"
        │
        └── Không → Ticket stays unassigned:
                - id_employee = NULL
                - status = "New"
                → Cần manual assign
```

### Load Balancing Algorithm

```python
def get_best_employee_for_department(department):
    # 1. Get all ACTIVE employees in department, ordered by csat_score DESC
    employees = db.query(Employee).filter(
        Employee.department == department,
        Employee.status == "Active"
    ).order_by(Employee.csat_score.desc()).all()
    
    # 2. For each employee, check capacity
    for emp in employees:
        current_count = count_active_tickets(emp.id)
        if current_count < emp.max_ticket_capacity:
            return emp  # Best match: highest csat_score with capacity
    
    return None  # No available employee
```

### Active Ticket Count

Chỉ tính tickets có status:
- `New`
- `In Progress`
- `Pending`
- `On Hold`

**Không tính:** `Resolved`, `Closed`, `Cancelled`

---

## Ví dụ sử dụng

### 1. Tạo Ticket (Auto-Assignment Enabled)

```bash
POST /api/v1/tickets
{
    "title": "Billing Issue",
    "description": "Tôi bị tính sai tiền",
    "severity": "High",
    "id_category": "uuid-của-billing-category"
}
```

**Response (auto_assign=True, có employee available):**
```json
{
    "status": true,
    "code": 201,
    "message": "Tạo ticket thành công",
    "data": {
        "id_ticket": "uuid-ticket",
        "title": "Billing Issue",
        "status": "In Progress",
        "id_employee": "uuid-employee-được-assign",
        "id_category": "uuid-của-billing-category"
    }
}
```

**Response (auto_assign=False hoặc không có employee):**
```json
{
    "status": true,
    "code": 201,
    "message": "Tạo ticket thành công",
    "data": {
        "id_ticket": "uuid-ticket",
        "title": "Billing Issue",
        "status": "New",
        "id_employee": null,
        "id_category": "uuid-của-billing-category"
    }
}
```

### 2. Manual Assign Ticket

```bash
POST /api/v1/tickets/assign
{
    "id_employee": "uuid-employee"
}
```

### 3. Lấy Tickets của Employee hiện tại

```bash
GET /api/v1/tickets/my-tickets
```

### 4. Lấy Tickets chưa được assign

```bash
GET /api/v1/tickets/unassigned
```

### 5. Cập nhật Ticket (đổi category → trigger re-assign)

```bash
PATCH /api/v1/tickets/{id}
{
    "id_category": "uuid-category-mới"
}
```

---

## Cấu hình Category

### Tạo Category với Auto-Assignment

```bash
POST /api/v1/ticket-categories
{
    "name": "Billing",
    "description": "Các vấn đề về thanh toán",
    "department": "Finance",
    "auto_assign": true
}
```

### Tạo Category không có Auto-Assignment

```bash
POST /api/v1/ticket-categories
{
    "name": "VIP Support",
    "description": "Hỗ trợ khách hàng VIP",
    "department": "VIP",
    "auto_assign": false
}
```

---

## Các File đã thay đổi/thêm mới

### Models
- `app/models/ticket.py` - Thêm `department` và `auto_assign` vào TicketCategory

### Schemas
- `app/schemas/ticketCategorySchema.py` - Thêm department, auto_assign
- `app/schemas/ticketSchema.py` - **NEW** - TicketCreate, TicketOut, etc.

### Repositories
- `app/repositories/ticketCategoryRepository.py` - Thêm get_by_department()
- `app/repositories/ticketRepository.py` - **NEW** - CRUD + queries
- `app/repositories/employeeRepository.py` - Thêm load balancing queries

### Services
- `app/services/loadBalancer.py` - **NEW** - Load balancing algorithm
- `app/services/ticketService.py` - **NEW** - Auto-assignment business logic

### API
- `app/api/v1/tickets.py` - **NEW** - 9 endpoints
- `main.py` - Đăng ký tickets router

### Database
- `migrations/versions/c8ef65d838e9_...py` - Migration thêm columns

### Tests
- `tests/test_load_balancer.py` - 4 unit tests
- `tests/test_ticket_service.py` - 5 unit tests

---

## Status Flow

```
New → In Progress → Pending → On Hold
  │        │           │          │
  │        └───────────┴──────────┴──→ Resolved → Closed
  │
  └────────────────────────────────→ Cancelled
```

---

## Notes

1. **Department** là free-form string trên Employee (không cần tạo bảng riêng)
2. **Auto-assignment** chỉ xảy ra khi `category.auto_assign = True`
3. **Khi đổi category** → ticket được re-assign theo category mới (nếu auto_assign=True)
4. **Load balancing** dựa trên `csat_score` (customer satisfaction) và `max_ticket_capacity`
