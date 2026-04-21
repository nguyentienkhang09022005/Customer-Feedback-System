from sqlalchemy.orm import Session
from app.models.appointment import Appointment
from typing import List, Optional
import uuid
from datetime import datetime


class AppointmentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, appointment: Appointment) -> Appointment:
        self.db.add(appointment)
        self.db.commit()
        self.db.refresh(appointment)
        return appointment

    def get_by_id(self, appointment_id: uuid.UUID) -> Optional[Appointment]:
        return self.db.query(Appointment).filter(
            Appointment.id_appointment == appointment_id
        ).first()

    def get_by_ticket(self, ticket_id: uuid.UUID) -> List[Appointment]:
        return self.db.query(Appointment).filter(
            Appointment.id_ticket == ticket_id
        ).order_by(Appointment.created_at.desc()).all()

    def get_by_customer(self, customer_id: uuid.UUID) -> List[Appointment]:
        return self.db.query(Appointment).filter(
            Appointment.id_customer == customer_id
        ).order_by(Appointment.created_at.desc()).all()

    def get_by_employee(self, employee_id: uuid.UUID) -> List[Appointment]:
        return self.db.query(Appointment).filter(
            Appointment.id_employee == employee_id
        ).order_by(Appointment.scheduled_at.asc()).all()

    def get_pending_by_employee(self, employee_id: uuid.UUID) -> List[Appointment]:
        return self.db.query(Appointment).filter(
            Appointment.id_employee == employee_id,
            Appointment.status == "pending"
        ).order_by(Appointment.scheduled_at.asc()).all()

    def update(self, appointment: Appointment) -> Appointment:
        self.db.commit()
        self.db.refresh(appointment)
        return appointment

    def delete(self, appointment: Appointment):
        self.db.delete(appointment)
        self.db.commit()