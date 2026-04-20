from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.repositories.ticketRepository import TicketRepository
from app.repositories.ticketTemplateRepository import TicketTemplateRepository
from app.repositories.slaRepository import SLAPolicyRepository
from app.repositories.humanRepository import HumanRepository
from app.models.ticket import Ticket, TicketTemplate
from app.schemas.ticketSchema import TicketUpdate, TicketAssign, TicketFromTemplateCreate, TicketCustomerUpdate
from app.services.loadBalancer import LoadBalancer
from app.core.constants import TicketStatusConstants
from typing import List, Optional
import uuid
from datetime import datetime, timedelta
import logging

from app.services.notificationService import NotificationService

logger = logging.getLogger(__name__)


def _validate_status_transition(current_status: str, new_status: str) -> bool:
    if current_status == new_status:
        return True
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
    try:
        from app.services.emailService import email_service
        
        if not recipient_email:
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
        self.template_repo = TicketTemplateRepository(db)
        self.sla_repo = SLAPolicyRepository(db)
        self.load_balancer = LoadBalancer(db)

    def _calculate_expired_date(self, severity: str = None):
        if not severity:
            return None
        active_sla = self.sla_repo.get_active_by_severity(severity)
        if active_sla:
            return datetime.utcnow() + timedelta(days=active_sla.max_resolution_days)
        return None

    def create_ticket_from_template(self, data: TicketFromTemplateCreate, customer_id: uuid.UUID) -> Ticket:
        template = self.template_repo.get_latest_version(data.id_template)
        if not template:
            raise HTTPException(status_code=404, detail="Không tìm thấy template!")
        if template.is_deleted:
            raise HTTPException(status_code=400, detail="Template đã bị xóa!")
        if not template.is_active:
            raise HTTPException(status_code=400, detail="Template không còn hoạt động!")

        if not self._check_ticket_creation_rate_limit(customer_id):
            raise HTTPException(
                status_code=429, 
                detail="Bạn đã tạo quá nhiều tickets. Vui lòng thử lại sau."
            )

        severity = data.severity or template.fields_config.get("severity", {}).get("default_value")

        ticket = Ticket(
            title=data.title,
            custom_fields=data.custom_fields,
            severity=severity,
            status="New",
            id_customer=customer_id,
            id_employee=None,
            expired_date=self._calculate_expired_date(severity),
            id_template=template.id_template,
            template_version=template.version
        )

        created_ticket = self.repo.create(ticket)

        if template.id_category:
            try:
                from app.repositories.employeeRepository import EmployeeRepository
                emp_repo = EmployeeRepository(self.db)
                members = emp_repo.get_department_all_members(template.id_category)
                
                if members:
                    short_title = ticket.title[:30] + "..." if len(ticket.title) > 30 else ticket.title
                    title = f"Ticket mới chưa được phân công"
                    content = f"Ticket #{str(ticket.id_ticket)[:8]}: '{short_title}' đang chờ được tiếp nhận."
                    
                    noti_service = NotificationService(self.db)
                    for member in members:
                        if member.status == "Active":
                            try:
                                from app.schemas.notificationSchema import NotificationCreate
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
                logger.warning(f"Failed to notify department: {e}")

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

    def get_tickets_by_employee(self, employee_id: uuid.UUID, include_closed: bool = False) -> List[Ticket]:
        return self.repo.get_by_employee(employee_id, include_closed)

    def get_tickets_by_customer(self, customer_id: uuid.UUID, include_closed: bool = False) -> List[Ticket]:
        return self.repo.get_by_customer(customer_id, include_closed)

    def get_tickets_by_department(self, dept_id: uuid.UUID) -> List[Ticket]:
        return self.repo.get_by_department(dept_id)

    def update_ticket(self, ticket_id: uuid.UUID, data: TicketUpdate, actor_id: uuid.UUID = None, actor_type: str = None) -> Ticket:
        ticket = self.repo.get_by_id(ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Không tìm thấy ticket!")
        
        if ticket.is_deleted:
            raise HTTPException(status_code=400, detail="Ticket đã bị xóa!")
        
        update_data = data.model_dump(exclude_unset=True)

        if "status" in update_data:
            new_status = update_data["status"]
            if not _validate_status_transition(ticket.status, new_status):
                raise HTTPException(
                    status_code=400,
                    detail=f"Không thể chuyển từ '{ticket.status}' sang '{new_status}'. "
                           f"Các trạng thái cho phép: {TicketStatusConstants.STATUS_TRANSITIONS.get(ticket.status, [])}"
                )
        
        if "status" in update_data and update_data["status"] not in TicketStatusConstants.VALID_STATUSES:
            raise HTTPException(status_code=400, detail=f"Trạng thái '{update_data['status']}' không hợp lệ!")

        if "severity" in update_data and update_data["severity"] != ticket.severity:
            update_data["expired_date"] = self._calculate_expired_date(update_data["severity"])

        if actor_type == "employee":
            if "title" in update_data or "custom_fields" in update_data:
                raise HTTPException(
                    status_code=403,
                    detail="Employee chỉ được cập nhật trạng thái ticket!"
                )

        for key, value in update_data.items():
            setattr(ticket, key, value)

        return self.repo.update(ticket)

    def update_ticket_customer(self, ticket_id: uuid.UUID, data: TicketCustomerUpdate, customer_id: uuid.UUID) -> Ticket:
        ticket = self.repo.get_by_id(ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Không tìm thấy ticket!")
        
        if ticket.is_deleted:
            raise HTTPException(status_code=400, detail="Ticket đã bị xóa!")
        
        if ticket.status != "New":
            raise HTTPException(status_code=400, detail="Chỉ được cập nhật khi ticket còn ở trạng thái New!")
        
        if ticket.id_customer != customer_id:
            raise HTTPException(status_code=403, detail="Bạn không có quyền cập nhật ticket này!")
        
        update_data = data.model_dump(exclude_unset=True)
        
        if "custom_fields" in update_data and ticket.id_template:
            self._validate_custom_fields_by_template_version(
                update_data["custom_fields"],
                ticket.id_template,
                ticket.template_version
            )
        
        for key, value in update_data.items():
            setattr(ticket, key, value)
        
        return self.repo.update(ticket)

    def _validate_custom_fields_by_template_version(self, custom_fields: dict, id_template: uuid.UUID, template_version: int):
        template = self.template_repo.get_by_id_version(id_template, template_version)
        if not template:
            raise HTTPException(status_code=404, detail="Template version không tồn tại!")
        
        fields_config = template.fields_config
        required_fields = [
            f["name"] for f in fields_config.get("fields", [])
            if f.get("required", False)
        ]
        
        for field_name in required_fields:
            if field_name not in custom_fields:
                raise HTTPException(status_code=400, detail=f"Thiếu field bắt buộc: {field_name}")

    def assign_ticket(self, ticket_id: uuid.UUID, data: TicketAssign) -> Ticket:
        ticket = self.repo.get_by_id(ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Không tìm thấy ticket!")
        
        if ticket.is_deleted:
            raise HTTPException(status_code=400, detail="Ticket đã bị xóa!")
        
        result = self.repo.assign_to_employee(ticket_id, data.id_employee)
        
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
        if ticket.is_deleted:
            raise HTTPException(status_code=400, detail="Ticket đã bị xóa!")
        
        return self.repo.soft_delete(ticket)

    def _check_ticket_creation_rate_limit(self, customer_id: uuid.UUID) -> bool:
        try:
            from app.services.redisService import RedisService
            redis_service = RedisService()
            
            key = f"rate_limit:ticket_create:{customer_id}"
            current_count = redis_service.get(key)
            
            if current_count is None:
                redis_service.set_with_expiry(key, "1", TicketStatusConstants.RATE_LIMIT_WINDOW_SECONDS)
                return True
            
            if int(current_count) >= TicketStatusConstants.RATE_LIMIT_TICKETS:
                return False
            
            redis_service.increment(key)
            return True
        except Exception as e:
            logger.warning(f"Rate limit check failed, allowing request: {e}")
            return True

    def _trigger_csat_survey(self, ticket: Ticket):
        try:
            logger.info(f"CSAT survey triggered for ticket {ticket.id_ticket}")
        except Exception as e:
            logger.warning(f"Failed to trigger CSAT survey: {e}")

    def resolve_ticket(self, ticket_id: uuid.UUID, resolution_note: str = None, actor_id: uuid.UUID = None) -> Ticket:
        ticket = self.repo.get_by_id(ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Không tìm thấy ticket!")
        if ticket.is_deleted:
            raise HTTPException(status_code=400, detail="Ticket đã bị xóa!")
        
        if not _validate_status_transition(ticket.status, "Resolved"):
            raise HTTPException(
                status_code=400,
                detail=f"Không thể giải quyết ticket từ trạng thái '{ticket.status}'. "
                       f"Ticket phải ở trạng thái In Progress, Pending, hoặc On Hold."
            )
        
        ticket.status = "Resolved"
        ticket.resolved_at = datetime.utcnow()
        
        if resolution_note:
            ticket.resolution_note = resolution_note
        
        updated_ticket = self.repo.update(ticket)
        self._trigger_csat_survey(ticket)
        
        return updated_ticket

    def close_ticket(self, ticket_id: uuid.UUID, reason: str = None, actor_id: uuid.UUID = None, actor_type: str = None) -> Ticket:
        ticket = self.repo.get_by_id(ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Không tìm thấy ticket!")
        if ticket.is_deleted:
            raise HTTPException(status_code=400, detail="Ticket đã bị xóa!")
        
        if ticket.status != "Resolved":
            raise HTTPException(status_code=400, detail="Chỉ có thể đóng ticket từ trạng thái Resolved!")
        
        ticket.status = "Closed"
        
        if reason:
            ticket.resolution_note = reason
        
        updated_ticket = self.repo.update(ticket)
        
        try:
            from app.services.ticketHistoryService import TicketHistoryService
            history_service = TicketHistoryService(self.db)
            history_service.log_closure(updated_ticket, reason, actor_id, actor_type)
        except Exception as e:
            logger.warning(f"Failed to log ticket closure: {e}")
        
        return updated_ticket

    def reopen_ticket(self, ticket_id: uuid.UUID, reason: str, actor_id: uuid.UUID = None, actor_type: str = None) -> Ticket:
        ticket = self.repo.get_by_id(ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Không tìm thấy ticket!")
        if ticket.is_deleted:
            raise HTTPException(status_code=400, detail="Ticket đã bị xóa!")
        
        if ticket.status != "Closed":
            raise HTTPException(
                status_code=400, 
                detail=f"Chỉ có thể mở lại ticket từ trạng thái 'Closed'! Trạng thái hiện tại: '{ticket.status}'"
            )
        
        if not reason or len(reason.strip()) == 0:
            raise HTTPException(status_code=400, detail="Vui lòng cung cấp lý do mở lại ticket!")
        
        if ticket.id_employee:
            ticket.status = "In Progress"
        else:
            ticket.status = "New"
        
        ticket.resolution_note = None
        
        updated_ticket = self.repo.update(ticket)
        
        try:
            from app.services.ticketHistoryService import TicketHistoryService
            history_service = TicketHistoryService(self.db)
            history_service.log_reopen(updated_ticket, reason, actor_id, actor_type)
        except Exception as e:
            logger.warning(f"Failed to log ticket reopen: {e}")
        
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