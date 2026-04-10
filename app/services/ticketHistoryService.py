from sqlalchemy.orm import Session
from app.repositories.ticketHistoryRepository import TicketHistoryRepository
from app.models.ticketHistory import TicketHistory, TicketAction
from app.models.human import Human
from typing import List, Optional, Any
import uuid
import logging

logger = logging.getLogger(__name__)


class TicketHistoryService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = TicketHistoryRepository(db)

    def log_ticket_created(self, ticket, actor_id: uuid.UUID, actor_type: str) -> TicketHistory:
        """Log ticket creation"""
        history = TicketHistory(
            id_ticket=ticket.id_ticket,
            id_actor=actor_id,
            actor_type=actor_type,
            action=TicketAction.CREATED,
            new_value={
                "title": ticket.title,
                "description": ticket.description,
                "severity": ticket.severity,
                "category": str(ticket.id_category)
            }
        )
        return self.repo.create(history)

    def log_status_change(
        self, 
        ticket, 
        old_status: str, 
        new_status: str, 
        actor_id: uuid.UUID = None, 
        actor_type: str = None
    ) -> TicketHistory:
        """Log status change"""
        history = TicketHistory(
            id_ticket=ticket.id_ticket,
            id_actor=actor_id,
            actor_type=actor_type or "system",
            action=TicketAction.STATUS_CHANGED,
            old_value={"status": old_status},
            new_value={"status": new_status}
        )
        return self.repo.create(history)

    def log_assignment(
        self, 
        ticket, 
        old_employee_id: Optional[uuid.UUID], 
        new_employee_id: Optional[uuid.UUID], 
        actor_id: uuid.UUID = None,
        actor_type: str = None
    ) -> TicketHistory:
        """Log ticket assignment/unassignment"""
        if new_employee_id:
            action = TicketAction.ASSIGNED
        else:
            action = TicketAction.UNASSIGNED
            
        history = TicketHistory(
            id_ticket=ticket.id_ticket,
            id_actor=actor_id,
            actor_type=actor_type or "system",
            action=action,
            old_value={"id_employee": str(old_employee_id) if old_employee_id else None},
            new_value={"id_employee": str(new_employee_id) if new_employee_id else None}
        )
        return self.repo.create(history)

    def log_category_change(
        self, 
        ticket, 
        old_category_id: uuid.UUID, 
        new_category_id: uuid.UUID, 
        actor_id: uuid.UUID = None,
        actor_type: str = None
    ) -> TicketHistory:
        """Log category change"""
        history = TicketHistory(
            id_ticket=ticket.id_ticket,
            id_actor=actor_id,
            actor_type=actor_type or "system",
            action=TicketAction.CATEGORY_CHANGED,
            old_value={"id_category": str(old_category_id)},
            new_value={"id_category": str(new_category_id)}
        )
        return self.repo.create(history)

    def log_severity_change(
        self, 
        ticket, 
        old_severity: str, 
        new_severity: str, 
        actor_id: uuid.UUID = None,
        actor_type: str = None
    ) -> TicketHistory:
        """Log severity change"""
        history = TicketHistory(
            id_ticket=ticket.id_ticket,
            id_actor=actor_id,
            actor_type=actor_type or "system",
            action=TicketAction.SEVERITY_CHANGED,
            old_value={"severity": old_severity},
            new_value={"severity": new_severity}
        )
        return self.repo.create(history)

    def log_resolution(
        self, 
        ticket, 
        resolution_note: str = None, 
        actor_id: uuid.UUID = None,
        actor_type: str = None
    ) -> TicketHistory:
        """Log ticket resolution"""
        history = TicketHistory(
            id_ticket=ticket.id_ticket,
            id_actor=actor_id,
            actor_type=actor_type or "employee",
            action=TicketAction.RESOLVED,
            new_value={"status": "Resolved"},
            note=resolution_note
        )
        return self.repo.create(history)

    def log_closure(
        self, 
        ticket, 
        close_reason: str = None, 
        actor_id: uuid.UUID = None,
        actor_type: str = None
    ) -> TicketHistory:
        """Log ticket closure"""
        history = TicketHistory(
            id_ticket=ticket.id_ticket,
            id_actor=actor_id,
            actor_type=actor_type or "customer",
            action=TicketAction.CLOSED,
            new_value={"status": "Closed"},
            note=close_reason
        )
        return self.repo.create(history)

    def log_reopen(
        self, 
        ticket, 
        reason: str, 
        actor_id: uuid.UUID = None,
        actor_type: str = None
    ) -> TicketHistory:
        """Log ticket reopen"""
        history = TicketHistory(
            id_ticket=ticket.id_ticket,
            id_actor=actor_id,
            actor_type=actor_type or "customer",
            action=TicketAction.REOPENED,
            old_value={"status": "Closed"},
            new_value={"status": "In Progress"},
            note=reason
        )
        return self.repo.create(history)

    def get_ticket_history(self, ticket_id: uuid.UUID) -> List[TicketHistory]:
        """Lấy lịch sử của ticket"""
        return self.repo.get_by_ticket(ticket_id)

    def get_ticket_history_with_actor_names(self, ticket_id: uuid.UUID) -> List[dict]:
        """Lấy lịch sử của ticket kèm tên actor"""
        histories = self.repo.get_by_ticket(ticket_id)
        result = []
        
        for h in histories:
            actor_name = None
            if h.id_actor:
                human = self.db.query(Human).filter(Human.id == h.id_actor).first()
                if human:
                    actor_name = f"{human.first_name} {human.last_name}".strip()
            
            result.append({
                "id_history": h.id_history,
                "id_ticket": h.id_ticket,
                "id_actor": h.id_actor,
                "actor_type": h.actor_type,
                "actor_name": actor_name,
                "action": h.action,
                "old_value": h.old_value,
                "new_value": h.new_value,
                "note": h.note,
                "created_at": h.created_at
            })
        
        return result
