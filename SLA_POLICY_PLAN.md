# SLA Policies - Phân tích & Kế hoạch thay đổi

## 1. Toggle Endpoint `/api/v1/sla-policies/{policy_id}/toggle`

**Chức năng:** Bật/tắt trạng thái active của một SLA policy.

**Logic thực hiện:**
```python
def toggle_policy(self, policy_id: uuid.UUID):
    policy = self.repo.get_by_id(policy_id)  # Tìm policy
    if not policy:
        raise HTTPException(status_code=404, detail="SLA Policy không tồn tại!")
    
    policy.is_active = not policy.is_active  # Đảo ngược trạng thái
    update_schema = SLAUpdate(is_active=policy.is_active)
    return self.repo.update(policy, update_schema)  # Lưu vào DB
```

**Ý nghĩa:**
- Khi `is_active=True` → SLA policy đang được áp dụng khi tạo ticket mới
- Khi `is_active=False` → SLA policy bị vô hiệu hóa, không được sử dụng
- Khi tạo ticket mới, hệ thống chỉ lấy SLA policy có `is_active=True` và `severity` khớp với ticket

---

## 2. SLA Policies được thiết lập PER TICKET (theo severity) hay FOR ALL TICKETS?

### Kết luận: **FOR ALL TICKETS (theo mức độ nghiêm trọng - severity)**

**Chi tiết:**

Mỗi SLA policy được định nghĩa cho một **severity cụ thể**:
```
Low       → 1 SLA policy
Medium    → 1 SLA policy  
High      → 1 SLA policy
Critical  → 1 SLA policy
```

**Cách hoạt động khi tạo ticket (trong `ticketService.py` line 86-91):**
```python
active_sla = self.sla_repo.get_active_by_severity(data.severity)

if active_sla:
    expired_date = datetime.utcnow() + timedelta(minutes=active_sla.max_resolution_minutes)
else:
    expired_date = None
```

Hệ thống tìm SLA policy **đang active** và có **severity khớp** với ticket để tính `expired_date`.

### Đặc điểm của hệ thống hiện tại:
| Đặc điểm | Mô tả |
|----------|-------|
| Áp dụng cho | Tất cả tickets cùng severity |
| Có thể có nhiều policies cho cùng severity? | Có thể, nhưng chỉ có **1 policy active** được dùng |
| Mỗi ticket có lưu SLA riêng? | **KHÔNG** - Ticket chỉ lưu `expired_date` đã tính sẵn |
| Khi sửa severity ticket | `expired_date` được **tính lại** theo SLA mới (line 156-159) |

### Thiếu sót so với "lập riêng cho từng ticket":
- ❌ Không thể gán SLA cụ thể cho một ticket cụ thể
- ❌ Không thể tạo SLA dựa trên: khách hàng VIP, department, thời gian...
- ❌ Không có SLA theo từng khách hàng/category

---

## 3. Kế hoạch đổi `max_resolution_minutes` → `max_resolution_days`

### Bước 1: Sửa Schema (`app/schemas/slaSchema.py`)

```python
# Trước
class SLACreate(BaseModel):
    max_resolution_minutes: int

class SLAUpdate(BaseModel):
    max_resolution_minutes: Optional[int] = None

class SLAOut(BaseModel):
    max_resolution_minutes: int

# Sau
class SLACreate(BaseModel):
    max_resolution_days: int

class SLAUpdate(BaseModel):
    max_resolution_days: Optional[int] = None

class SLAOut(BaseModel):
    max_resolution_days: int
```

### Bước 2: Sửa Model (`app/models/ticket.py`)

```python
# Trước
class SLAPolicy(Base):
    __tablename__ = "sla_policies"
    max_resolution_minutes = Column(Integer, nullable=False)

# Sau
class SLAPolicy(Base):
    __tablename__ = "sla_policies"
    max_resolution_days = Column(Integer, nullable=False)
```

### Bước 3: Sửa TicketService (`app/services/ticketService.py`)

```python
# Trước (line 89, 159)
expired_date = datetime.utcnow() + timedelta(minutes=active_sla.max_resolution_minutes)

# Sau
expired_date = datetime.utcnow() + timedelta(days=active_sla.max_resolution_days)
```

### Bước 4: Cập nhật Migration (nếu có database migration)
Cần chạy Alembic migration để đổi column name trong database:
```bash
alembic revision --autogenerate -m "Rename max_resolution_minutes to max_resolution_days in sla_policies"
```

### Bước 5: Cập nhật API response message (tùy chọn)
Cập nhật message trong SLA API nếu muốn hiển thị "ngày" thay vì "phút".

---

## 4. Các phần mở rộng SLA khuyến nghị

### 4.1 Automatic Escalation khi quá hạn

**Mô tả:** Khi ticket vượt quá `expired_date` mà chưa được resolve/close, hệ thống tự động escalate.

**Các cấp escalation có thể có:**

| Cấp | Điều kiện | Action |
|-----|-----------|--------|
| Level 1 | Quá hạn 1 ngày | Gửi notification đến assignee |
| Level 2 | Quá hạn 2 ngày | Escalate lên manager + notify assignee |
| Level 3 | Quá hạn 3 ngày | Reassign ticket + notify manager |

**Cần thêm:**
```python
# Trong ticketService.py, thêm method:
def check_and_escalate_overdue_tickets(self):
    """Chạy định kỳ để check và escalate tickets quá hạn"""
    overdue_tickets = self.repo.get_overdue_tickets()
    for ticket in overdue_tickets:
        self._escalate_ticket(ticket)
```

**Cần thêm bảng/esquema:**
```python
class EscalationRule(Base):
    __tablename__ = "escalation_rules"
    id_rule = Column(UUID, primary_key=True)
    level = Column(Integer)  # 1, 2, 3...
    hours_overdue = Column(Integer)  # Số giờ quá hạn để trigger
    action_type = Column(String)  # "notify", "reassign", "escalate_to_manager"
    target_role = Column(String)  # "manager", "supervisor", "admin"
```

---

### 4.2 Reminder/Notification trước deadline

**Mô tả:** Gửi notification (email/SMS/Socket) trước khi ticket sắp quá hạn.

**Các mốc reminder có thể:**

| Mốc | Thời điểm | Nội dung |
|-----|-----------|----------|
| 24h warning | 24h trước deadline | "Ticket sắp quá hạn trong 24h" |
| 4h warning | 4h trước deadline | "Ticket sắp quá hạn trong 4h" |
| 1h warning | 1h trước deadline | "Ticket sắp quá hạn trong 1h!" |

**Cần thêm:**
```python
# Trong SLA Policy schema, thêm các field:
class SLACreate(BaseModel):
    reminder_24h: bool = True      # Gửi reminder 24h trước
    reminder_4h: bool = True       # Gửi reminder 4h trước
    reminder_1h: bool = True       # Gửi reminder 1h trước
    
# Background job để check và gửi reminder
async def send_sla_reminders():
    """Chạy mỗi 15-30 phút để check và gửi reminder"""
    tickets_near_deadline = sla_repo.get_tickets_near_deadline()
    for ticket in tickets_near_deadline:
        send_reminder_notification(ticket)
```

---

### 4.3 SLA Report & Dashboard

**Mô tả:** Thống kê và báo cáo về SLA compliance.

**Các metrics cần theo dõi:**

| Metric | Công thức |
|--------|-----------|
| SLA Compliance Rate | (Tickets resolved on time / Total tickets) × 100% |
| Average Resolution Time | Trung bình thời gian resolve ticket |
| Overdue Tickets | Số lượng tickets đang quá hạn |
| Breach Rate by Severity | Tỷ lệ breach theo từng severity |

**API endpoints cần thêm:**
```python
@router.get("/sla-reports/summary", dependencies=[Depends(get_current_admin)])
def get_sla_summary(
    start_date: date,
    end_date: date,
    severity: Optional[SeverityEnum] = None
):
    """Lấy tổng hợp SLA report"""
    return {
        "total_tickets": 100,
        "on_time_tickets": 85,
        "overdue_tickets": 15,
        "compliance_rate": 85.0,
        "avg_resolution_hours": 24.5
    }

@router.get("/sla-reports/breaches", dependencies=[Depends(get_current_admin)])
def get_sla_breaches(
    start_date: date,
    end_date: date
):
    """Lấy danh sách tickets vi phạm SLA"""
    pass

@router.get("/sla-reports/performance", dependencies=[Depends(get_current_admin)])
def get_employee_sla_performance(
    employee_id: UUID
):
    """Lấy SLA performance của từng employee"""
    pass
```

**Schema cần thêm:**
```python
class SLAReport(BaseModel):
    total_tickets: int
    on_time_tickets: int
    overdue_tickets: int
    compliance_rate: float
    avg_resolution_days: float
    breach_by_severity: Dict[SeverityEnum, int]
```

---

### 4.4 Gán SLA riêng cho từng ticket

**Mô tả:** Cho phép override SLA mặc định (theo severity) bằng SLA tùy chỉnh cho từng ticket.

**Cách implementation:**

**Option A: Thêm field `id_sla_policy` vào Ticket model**
```python
class Ticket(Base):
    # ... existing fields ...
    id_sla_policy = Column(UUID, ForeignKey("sla_policies.id_policy"), nullable=True)

# Khi tính expired_date:
if ticket.id_sla_policy:
    # Dùng SLA riêng của ticket
    custom_sla = sla_repo.get_by_id(ticket.id_sla_policy)
    expired_date = datetime.utcnow() + timedelta(days=custom_sla.max_resolution_days)
else:
    # Dùng SLA theo severity
    active_sla = sla_repo.get_active_by_severity(ticket.severity)
    expired_date = datetime.utcnow() + timedelta(days=active_sla.max_resolution_days)
```

**Option B: Thêm bảng TicketSLA riêng (many-to-many)**
```python
class TicketSLA(Base):
    __tablename__ = "ticket_sla"
    id_ticket = Column(UUID, ForeignKey("tickets.id_ticket"), primary_key=True)
    id_sla_policy = Column(UUID, ForeignKey("sla_policies.id_policy"), primary_key=True)
    custom_deadline = Column(DateTime)  # Override hoàn toàn deadline
    created_at = Column(DateTime)
```

**Schema cần thêm cho ticket create/update:**
```python
class TicketCreate(BaseModel):
    # ... existing fields ...
    id_sla_policy: Optional[UUID] = None  # Override SLA mặc định
```

---

### 4.5 SLA theo Khách hàng VIP / Department / Category

**Mô tả:** Mở rộng SLA không chỉ theo severity mà còn theo các yếu tố khác.

**Cấu trúc database đề xuất:**

```python
class SLAPolicy(Base):
    __tablename__ = "sla_policies"
    id_policy = Column(UUID, primary_key=True)
    policy_name = Column(String(100))
    
    # Tiêu chí áp dụng - có thể kết hợp
    severity = Column(String(50))              # Low, Medium, High, Critical
    id_category = Column(UUID, nullable=True)   # Áp dụng cho category cụ thể
    id_department = Column(UUID, nullable=True) # Áp dụng cho department cụ thể
    membership_tier = Column(String, nullable=True) # Standard, Silver, Gold, VIP
    
    # Thời hạn
    max_resolution_days = Column(Integer)
    response_time_days = Column(Integer)  # Thời gian phản hồi lần đầu
    
    # Trạng thái
    is_active = Column(Boolean, default=True)
    priority = Column(Integer)  # Độ ưu tiên khi nhiều policies match
```

**Logic khi tạo ticket - tìm SLA phù hợp nhất:**
```python
def get_best_sla_policy(self, ticket: TicketCreate, customer_id: UUID):
    """
    Tìm SLA policy phù hợp nhất cho ticket.
    Ưu tiên: VIP customer > Department > Category > Severity
    """
    # 1. Check VIP customer SLA
    customer = human_repo.get_customer_by_id(customer_id)
    if customer.membership_tier == "VIP":
        vip_sla = self.repo.get_vip_sla()
        if vip_sla:
            return vip_sla
    
    # 2. Check department SLA
    category = category_repo.get_by_id(str(ticket.id_category))
    if category and category.id_department:
        dept_sla = self.repo.get_active_by_department(category.id_department)
        if dept_sla:
            return dept_sla
    
    # 3. Check category SLA
    cat_sla = self.repo.get_active_by_category(ticket.id_category)
    if cat_sla:
        return cat_sla
    
    # 4. Fallback: severity-based SLA
    return self.repo.get_active_by_severity(ticket.severity)
```

---

### 4.6 Response Time SLA (Thời gian phản hồi)

**Mô tả:** Bổ sung thêm thời gian phản hồi lần đầu, không chỉ resolution time.

```python
class SLAPolicy(Base):
    # ... existing fields ...
    response_time_hours = Column(Integer)  # Thời gian phải assign được employee
    
# Trong ticketService.create_ticket():
# Sau khi gán employee thành công, check response SLA
if created_ticket.id_employee and active_sla.response_time_hours:
    response_deadline = created_at + timedelta(hours=active_sla.response_time_hours)
    # Lưu vào ticket.response_deadline
    ticket.response_deadline = response_deadline
```

---

## 5. Tổng hợp các file cần thêm/sửa cho phần mở rộng

### File cần THÊM MỚI:

| File | Mô tả |
|------|-------|
| `app/models/escalationRule.py` | Bảng escalation rules |
| `app/schemas/escalationSchema.py` | Schema cho escalation |
| `app/services/escalationService.py` | Logic xử lý escalation |
| `app/schemas/slaReportSchema.py` | Schema cho SLA reports |
| `app/services/slaReportService.py` | Tính toán và generate reports |
| `app/tasks/slaReminderTask.py` | Background job gửi reminders |

### File cần SỬA:

| File | Thay đổi |
|------|----------|
| `app/models/ticket.py` | Thêm `id_sla_policy`, `response_deadline` |
| `app/schemas/ticketSchema.py` | Thêm `id_sla_policy` vào create/update |
| `app/schemas/slaSchema.py` | Thêm reminder flags, response_time_hours |
| `app/services/ticketService.py` | Cập nhật logic tìm SLA, thêm response deadline |
| `app/repositories/slaRepository.py` | Thêm methods tìm kiếm theo department/category/VIP |

### Background Jobs cần thêm (dùng Celery hoặc APScheduler):

| Job | Tần suất | Chức năng |
|-----|----------|-----------|
| `check_overdue_tickets` | Mỗi 15 phút | Check và trigger escalation |
| `send_sla_reminders` | Mỗi 15 phút | Gửi reminder notifications |
| `generate_sla_reports` | Hàng ngày | Tính toán daily SLA metrics |

---

## 6. Thứ tự ưu tiên triển khai

| Prio | Tính năng | Lý do |
|------|-----------|-------|
| 1 | SLA riêng cho từng ticket (4.4) | Ít impact nhất, dễ implement |
| 2 | SLA theo category/department (4.5) | Mở rộng từ hệ thống hiện |
| 3 | Reminder notifications (4.2) | Cải thiện UX, giảm breach |
| 4 | Response time SLA (4.6) | Bổ sung missing feature |
| 5 | Escalation rules (4.1) | Cần thiết khi scale |
| 6 | SLA Reports (4.3) | Cần cho management |

---

## Tóm tắt các file cần sửa (phần 3 - đổi minutes→days)

| File | Thay đổi |
|------|----------|
| `app/schemas/slaSchema.py` | Đổi `max_resolution_minutes` → `max_resolution_days` |
| `app/models/ticket.py` | Đổi `max_resolution_minutes` → `max_resolution_days` |
| `app/services/ticketService.py` | Đổi `timedelta(minutes=...)` → `timedelta(days=...)` |
| Database | Chạy migration để rename column |
