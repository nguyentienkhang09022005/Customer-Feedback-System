from sqlalchemy.orm import Session
from app.models.system import AuditLog # Điều chỉnh đường dẫn import model
from app.schemas.auditLogSchema import AuditLogCreate
from typing import List
import uuid

class AuditLogRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_log(self, data: AuditLogCreate) -> AuditLog:
        log = AuditLog(
            log_type=data.log_type,
            action=data.action,
            old_value=data.old_value,
            new_value=data.new_value,
            id_reference=data.id_reference,
            id_employee=data.id_employee
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    def get_logs_by_reference(self, reference_id: uuid.UUID) -> List[AuditLog]:
        return self.db.query(AuditLog)\
            .filter(AuditLog.id_reference == reference_id)\
            .order_by(AuditLog.created_at.desc())\
            .all()

    def get_all_logs(self, page: int = 1, limit: int = 20, log_type: str = None):
        return self.repo.get_all_logs(page=page, limit=limit, log_type=log_type)