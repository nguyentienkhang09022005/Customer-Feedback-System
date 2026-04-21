from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.repositories.appointmentRepository import AppointmentRepository
from app.models.appointment import Appointment
from app.models.ticket import Ticket
from app.schemas.appointmentSchema import AppointmentCreate
from app.core.constants import AppointmentStatus, AppointmentConstants
from typing import List
import uuid
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class AppointmentService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = AppointmentRepository(db)

    def create_appointment(
        self,
        data: AppointmentCreate,
        customer_id: uuid.UUID
    ) -> Appointment:
        ticket = self.db.query(Ticket).filter(Ticket.id_ticket == data.id_ticket).first()

        if not ticket:
            raise HTTPException(status_code=404, detail="Không tìm thấy ticket!")

        if ticket.is_deleted:
            raise HTTPException(status_code=400, detail="Ticket đã bị xóa!")

        if ticket.id_customer != customer_id:
            raise HTTPException(status_code=403, detail="Bạn không có quyền đặt lịch hẹn cho ticket này!")

        if not ticket.id_employee:
            raise HTTPException(status_code=400, detail="Ticket chưa có nhân viên đảm nhận. Không thể đặt lịch hẹn!")

        if ticket.status in ["Resolved", "Closed"]:
            raise HTTPException(status_code=400, detail="Ticket đã được giải quyết hoặc đóng. Không thể đặt lịch hẹn!")

        if data.scheduled_at <= datetime.now(timezone.utc):
            raise HTTPException(status_code=400, detail="Thời gian hẹn phải lớn hơn thời gian hiện tại!")

        if not data.reason or len(data.reason.strip()) == 0:
            raise HTTPException(status_code=400, detail="Vui lòng cung cấp lý do/yêu cầu tư vấn!")

        existing_pending = self.repo.get_by_ticket(data.id_ticket)
        for apt in existing_pending:
            if apt.status == AppointmentStatus.PENDING:
                raise HTTPException(status_code=400, detail="Đã có lịch hẹn đang chờ xử lý cho ticket này!")

        appointment = Appointment(
            id_ticket=data.id_ticket,
            id_customer=customer_id,
            id_employee=ticket.id_employee,
            scheduled_at=data.scheduled_at,
            reason=data.reason.strip(),
            status=AppointmentStatus.PENDING
        )

        created = self.repo.create(appointment)

        try:
            from app.services.notificationService import NotificationService
            noti_service = NotificationService(self.db)
            from app.schemas.notificationSchema import NotificationCreate

            short_reason = data.reason[:50] + "..." if len(data.reason) > 50 else data.reason
            noti_data = NotificationCreate(
                title="Yêu cầu đặt lịch hẹn mới",
                content=f"Khách hàng yêu cầu đặt lịch hẹn tư vấn vào lúc {data.scheduled_at}. Lý do: {short_reason}",
                notification_type="APPOINTMENT_REQUEST",
                id_reference=created.id_appointment,
                id_receiver=ticket.id_employee
            )
            noti_service.create_and_send(noti_data)
        except Exception as e:
            logger.warning(f"Failed to send appointment notification: {e}")

        return created

    def get_appointment_by_id(self, appointment_id: uuid.UUID) -> Appointment:
        appointment = self.repo.get_by_id(appointment_id)
        if not appointment:
            raise HTTPException(status_code=404, detail="Không tìm thấy lịch hẹn!")
        return appointment

    def get_appointments_by_ticket(self, ticket_id: uuid.UUID) -> List[Appointment]:
        return self.repo.get_by_ticket(ticket_id)

    def get_appointments_by_employee(self, employee_id: uuid.UUID) -> List[Appointment]:
        return self.repo.get_by_employee(employee_id)

    def get_pending_appointments_by_employee(self, employee_id: uuid.UUID) -> List[Appointment]:
        return self.repo.get_pending_by_employee(employee_id)

    def accept_appointment(
        self,
        appointment_id: uuid.UUID,
        employee_id: uuid.UUID
    ) -> Appointment:
        appointment = self.repo.get_by_id(appointment_id)

        if not appointment:
            raise HTTPException(status_code=404, detail="Không tìm thấy lịch hẹn!")

        if appointment.id_employee != employee_id:
            raise HTTPException(status_code=403, detail="Bạn không có quyền xác nhận lịch hẹn này!")

        if appointment.status != AppointmentStatus.PENDING:
            raise HTTPException(status_code=400, detail=f"Lịch hẹn đang ở trạng thái '{appointment.status}', không thể xác nhận!")

        appointment.status = AppointmentStatus.ACCEPTED
        updated = self.repo.update(appointment)

        try:
            from app.services.notificationService import NotificationService
            noti_service = NotificationService(self.db)
            from app.schemas.notificationSchema import NotificationCreate

            noti_data = NotificationCreate(
                title="Lịch hẹn được chấp nhận",
                content=f"Nhân viên đã chấp nhận lịch hẹn tư vấn vào lúc {appointment.scheduled_at}",
                notification_type="APPOINTMENT_ACCEPTED",
                id_reference=appointment.id_appointment,
                id_receiver=appointment.id_customer
            )
            noti_service.create_and_send(noti_data)
        except Exception as e:
            logger.warning(f"Failed to send appointment accepted notification: {e}")

        return updated

    def reject_appointment(
        self,
        appointment_id: uuid.UUID,
        employee_id: uuid.UUID,
        rejection_reason: str
    ) -> Appointment:
        if not rejection_reason or len(rejection_reason.strip()) == 0:
            raise HTTPException(status_code=400, detail="Vui lòng cung cấp lý do từ chối!")

        appointment = self.repo.get_by_id(appointment_id)

        if not appointment:
            raise HTTPException(status_code=404, detail="Không tìm thấy lịch hẹn!")

        if appointment.id_employee != employee_id:
            raise HTTPException(status_code=403, detail="Bạn không có quyền từ chối lịch hẹn này!")

        if appointment.status != AppointmentStatus.PENDING:
            raise HTTPException(status_code=400, detail=f"Lịch hẹn đang ở trạng thái '{appointment.status}', không thể từ chối!")

        appointment.status = AppointmentStatus.REJECTED
        appointment.rejection_reason = rejection_reason.strip()
        updated = self.repo.update(appointment)

        try:
            from app.services.notificationService import NotificationService
            noti_service = NotificationService(self.db)
            from app.schemas.notificationSchema import NotificationCreate

            noti_data = NotificationCreate(
                title="Lịch hẹn bị từ chối",
                content=f"Nhân viên đã từ chối lịch hẹn. Lý do: {rejection_reason}",
                notification_type="APPOINTMENT_REJECTED",
                id_reference=appointment.id_appointment,
                id_receiver=appointment.id_customer
            )
            noti_service.create_and_send(noti_data)
        except Exception as e:
            logger.warning(f"Failed to send appointment rejected notification: {e}")

        return updated

    def cancel_appointment(
        self,
        appointment_id: uuid.UUID,
        customer_id: uuid.UUID
    ) -> Appointment:
        appointment = self.repo.get_by_id(appointment_id)

        if not appointment:
            raise HTTPException(status_code=404, detail="Không tìm thấy lịch hẹn!")

        if appointment.id_customer != customer_id:
            raise HTTPException(status_code=403, detail="Bạn không có quyền hủy lịch hẹn này!")

        if appointment.status not in AppointmentConstants.CANCELABLE_STATUSES:
            raise HTTPException(status_code=400, detail=f"Không thể hủy lịch hẹn ở trạng thái '{appointment.status}'!")

        appointment.status = AppointmentStatus.CANCELLED
        updated = self.repo.update(appointment)

        try:
            from app.services.notificationService import NotificationService
            noti_service = NotificationService(self.db)
            from app.schemas.notificationSchema import NotificationCreate

            noti_data = NotificationCreate(
                title="Lịch hẹn bị hủy",
                content=f"Khách hàng đã hủy lịch hẹn tư vấn vào lúc {appointment.scheduled_at}",
                notification_type="APPOINTMENT_CANCELLED",
                id_reference=appointment.id_appointment,
                id_receiver=appointment.id_employee
            )
            noti_service.create_and_send(noti_data)
        except Exception as e:
            logger.warning(f"Failed to send appointment cancelled notification: {e}")

        return updated