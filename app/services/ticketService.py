from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.repositories.ticketRepository import TicketRepository
from app.repositories.ticketCategoryRepository import TicketCategoryRepository
from app.repositories.slaRepository import SLAPolicyRepository
from app.repositories.humanRepository import HumanRepository
from app.models.ticket import Ticket
from app.schemas.ticketSchema import TicketCreate, TicketUpdate, TicketAssign
from app.services.loadBalancer import LoadBalancer
from typing import List, Optional
import uuid
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


async def broadcast_ticket_assigned(ticket_id: str, employee_id: str):
    try:
        from app.socketio.manager import broadcast_to_ticket
        await broadcast_to_ticket(
            str(ticket_id),
            "ticket_assigned",
            {
                "ticket_id": str(ticket_id),
                "employee_id": str(employee_id)
            }
        )
    except Exception:
        pass


def _send_ticket_email_notification(ticket: Ticket, event_type: str, recipient_email: str = None):
    """Helper to send ticket email notification"""
    try:
        from app.services.emailService import email_service
        
        # If no recipient email provided, try to determine from ticket
        if not recipient_email:
            # This would require additional queries to get emails
            # For now, skip if no email
            return
        
        email_service.send_ticket_notification(
            to_email=recipient_email,
            ticket_id=str(ticket.id_ticket),
            event_type=event_type,
            additional_info={
                "title": ticket.title,
                "status": ticket.status,
                "severity": ticket.severity
            }
        )
    except Exception as e:
        logger.warning(f"Failed to send ticket email notification: {e}")


class TicketService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = TicketRepository(db)
        self.category_repo = TicketCategoryRepository(db)
        self.sla_repo = SLAPolicyRepository(db)
        self.load_balancer = LoadBalancer(db)

    def create_ticket(self, data: TicketCreate, customer_id: uuid.UUID) -> Ticket:
        category = self.category_repo.get_by_id(str(data.id_category))
        if not category:
            raise HTTPException(status_code=404, detail="Không tìm thấy danh mục!")

        if not category.is_active:
            raise HTTPException(status_code=400, detail="Danh mục không hoạt động!")

        expired_date = None
        active_sla = self.sla_repo.get_active_by_severity(data.severity)

        if active_sla:
            expired_date = datetime.utcnow() + timedelta(minutes=active_sla.max_resolution_minutes)
        else:
            expired_date = None

        ticket = Ticket(
            title=data.title,
            description=data.description,
            severity=data.severity,
            status="New",
            id_category=data.id_category,
            id_customer=customer_id,
            id_employee=None,
            expired_date=expired_date
        )

        created_ticket = self.repo.create(ticket)

        # Send email notification to customer
        try:
            human_repo = HumanRepository(self.db)
            customer = human_repo.get_by_id(str(customer_id))
            if customer and customer.email:
                _send_ticket_email_notification(created_ticket, 'created', customer.email)
        except Exception as e:
            logger.warning(f"Failed to send ticket created email: {e}")

        if category.auto_assign and category.id_department:
            best_employee = self.load_balancer.get_best_employee_for_department(category.id_department)
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

    def get_tickets_by_department(self, dept_id: uuid.UUID) -> List[Ticket]:
        return self.repo.get_by_department(dept_id)

    def get_tickets_by_employee(self, employee_id: uuid.UUID) -> List[Ticket]:
        return self.repo.get_by_employee(employee_id)

    def get_tickets_by_customer(self, customer_id: uuid.UUID) -> List[Ticket]:
        return self.repo.get_by_customer(customer_id)

    def update_ticket(self, ticket_id: uuid.UUID, data: TicketUpdate) -> Ticket:
        ticket = self.repo.get_by_id(ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Không tìm thấy ticket!")

        update_data = data.model_dump(exclude_unset=True)

        if "severity" in update_data and update_data["severity"] != ticket.severity:
            active_sla = self.sla_repo.get_active_by_severity(update_data["severity"])
            if active_sla:
                update_data["expired_date"] = datetime.utcnow() + timedelta(minutes=active_sla.max_resolution_minutes)

        if "id_category" in update_data and update_data["id_category"] != ticket.id_category:
            new_category = self.category_repo.get_by_id(str(update_data["id_category"]))
            if not new_category:
                raise HTTPException(status_code=404, detail="Không tìm thấy danh mục mới!")

            update_data["id_employee"] = None
            if new_category.auto_assign and new_category.id_department:
                best_employee = self.load_balancer.get_best_employee_for_department(new_category.id_department)
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
        
        result = self.repo.assign_to_employee(ticket_id, data.id_employee)
        
        # Send email notification to assigned employee
        try:
            human_repo = HumanRepository(self.db)
            employee = human_repo.get_by_id(str(data.id_employee))
            if employee and employee.email:
                _send_ticket_email_notification(result, 'assigned', employee.email)
        except Exception as e:
            logger.warning(f"Failed to send ticket assigned email: {e}")
        
        try:
            import asyncio
            asyncio.create_task(broadcast_ticket_assigned(str(ticket_id), str(data.id_employee)))
        except RuntimeError:
            pass
        return result

    def delete_ticket(self, ticket_id: uuid.UUID):
        ticket = self.repo.get_by_id(ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Không tìm thấy ticket!")
        self.repo.delete(ticket)

    def get_unassigned_tickets_by_department(self, dept_id: uuid.UUID) -> List[Ticket]:
        return self.repo.get_unassigned_by_department(dept_id)

    def _trigger_csat_survey(self, ticket: Ticket):
        """Trigger CSAT survey for resolved ticket - placeholder for future implementation"""
        try:
            # TODO: Implement CSAT survey triggering logic
            # This could send an email/SMS with survey link to customer
            logger.info(f"CSAT survey triggered for ticket {ticket.id_ticket}")
        except Exception as e:
            logger.warning(f"Failed to trigger CSAT survey: {e}")

    def resolve_ticket(self, ticket_id: uuid.UUID, resolution_note: str = None) -> Ticket:
        """Resolve ticket - chuyển sang Resolved status và trigger CSAT survey"""
        ticket = self.repo.get_by_id(ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Không tìm thấy ticket!")
        
        ticket.status = "Resolved"
        ticket.resolution_note = resolution_note
        
        updated_ticket = self.repo.update(ticket)
        
        # Trigger CSAT survey
        self._trigger_csat_survey(ticket)
        
        return updated_ticket

    def close_ticket(self, ticket_id: uuid.UUID, reason: str = None) -> Ticket:
        """Close ticket - chỉ cho phép close từ Resolved"""
        ticket = self.repo.get_by_id(ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Không tìm thấy ticket!")
        
        if ticket.status != "Resolved":
            raise HTTPException(status_code=400, detail="Chỉ có thể đóng ticket từ trạng thái Resolved!")
        
        ticket.status = "Closed"
        ticket.resolution_note = reason
        
        return self.repo.update(ticket)
