from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.repositories.tagRepository import TagRepository
from app.models.tag import Tag
from app.schemas.admin.tag import TagCreate, TagUpdate
from typing import List


class TagService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = TagRepository(db)

    def create_tag(self, data: TagCreate) -> Tag:
        existing_tag = self.repo.get_by_name(data.name)
        if existing_tag:
            raise HTTPException(status_code=400, detail="Tag with this name already exists!")

        new_tag = Tag(**data.model_dump())
        return self.repo.create(new_tag)

    def get_all_tags(self) -> List[Tag]:
        return self.repo.get_all()

    def get_tag_by_id(self, tag_id: str) -> Tag:
        tag = self.repo.get_by_id(tag_id)
        if not tag:
            raise HTTPException(status_code=404, detail="Tag not found!")
        return tag

    def update_tag(self, tag_id: str, data: TagUpdate) -> Tag:
        tag = self.repo.get_by_id(tag_id)
        if not tag:
            raise HTTPException(status_code=404, detail="Tag not found!")

        update_data = data.model_dump(exclude_unset=True)
        if update_data.get("name") and update_data["name"] != tag.name:
            if self.repo.get_by_name(update_data["name"]):
                raise HTTPException(status_code=400, detail="Tag with this name already exists!")

        for key, value in update_data.items():
            setattr(tag, key, value)

        return self.repo.update(tag)

    def delete_tag(self, tag_id: str) -> None:
        tag = self.repo.get_by_id(tag_id)
        if not tag:
            raise HTTPException(status_code=404, detail="Tag not found!")
        self.repo.delete(tag)