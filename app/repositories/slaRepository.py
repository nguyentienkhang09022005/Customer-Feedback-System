from sqlalchemy.orm import Session
from app.models.ticket import SLAPolicy
from app.schemas.slaSchema import SLACreate, SLAUpdate
from typing import List, Optional
import uuid

class SLAPolicyRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> List[SLAPolicy]:
        return self.db.query(SLAPolicy).all()

    def get_by_id(self, id_policy: uuid.UUID) -> Optional[SLAPolicy]:
        return self.db.query(SLAPolicy).filter(SLAPolicy.id_policy == id_policy).first()

    # Lấy chính sách SLA đang Active dựa trên mức độ nghiêm trọng
    def get_active_by_severity(self, severity: str) -> Optional[SLAPolicy]:
        return self.db.query(SLAPolicy).filter(
            SLAPolicy.severity == severity,
            SLAPolicy.is_active == True
        ).first()

    def create(self, data: SLACreate) -> SLAPolicy:
        policy = SLAPolicy(**data.model_dump())
        self.db.add(policy)
        self.db.commit()
        self.db.refresh(policy)
        return policy

    def update(self, policy: SLAPolicy, data: SLAUpdate) -> SLAPolicy:
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(policy, key, value)
        self.db.commit()
        self.db.refresh(policy)
        return policy