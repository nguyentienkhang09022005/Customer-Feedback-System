# Luồng Category - Template - Ticket

## Tổng quan

Hệ thống Customer Feedback sử dụng 3 entity chính: **Category (Danh mục)**, **Template (Mẫu biểu)** và **Ticket (Phiếu góp ý)**. Luồng dữ liệu được thiết kế theo hướng: Customer chọn Category → chọn Template → điền form và tạo Ticket.

## Mô hình dữ liệu

### 1. TicketCategory (Danh mục)

Bảng `tickets_category` lưu trữ các danh mục ticket (ví dụ: "Góp ý dịch vụ", "Khiếu nại", "Hỗ trợ kỹ thuật").

| Trường | Kiểu | Mô tả |
|--------|------|-------|
| `id_category` | UUID | Khóa chính |
| `name` | String(100) | Tên danh mục |
| `description` | Text | Mô tả danh mục |
| `is_active` | Boolean | Danh mục có đang hoạt động không |
| `id_department` | UUID | Phòng ban phụ trách (FK) |
| `auto_assign` | Boolean | Tự động gán ticket cho nhân viên |
| `is_deleted` | Boolean | Đánh dấu xóa mềm |
| `deleted_at` | DateTime | Thời điểm xóa mềm |
| `created_at` | DateTime | Thời điểm tạo |
| `updated_at` | DateTime | Thời điểm cập nhật cuối |

**Mối quan hệ:**
- 1 Category có nhiều Template (`templates` relationship)
- Category thuộc về 1 Department (`id_department` FK)

### 2. TicketTemplate (Mẫu biểu)

Bảng `ticket_templates` lưu trữ các mẫu biểu với **composite primary key** `(id_template, version)` để hỗ trợ versioning.

| Trường | Kiểu | Mô tả |
|--------|------|-------|
| `id_template` | UUID | Part của PK, ID mẫu |
| `version` | Integer | Part của PK, số version (1, 2, 3...) |
| `name` | String(100) | Tên mẫu biểu |
| `description` | Text | Mô tả mẫu biểu |
| `fields_config` | JSON | Cấu hình các field động |
| `id_category` | UUID | Danh mục cha (nullable) |
| `id_author` | UUID | Người tạo (Employee, nullable) |
| `is_active` | Boolean | Version này có đang active không |
| `is_deleted` | Boolean | Đánh dấu xóa mềm |
| `deleted_at` | DateTime | Thời điểm xóa mềm |
| `created_at` | DateTime | Thời điểm tạo |
| `updated_at` | DateTime | Thời điểm cập nhật cuối |

**Mối quan hệ:**
- 1 Template thuộc về 1 Category (`id_category` FK, nullable)
- 1 Template có nhiều Ticket (`tickets` relationship)

**Về fields_config:**
```json
{
  "fields": [
    {
      "name": "full_name",
      "type": "text",
      "label": "Họ và tên",
      "required": true,
      "placeholder": "Nhập họ và tên"
    },
    {
      "name": "service_rating",
      "type": "rating",
      "label": "Đánh giá dịch vụ",
      "required": true,
      "max_stars": 5
    },
    {
      "name": "feedback_type",
      "type": "select",
      "label": "Loại góp ý",
      "options": [
        {"value": "complaint", "label": "Khiếu nại"},
        {"value": "suggestion", "label": "Đề xuất"}
      ]
    }
  ],
  "severity": {
    "type": "select",
    "label": "Mức độ ưu tiên",
    "default_value": "Medium",
    "options": [
      {"value": "Low", "label": "Thấp"},
      {"value": "Medium", "label": "Trung bình"},
      {"value": "High", "label": "Cao"}
    ]
  }
}
```

**Các loại field được hỗ trợ:**
- `text`, `textarea`, `email`, `phone`, `number`, `url`
- `date`, `time`, `datetime`
- `select`, `select_multi`, `radio`
- `checkbox`, `checkbox_group`
- `file`, `file_multi`
- `rating`, `rich_text`, `hidden`, `readonly`, `info`

### 3. Ticket (Phiếu góp ý)

Bảng `tickets` lưu trữ các phiếu góp ý từ khách hàng.

| Trường | Kiểu | Mô tả |
|--------|------|-------|
| `id_ticket` | UUID | Khóa chính |
| `title` | String(255) | Tiêu đề ticket |
| `custom_fields` | JSON | Dữ liệu form động từ template |
| `status` | String(50) | Trạng thái (New, In Progress, Resolved, Closed...) |
| `severity` | String(50) | Mức độ ưu tiên |
| `resolution_note` | Text | Ghi chú giải quyết |
| `expired_date` | DateTime | Hạn xử lý (tính từ SLA) |
| `id_customer` | UUID | Khách hàng tạo (FK, required) |
| `id_employee` | UUID | Nhân viên phụ trách (FK, nullable) |
| `id_template` | UUID | Template đã sử dụng (FK, nullable) |
| `template_version` | Integer | Version của template đã sử dụng |
| `is_deleted` | Boolean | Đánh dấu xóa mềm |
| `deleted_at` | DateTime | Thời điểm xóa mềm |
| `created_at` | DateTime | Thời điểm tạo |
| `updated_at` | DateTime | Thời điểm cập nhật cuối |

**Mối quan hệ:**
- 1 Ticket thuộc về 1 Customer (`id_customer` FK)
- 1 Ticket được phụ trách bởi 1 Employee (`id_employee` FK, nullable)
- 1 Ticket được tạo từ 1 Template (`id_template`, `template_version` FK)

## Luồng xử lý

### Luồng 1: Tạo Ticket từ Template

```
Customer → Chọn Category → Chọn Template → Điền form → Tạo Ticket
```

**Chi tiết các bước:**

1. **Customer chọn Category**
   - Customer xem danh sách Category đang active
   - Mỗi Category hiển thị danh sách Template active của nó

2. **Customer chọn Template**
   - Template được lọc theo Category và chỉ lấy version mới nhất đang active
   - Customer xem `fields_config` để biết form gồm những field nào

3. **Customer điền form và gửi**
   - API: `POST /api/v1/tickets/from-template`
   - Body:
     ```json
     {
       "title": "Góp ý về dịch vụ",
       "severity": "Medium",
       "id_template": "uuid-của-template",
       "custom_fields": {
         "full_name": "Nguyễn Văn A",
         "service_rating": 5,
         "feedback_type": "suggestion"
       }
     }
     ```

4. **Hệ thống xử lý:**
   - Validate template tồn tại, active, chưa bị xóa
   - Check rate limit (giới hạn số ticket được tạo trong 1 khoảng thời gian)
   - Tính `expired_date` dựa trên SLA policy của severity
   - Tạo Ticket với `id_template` và `template_version` (để tracking version nào đã dùng)
   - Nếu template có `id_category`:
     - Gửi notification cho các thành viên trong department của category

5. **Kết quả:**
   - Ticket được tạo với `status = "New"`, `id_employee = null`
   - Customer nhận được thông báo tạo thành công

### Luồng 2: Quản lý Template (Versioning)

```
Employee tạo Template (v1) → Cập nhật fields_config → Tạo Version mới (v2)
```

**Chi tiết các bước:**

1. **Tạo Template mới**
   - API: `POST /api/v1/templates`
   - Khởi tạo với `version = 1`, `is_active = true`
   - Có thể gắn với 1 Category hoặc để null

2. **Cập nhật Template**
   - API: `PATCH /api/v1/templates/{id}`

   **Trường hợp A: Cập nhật `fields_config`**
   - Tạo row mới với `version = version_cũ + 1`
   - Row cũ được set `is_active = false`
   - Row mới có `is_active = true`

   **Trường hợp B: Cập nhật các trường khác** (name, description, id_category, is_active)
   - Cập nhật trực tiếp trên row mới nhất (không tạo version mới)
   - Chỉ update `updated_at`

3. **Kích hoạt Template**
   - API: `POST /api/v1/templates/{id}/activate`
   - Set `is_active = true` trên version mới nhất (không tạo version mới)

4. **Xóa Template**
   - API: `DELETE /api/v1/templates/{id}`
   - Soft delete TẤT CẢ các version của template đó
   - Tickets đã tạo từ template vẫn giữ nguyên reference

### Luồng 3: Quản lý Category

```
Employee tạo Category → Gắn Department → Gắn Templates → Auto-assign settings
```

**Chi tiết các bước:**

1. **Tạo Category**
   - API: `POST /api/v1/categories`
   - Yêu cầu: `name`, `id_department`
   - Mặc định: `is_active = true`, `auto_assign = true`

2. **Xóa Category**
   - API: `DELETE /api/v1/categories/{id}`
   - Soft delete Category
   - Tất cả Templates thuộc category cũng được soft delete
   - Tickets đã tạo không bị ảnh hưởng

3. **Auto-assign**
   - Khi `auto_assign = true`:
     - Ticket được tạo sẽ có `id_employee = null` (chờ assign)
     - Hệ thống sẽ notify các thành viên trong department
   - Khi `auto_assign = false`:
     - Ticket được tạo vẫn có `id_employee = null`
     - Cần assign thủ công

### Luồng 4: Ticket Lifecycle

```
New → In Progress → Resolved → Closed
         ↓            ↓
       Reopen    Reopen ↓
```

**Các trạng thái hợp lệ:**
- `New`: Ticket mới tạo
- `In Progress`: Đang xử lý
- `Pending`: Chờ phản hồi từ khách hàng
- `On Hold`: Tạm dừng
- `Resolved`: Đã giải quyết
- `Closed`: Đã đóng

**Các API xử lý:**

| API | Mô tả |
|-----|-------|
| `POST /tickets/{id}/assign` | Gán ticket cho employee |
| `POST /tickets/{id}/resolve` | Đánh dấu đã giải quyết |
| `POST /tickets/{id}/close` | Đóng ticket |
| `POST /tickets/{id}/reopen` | Mở lại ticket đã đóng |

**Quy tắc chuyển trạng thái:**
- `New` → `In Progress`: Khi được assign
- `In Progress`, `Pending`, `On Hold` → `Resolved`: Khi employee giải quyết xong
- `Resolved` → `Closed`: Khi customer xác nhận hoặc auto-close
- `Closed` → `In Progress` (nếu có employee) hoặc `New` (nếu chưa có): Khi customer mở lại

## API Endpoints

### Template APIs

| Method | Endpoint | Mô tả |
|--------|----------|--------|
| `GET` | `/api/v1/templates` | Lấy tất cả template (chỉ version mới nhất, active) |
| `GET` | `/api/v1/templates/category/{category_id}` | Lấy templates theo category |
| `GET` | `/api/v1/templates/{id}` | Lấy template chi tiết (version mới nhất) |
| `GET` | `/api/v1/templates/{id}?version=N` | Lấy template version cụ thể |
| `GET` | `/api/v1/templates/{id}/versions` | Lấy tất cả versions của template |
| `POST` | `/api/v1/templates` | Tạo template mới |
| `PATCH` | `/api/v1/templates/{id}` | Cập nhật template |
| `DELETE` | `/api/v1/templates/{id}` | Xóa template (soft delete) |
| `POST` | `/api/v1/templates/{id}/activate` | Kích hoạt template |

### Category APIs

| Method | Endpoint | Mô tả |
|--------|----------|--------|
| `GET` | `/api/v1/categories` | Lấy tất cả category |
| `GET` | `/api/v1/categories/active` | Lấy category đang active |
| `GET` | `/api/v1/categories/{id}` | Lấy category chi tiết |
| `POST` | `/api/v1/categories` | Tạo category mới |
| `PATCH` | `/api/v1/categories/{id}` | Cập nhật category |
| `DELETE` | `/api/v1/categories/{id}` | Xóa category (soft delete) |

### Ticket APIs

| Method | Endpoint | Mô tả |
|--------|----------|--------|
| `POST` | `/api/v1/tickets/from-template` | Tạo ticket từ template |
| `GET` | `/api/v1/tickets/user` | Lấy tickets của customer hiện tại |
| `GET` | `/api/v1/tickets/user/closed` | Lấy tickets đã đóng của customer |
| `GET` | `/api/v1/tickets/unassigned` | Lấy tickets chưa được gán |
| `GET` | `/api/v1/tickets/department/{dept_id}` | Lấy tickets theo department |
| `GET` | `/api/v1/tickets/employee-tickets` | Lấy tickets của employee |
| `GET` | `/api/v1/tickets/employee-tickets/closed` | Lấy tickets đã đóng của employee |
| `GET` | `/api/v1/tickets/all` | Lấy tất cả tickets |
| `GET` | `/api/v1/tickets/{id}` | Lấy ticket chi tiết |
| `PATCH` | `/api/v1/tickets/{id}` | Cập nhật ticket |
| `DELETE` | `/api/v1/tickets/{id}` | Xóa ticket (soft delete) |
| `POST` | `/api/v1/tickets/{id}/assign` | Gán ticket cho employee |
| `POST` | `/api/v1/tickets/{id}/resolve` | Đánh dấu đã giải quyết |
| `POST` | `/api/v1/tickets/{id}/close` | Đóng ticket |
| `POST` | `/api/v1/tickets/{id}/reopen` | Mở lại ticket |

## Soft Delete

Tất cả 3 entity đều hỗ trợ **soft delete**:

- `is_deleted = true`: Đánh dấu đã xóa
- `deleted_at`: Thời điểm xóa

**Tác động khi xóa:**

| Entity bị xóa | Ảnh hưởng đến |
|---------------|----------------|
| Category | Templates thuộc category cũng bị soft delete |
| Template | Tickets đã tạo không bị ảnh hưởng, chỉ không thể tạo ticket mới từ template đó |
| Ticket | Chỉ đánh dấu is_deleted, không ảnh hưởng đến comments, history |

## Rate Limiting

Khi tạo ticket:
- Customer bị giới hạn số lượng ticket được tạo trong 1 khoảng thời gian
- Nếu vượt quá giới hạn, API trả về HTTP 429

## SLA và Expired Date

- Mỗi severity (Low, Medium, High, Critical) có SLA policy riêng
- Khi ticket được tạo, `expired_date` được tính dựa trên:
  - `created_at + max_resolution_days` của SLA policy tương ứng với severity
- Ticket được coi là "overdue" khi `expired_date < now` và `status không phải Resolved/Closed`

## Notification

Khi ticket mới được tạo:
- Nếu template có `id_category`:
  - Hệ thống lấy danh sách thành viên trong department của category
  - Gửi notification `TICKET_UNASSIGNED` cho các thành viên đang active
- Notification chứa:
  - Tiêu đề: "Ticket mới chưa được phân công"
  - Nội dung: "Ticket #{id_ticket}: '{title}' đang chờ được tiếp nhận"
