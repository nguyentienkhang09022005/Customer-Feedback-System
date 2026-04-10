from sqlalchemy.orm import Session
from app.models.ticketHistory import TicketHistory
from typing import List, Optional
import uuid


class TicketHistoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, history_id: uuid.UUID) -> Optional[TicketHistory]:
        return self.db.query(TicketHistory).filter(
            TicketHistory.id_history == history_id
        ).first()

    def get_by_ticket(self, ticket_id: uuid.UUID) -> List[TicketHistory]:
        return self.db.query(TicketHistory).filter(
            TicketHistory.id_ticket == ticket_id
        ).order_by(TicketHistory.created_at.desc()).all()

    def get_by_actor(self, actor_id: uuid.UUID) -> List[TicketHistory]:
        return self.db.query(TicketHistory).filter(
            TicketHistory.id_actor == actor_id
        ).order_by(TicketHistory.created_at.desc()).all()

    def create(self, history: TicketHistory) -> TicketHistory:
        self.db.add(history)
        self.db.commit()
        self.db.refresh(history)
        return history

    def delete(self, history: TicketHistory):
        self.db.delete(history)
        self.db.commit()
