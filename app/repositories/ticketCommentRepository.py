from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.ticketComment import TicketComment
from typing import List, Optional
import uuid


class TicketCommentRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, comment_id: uuid.UUID) -> Optional[TicketComment]:
        return self.db.query(TicketComment).filter(
            TicketComment.id_comment == comment_id
        ).first()

    def get_by_ticket(self, ticket_id: uuid.UUID, include_internal: bool = False) -> List[TicketComment]:
        """Lấy comments theo ticket"""
        query = self.db.query(TicketComment).filter(
            TicketComment.id_ticket == ticket_id
        )
        
        if not include_internal:
            query = query.filter(TicketComment.is_internal == False)
        
        return query.order_by(TicketComment.created_at.asc()).all()

    def get_by_author(self, author_id: uuid.UUID) -> List[TicketComment]:
        return self.db.query(TicketComment).filter(
            TicketComment.id_author == author_id
        ).order_by(TicketComment.created_at.desc()).all()

    def create(self, comment: TicketComment) -> TicketComment:
        self.db.add(comment)
        self.db.commit()
        self.db.refresh(comment)
        return comment

    def update(self, comment: TicketComment) -> TicketComment:
        self.db.commit()
        self.db.refresh(comment)
        return comment

    def delete(self, comment: TicketComment):
        self.db.delete(comment)
        self.db.commit()
