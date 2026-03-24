from sqlalchemy.orm import Session
from app.models.ticket import TicketCategory
from typing import List
import uuid


class TicketCategoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self):
        return self.db.query(TicketCategory).all()

    def get_by_id(self, cat_id: uuid.UUID):
        return self.db.query(TicketCategory).filter(TicketCategory.id_category == cat_id).first()

    def get_by_name(self, name: str):
        return self.db.query(TicketCategory).filter(TicketCategory.name == name).first()

    def get_by_department(self, dept_id: uuid.UUID) -> List[TicketCategory]:
        return self.db.query(TicketCategory).filter(
            TicketCategory.id_department == dept_id,
            TicketCategory.is_active == True
        ).all()

    def get_active_all(self):
        return self.db.query(TicketCategory).filter(TicketCategory.is_active == True).all()

    def create(self, category: TicketCategory):
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category

    def update(self, category: TicketCategory):
        self.db.commit()
        self.db.refresh(category)
        return category

    def delete(self, category: TicketCategory):
        self.db.delete(category)
        self.db.commit()