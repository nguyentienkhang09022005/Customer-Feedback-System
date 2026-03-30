from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException
from app.repositories.evaluateRepository import EvaluateRepository
from app.repositories.ticketRepository import TicketRepository
from app.models.interaction import Evaluate
from app.models.ticket import Ticket
from app.models.human import Employee
from app.schemas.evaluateSchema import EvaluateCreate, EvaluateUpdate
from typing import List
import uuid

from app.schemas.notificationSchema import NotificationCreate
from app.services.notificationService import NotificationService


class EvaluateService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = EvaluateRepository(db)
        self.ticket_repo = TicketRepository(db)

    def create_evaluate(self, data: EvaluateCreate, customer_id: uuid.UUID) -> Evaluate:
        ticket = self.ticket_repo.get_by_id(data.id_ticket)
        if not ticket:
            raise HTTPException(status_code=404, detail="Không tìm thấy Ticket!")

        evaluate = Evaluate(
            star=data.star,
            comment=data.comment,
            id_ticket=data.id_ticket,
            id_customer=customer_id
        )
        created_evaluate = self.repo.create(evaluate)

        if ticket.id_employee:
            noti_service = NotificationService(self.db)

            content = f"Khách hàng đã đánh giá {data.star} sao cho Ticket #{str(ticket.title)[:8]}."
            if data.comment:
                short_comment = data.comment[:30] + "..." if len(data.comment) > 30 else data.comment
                content += f" Nhận xét: '{short_comment}'"

            noti_data = NotificationCreate(
                title="Đánh giá Ticket mới \u2B50",
                content=content,
                notification_type="EVALUATE",
                id_reference=ticket.id_ticket,
                id_receiver=ticket.id_employee
            )
            noti_service.create_and_send(noti_data)
            self._update_employee_csat_score(ticket.id_employee)

        return created_evaluate

    def get_evaluates_by_ticket(self, ticket_id: uuid.UUID) -> List[Evaluate]:
        return self.repo.get_by_ticket(ticket_id)

    def update_evaluate(self, evaluate_id: uuid.UUID, data: EvaluateUpdate, customer_id: uuid.UUID) -> Evaluate:
        evaluate = self.repo.get_by_id(evaluate_id)
        if not evaluate:
            raise HTTPException(status_code=404, detail="Không tìm thấy đánh giá!")

        if evaluate.id_customer != customer_id:
            raise HTTPException(status_code=403, detail="Bạn không có quyền chỉnh sửa đánh giá này!")

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(evaluate, key, value)

        return self.repo.update(evaluate)

    def delete_evaluate(self, evaluate_id: uuid.UUID, customer_id: uuid.UUID):
        evaluate = self.repo.get_by_id(evaluate_id)
        if not evaluate:
            raise HTTPException(status_code=404, detail="Không tìm thấy đánh giá!")

        if evaluate.id_customer != customer_id:
            raise HTTPException(status_code=403, detail="Bạn không có quyền xóa đánh giá này!")

        self.repo.delete(evaluate)

    def _update_employee_csat_score(self, employee_id: uuid.UUID):
        """Tính trung bình cộng tất cả đánh giá của employee và cập nhật csat_score"""
        # Query lấy trung bình đánh giá của employee này
        # Join Evaluate với Ticket để filter theo id_employee của ticket
        result = self.db.query(func.avg(Evaluate.star)).join(
            Ticket, Evaluate.id_ticket == Ticket.id_ticket
        ).filter(Ticket.id_employee == employee_id).scalar()
        
        avg_score = result or 0.0
        
        # Cập nhật csat_score cho employee
        employee = self.db.query(Employee).filter(Employee.id_employee == employee_id).first()
        if employee:
            employee.csat_score = float(avg_score)
            self.db.commit()