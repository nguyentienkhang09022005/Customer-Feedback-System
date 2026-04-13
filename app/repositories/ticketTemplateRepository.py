from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from app.models.ticket import TicketTemplate, TicketCategory
from app.models.human import Employee
from typing import List, Optional
import uuid
from datetime import datetime


class TicketTemplateRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> List[TicketTemplate]:
        return self.db.query(TicketTemplate).filter(
            TicketTemplate.is_deleted == False
        ).order_by(TicketTemplate.created_at.desc()).all()

    def get_by_id_version(self, id_template: uuid.UUID, version: int) -> Optional[TicketTemplate]:
        return self.db.query(TicketTemplate).filter(
            and_(
                TicketTemplate.id_template == id_template,
                TicketTemplate.version == version,
                TicketTemplate.is_deleted == False
            )
        ).first()

    def get_latest_version(self, id_template: uuid.UUID) -> Optional[TicketTemplate]:
        return self.db.query(TicketTemplate).filter(
            and_(
                TicketTemplate.id_template == id_template,
                TicketTemplate.is_deleted == False
            )
        ).order_by(TicketTemplate.version.desc()).first()

    def get_by_category(self, id_category: uuid.UUID) -> List[TicketTemplate]:
        latest_templates = self.db.query(
            TicketTemplate
        ).filter(
            and_(
                TicketTemplate.id_category == id_category,
                TicketTemplate.is_deleted == False,
                TicketTemplate.is_active == True
            )
        ).all()

        template_map = {}
        for t in latest_templates:
            if t.id_template not in template_map or t.version > template_map[t.id_template].version:
                template_map[t.id_template] = t

        return list(template_map.values())

    def get_active_all(self) -> List[TicketTemplate]:
        all_templates = self.db.query(TicketTemplate).filter(
            TicketTemplate.is_deleted == False
        ).all()

        template_map = {}
        for t in all_templates:
            if t.id_template not in template_map or t.version > template_map[t.id_template].version:
                template_map[t.id_template] = t

        return list(template_map.values())

    def get_versions(self, id_template: uuid.UUID) -> List[TicketTemplate]:
        return self.db.query(TicketTemplate).filter(
            and_(
                TicketTemplate.id_template == id_template,
                TicketTemplate.is_deleted == False
            )
        ).order_by(TicketTemplate.version.desc()).all()

    def create(self, template: TicketTemplate) -> TicketTemplate:
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        return template

    def update(self, template: TicketTemplate) -> TicketTemplate:
        self.db.commit()
        self.db.refresh(template)
        return template

    def soft_delete(self, template: TicketTemplate) -> TicketTemplate:
        template.is_deleted = True
        template.deleted_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(template)
        return template

    def soft_delete_all_versions(self, id_template: uuid.UUID) -> None:
        self.db.query(TicketTemplate).filter(
            TicketTemplate.id_template == id_template
        ).update({
            TicketTemplate.is_deleted: True,
            TicketTemplate.deleted_at: datetime.utcnow()
        })
        self.db.commit()

    def get_next_version(self, id_template: uuid.UUID) -> int:
        latest = self.get_latest_version(id_template)
        return (latest.version + 1) if latest else 1

    def get_by_id(self, id_template: uuid.UUID) -> Optional[TicketTemplate]:
        return self.db.query(TicketTemplate).filter(
            TicketTemplate.id_template == id_template
        ).first()

    def soft_delete_all_versions_by_category(self, id_category: uuid.UUID) -> None:
        self.db.query(TicketTemplate).filter(
            TicketTemplate.id_category == id_category
        ).update({
            TicketTemplate.is_deleted: True,
            TicketTemplate.deleted_at: datetime.utcnow()
        })
        self.db.commit()