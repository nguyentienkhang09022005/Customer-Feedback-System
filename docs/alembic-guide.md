# Alembic Migration Guide

## Overview

Project sử dụng **Alembic** để quản lý database schema migrations, thay thế cho cách cũ dùng `create_db.py` + `Base.metadata.create_all()`.

## Tại sao cần Alembic?

| Cách cũ (`create_db.py`) | Alembic |
|--------------------------|---------|
| Chỉ tạo table mới, không alter existing | Tự sinh `ALTER TABLE` khi đổi model |
| Mất data khi drop/create table | Giữ data khi migrate |
| Không rollback được | Có `downgrade` để quay lại |

## Quick Start

### Commands thường dùng

```bash
# Tạo migration mới khi thay đổi model
alembic revision --autogenerate -m "description"

# Apply migration lên database
alembic upgrade head

# Rollback 1 version
alembic downgrade -1

# Rollback về ban đầu (xóa hết)
alembic downgrade base

# Xem migration history
alembic history

# Xem current version
alembic current

# Kiểm tra schema có sync không
alembic check

# Tạo migration rỗng (manual viết SQL)
alembic revision -m "empty migration"
```

### Ví dụ: Thêm column mới

1. **Sửa model** (ví dụ thêm `avatar` vào `Human`):
```python
# app/models/human.py
class Human(Base):
    # ... existing columns ...
    avatar = Column(String(255))  # Thêm dòng này
```

2. **Tạo migration**:
```bash
alembic revision --autogenerate -m "add avatar to humans"
```

3. **Kiểm tra migration file** trong `migrations/versions/`:
```python
# Xem nội dung, убедитесь SQL đúng
def upgrade() -> None:
    with op.batch_alter_table("humans") as batch_op:
        batch_op.add_column(sa.Column('avatar', sa.String(length=255), nullable=True))
```

4. **Apply**:
```bash
alembic upgrade head
```

### Ví dụ: Rollback

Nếu lỗi và muốn quay lại:
```bash
alembic downgrade -1
```

## Project Structure

```
Customer-Feedback-System/
├── alembic.ini              # Alembic configuration
├── migrations/
│   ├── env.py              # Migration environment - import models và setup
│   ├── script.py.mako      # Template cho migration files
│   ├── README              # Alembic README
│   └── versions/           # Migration files
│       └── xxxxx_initial_schema.py
├── app/
│   ├── db/
│   │   ├── base.py         # Chỉ chứa Base = declarative_base()
│   │   └── session.py      # Engine, SessionLocal, get_db()
│   └── models/             # Tất cả models đặt ở đây
└── create_db.py            # DEPRECATED - chỉ dùng để reference
```

## Configuration

### Database URL

URL được lấy từ `settings.DATABASE_URL` trong `app/core/config.py`, không hardcode trong `alembic.ini`.

Xem trong `migrations/env.py`:
```python
from app.core.config import settings
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
```

### Models Import

Tất cả models được import trong `migrations/env.py` để Alembic autogenerate so sánh được:
```python
from app.models.human import Role, CustomerType, Human, Employee, Customer
from app.models.ticket import TicketCategory, SLAPolicy, Ticket
from app.models.interaction import Message, Attachment, Evaluate, Notification
from app.models.system import AuditLog, FAQArticle
from app.db.base import Base
```

## Migration File Structure

```python
"""migration description

Revision ID: xxxxx
Revises: xxxxx (hoặc None nếu là initial)
Create Date: 2024-01-01 00:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'xxxxx'
down_revision: Union[str, Sequence[str], None] = 'xxxxx'  # Migration trước đó
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Upgrade schema."""
    # SQL commands here
    op.create_table('new_table', ...)
    op.add_column('existing_table', sa.Column('new_col', sa.String()))

def downgrade() -> None:
    """Downgrade schema."""
    # Reverse SQL commands
    op.drop_column('existing_table', 'new_col')
    op.drop_table('new_table')
```

## Best Practices

### 1. Mỗi migration nên nhỏ, tập trung vào 1 thay đổi

```bash
# Tốt - mỗi migration 1 thay đổi
alembic revision --autogenerate -m "add email to customers"
alembic revision --autogenerate -m "add phone to customers"

# Tránh - 1 migration nhiều thay đổi không liên quan
alembic revision --autogenerate -m "add email and phone and address"
```

### 2. Viết migration message rõ ràng

```bash
# Tốt
alembic revision --autogenerate -m "add membership_tier column to customers table"

# Tránh
alembic revision --autogenerate -m "update"
alembic revision --autogenerate -m "fix stuff"
```

### 3. Không edit migration đã apply

Một khi `alembic upgrade head` đã chạy, **KHÔNG** edit migration đó. Nếu cần thay đổi:
- Tạo migration mới để fix
- Hoặc rollback rồi tạo lại (chỉ dev environment)

### 4. Test downgrade trước khi merge

```bash
# Apply
alembic upgrade head

# Test downgrade
alembic downgrade -1

# Re-apply
alembic upgrade head
```

## Troubleshooting

### "Target database is not up to date"

```bash
# Kiểm tra current
alembic current

# Check
alembic check

# Nếu cần, stamp với current migration
alembic stamp head
```

### "Can't locate revision"

```bash
# Xem history
alembic history

# Hoặc stamp trực tiếp
alembic stamp <revision_id>
```

### Autogenerate không detect thay đổi

Kiểm tra:
1. Model đã được import trong `env.py`?
2. `target_metadata = Base.metadata` đã set?
3. Column có đặt trong model class, không phải `__init__`?

### Lỗi khi apply migration có data

Nếu migration thêm column với `NOT NULL` mà không có default:
```python
# Sai - sẽ fail nếu có data
op.add_column('table', sa.Column('new_col', sa.String(), nullable=False))

# Đúng - thêm nullable trước, rồi update, rồi alter NOT NULL
op.add_column('table', sa.Column('new_col', sa.String(), nullable=True))
# ... batch op.execute("UPDATE table SET new_col = 'default' WHERE new_col IS NULL")
# ... op.alter_column('table', 'new_col', nullable=False)
```

## Deprecation Notice

`create_db.py` đã deprecated. **KHÔNG** dùng `python create_db.py` để tạo/cập nhật database nữa.

Thay bằng:
```bash
alembic upgrade head
```

## Further Reading

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [Autogenerate Reference](https://alembic.sqlalchemy.org/en/latest/autogenerate.html)
- [Migration API](https://alembic.sqlalchemy.org/en/latest/ops.html)