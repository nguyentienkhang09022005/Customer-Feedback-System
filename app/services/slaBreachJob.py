from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.ticket import Ticket
from app.models.human import Employee
from app.repositories.ticketRepository import TicketRepository
from app.repositories.employeeRepository import EmployeeRepository
from app.schemas.notificationSchema import NotificationCreate
from app.services.notificationService import NotificationService
from datetime import datetime
import logging
import uuid

logger = logging.getLogger(__name__)


class SLABreachJob:
    """Background job to check and handle SLA breaches"""
    
    def __init__(self, db: Session):
        self.db = db
        self.ticket_repo = TicketRepository(db)
        self.employee_repo = EmployeeRepository(db)
        self.noti_service = NotificationService(db)
    
    def check_overdue_tickets(self) -> dict:
        """
        Kiểm tra tất cả ticket đang active và xử lý quá hạn SLA.
        Trả về dict với số lượng tickets đã xử lý.
        """
        result = {
            "checked": 0,
            "overdue": 0,
            "warning": 0,
            "escalated": 0
        }
        
        try:
            # Lấy tất cả ticket đang active (chưa resolved/closed)
            active_tickets = self.db.query(Ticket).filter(
                Ticket.status.in_(["New", "In Progress", "Pending", "On Hold"])
            ).all()
            
            result["checked"] = len(active_tickets)
            now = datetime.utcnow()
            
            for ticket in active_tickets:
                if not ticket.expired_date:
                    continue
                
                # Kiểm tra overdue
                if ticket.expired_date < now:
                    result["overdue"] += 1
                    self._handle_overdue_ticket(ticket)
                
                # Kiểm tra cảnh báo (sắp hết SLA - trong vòng 24h)
                elif self._is_within_warning_window(ticket.expired_date, now):
                    result["warning"] += 1
                    self._send_sla_warning(ticket)
            
            return result
            
        except Exception as e:
            logger.error(f"Error checking overdue tickets: {e}")
            return result
    
    def _is_within_warning_window(self, expired_date: datetime, now: datetime, window_hours: int = 24) -> bool:
        """Kiểm tra xem ticket có trong cửa sổ cảnh báo không (trước khi hết hạn window_hours giờ)"""
        time_diff = expired_date - now
        return 0 < time_diff.total_seconds() <= (window_hours * 3600)
    
    def _handle_overdue_ticket(self, ticket: Ticket):
        """Xử lý ticket đã quá hạn SLA - gửi notification và escalate"""
        try:
            logger.warning(f"Ticket {ticket.id_ticket} is overdue! Escalating...")
            
            # 1. Notify assigned employee
            if ticket.id_employee:
                self._notify_employee_breach(ticket, ticket.id_employee)
                
                # 2. Escalate to manager
                if ticket.id_category:
                    from app.models.ticket import TicketCategory
                    category = self.db.query(TicketCategory).filter(
                        TicketCategory.id_category == ticket.id_category
                    ).first()
                    
                    if category and category.id_department:
                        manager = self.employee_repo.get_department_manager(category.id_department)
                        if manager and manager.id != ticket.id_employee:
                            self._notify_manager_breach(ticket, manager.id_employee)
                            logger.info(f"Escalated ticket {ticket.id_ticket} to manager {manager.id_employee}")
            
            # 3. Update ticket status if critical overdue (optional - configurable)
            # Có thể tự động chuyển sang escalated status
            
        except Exception as e:
            logger.error(f"Error handling overdue ticket {ticket.id_ticket}: {e}")
    
    def _send_sla_warning(self, ticket: Ticket):
        """Gửi cảnh báo SLA sắp hết hạn cho assigned employee"""
        try:
            if not ticket.id_employee:
                return
            
            short_title = ticket.title[:30] + "..." if len(ticket.title) > 30 else ticket.title
            hours_remaining = self._get_hours_remaining(ticket.expired_date)
            
            noti_data = NotificationCreate(
                title=f"SLA cảnh báo - {hours_remaining:.1f}h còn lại",
                content=f"Ticket #{str(ticket.id_ticket)[:8]}: '{short_title}' sắp hết SLA. Vui lòng ưu tiên xử lý!",
                notification_type="SLA_WARNING",
                id_reference=ticket.id_ticket,
                id_receiver=ticket.id_employee
            )
            self.noti_service.create_and_send(noti_data)
            
        except Exception as e:
            logger.error(f"Error sending SLA warning for ticket {ticket.id_ticket}: {e}")
    
    def _notify_employee_breach(self, ticket: Ticket, employee_id: uuid.UUID):
        """Notify employee that their ticket is breached"""
        try:
            short_title = ticket.title[:30] + "..." if len(ticket.title) > 30 else ticket.title
            
            noti_data = NotificationCreate(
                title=f"SLA BREACHED - Ticket quá hạn!",
                content=f"Ticket #{str(ticket.id_ticket)[:8]}: '{short_title}' đã quá hạn SLA. Vui lòng xử lý ngay!",
                notification_type="SLA_BREACHED",
                id_reference=ticket.id_ticket,
                id_receiver=employee_id
            )
            self.noti_service.create_and_send(noti_data)
        except Exception as e:
            logger.error(f"Error notifying employee breach: {e}")
    
    def _notify_manager_breach(self, ticket: Ticket, manager_id: uuid.UUID):
        """Notify manager about breached ticket"""
        try:
            short_title = ticket.title[:30] + "..." if len(ticket.title) > 30 else ticket.title
            
            noti_data = NotificationCreate(
                title=f"Ticket bị quá hạn SLA - Cần escalation",
                content=f"Ticket #{str(ticket.id_ticket)[:8]}: '{short_title}' đã quá hạn. Nhân viên được giao chưa xử lý kịp.",
                notification_type="SLA_ESCALATED",
                id_reference=ticket.id_ticket,
                id_receiver=manager_id
            )
            self.noti_service.create_and_send(noti_data)
        except Exception as e:
            logger.error(f"Error notifying manager breach: {e}")
    
    def _get_hours_remaining(self, expired_date: datetime) -> float:
        """Tính số giờ còn lại trước khi hết hạn"""
        now = datetime.utcnow()
        diff = expired_date - now
        return diff.total_seconds() / 3600


def run_sla_breach_check(db: Session):
    """Standalone function để chạy SLA breach check (có thể gọi từ scheduler)"""
    job = SLABreachJob(db)
    result = job.check_overdue_tickets()
    logger.info(f"SLA breach check completed: {result}")
    return result
