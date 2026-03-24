import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Float, Date, UUID, Integer
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base


class Role(Base):
    __tablename__ = "roles"
    role_name = Column(String(50), primary_key=True, index=True)
    description = Column(String(255))


class CustomerType(Base):
    __tablename__ = "customer_type"
    type_name = Column(String(50), primary_key=True, index=True)
    description = Column(String(255))


class Human(Base):
    __tablename__ = "humans"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    first_name = Column(String(50))
    last_name = Column(String(50))
    email = Column(String(100), unique=True, index=True, nullable=False)
    phone = Column(String(20))
    address = Column(String(255))
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    status = Column(String(20), default="Active")
    avatar = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    type = Column(String(50))
    __mapper_args__ = {
        "polymorphic_identity": "human",
        "polymorphic_on": type,
    }


class Employee(Human):
    __tablename__ = "employees"
    id_employee = Column(UUID(as_uuid=True), ForeignKey("humans.id", ondelete="CASCADE"), primary_key=True)
    id_department = Column(UUID(as_uuid=True), ForeignKey("departments.id_department", ondelete="SET NULL"), nullable=True)
    employee_code = Column(String(20), unique=True)
    job_title = Column(String(50))
    max_ticket_capacity = Column(Integer, default=5)
    csat_score = Column(Float, default=0.0)
    hire_date = Column(Date)

    role_name = Column(String(50), ForeignKey("roles.role_name", ondelete="SET NULL"))

    __mapper_args__ = {
        "polymorphic_identity": "employee",
    }


class Customer(Human):
    __tablename__ = "customers"
    id_customer = Column(UUID(as_uuid=True), ForeignKey("humans.id", ondelete="CASCADE"), primary_key=True)
    customer_code = Column(String(20), unique=True)
    membership_tier = Column(String(20))
    timezone = Column(String(50))

    customer_type = Column(String(50), ForeignKey("customer_type.type_name", ondelete="SET NULL"))

    __mapper_args__ = {
        "polymorphic_identity": "customer",
    }