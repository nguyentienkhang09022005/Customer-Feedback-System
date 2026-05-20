# Appointment, FAQ, SLA & Attachment

## 1. Tổng quan

| Module | Mô tả |
|--------|--------|
| **Appointment** | Lịch hẹn tư vấn giữa khách hàng và nhân viên, gắn với ticket |
| **FAQ** | Bài viết câu hỏi thường gặp (public/private), đếm lượt xem |
| **SLA** | Chính sách thời gian giải quyết theo mức độ nghiêm trọng |
| **Attachment** | Upload/quản lý file qua Cloudinary |

---

## 2. Database Schema

### Appointment (`appointments`)
| Cột | Kiểu | Mô tả |
|-----|------|--------|
| id_appointment | UUID, PK | ID lịch hẹn |
| id_ticket | UUID, FK | Ticket liên quan |
| id_customer | UUID, FK | Khách hàng |
| id_employee | UUID, FK | Nhân viên |
| scheduled_at | DateTime | Thời gian hẹn |
| reason | Text | Lý do tư vấn |
| status | String(20) | pending / accepted / rejected / cancelled |
| rejection_reason | Text (nullable) | Lý do từ chối |
| created_at / updated_at | DateTime | Timestamps |

### FAQArticle (`faq_articles`)
| Cột | Kiểu | Mô tả |
|-----|------|--------|
| id_article | UUID, PK | ID bài viết |
| title | String(255) | Tiêu đề |
| content | Text | Nội dung |
| view_count | Integer | Lượt xem |
| is_published | Boolean | Công khai |
| id_category | UUID, FK→tickets_category | Danh mục |
| id_author | UUID, FK→employees | Tác giả |

### SLAPolicy (`sla_policies`)
| Cột | Kiểu | Mô tả |
|-----|------|--------|
| id_policy | UUID, PK | ID |
| policy_name | String(100) | Tên |
| severity | String(50) | Mức severity |
| max_resolution_days | Integer | Số ngày tối đa |
| is_active | Boolean | Đang hoạt động |

### Attachment (`attachments`)
| Cột | Kiểu | Mô tả |
|-----|------|--------|
| id_attachment | UUID, PK | ID |
| attach_name | String | Tên file |
| attach_type | String | MIME type |
| attach_extension | String | Extension |
| file_size | Integer | Kích thước (bytes) |
| url | String | URL Cloudinary |
| thumbnail_url | String (nullable) | Thumbnail (cho ảnh) |
| public_id | String | Cloudinary public ID |
| reference_type | String | ticket / message |
| id_reference | UUID | ID entity tham chiếu |
| id_uploader | UUID | Người upload |
| is_deleted | Boolean | Soft delete |
| is_permanent | Boolean | Không bị cleanup |

---

## 3. API Endpoints

### Appointment (`/api/v1/appointments`)

| Method | Path | Quyền | Mô tả |
|--------|------|-------|--------|
| POST | `/` | Customer | Tạo lịch hẹn |
| GET | `/ticket/{ticket_id}` | User | Lịch hẹn theo ticket |
| GET | `/employee` | Employee | Tất cả lịch hẹn của NV |
| GET | `/employee/pending` | Employee | Lịch hẹn đang chờ |
| GET | `/{id}` | User (owner) | Chi tiết |
| PATCH | `/{id}/accept` | Employee | Chấp nhận |
| PATCH | `/{id}/reject` | Employee | Từ chối (kèm lý do) |
| PATCH | `/{id}/cancel` | Customer | Hủy |

### FAQ (`/api/v1/faqs`)

| Method | Path | Quyền | Mô tả |
|--------|------|-------|--------|
| POST | `/` | Employee | Tạo FAQ |
| GET | `/` | Employee | Tất cả FAQ |
| GET | `/public` | Public | FAQ công khai (phân trang, search, filter) |
| GET | `/private` | Employee | FAQ nội bộ |
| PATCH | `/{id}` | Employee | Cập nhật |
| DELETE | `/{id}` | Employee | Xóa |

### SLA (`/api/v1/sla-policies`)

| Method | Path | Quyền | Mô tả |
|--------|------|-------|--------|
| GET | `/` | Employee | Tất cả SLA policies |
| POST | `/` | Admin | Tạo mới |
| PUT | `/{id}` | Admin | Cập nhật |
| PATCH | `/{id}/toggle` | Admin | Bật/tắt |

### Attachments (`/api/v1/attachments`)

| Method | Path | Quyền | Mô tả |
|--------|------|-------|--------|
| POST | `/upload` | User | Upload 1 file |
| POST | `/upload-multiple` | User | Upload nhiều file |
| GET | `/{id}` | Public | Chi tiết attachment |
| GET | `/reference/{type}/{id}` | Public | File theo ticket/message |
| DELETE | `/{id}` | User (owner) | Xóa |
| POST | `/cleanup` | Admin | Dọn file mồ côi |

### Cloudinary Signature (`/api/v1/chat`)

| Method | Path | Quyền | Mô tả |
|--------|------|-------|--------|
| POST | `/upload-signature` | User | Tạo chữ ký upload trực tiếp |

---

## 4. Appointment Flow

```
Customer tạo (POST /appointments)
  → Validate: ticket hợp lệ, có employee, chưa đóng, thời gian tương lai, không trùng pending
  → status = "pending" → Notify Employee

Employee chấp nhận (PATCH /{id}/accept)
  → status = "accepted" → Notify Customer

Employee từ chối (PATCH /{id}/reject)
  → status = "rejected" + lý do → Notify Customer

Customer hủy (PATCH /{id}/cancel)
  → status = "cancelled" → Notify Employee
```

Customer chỉ hủy được khi status ∈ {pending, accepted}.

---

## 5. FAQ Management

- **Anti-spam view count**: In-memory cache, cooldown 300s/IP/bài viết
- **Public endpoint**: Không cần auth, phân trang, filter category, search ILIKE
- **Chatbot sync**: Mọi thay đổi FAQ → invalidate chatbot cache
- **Bảo mật**: Public chỉ trả bài `is_published=True`

---

## 6. SLA Configuration

- Định nghĩa thời gian giải quyết tối đa (ngày) theo severity
- Repository: `get_active_by_severity()` để ticket tự động áp dụng SLA
- Toggle: Bật/tắt nhanh mà không cần xóa
- Thay đổi SLA → invalidate chatbot cache

---

## 7. File Attachment & Cloudinary

### Upload Server-side
```
Frontend gửi file → Backend validate → Upload Cloudinary → Lưu metadata DB
```
- `resource_type="auto"` (tự nhận diện)
- Thumbnail tự động (300x300, crop) cho ảnh

### Upload Frontend (Signed)
```
POST /chat/upload-signature → Validate file type → Trả signature + params
Frontend upload trực tiếp lên Cloudinary
```

### File Validation
- Extension whitelist: image (jpeg, png, gif, webp), document (pdf, doc, docx, xls, xlsx), archive (zip, rar)
- MIME type check + magic bytes detection (chống giả mạo extension)
- Giới hạn kích thước (`MAX_FILE_SIZE_BYTES`)
- Sanitize filename (chống path traversal, max 100 ký tự)

### Cleanup
- Soft delete mặc định
- Hard delete khi cleanup file mồ côi (không liên kết entity)
- Xóa cả file trên Cloudinary
