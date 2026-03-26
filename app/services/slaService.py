from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.repositories.slaRepository import SLAPolicyRepository
from app.schemas.slaSchema import SLACreate, SLAUpdate
import uuid


class SLAService:
    def __init__(self, db: Session):
        self.repo = SLAPolicyRepository(db)

    def get_all_policies(self):
        return self.repo.get_all()

    def create_policy(self, data: SLACreate):
        return self.repo.create(data)

    def update_policy(self, policy_id: uuid.UUID, data: SLAUpdate):
        policy = self.repo.get_by_id(policy_id)
        if not policy:
            raise HTTPException(status_code=404, detail="SLA Policy không tồn tại!")
        return self.repo.update(policy, data)

    def toggle_policy(self, policy_id: uuid.UUID):
        policy = self.repo.get_by_id(policy_id)
        if not policy:
            raise HTTPException(status_code=404, detail="SLA Policy không tồn tại!")

        policy.is_active = not policy.is_active
        update_schema = SLAUpdate(is_active=policy.is_active)
        return self.repo.update(policy, update_schema)