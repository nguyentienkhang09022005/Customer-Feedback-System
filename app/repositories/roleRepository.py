from sqlalchemy.orm import Session
from app.models.human import Role

class RoleRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self):
        return self.db.query(Role).all()

    def get_by_name(self, role_name: str):
        return self.db.query(Role).filter(Role.role_name == role_name).first()

    def create(self, role: Role):
        self.db.add(role)
        self.db.commit()
        self.db.refresh(role)
        return role

    def update(self, role: Role):
        self.db.commit()
        self.db.refresh(role)
        return role

    def delete(self, role: Role):
        self.db.delete(role)
        self.db.commit()