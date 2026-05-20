from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.tag import Tag, ticket_tags
from app.models.ticket import Ticket
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

    # --- ticket_tags methods ---

    def get_tags_by_ticket(self, ticket_id: uuid.UUID) -> List[Tag]:
        return self.db.query(Tag).join(ticket_tags).filter(ticket_tags.c.ticket_id == ticket_id).all()

    def assign_tag_to_ticket(self, ticket_id: uuid.UUID, tag_id: str) -> None:
        self.db.execute(ticket_tags.insert().values(ticket_id=ticket_id, tag_id=tag_id))
        self.db.commit()

    def remove_tag_from_ticket(self, ticket_id: uuid.UUID, tag_id: str) -> None:
        self.db.execute(
            ticket_tags.delete().where(
                and_(ticket_tags.c.ticket_id == ticket_id, ticket_tags.c.tag_id == tag_id)
            )
        )
        self.db.commit()

    def is_tag_assigned(self, ticket_id: uuid.UUID, tag_id: str) -> bool:
        result = self.db.query(ticket_tags).filter(
            and_(ticket_tags.c.ticket_id == ticket_id, ticket_tags.c.tag_id == tag_id)
        ).first()
        return result is not None