from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.repositories.ticketTemplateRepository import TicketTemplateRepository
from app.repositories.ticketCategoryRepository import TicketCategoryRepository
from app.models.ticket import TicketTemplate
from app.schemas.ticketCategorySchema import TicketTemplateCreate, TicketTemplateUpdate, TicketTemplateOut
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime


class TicketTemplateService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = TicketTemplateRepository(db)
        self.category_repo = TicketCategoryRepository(db)

    def _build_template_out(self, template: TicketTemplate) -> TicketTemplateOut:
        return TicketTemplateOut(
            id_template=template.id_template,
            version=template.version,
            name=template.name,
            description=template.description,
            fields_config=template.fields_config,
            id_category=template.id_category,
            id_author=template.id_author,
            is_active=template.is_active,
            is_deleted=template.is_deleted,
            deleted_at=template.deleted_at,
            created_at=template.created_at,
            updated_at=template.updated_at
        )

    def create_template(self, data: TicketTemplateCreate, author_id: uuid.UUID = None) -> TicketTemplate:
        new_id = uuid.uuid4()

        if data.id_category:
            category = self.category_repo.get_by_id(data.id_category)
            if not category:
                raise HTTPException(status_code=404, detail="Không tìm thấy danh mục!")
            if category.is_deleted:
                raise HTTPException(status_code=400, detail="Danh mục đã bị xóa!")

        template = TicketTemplate(
            id_template=new_id,
            version=1,
            name=data.name,
            description=data.description,
            fields_config=data.fields_config,
            id_category=data.id_category,
            id_author=author_id,
            is_active=data.is_active if data.is_active is not None else True,
            is_deleted=False
        )

        return self.repo.create(template)

    def update_template(self, id_template: uuid.UUID, data: TicketTemplateUpdate, author_id: uuid.UUID = None) -> TicketTemplate:
        latest = self.repo.get_latest_version(id_template)
        if not latest:
            raise HTTPException(status_code=404, detail="Không tìm thấy template!")
        if latest.is_deleted:
            raise HTTPException(status_code=400, detail="Template đã bị xóa!")

        if data.fields_config is not None and data.fields_config != latest.fields_config:
            new_version = self.repo.get_next_version(id_template)
            latest.is_active = False
            self.repo.update(latest)

            new_template = TicketTemplate(
                id_template=id_template,
                version=new_version,
                name=data.name if data.name else latest.name,
                description=data.description if data.description else latest.description,
                fields_config=data.fields_config,
                id_category=data.id_category if data.id_category else latest.id_category,
                id_author=author_id or latest.id_author,
                is_active=True,
                is_deleted=False
            )
            return self.repo.create(new_template)

        if data.name is not None:
            latest.name = data.name
        if data.description is not None:
            latest.description = data.description
        if data.id_category is not None:
            latest.id_category = data.id_category
        if data.is_active is not None:
            latest.is_active = data.is_active

        latest.updated_at = datetime.utcnow()
        return self.repo.update(latest)

    def get_template(self, id_template: uuid.UUID, version: int = None) -> Optional[TicketTemplate]:
        if version:
            return self.repo.get_by_id_version(id_template, version)
        return self.repo.get_latest_version(id_template)

    def get_templates_by_category(self, id_category: uuid.UUID) -> List[TicketTemplate]:
        return self.repo.get_by_category(id_category)

    def get_all_templates(self) -> List[TicketTemplate]:
        return self.repo.get_active_all()

    def get_all_versions(self, id_template: uuid.UUID) -> List[TicketTemplate]:
        return self.repo.get_versions(id_template)

    def delete_template(self, id_template: uuid.UUID) -> None:
        template = self.repo.get_latest_version(id_template)
        if not template:
            raise HTTPException(status_code=404, detail="Không tìm thấy template!")

        self.repo.soft_delete_all_versions(id_template)

    def activate_template(self, id_template: uuid.UUID) -> TicketTemplate:
        template = self.repo.get_latest_version(id_template)
        if not template:
            raise HTTPException(status_code=404, detail="Không tìm thấy template!")

        template.is_active = True
        template.updated_at = datetime.utcnow()
        return self.repo.update(template)

    def validate_fields_config(self, fields_config: dict) -> bool:
        if "fields" not in fields_config:
            return False

        required_types = ["text", "textarea", "select", "file", "checkbox"]
        supported_types = [
            "text", "textarea", "email", "phone", "number", "url",
            "date", "time", "datetime", "select", "select_multi",
            "radio", "checkbox", "checkbox_group", "file", "file_multi",
            "rating", "rich_text", "hidden", "readonly", "info"
        ]

        for field in fields_config["fields"]:
            if "name" not in field or "type" not in field:
                return False
            if field["type"] not in supported_types:
                return False

        return True