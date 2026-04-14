from sqlalchemy.orm import Session
from sqlalchemy import and_, func, extract
from app.models.sentiment import SentimentReport, SentimentDetail
from app.models.interaction import Message, Evaluate
from app.models.ticketComment import TicketComment
from app.models.chatbot import ChatMessage, ChatSession
from app.models.ticket import Ticket
from app.models.department import Department
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime, date
from uuid import UUID
import logging

logger = logging.getLogger(__name__)


class SentimentReportRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_period_scope(
        self,
        year: int,
        month: int,
        scope: str,
        id_department: Optional[UUID] = None
    ) -> Optional[SentimentReport]:
        query = self.db.query(SentimentReport).filter(
            and_(
                SentimentReport.year == year,
                SentimentReport.month == month,
                SentimentReport.scope == scope
            )
        )
        if scope == "department" and id_department:
            query = query.filter(SentimentReport.id_department == id_department)
        return query.first()

    def get_system_trends(self, year: int) -> List[SentimentReport]:
        return self.db.query(SentimentReport).filter(
            and_(
                SentimentReport.year == year,
                SentimentReport.scope == "system"
            )
        ).order_by(SentimentReport.month).all()

    def get_department_trends(
        self,
        year: int,
        id_department: UUID
    ) -> List[SentimentReport]:
        return self.db.query(SentimentReport).filter(
            and_(
                SentimentReport.year == year,
                SentimentReport.scope == "department",
                SentimentReport.id_department == id_department
            )
        ).order_by(SentimentReport.month).all()

    def get_by_department_month(
        self,
        year: int,
        month: int
    ) -> List[SentimentReport]:
        return self.db.query(SentimentReport).filter(
            and_(
                SentimentReport.year == year,
                SentimentReport.month == month,
                SentimentReport.scope == "department"
            )
        ).all()

    def create_or_update(
        self,
        year: int,
        month: int,
        scope: str,
        id_department: Optional[UUID],
        data: Dict[str, Any]
    ) -> SentimentReport:
        report = self.get_by_period_scope(year, month, scope, id_department)

        if report:
            for key, value in data.items():
                setattr(report, key, value)
            report.updated_at = datetime.utcnow()
        else:
            report = SentimentReport(
                year=year,
                month=month,
                scope=scope,
                id_department=id_department,
                **data
            )
            self.db.add(report)

        self.db.commit()
        self.db.refresh(report)
        return report

    def get_comparison(
        self,
        from_year: int,
        from_month: int,
        to_year: int,
        to_month: int,
        scope: str,
        id_department: Optional[UUID] = None
    ) -> Tuple[Optional[SentimentReport], Optional[SentimentReport]]:
        from_report = self.get_by_period_scope(from_year, from_month, scope, id_department)
        to_report = self.get_by_period_scope(to_year, to_month, scope, id_department)
        return from_report, to_report


class SentimentDetailRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, data: Dict[str, Any]) -> SentimentDetail:
        detail = SentimentDetail(**data)
        self.db.add(detail)
        return detail

    def create_batch(self, details: List[Dict[str, Any]]) -> int:
        count = 0
        for data in details:
            detail = SentimentDetail(**data)
            self.db.add(detail)
            count += 1
        return count

    def get_by_report(self, id_report: UUID) -> List[SentimentDetail]:
        return self.db.query(SentimentDetail).filter(
            SentimentDetail.id_report == id_report
        ).all()

    def delete_by_report(self, id_report: UUID) -> int:
        count = self.db.query(SentimentDetail).filter(
            SentimentDetail.id_report == id_report
        ).delete()
        return count


class SentimentDataRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_messages_created_between(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[Tuple[UUID, str, UUID, UUID, UUID]]:
        return self.db.query(
            Message.id_message,
            Message.message,
            Message.id_ticket,
            Ticket.id_customer,
            Ticket.id_department
        ).join(
            Ticket, Message.id_ticket == Ticket.id_ticket
        ).filter(
            and_(
                Message.created_at >= start_date,
                Message.created_at < end_date,
                Message.is_deleted == False
            )
        ).all()

    def get_evaluations_created_between(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[Tuple[UUID, str, int, UUID, UUID, UUID]]:
        return self.db.query(
            Evaluate.id_evaluate,
            Evaluate.comment,
            Evaluate.star,
            Evaluate.id_ticket,
            Ticket.id_customer,
            Ticket.id_department
        ).join(
            Ticket, Evaluate.id_ticket == Ticket.id_ticket
        ).filter(
            and_(
                Evaluate.created_at >= start_date,
                Evaluate.created_at < end_date
            )
        ).all()

    def get_comments_created_between(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[Tuple[UUID, str, UUID, UUID, UUID]]:
        return self.db.query(
            TicketComment.id_comment,
            TicketComment.content,
            TicketComment.id_ticket,
            Ticket.id_customer,
            Ticket.id_department
        ).join(
            Ticket, TicketComment.id_ticket == Ticket.id_ticket
        ).filter(
            and_(
                TicketComment.created_at >= start_date,
                TicketComment.created_at < end_date
            )
        ).all()

    def get_chatbot_messages_created_between(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[Tuple[UUID, str, UUID]]:
        return self.db.query(
            ChatMessage.id_message,
            ChatMessage.content,
            ChatSession.customer_id
        ).join(
            ChatSession, ChatMessage.session_id == ChatSession.id_session
        ).filter(
            and_(
                ChatMessage.created_at >= start_date,
                ChatMessage.created_at < end_date,
                ChatMessage.role == "user"
            )
        ).all()

    def get_department_by_id(self, id_department: UUID) -> Optional[Department]:
        return self.db.query(Department).filter(Department.id_department == id_department).first()

    def get_all_active_departments(self) -> List[Department]:
        return self.db.query(Department).filter(Department.is_active == True).all()

    def aggregate_by_department(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        result = []
        departments = self.get_all_active_departments()

        for dept in departments:
            counts = {
                "message": {"positive": 0, "neutral": 0, "negative": 0},
                "evaluation": {"positive": 0, "neutral": 0, "negative": 0},
                "comment": {"positive": 0, "neutral": 0, "negative": 0},
                "chatbot": {"positive": 0, "neutral": 0, "negative": 0},
            }
            total_interactions = 0

            messages = self.get_messages_created_between(start_date, end_date)
            for msg in messages:
                if msg[4] == dept.id_department:
                    total_interactions += 1

            evaluations = self.get_evaluations_created_between(start_date, end_date)
            for eval in evaluations:
                if eval[5] == dept.id_department:
                    total_interactions += 1

            comments = self.get_comments_created_between(start_date, end_date)
            for comment in comments:
                if comment[4] == dept.id_department:
                    total_interactions += 1

            result.append({
                "id_department": dept.id_department,
                "department_name": dept.name,
                "counts": counts,
                "total_interactions": total_interactions
            })

        return result