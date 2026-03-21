from sqlalchemy.orm import Session
from uuid import UUID
from app.models.human import Human

class HumanRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_username(self, username: str) -> Human:
        return self.db.query(Human).filter(Human.username == username).first()

    def get_by_email(self, email: str) -> Human:
        return self.db.query(Human).filter(Human.email == email).first()

    def get_by_id(self, user_id: str) -> Human:
        return self.db.query(Human).filter(Human.id == UUID(user_id)).first()