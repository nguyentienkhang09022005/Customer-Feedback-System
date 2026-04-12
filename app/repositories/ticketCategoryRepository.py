from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.ticket import TicketCategory
from typing import List, Optional
import uuid
from datetime import datetime


class TicketCategoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> List[TicketCategory]:
        return self.db.query(TicketCategory).filter(
            TicketCategory.is_deleted == False
        ).all()

    def get_by_id(self, cat_id: uuid.UUID) -> Optional[TicketCategory]:
        return self.db.query(TicketCategory).filter(
            and_(
                TicketCategory.id_category == cat_id,
                TicketCategory.is_deleted == False
            )
        ).first()

    def get_by_name(self, name: str) -> Optional[TicketCategory]:
        return self.db.query(TicketCategory).filter(
            and_(
                TicketCategory.name == name,
                TicketCategory.is_deleted == False
            )
        ).first()

    def get_by_department(self, dept_id: uuid.UUID) -> List[TicketCategory]:
        return self.db.query(TicketCategory).filter(
            and_(
                TicketCategory.id_department == dept_id,
                TicketCategory.is_active == True,
                TicketCategory.is_deleted == False
            )
        ).all()

    def get_active_all(self) -> List[TicketCategory]:
        return self.db.query(TicketCategory).filter(
            and_(
                TicketCategory.is_active == True,
                TicketCategory.is_deleted == False
            )
        ).all()

    def create(self, category: TicketCategory) -> TicketCategory:
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category

    def update(self, category: TicketCategory) -> TicketCategory:
        self.db.commit()
        self.db.refresh(category)
        return category

    def soft_delete(self, category: TicketCategory) -> TicketCategory:
        category.is_deleted = True
        category.deleted_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(category)
        return category

    def permanent_delete(self, category: TicketCategory) -> None:
        self.db.delete(category)
        self.db.commit()