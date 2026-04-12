from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.repositories.ticketRepository import TicketRepository
from app.repositories.ticketCategoryRepository import TicketCategoryRepository
from app.repositories.slaRepository import SLAPolicyRepository
from app.repositories.humanRepository import HumanRepository
from app.models.ticket import Ticket
from app.schemas.ticketSchema import TicketCreate, TicketUpdate, TicketAssign
from app.services.loadBalancer import LoadBalancer
from app.core.constants import TicketStatusConstants
from typing import List, Optional
import uuid
from datetime import datetime, timedelta
import logging

from app.services.notificationService import NotificationService

logger = logging.getLogger(__name__)


def _validate_status_transition(current_status: str, new_status: str) -> bool:
    """Check if a status transition is valid"""
    if current_status == new_status:
        return True  # No change
    allowed_transitions = TicketStatusConstants.STATUS_TRANSITIONS.get(current_status, [])
    return new_status in allowed_transitions


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
        # Check rate limit
        if not self._check_ticket_creation_rate_limit(customer_id):
            raise HTTPException(
                status_code=429, 
                detail="Bạn đã tạo quá nhiều tickets. Vui lòng thử lại sau."
            )
        
        category = self.category_repo.get_by_id(str(data.id_category))
        if not category:
            raise HTTPException(status_code=404, detail="Không tìm thấy danh mục!")

        if not category.is_active:
            raise HTTPException(status_code=400, detail="Danh mục không hoạt động!")

        expired_date = None
        active_sla = self.sla_repo.get_active_by_severity(data.severity)

        if active_sla:
            expired_date = datetime.utcnow() + timedelta(days=active_sla.max_resolution_days)
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
            # Use assign_ticket_with_lock to prevent race condition when multiple
            # concurrent requests try to assign tickets to the same employee
            best_employee = self.load_balancer.assign_ticket_with_lock(
                created_ticket.id_ticket, 
                category.id_department
            )
            if best_employee:
                created_ticket.status = "In Progress"
                self.repo.update(created_ticket)
        else:
            # Notify department members about unassigned ticket
            self._notify_department_about_unassigned_ticket(created_ticket, category)

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

    def update_ticket(self, ticket_id: uuid.UUID, data: TicketUpdate, actor_id: uuid.UUID = None) -> Ticket:
        ticket = self.repo.get_by_id(ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Không tìm thấy ticket!")

        update_data = data.model_dump(exclude_unset=True)

        # Validate status transition if status is being changed
        if "status" in update_data:
            new_status = update_data["status"]
            if not _validate_status_transition(ticket.status, new_status):
                raise HTTPException(
                    status_code=400,
                    detail=f"Không thể chuyển từ '{ticket.status}' sang '{new_status}'. "
                           f"Các trạng thái cho phép: {STATUS_TRANSITIONS.get(ticket.status, [])}"
                )
        
        # Validate new status value is valid
        if "status" in update_data and update_data["status"] not in TicketStatusConstants.VALID_STATUSES:
            raise HTTPException(status_code=400, detail=f"Trạng thái '{update_data['status']}' không hợp lệ!")

        if "severity" in update_data and update_data["severity"] != ticket.severity:
            active_sla = self.sla_repo.get_active_by_severity(update_data["severity"])
            if active_sla:
                update_data["expired_date"] = datetime.utcnow() + timedelta(days=active_sla.max_resolution_days)

        if "id_category" in update_data and update_data["id_category"] != ticket.id_category:
            new_category = self.category_repo.get_by_id(str(update_data["id_category"]))
            if not new_category:
                raise HTTPException(status_code=404, detail="Không tìm thấy danh mục mới!")

            update_data["id_employee"] = None
            if new_category.auto_assign and new_category.id_department:
                # Use assign_ticket_with_lock to prevent race condition
                best_employee = self.load_balancer.assign_ticket_with_lock(
                    ticket_id, 
                    new_category.id_department
                )
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

    def _check_ticket_creation_rate_limit(self, customer_id: uuid.UUID) -> bool:
        """Check if customer has exceeded ticket creation rate limit"""
        try:
            from app.services.redisService import RedisService
            redis_service = RedisService()
            
            key = f"rate_limit:ticket_create:{customer_id}"
            current_count = redis_service.get(key)
            
            if current_count is None:
                # First ticket in window
                redis_service.set_with_expiry(key, "1", TicketStatusConstants.RATE_LIMIT_WINDOW_SECONDS)
                return True
            
            if int(current_count) >= TicketStatusConstants.RATE_LIMIT_TICKETS:
                return False
            
            # Increment counter
            redis_service.increment(key)
            return True
        except Exception as e:
            # If Redis fails, allow the request (fail-open)
            logger.warning(f"Rate limit check failed, allowing request: {e}")
            return True

    def get_unassigned_tickets_by_department(self, dept_id: uuid.UUID) -> List[Ticket]:
        return self.repo.get_unassigned_by_department(dept_id)

    def _notify_department_about_unassigned_ticket(self, ticket: Ticket, category):
        """Notify department members about a new unassigned ticket"""
        try:
            from app.repositories.employeeRepository import EmployeeRepository
            from app.schemas.notificationSchema import NotificationCreate
            from app.services.notificationService import NotificationService
            
            emp_repo = EmployeeRepository(self.db)
            noti_service = NotificationService(self.db)
            
            # Get all active department members (including manager)
            members = emp_repo.get_department_all_members(category.id_department)
            
            if not members:
                return
            
            short_title = ticket.title[:30] + "..." if len(ticket.title) > 30 else ticket.title
            title = f"Ticket mới chưa được phân công"
            content = f"Ticket #{str(ticket.id_ticket)[:8]}: '{short_title}' đang chờ được tiếp nhận."
            
            for member in members:
                if member.status == "Active":
                    try:
                        noti_data = NotificationCreate(
                            title=title,
                            content=content,
                            notification_type="TICKET_UNASSIGNED",
                            id_reference=ticket.id_ticket,
                            id_receiver=member.id
                        )
                        noti_service.create_and_send(noti_data)
                    except Exception as e:
                        logger.warning(f"Failed to notify member {member.id}: {e}")
                        
        except Exception as e:
            logger.warning(f"Failed to notify department about unassigned ticket: {e}")

    def _trigger_csat_survey(self, ticket: Ticket):
        """Trigger CSAT survey for resolved ticket - placeholder for future implementation"""
        try:
            # TODO: Implement CSAT survey triggering logic
            # This could send an email/SMS with survey link to customer
            logger.info(f"CSAT survey triggered for ticket {ticket.id_ticket}")
        except Exception as e:
            logger.warning(f"Failed to trigger CSAT survey: {e}")

    def resolve_ticket(self, ticket_id: uuid.UUID, resolution_note: str = None, actor_id: uuid.UUID = None) -> Ticket:
        """Resolve ticket - chuyển sang Resolved status và trigger CSAT survey"""
        ticket = self.repo.get_by_id(ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Không tìm thấy ticket!")
        
        # Validate status transition
        if not _validate_status_transition(ticket.status, "Resolved"):
            raise HTTPException(
                status_code=400,
                detail=f"Không thể giải quyết ticket từ trạng thái '{ticket.status}'. "
                       f"Ticket phải ở trạng thái In Progress, Pending, hoặc On Hold."
            )
        
        ticket.status = "Resolved"
        
        # Store resolution note if provided (requires model update, set as attribute for now)
        if resolution_note:
            ticket.resolution_note = resolution_note
        
        updated_ticket = self.repo.update(ticket)
        
        # Trigger CSAT survey
        self._trigger_csat_survey(ticket)
        
        return updated_ticket

    def close_ticket(self, ticket_id: uuid.UUID, reason: str = None, actor_id: uuid.UUID = None, actor_type: str = None) -> Ticket:
        """Close ticket - chỉ cho phép close từ Resolved"""
        ticket = self.repo.get_by_id(ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Không tìm thấy ticket!")
        
        if ticket.status != "Resolved":
            raise HTTPException(status_code=400, detail="Chỉ có thể đóng ticket từ trạng thái Resolved!")
        
        old_status = ticket.status
        ticket.status = "Closed"
        
        # Store close reason if provided
        if reason:
            ticket.resolution_note = reason
        
        updated_ticket = self.repo.update(ticket)
        
        # Log closure to history
        try:
            from app.services.ticketHistoryService import TicketHistoryService
            history_service = TicketHistoryService(self.db)
            history_service.log_closure(updated_ticket, reason, actor_id, actor_type)
        except Exception as e:
            logger.warning(f"Failed to log ticket closure: {e}")
        
        return updated_ticket

    def reopen_ticket(self, ticket_id: uuid.UUID, reason: str, actor_id: uuid.UUID = None, actor_type: str = None) -> Ticket:
        """
        Reopen a closed ticket - customer can reopen their own ticket.
        Ticket goes back to 'In Progress' status if it was assigned, otherwise 'New'.
        """
        ticket = self.repo.get_by_id(ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Không tìm thấy ticket!")
        
        # Can only reopen from Closed status
        if ticket.status != "Closed":
            raise HTTPException(
                status_code=400, 
                detail=f"Chỉ có thể mở lại ticket từ trạng thái 'Closed'! Trạng thái hiện tại: '{ticket.status}'"
            )
        
        if not reason or len(reason.strip()) == 0:
            raise HTTPException(status_code=400, detail="Vui lòng cung cấp lý do mở lại ticket!")
        
        old_status = ticket.status
        
        # If ticket was assigned before, keep assignment, otherwise set to New for re-assignment
        if ticket.id_employee:
            ticket.status = "In Progress"
        else:
            ticket.status = "New"
        
        # Clear resolution note since we're reopening
        ticket.resolution_note = None
        
        updated_ticket = self.repo.update(ticket)
        
        # Log the reopen action to history
        try:
            from app.services.ticketHistoryService import TicketHistoryService
            history_service = TicketHistoryService(self.db)
            history_service.log_reopen(updated_ticket, reason, actor_id, actor_type)
        except Exception as e:
            logger.warning(f"Failed to log ticket reopen: {e}")
        
        # Notify assigned employee about the reopen
        if updated_ticket.id_employee:
            try:
                from app.schemas.notificationSchema import NotificationCreate
                noti_service = NotificationService(self.db)
                short_title = ticket.title[:30] + "..." if len(ticket.title) > 30 else ticket.title
                short_reason = reason[:50] + "..." if len(reason) > 50 else reason
                
                noti_data = NotificationCreate(
                    title="Ticket được mở lại",
                    content=f"Khách hàng đã mở lại ticket #{str(ticket.id_ticket)[:8]}: '{short_title}'. Lý do: {short_reason}",
                    notification_type="TICKET_REOPENED",
                    id_reference=ticket.id_ticket,
                    id_receiver=updated_ticket.id_employee
                )
                noti_service.create_and_send(noti_data)
            except Exception as e:
                logger.warning(f"Failed to send reopen notification: {e}")
        
        return updated_ticket
