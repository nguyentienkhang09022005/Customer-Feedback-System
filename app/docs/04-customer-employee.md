# Customer & Employee Management

## 1. Tổng quan

Quản lý thông tin khách hàng, nhân viên, phòng ban và phân bổ nhân sự:
- CRUD Customer & Employee
- Quản lý phòng ban (Department)
- Phân bổ nhân viên vào phòng ban (Assignment)
- Chỉ định Manager
- Xem workload theo phòng ban

---

## 2. Database Schema

### Department (`departments`)
| Cột | Kiểu | Mô tả |
|-----|------|--------|
| id_department | UUID, PK | ID phòng ban |
| name | String(100), unique | Tên phòng ban |
| description | Text | Mô tả |
| is_active | Boolean, default=True | Đang hoạt động |

### Customer Type (`customer_type`)
| Cột | Kiểu | Mô tả |
|-----|------|--------|
| type_name | String(50), PK | Tên loại KH |
| description | String(255) | Mô tả |

*(Xem thêm bảng `humans`, `employees`, `customers` tại [01-authentication.md](./01-authentication.md))*

---

## 3. API Endpoints

### Customers (`/api/v1/customers`)

| Method | Path | Quyền | Mô tả |
|--------|------|-------|--------|
| GET | `/customers` | Employee | Lấy danh sách khách hàng |
| POST | `/customers` | Employee | Tạo khách hàng |
| PATCH | `/customers/{cus_id}` | Employee | Cập nhật khách hàng |
| DELETE | `/customers/{cus_id}` | Employee | Xóa khách hàng |

### Employees (`/api/v1/employees`)

| Method | Path | Quyền | Mô tả |
|--------|------|-------|--------|
| GET | `/employees` | Employee | Danh sách nhân viên |
| POST | `/employees` | Employee | Tạo nhân viên |
| GET | `/employees/{emp_id}` | Employee | Chi tiết nhân viên |
| PATCH | `/employees/{emp_id}` | Employee | Cập nhật (Admin không sửa Admin khác) |
| DELETE | `/employees/{emp_id}` | Employee | Xóa (Admin không xóa Admin khác) |
| GET | `/employees/department/{dept_id}` | Employee | NV theo phòng ban |
| GET | `/employees/workload/department/{dept_id}` | Manager | Workload team |
| PATCH | `/employees/manager/{emp_id}` | Manager | Manager cập nhật NV |
| GET | `/employees/department/{dept_id}/members` | Manager | Thành viên phòng ban |

### Customer Types (`/api/v1/customer-types`)

| Method | Path | Quyền | Mô tả |
|--------|------|-------|--------|
| GET | `/customer-types` | Employee | Danh sách loại KH |
| POST | `/customer-types` | Employee | Tạo loại KH |
| PUT | `/customer-types/{type_name}` | Employee | Cập nhật |
| DELETE | `/customer-types/{type_name}` | Employee | Xóa |

### Departments (`/api/v1/departments`)

| Method | Path | Quyền | Mô tả |
|--------|------|-------|--------|
| GET | `/departments` | Employee | Danh sách phòng ban |
| POST | `/departments` | Employee | Tạo phòng ban |
| GET | `/departments/{dept_id}` | Employee | Chi tiết |
| PATCH | `/departments/{dept_id}` | Employee | Cập nhật |
| DELETE | `/departments/{dept_id}` | Employee | Xóa |

### Department Assignments (`/api/v1/department-assignments`)

| Method | Path | Quyền | Mô tả |
|--------|------|-------|--------|
| GET | `/department-assignments` | Admin | Tất cả phân bổ |
| GET | `/department-assignments/employees/{emp_id}` | Admin | Phân bổ của NV |
| GET | `/department-assignments/departments/{dept_id}/members` | Admin | Thành viên phòng ban |
| POST | `/department-assignments` | Admin | Gán NV vào phòng ban |
| POST | `/department-assignments/transfer` | Admin | Chuyển phòng ban |
| POST | `/department-assignments/manager` | Admin | Chỉ định Manager |
| DELETE | `/department-assignments` | Admin | Xóa NV khỏi phòng ban |

---

## 4. Service Layer

### CustomerService
- `create_customer`: Kiểm tra trùng email/username/phone → sinh mã KH (KH{YY}{NNN}) → tạo
- `update_customer`: Partial update (exclude_unset)
- `delete_customer`: Xóa vật lý

### EmployeeService
- `create_employee`: Kiểm tra trùng → sinh mã NV (NV{YY}{NNN}) → tạo với default capacity=5, csat=0.0
- `update_employee`: Admin không sửa Admin khác
- `manager_update_employee`: Manager chỉ sửa NV trong phòng ban mình, chỉ được sửa: job_title, status, phone, avatar
- `delete_employee`: Admin không xóa Admin khác
- `get_department_workload`: Lấy workload NV trong phòng ban

### DepartmentService
- CRUD phòng ban
- Validate tên không trùng
- Thay đổi department → invalidate chatbot cache

### DepartmentAssignmentService
- `assign_employee_to_department`: Kiểm tra NV + dept tồn tại, nếu NV là Manager → kiểm tra dept đã có Manager chưa
- `transfer_employee_to_department`: Không chuyển Manager cuối cùng khỏi dept cũ, kiểm tra dept mới đã có Manager chưa
- `remove_employee_from_department`: Không xóa Manager cuối cùng
- `set_department_manager`: Chỉ NV có role Manager mới được chỉ định
- `get_department_with_members`: Trả về dept info + manager + members list

---

## 5. Quy tắc nghiệp vụ

### Mã tự sinh
- Customer: `KH{YY}{NNN}` (VD: KH25001, KH25002...)
- Employee: `NV{YY}{NNN}` (VD: NV25001, NV25002...)

### Phân quyền Manager
- Manager chỉ xem/sửa NV trong phòng ban của mình
- Admin bypass tất cả giới hạn phòng ban
- Manager chỉ được sửa: job_title, status, phone, avatar

### Department Assignment Rules
- Mỗi phòng ban chỉ có 1 Manager
- Không thể chuyển/xóa Manager cuối cùng khỏi phòng ban
- Phải chỉ định Manager mới trước khi chuyển Manager cũ

### Workload
- `capacity_usage = current_ticket_count / max_ticket_capacity * 100%`
- Hiển thị cho Manager xem để phân công hợp lý
