from sqlalchemy.orm import Session
from app.models.ticket import Ticket
from app.models.human import Employee
from app.repositories.ticketRepository import TicketRepository
from app.repositories.employeeRepository import EmployeeRepository
from app.schemas.notificationSchema import NotificationCreate
from app.services.notificationService import NotificationService
import logging
import uuid
from typing import Optional

logger = logging.getLogger(__name__)


class EscalationService:
    """
    Service xử lý escalation khi ticket cần được chuyển lên cấp cao hơn.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.ticket_repo = TicketRepository(db)
        self.employee_repo = EmployeeRepository(db)
        self.noti_service = NotificationService(db)
    
    def escalate_to_manager(self, ticket: Ticket, reason: str = None) -> bool:
        """
        Escalate ticket lên manager của department.
        Trả về True nếu thành công.
        """
        try:
            if not ticket.id_category:
                logger.warning(f"Cannot escalate ticket {ticket.id_ticket}: no category assigned")
                return False
            
            from app.models.ticket import TicketCategory
            category = self.db.query(TicketCategory).filter(
                TicketCategory.id_category == ticket.id_category
            ).first()
            
            if not category or not category.id_department:
                return False
            
            manager = self.employee_repo.get_department_manager(category.id_department)
            if not manager:
                logger.warning(f"No manager found for department {category.id_department}")
                return False
            
            # Don't notify if manager is already assigned to this ticket
            if manager.id_employee == ticket.id_employee:
                return False
            
            short_title = ticket.title[:30] + "..." if len(ticket.title) > 30 else ticket.title
            reason_text = f" - Lý do: {reason}" if reason else ""
            
            noti_data = NotificationCreate(
                title=f"Ticket được escalation",
                content=f"Ticket #{str(ticket.id_ticket)[:8]}: '{short_title}'{reason_text}.",
                notification_type="SLA_ESCALATED",
                id_reference=ticket.id_ticket,
                id_receiver=manager.id_employee
            )
            self.noti_service.create_and_send(noti_data)
            
            logger.info(f"Ticket {ticket.id_ticket} escalated to manager {manager.id_employee}")
            return True
            
        except Exception as e:
            logger.error(f"Error escalating ticket {ticket.id_ticket} to manager: {e}")
            return False
    
    def escalate_to_level2(self, ticket: Ticket) -> bool:
        """
        Escalate ticket lên cấp Level 2 (hotline/support tier 2).
        Có thể implement thêm department cho Level 2.
        """
        try:
            # TODO: Implement theo business requirement
            # Có thể tạo một department "Level2Support" và escalate vào đó
            
            short_title = ticket.title[:30] + "..." if len(ticket.title) > 30 else ticket.title
            
            # Notify current assignee
            if ticket.id_employee:
                noti_data = NotificationCreate(
                    title=f"Ticket được escalation lên Level 2",
                    content=f"Ticket #{str(ticket.id_ticket)[:8]}: '{short_title}' đã được chuyển lên bộ phận hỗ trợ cấp cao hơn.",
                    notification_type="SLA_ESCALATED",
                    id_reference=ticket.id_ticket,
                    id_receiver=ticket.id_employee
                )
                self.noti_service.create_and_send(noti_data)
            
            return True
            
        except Exception as e:
            logger.error(f"Error escalating ticket {ticket.id_ticket} to level 2: {e}")
            return False
    
    def auto_escalate_overdue_tickets(self) -> dict:
        """
        Auto-escalate tất cả overdue tickets.
        Chạy định kỳ bằng scheduler.
        """
        result = {
            "total_overdue": 0,
            "escalated": 0,
            "errors": 0
        }
        
        try:
            # Lấy tất cả ticket đã quá hạn
            from datetime import datetime
            now = datetime.utcnow()
            
            overdue_tickets = self.db.query(Ticket).filter(
                Ticket.status.in_(["New", "In Progress", "Pending", "On Hold"]),
                Ticket.expired_date < now
            ).all()
            
            result["total_overdue"] = len(overdue_tickets)
            
            for ticket in overdue_tickets:
                try:
                    if self.escalate_to_manager(ticket, "Quá hạn SLA"):
                        result["escalated"] += 1
                except Exception as e:
                    result["errors"] += 1
                    logger.error(f"Error auto-escalating ticket {ticket.id_ticket}: {e}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in auto_escalate_overdue_tickets: {e}")
            return result
