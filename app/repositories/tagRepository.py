from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.tag import Tag
from typing import List, Optional
import uuid


class TagRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> List[Tag]:
        return self.db.query(Tag).all()

    def get_by_id(self, tag_id: str) -> Optional[Tag]:
        return self.db.query(Tag).filter(Tag.id_tag == tag_id).first()

    def get_by_name(self, name: str) -> Optional[Tag]:
        return self.db.query(Tag).filter(Tag.name == name).first()

    def create(self, tag: Tag) -> Tag:
        self.db.add(tag)
        self.db.commit()
        self.db.refresh(tag)
        return tag

    def update(self, tag: Tag) -> Tag:
        self.db.commit()
        self.db.refresh(tag)
        return tag

    def delete(self, tag: Tag) -> None:
        self.db.delete(tag)
        self.db.commit()