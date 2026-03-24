"""create departments table and migrate department FK

Revision ID: 2026_03_24_0001
Revises: c8ef65d838e9
Create Date: 2026-03-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid


revision: str = '2026_03_24_0001'
down_revision: Union[str, Sequence[str], None] = 'c8ef65d838e9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Step 1: Create departments table
    op.create_table(
        'departments',
        sa.Column('id_department', sa.UUID(), primary_key=True, default=uuid.uuid4),
        sa.Column('name', sa.String(length=50), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
    )
    
    # Step 2: Seed departments data
    departments = [
        ('Finance', 'Phòng Tài Chính'),
        ('HR', 'Phòng Nhân Sự'),
        ('IT', 'Phòng Công Nghệ Thông Tin'),
        ('Support', 'Phòng Hỗ Trợ Khách Hàng'),
        ('Sales', 'Phòng Kinh Doanh'),
    ]
    
    dept_ids = {}
    for name, description in departments:
        dept_id = str(uuid.uuid4())
        dept_ids[name] = dept_id
        op.execute(
            f"INSERT INTO departments (id_department, name, description) VALUES ('{dept_id}', '{name}', '{description}')"
        )
    
    # Step 3: Add id_department FK to employees (nullable initially)
    op.add_column('employees', sa.Column('id_department', sa.UUID(), sa.ForeignKey("departments.id_department"), nullable=True))
    
    # Step 4: Add id_department FK to tickets_category (nullable initially)
    op.add_column('tickets_category', sa.Column('id_department', sa.UUID(), sa.ForeignKey("departments.id_department"), nullable=True))
    
    # Step 5: Migrate employees.department string to id_department FK
    for name, dept_id in dept_ids.items():
        op.execute(f"UPDATE employees SET id_department = '{dept_id}' WHERE department = '{name}'")
    
    # Step 6: Migrate tickets_category.department string to id_department FK
    for name, dept_id in dept_ids.items():
        op.execute(f"UPDATE tickets_category SET id_department = '{dept_id}' WHERE department = '{name}'")
    
    # Step 7: Set default department 'Support' for employees without department
    if 'Support' in dept_ids:
        op.execute(f"UPDATE employees SET id_department = '{dept_ids['Support']}' WHERE id_department IS NULL")
        op.execute(f"UPDATE tickets_category SET id_department = '{dept_ids['Support']}' WHERE id_department IS NULL")
    
    # Step 8: Make id_department NOT NULL
    op.alter_column('employees', 'id_department', nullable=False)
    op.alter_column('tickets_category', 'id_department', nullable=False)
    
    # Step 9: Drop old department string columns
    op.drop_column('employees', 'department')
    op.drop_column('tickets_category', 'department')


def downgrade() -> None:
    # Need to create string department columns and migrate data back
    op.add_column('employees', sa.Column('department', sa.String(length=50), nullable=True))
    op.add_column('tickets_category', sa.Column('department', sa.String(length=50), nullable=True))
    
    # Get department names from FK ids
    op.execute("""
        UPDATE employees e
        SET department = d.name
        FROM departments d
        WHERE e.id_department = d.id_department
    """)
    
    op.execute("""
        UPDATE tickets_category tc
        SET department = d.name
        FROM departments d
        WHERE tc.id_department = d.id_department
    """)
    
    op.alter_column('employees', 'department', nullable=False)
    op.alter_column('tickets_category', 'department', nullable=False)
    
    op.drop_column('tickets_category', 'id_department')
    op.drop_column('employees', 'id_department')
    op.drop_table('departments')
