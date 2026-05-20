from uuid import UUID
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.repositories.tagRepository import TagRepository
from app.repositories.ticketRepository import TicketRepository
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

    # --- Ticket-Tag assignment ---

    def get_tags_by_ticket(self, ticket_id: UUID) -> List[Tag]:
        ticket_repo = TicketRepository(self.db)
        if not ticket_repo.get_by_id(ticket_id):
            raise HTTPException(status_code=404, detail="Ticket not found!")
        return self.repo.get_tags_by_ticket(ticket_id)

    def assign_tag_to_ticket(self, ticket_id: UUID, tag_id: str) -> None:
        ticket_repo = TicketRepository(self.db)
        if not ticket_repo.get_by_id(ticket_id):
            raise HTTPException(status_code=404, detail="Ticket not found!")
        if not self.repo.get_by_id(tag_id):
            raise HTTPException(status_code=404, detail="Tag not found!")
        if self.repo.is_tag_assigned(ticket_id, tag_id):
            raise HTTPException(status_code=400, detail="Tag already assigned to this ticket!")
        self.repo.assign_tag_to_ticket(ticket_id, tag_id)

    def remove_tag_from_ticket(self, ticket_id: UUID, tag_id: str) -> None:
        if not self.repo.is_tag_assigned(ticket_id, tag_id):
            raise HTTPException(status_code=404, detail="Tag is not assigned to this ticket!")
        self.repo.remove_tag_from_ticket(ticket_id, tag_id)