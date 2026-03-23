from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.repositories.ticketCategoryRepository import TicketCategoryRepository
from app.models.ticket import TicketCategory
from app.schemas.ticketCategorySchema import TicketCategoryCreate, TicketCategoryUpdate


class TicketCategoryService:
    def __init__(self, db: Session):
        self.repo = TicketCategoryRepository(db)

    def create_category(self, data: TicketCategoryCreate):
        existing_cat = self.repo.get_by_name(data.name)
        if existing_cat:
            raise HTTPException(status_code=400, detail="Tên danh mục này đã tồn tại!")

        new_cat = TicketCategory(**data.dict())
        return self.repo.create(new_cat)

    def get_all(self):
        return self.repo.get_all()

    def update_category(self, cat_id: str, data: TicketCategoryUpdate):
        category = self.repo.get_by_id(cat_id)
        if not category:
            raise HTTPException(status_code=404, detail="Không tìm thấy danh mục!")

        update_data = data.dict(exclude_unset=True)
        if "name" in update_data and update_data["name"] != category.name:
            if self.repo.get_by_name(update_data["name"]):
                raise HTTPException(status_code=400, detail="Tên danh mục này đã tồn tại!")

        for key, value in update_data.items():
            setattr(category, key, value)

        return self.repo.update(category)

    def delete_category(self, cat_id: str):
        category = self.repo.get_by_id(cat_id)
        if not category:
            raise HTTPException(status_code=404, detail="Không tìm thấy danh mục!")

        self.repo.delete(category)