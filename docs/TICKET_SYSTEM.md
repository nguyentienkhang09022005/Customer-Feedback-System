# Ticket System Documentation

## Overview

Hệ thống Ticket cho phép customers tạo tickets với categories, employees có thể xem và assign tickets theo department, và tính năng auto-assignment với load balancing.

---

## Database Schema

### Department Table (NEW)

| Column | Type | Description |
|--------|------|-------------|
| `id_department` | UUID | Primary key |
| `name` | String(50) | Tên department (unique) - VD: "Finance", "HR", "IT", "Support", "Sales" |
| `description` | Text | Mô tả department |
| `is_active` | Boolean | Department có đang hoạt động không |
| `created_at` | DateTime | Thời gian tạo |

### Employee Table (Modified)

| Column | Type | Description |
|--------|------|-------------|
| `id_employee` | UUID | Primary key (FK → humans.id) |
| `id_department` | UUID | Foreign key → departments.id_department (nullable cho admin) |
| `employee_code` | String(20) | Mã nhân viên - VD: "NV26001" |
| `job_title` | String(50) | Chức danh |
| `role_name` | String(50) | Foreign key → roles.role_name |
| `max_ticket_capacity` | Integer | Số ticket tối đa có thể nhận (default: 5) |
| `csat_score` | Float | Điểm satisfaction (0.0 - 5.0) |
| `hire_date` | Date | Ngày vào làm |

### TicketCategory Table (Modified)

| Column | Type | Description |
|--------|------|-------------|
| `id_category` | UUID | Primary key |
| `name` | String(100) | Tên category |
| `description` | Text | Mô tả |
| `is_active` | Boolean | Category có đang hoạt động không |
| `id_department` | UUID | Foreign key → departments.id_department |
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

### Department Management (NEW)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/v1/departments` | Employee | Lấy danh sách departments |
| POST | `/api/v1/departments` | Employee | Tạo department mới |
| GET | `/api/v1/departments/{id}` | Employee | Lấy department theo ID |
| PATCH | `/api/v1/departments/{id}` | Employee | Cập nhật department |
| DELETE | `/api/v1/departments/{id}` | Employee | Xóa department |

### Ticket Management

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/v1/tickets` | Customer | Tạo ticket mới |
| GET | `/api/v1/tickets/user` | Any | Lấy danh sách tất cả tickets |
| GET | `/api/v1/tickets/{id}` | Any | Lấy ticket theo ID |
| PATCH | `/api/v1/tickets/{id}` | Employee | Cập nhật ticket |
| DELETE | `/api/v1/tickets/{id}` | Employee | Xóa ticket |

### Ticket Assignment

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/v1/tickets/unassigned` | Employee | Lấy tickets chưa được assign |
| GET | `/api/v1/tickets/department/{dept_id}` | Employee | Lấy tickets theo department ID |
| GET | `/api/v1/tickets/employee-tickets` | Employee | Lấy tickets của employee hiện tại |
| POST | `/api/v1/tickets/assign` | Employee | Manual assign ticket cho employee |

### Ticket Category Management

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/v1/ticket-categories` | Employee | Lấy danh sách categories |
| POST | `/api/v1/ticket-categories` | Employee | Tạo category mới |
| PATCH | `/api/v1/ticket-categories/{id}` | Employee | Cập nhật category |
| DELETE | `/api/v1/ticket-categories/{id}` | Employee | Xóa category |

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
    LoadBalancer.get_best_employee_for_department(dept_id)
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
def get_best_employee_for_department(dept_id: UUID):
    # 1. Get all ACTIVE employees in department, ordered by csat_score DESC
    employees = db.query(Employee).filter(
        Employee.id_department == dept_id,
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

## Seed Data

Khi migrate, hệ thống sẽ tạo sẵn 5 departments:

| Name | Description |
|------|-------------|
| Finance | Phòng Tài Chính |
| HR | Phòng Nhân Sự |
| IT | Phòng Công Nghệ Thông Tin |
| Support | Phòng Hỗ Trợ Khách Hàng |
| Sales | Phòng Kinh Doanh |

---

## Ví dụ sử dụng

### 1. Tạo Department

```bash
POST /api/v1/departments
{
    "name": "Marketing",
    "description": "Phòng Marketing"
}
```

### 2. Tạo Ticket (Auto-Assignment Enabled)

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

### 3. Lấy Tickets theo Department

```bash
GET /api/v1/tickets/department/{uuid-department-id}
```

---

## Các File đã thay đổi/thêm mới

### Models
- `app/models/department.py` - **NEW** - Department model
- `app/models/human.py` - Đổi `department` String → `id_department` FK
- `app/models/ticket.py` - Đổi `department` String → `id_department` FK

### Schemas
- `app/schemas/departmentSchema.py` - **NEW** - DepartmentCreate, DepartmentOut, etc.
- `app/schemas/employeeSchema.py` - Đổi `department` → `id_department`
- `app/schemas/ticketCategorySchema.py` - Đổi `department` → `id_department`

### Repositories
- `app/repositories/departmentRepository.py` - **NEW** - CRUD operations
- `app/repositories/employeeRepository.py` - Cập nhật query theo FK
- `app/repositories/ticketCategoryRepository.py` - Cập nhật query theo FK
- `app/repositories/ticketRepository.py` - Cập nhật JOIN theo FK

### Services
- `app/services/departmentService.py` - **NEW** - Business logic
- `app/services/loadBalancer.py` - Đổi sang nhận `dept_id` UUID
- `app/services/ticketService.py` - Đổi sang dùng `id_department`

### API
- `app/api/v1/departments.py` - **NEW** - Department endpoints
- `app/api/v1/tickets.py` - Đổi endpoint `/department/{dept_id}` nhận UUID
- `main.py` - Đăng ký departments router

### Database
- `migrations/versions/2026_03_24_0001_...py` - Migration tạo bảng + seed data

### Tests
- `tests/test_load_balancer.py` - Cập nhật dùng UUID
- `tests/test_ticket_service.py` - Cập nhật dùng UUID

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

1. **Admin Employees** → `id_department = NULL` (không thuộc department nào)
2. **Non-admin Employees** → phải có `id_department` hợp lệ
3. **Auto-assignment** chỉ xảy ra khi `category.auto_assign = True`
4. **Khi đổi category** → ticket được re-assign theo category mới (nếu auto_assign=True)
5. **Load balancing** dựa trên `csat_score` (customer satisfaction) và `max_ticket_capacity`
