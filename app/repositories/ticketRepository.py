from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from app.models.ticket import Ticket
from app.models.human import Employee
from app.core.constants import TicketStatusConstants
from typing import List, Optional
import uuid
from datetime import datetime


class TicketRepository:
    def __init__(self, db: Session):
        self.db = db

    def _base_query(self):
        return self.db.query(Ticket).filter(Ticket.is_deleted == False).options(
            joinedload(Ticket.template)
        )

    def get_all(self) -> List[Ticket]:
        return self._base_query().all()

    def get_by_id(self, ticket_id: uuid.UUID) -> Optional[Ticket]:
        return self._base_query().filter(Ticket.id_ticket == ticket_id).first()

    def get_unassigned(self) -> List[Ticket]:
        return self._base_query().filter(Ticket.id_employee == None).all()

    def get_by_department(self, dept_id: uuid.UUID) -> List[Ticket]:
        return self._base_query().join(
            Employee, Ticket.id_employee == Employee.id_employee
        ).filter(Employee.id_department == dept_id).all()

    def get_by_employee(self, employee_id: uuid.UUID, include_closed: bool = False) -> List[Ticket]:
        query = self._base_query().filter(Ticket.id_employee == employee_id)
        if not include_closed:
            query = query.filter(Ticket.status.in_(TicketStatusConstants.ACTIVE_STATUSES))
        else:
            query = query.filter(Ticket.status == "Closed")
        return query.all()

    def get_by_customer(self, customer_id: uuid.UUID, include_closed: bool = False, limit: int = 100) -> List[Ticket]:
        query = self._base_query().filter(Ticket.id_customer == customer_id)
        if not include_closed:
            query = query.filter(Ticket.status != "Closed")
        return query.order_by(Ticket.created_at.desc()).limit(limit).all()

    def get_active_ticket_count(self, employee_id: uuid.UUID) -> int:
        return self._base_query().filter(
            and_(
                Ticket.id_employee == employee_id,
                Ticket.status.in_(TicketStatusConstants.ACTIVE_STATUSES)
            )
        ).count()

    def create(self, ticket: Ticket) -> Ticket:
        self.db.add(ticket)
        self.db.commit()
        self.db.refresh(ticket)
        return ticket

    def update(self, ticket: Ticket) -> Ticket:
        self.db.commit()
        self.db.refresh(ticket)
        return ticket

    def assign_to_employee(self, ticket_id: uuid.UUID, employee_id: uuid.UUID) -> Ticket:
        ticket = self.get_by_id(ticket_id)
        if ticket:
            ticket.id_employee = employee_id
            self.db.commit()
            self.db.refresh(ticket)
        return ticket

    def soft_delete(self, ticket: Ticket) -> Ticket:
        ticket.is_deleted = True
        ticket.deleted_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(ticket)
        return ticket

    def delete(self, ticket: Ticket):
        self.db.delete(ticket)
        self.db.commit()
