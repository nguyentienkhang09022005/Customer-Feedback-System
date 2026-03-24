from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.repositories.ticketRepository import TicketRepository
from app.repositories.ticketCategoryRepository import TicketCategoryRepository
from app.models.ticket import Ticket
from app.schemas.ticketSchema import TicketCreate, TicketUpdate, TicketAssign
from app.services.loadBalancer import LoadBalancer
from typing import List, Optional
import uuid


class TicketService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = TicketRepository(db)
        self.category_repo = TicketCategoryRepository(db)
        self.load_balancer = LoadBalancer(db)

    def create_ticket(self, data: TicketCreate, customer_id: uuid.UUID) -> Ticket:
        category = self.category_repo.get_by_id(str(data.id_category))
        if not category:
            raise HTTPException(status_code=404, detail="Không tìm thấy danh mục!")
        
        if not category.is_active:
            raise HTTPException(status_code=400, detail="Danh mục không hoạt động!")
        
        ticket = Ticket(
            title=data.title,
            description=data.description,
            severity=data.severity,
            status="New",
            id_category=data.id_category,
            id_customer=customer_id,
            id_employee=None
        )
        
        created_ticket = self.repo.create(ticket)
        
        if category.auto_assign and category.department:
            best_employee = self.load_balancer.get_best_employee_for_department(category.department)
            if best_employee:
                created_ticket = self.repo.assign_to_employee(created_ticket.id_ticket, best_employee.id_employee)
                created_ticket.status = "In Progress"
                self.repo.update(created_ticket)
        
        return created_ticket

    def get_all_tickets(self) -> List[Ticket]:
        return self.repo.get_all()

    def get_ticket_by_id(self, ticket_id: uuid.UUID) -> Optional[Ticket]:
        ticket = self.repo.get_by_id(ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Không tìm thấy ticket!")
        return ticket

    def get_unassigned_tickets(self) -> List[Ticket]:
        return self.repo.get_unassigned()

    def get_tickets_by_department(self, department: str) -> List[Ticket]:
        return self.repo.get_by_department(department)

    def get_tickets_by_employee(self, employee_id: uuid.UUID) -> List[Ticket]:
        return self.repo.get_by_employee(employee_id)

    def update_ticket(self, ticket_id: uuid.UUID, data: TicketUpdate) -> Ticket:
        ticket = self.repo.get_by_id(ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Không tìm thấy ticket!")
        
        update_data = data.model_dump(exclude_unset=True)
        
        if "id_category" in update_data and update_data["id_category"] != ticket.id_category:
            new_category = self.category_repo.get_by_id(str(update_data["id_category"]))
            if not new_category:
                raise HTTPException(status_code=404, detail="Không tìm thấy danh mục mới!")
            
            update_data["id_employee"] = None
            if new_category.auto_assign and new_category.department:
                best_employee = self.load_balancer.get_best_employee_for_department(new_category.department)
                if best_employee:
                    update_data["id_employee"] = best_employee.id_employee
                    update_data["status"] = "In Progress"
        
        for key, value in update_data.items():
            setattr(ticket, key, value)
        
        return self.repo.update(ticket)

    def assign_ticket(self, ticket_id: uuid.UUID, data: TicketAssign) -> Ticket:
        ticket = self.repo.get_by_id(ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Không tìm thấy ticket!")
        
        return self.repo.assign_to_employee(ticket_id, data.id_employee)

    def delete_ticket(self, ticket_id: uuid.UUID):
        ticket = self.repo.get_by_id(ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Không tìm thấy ticket!")
        self.repo.delete(ticket)

    def get_unassigned_tickets_by_department(self, department: str) -> List[Ticket]:
        return self.repo.get_unassigned_by_department(department)
