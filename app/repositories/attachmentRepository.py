from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional
from app.models.interaction import Attachment
from datetime import datetime, timedelta


class AttachmentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, attachment: Attachment) -> Attachment:
        """Create a new attachment"""
        self.db.add(attachment)
        self.db.commit()
        self.db.refresh(attachment)
        return attachment

    def get_by_id(self, attachment_id: UUID) -> Optional[Attachment]:
        """Get attachment by ID"""
        return self.db.query(Attachment).filter(
            Attachment.id_attachment == attachment_id,
            Attachment.is_deleted == False
        ).first()

    def get_by_id_include_deleted(self, attachment_id: UUID) -> Optional[Attachment]:
        """Get attachment by ID including deleted ones"""
        return self.db.query(Attachment).filter(
            Attachment.id_attachment == attachment_id
        ).first()

    def get_by_reference(self, reference_type: str, reference_id: UUID) -> List[Attachment]:
        """Get all attachments for a reference (ticket/message)"""
        return self.db.query(Attachment).filter(
            Attachment.reference_type == reference_type,
            Attachment.id_reference == reference_id,
            Attachment.is_deleted == False
        ).all()

    def get_by_uploader(self, uploader_id: UUID, limit: int = 100) -> List[Attachment]:
        """Get attachments uploaded by a user"""
        return self.db.query(Attachment).filter(
            Attachment.id_uploader == uploader_id,
            Attachment.is_deleted == False
        ).order_by(Attachment.created_at.desc()).limit(limit).all()

    def update(self, attachment: Attachment) -> Attachment:
        """Update an attachment"""
        attachment.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(attachment)
        return attachment

    def soft_delete(self, attachment_id: UUID) -> bool:
        """Soft delete an attachment"""
        attachment = self.get_by_id(attachment_id)
        if attachment:
            attachment.is_deleted = True
            attachment.updated_at = datetime.utcnow()
            self.db.commit()
            return True
        return False

    def hard_delete(self, attachment_id: UUID) -> bool:
        """Permanently delete an attachment"""
        attachment = self.get_by_id_include_deleted(attachment_id)
        if attachment:
            self.db.delete(attachment)
            self.db.commit()
            return True
        return False

    def get_orphan_attachments(self, days: int = 30) -> List[Attachment]:
        """Get attachments not linked to any reference after X days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        return self.db.query(Attachment).filter(
            Attachment.reference_type == None,
            Attachment.id_reference == None,
            Attachment.is_deleted == False,
            Attachment.is_permanent == False,
            Attachment.created_at < cutoff_date
        ).all()

    def count_by_reference(self, reference_type: str, reference_id: UUID) -> int:
        """Count attachments for a reference"""
        return self.db.query(Attachment).filter(
            Attachment.reference_type == reference_type,
            Attachment.id_reference == reference_id,
            Attachment.is_deleted == False
        ).count()
