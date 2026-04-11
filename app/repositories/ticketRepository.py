from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.ticket import Ticket, TicketCategory
from app.models.human import Employee
from app.core.constants import TicketStatusConstants
from typing import List, Optional
import uuid


class TicketRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> List[Ticket]:
        return self.db.query(Ticket).all()

    def get_by_id(self, ticket_id: uuid.UUID) -> Optional[Ticket]:
        return self.db.query(Ticket).filter(Ticket.id_ticket == ticket_id).first()

    def get_unassigned(self) -> List[Ticket]:
        return self.db.query(Ticket).filter(Ticket.id_employee == None).all()

    def get_by_department(self, dept_id: uuid.UUID) -> List[Ticket]:
        return self.db.query(Ticket).join(
            Employee, Ticket.id_employee == Employee.id_employee
        ).filter(Employee.id_department == dept_id).all()

    def get_unassigned_by_department(self, dept_id: uuid.UUID) -> List[Ticket]:
        return self.db.query(Ticket).join(
            TicketCategory, Ticket.id_category == TicketCategory.id_category
        ).filter(
            and_(
                TicketCategory.id_department == dept_id,
                Ticket.id_employee == None
            )
        ).all()

    def get_by_employee(self, employee_id: uuid.UUID) -> List[Ticket]:
        return self.db.query(Ticket).filter(
            and_(
                Ticket.id_employee == employee_id,
                Ticket.status.in_(TicketStatusConstants.ACTIVE_STATUSES)
            )
        ).all()

    def get_by_customer(self, customer_id: uuid.UUID) -> List[Ticket]:
        return self.db.query(Ticket).filter(Ticket.id_customer == customer_id).all()

    def get_active_ticket_count(self, employee_id: uuid.UUID) -> int:
        return self.db.query(Ticket).filter(
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

    def delete(self, ticket: Ticket):
        self.db.delete(ticket)
        self.db.commit()
