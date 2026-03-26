from typing import Tuple, List

from sqlalchemy.orm import Session

from app.models.system import AuditLog
from app.repositories.auditLogRepository import AuditLogRepository
from app.schemas.auditLogSchema import AuditLogCreate
import uuid
import json


class AuditLogService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = AuditLogRepository(db)

    def log_action(
            self,
            log_type: str,
            action: str,
            old_data: dict,
            new_data: dict,
            id_reference: uuid.UUID,
            id_employee: uuid.UUID
    ):
        old_value_str = json.dumps(old_data, ensure_ascii=False) if old_data else None
        new_value_str = json.dumps(new_data, ensure_ascii=False) if new_data else None

        log_data = AuditLogCreate(
            log_type=log_type,
            action=action,
            old_value=old_value_str,
            new_value=new_value_str,
            id_reference=id_reference,
            id_employee=id_employee
        )
        return self.repo.create_log(log_data)

    def get_logs_for_entity(self, entity_id: uuid.UUID):
        return self.repo.get_logs_by_reference(entity_id)

    def get_all_logs(
            self,
            page: int = 1,
            limit: int = 20,
            log_type: str = None
    ) -> Tuple[List, int]:
        query = self.db.query(AuditLog)

        if log_type:
            query = query.filter(AuditLog.log_type == log_type)

        total = query.count()
        offset = (page - 1) * limit

        logs = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()

        return logs, total