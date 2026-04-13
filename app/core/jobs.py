from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from app.models.ticket import Ticket
from app.models.human import Employee, Customer
from app.models.ticket import TicketCategory
from app.repositories.ticketRepository import TicketRepository
from app.repositories.employeeRepository import EmployeeRepository
from app.schemas.notificationSchema import NotificationCreate
from app.services.notificationService import NotificationService
from app.core.constants import TicketStatusConstants
from app.core.config import settings
from datetime import datetime, timedelta
import logging
import uuid

logger = logging.getLogger(__name__)

BATCH_SIZE = 100


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
        Uses batch processing to avoid RAM overflow.
        """
        result = {
            "checked": 0,
            "overdue": 0,
            "warning": 0,
            "escalated": 0
        }

        try:
            offset = 0
            while True:
                batch = self.db.query(Ticket).filter(
                    Ticket.status.in_(TicketStatusConstants.ACTIVE_STATUSES)
                ).offset(offset).limit(BATCH_SIZE).all()

                if not batch:
                    break

                now = datetime.utcnow()

                for ticket in batch:
                    result["checked"] += 1

                    if not ticket.expired_date:
                        continue

                    if ticket.expired_date < now:
                        result["overdue"] += 1
                        self._handle_overdue_ticket(ticket)
                    elif self._is_within_warning_window(ticket.expired_date, now):
                        result["warning"] += 1
                        self._send_sla_warning(ticket)

                self.db.expire_all()
                offset += BATCH_SIZE

            return result

        except Exception as e:
            logger.error(f"Error checking overdue tickets: {e}")
            return result

    def _is_within_warning_window(self, expired_date: datetime, now: datetime, window_hours: int = 24) -> bool:
        time_diff = expired_date - now
        return 0 < time_diff.total_seconds() <= (window_hours * 3600)

    def _handle_overdue_ticket(self, ticket: Ticket):
        try:
            logger.warning(f"Ticket {ticket.id_ticket} is overdue! Escalating...")

            if ticket.id_employee:
                self._notify_employee_breach(ticket, ticket.id_employee)

                if ticket.id_category:
                    category = self.db.query(TicketCategory).filter(
                        TicketCategory.id_category == ticket.id_category
                    ).first()

                    if category and category.id_department:
                        manager = self.employee_repo.get_department_manager(category.id_department)
                        if manager and manager.id != ticket.id_employee:
                            self._notify_manager_breach(ticket, manager.id_employee)
                            logger.info(f"Escalated ticket {ticket.id_ticket} to manager {manager.id_employee}")

        except Exception as e:
            logger.error(f"Error handling overdue ticket {ticket.id_ticket}: {e}")

    def _send_sla_warning(self, ticket: Ticket):
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
        now = datetime.utcnow()
        diff = expired_date - now
        return diff.total_seconds() / 3600


class SurveyJob:
    """Background job to send CSAT survey emails after ticket is resolved"""

    SURVEY_DELAY_HOURS = settings.SURVEY_DELAY_HOURS
    BATCH_SIZE = settings.SURVEY_BATCH_SIZE

    def __init__(self, db: Session):
        self.db = db
        self.ticket_repo = TicketRepository(db)

    def check_and_send_pending_surveys(self) -> dict:
        """
        Tìm các ticket đã resolved hơn 1 giờ và gửi survey email.
        Uses batch processing to avoid RAM overflow.
        """
        result = {
            "checked": 0,
            "sent": 0,
            "errors": 0
        }

        try:
            offset = 0
            while True:
                batch = self._fetch_pending_batch(offset)
                if not batch:
                    break

                for ticket in batch:
                    result["checked"] += 1
                    try:
                        self._send_survey(ticket)
                        ticket.survey_sent = True
                        result["sent"] += 1
                    except Exception as e:
                        logger.error(f"Error sending survey for ticket {ticket.id_ticket}: {e}")
                        result["errors"] += 1

                self.db.commit()
                self.db.expire_all()
                offset += self.BATCH_SIZE

            return result

        except Exception as e:
            logger.error(f"Error in check_and_send_pending_surveys: {e}")
            self.db.rollback()
            return result

    def _fetch_pending_batch(self, offset: int):
        """Fetch a batch of tickets ready for survey"""
        cutoff_time = datetime.utcnow() - timedelta(hours=self.SURVEY_DELAY_HOURS)

        return self.db.query(Ticket).filter(
            Ticket.status == "Resolved",
            Ticket.survey_sent == False,
            Ticket.resolved_at != None,
            Ticket.resolved_at < cutoff_time
        ).offset(offset).limit(self.BATCH_SIZE).all()

    def _send_survey(self, ticket: Ticket):
        """Send survey email for a single ticket"""
        try:
            from app.services.emailService import email_service

            customer = self.db.query(Customer).filter(
                Customer.id_customer == ticket.id_customer
            ).first()

            if not customer or not customer.email:
                logger.warning(f"No customer email for ticket {ticket.id_ticket}")
                return

            email_service.send_csat_survey(
                to_email=customer.email,
                ticket_id=str(ticket.id_ticket),
                ticket_title=ticket.title,
                ticket_status=ticket.status,
                ticket_severity=ticket.severity
            )
            logger.info(f"Survey sent for ticket {ticket.id_ticket}")

        except Exception as e:
            logger.error(f"Error sending survey email for ticket {ticket.id_ticket}: {e}")
            raise


def run_sla_breach_check(db: Session):
    """Standalone function to run SLA breach check"""
    job = SLABreachJob(db)
    result = job.check_overdue_tickets()
    logger.info(f"SLA breach check completed: {result}")
    return result


def run_survey_job(db: Session):
    """Standalone function to run survey job"""
    job = SurveyJob(db)
    result = job.check_and_send_pending_surveys()
    logger.info(f"Survey job completed: {result}")
    return result
