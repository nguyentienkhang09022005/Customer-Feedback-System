from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.repositories.ticketCategoryRepository import TicketCategoryRepository
from app.repositories.ticketTemplateRepository import TicketTemplateRepository
from app.models.ticket import TicketCategory
from app.schemas.ticketCategorySchema import TicketCategoryCreate, TicketCategoryUpdate
from typing import List, Optional


class TicketCategoryService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = TicketCategoryRepository(db)
        self.template_repo = TicketTemplateRepository(db)

    def create_category(self, data: TicketCategoryCreate) -> TicketCategory:
        existing_cat = self.repo.get_by_name(data.name)
        if existing_cat:
            raise HTTPException(status_code=400, detail="Tên danh mục này đã tồn tại!")

        new_cat = TicketCategory(**data.model_dump())
        return self.repo.create(new_cat)

    def get_all(self) -> List[TicketCategory]:
        return self.repo.get_all()

    def get_active_all(self) -> List[TicketCategory]:
        return self.repo.get_active_all()

    def get_by_id(self, cat_id: str) -> Optional[TicketCategory]:
        return self.repo.get_by_id(cat_id)

    def update_category(self, cat_id: str, data: TicketCategoryUpdate) -> TicketCategory:
        category = self.repo.get_by_id(cat_id)
        if not category:
            raise HTTPException(status_code=404, detail="Không tìm thấy danh mục!")

        update_data = data.model_dump(exclude_unset=True)
        if update_data.get("name") and update_data["name"] != category.name:
            if self.repo.get_by_name(update_data["name"]):
                raise HTTPException(status_code=400, detail="Tên danh mục này đã tồn tại!")

        for key, value in update_data.items():
            setattr(category, key, value)

        return self.repo.update(category)

    def delete_category(self, cat_id: str) -> TicketCategory:
        category = self.repo.get_by_id(cat_id)
        if not category:
            raise HTTPException(status_code=404, detail="Không tìm thấy danh mục!")

        return self.repo.soft_delete(category)

    def hard_delete_category(self, cat_id: str) -> None:
        category = self.repo.get_by_id(cat_id)
        if not category:
            raise HTTPException(status_code=404, detail="Không tìm thấy danh mục!")

        self.template_repo.soft_delete_all_versions_by_category(cat_id)
        self.repo.permanent_delete(category)