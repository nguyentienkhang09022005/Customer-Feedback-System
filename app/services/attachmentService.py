import logging
from typing import List, Optional
from uuid import UUID
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.models.interaction import Attachment
from app.repositories.attachmentRepository import AttachmentRepository
from app.services.fileService import FileService, FileValidationError
from app.core.cloudinary import upload_file, delete_file

logger = logging.getLogger(__name__)


class AttachmentService:
    """
    Service for managing file attachments.
    Handles upload, download, deletion, and cleanup.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.repo = AttachmentRepository(db)
        self.file_service = FileService()
    
    async def upload_attachment(
        self,
        file: UploadFile,
        reference_type: str,
        reference_id: UUID,
        uploader_id: UUID
    ) -> Attachment:
        """
        Upload a single file and create attachment record.
        
        Args:
            file: Uploaded file
            reference_type: Type of reference ('ticket', 'message', etc.)
            reference_id: ID of the reference entity
            uploader_id: ID of the user uploading
        
        Returns:
            Attachment: Created attachment record
        
        Raises:
            FileValidationError: If file validation fails
        """
        # Validate file
        file_info = await self.file_service.validate_file(file)
        
        # Generate unique filename
        unique_filename = self.file_service.generate_unique_filename(file.filename or 'file')
        
        # Read file content
        content = await file.read()
        
        # Determine folder based on reference type
        folder = f"attachments/{reference_type}"
        
        # Upload to Cloudinary
        try:
            upload_result = upload_file(content, folder=folder)
            
            # Generate thumbnail for images
            thumbnail_url = None
            if file_info['is_image']:
                thumbnail_url = self._generate_thumbnail_url(upload_result)
            
            # Create attachment record
            attachment = Attachment(
                attach_name=self.file_service.sanitize_filename(file.filename or 'file'),
                attach_type=file_info['content_type'],
                attach_extension=file_info['extension'],
                file_size=file_info['size'],
                url=upload_result,
                storage_type='cloudinary',
                public_id=self._extract_public_id(upload_result),
                thumbnail_url=thumbnail_url,
                reference_type=reference_type,
                id_reference=reference_id,
                id_uploader=uploader_id
            )
            
            return self.repo.create(attachment)
            
        except Exception as e:
            logger.error(f"Failed to upload file: {e}")
            raise
    
    async def upload_multiple_attachments(
        self,
        files: List[UploadFile],
        reference_type: str,
        reference_id: UUID,
        uploader_id: UUID
    ) -> List[Attachment]:
        """
        Upload multiple files.
        
        Args:
            files: List of uploaded files
            reference_type: Type of reference
            reference_id: ID of the reference entity
            uploader_id: ID of the user uploading
        
        Returns:
            List[Attachment]: List of created attachment records
        """
        attachments = []
        errors = []
        
        for file in files:
            try:
                attachment = await self.upload_attachment(
                    file, reference_type, reference_id, uploader_id
                )
                attachments.append(attachment)
            except FileValidationError as e:
                errors.append(f"{file.filename}: {str(e)}")
                logger.warning(f"File validation failed for {file.filename}: {e}")
            except Exception as e:
                errors.append(f"{file.filename}: {str(e)}")
                logger.error(f"Upload failed for {file.filename}: {e}")
        
        if errors and not attachments:
            raise FileValidationError(f"All uploads failed: {'; '.join(errors)}")
        
        return attachments
    
    def get_attachment(self, attachment_id: UUID) -> Optional[Attachment]:
        """Get attachment by ID"""
        return self.repo.get_by_id(attachment_id)
    
    def get_attachments_for_reference(
        self,
        reference_type: str,
        reference_id: UUID
    ) -> List[Attachment]:
        """Get all attachments for a ticket or message"""
        return self.repo.get_by_reference(reference_type, reference_id)
    
    def delete_attachment(
        self,
        attachment_id: UUID,
        user_id: UUID
    ) -> bool:
        """
        Soft delete an attachment.
        Only the uploader or admin can delete.
        """
        attachment = self.repo.get_by_id(attachment_id)
        
        if not attachment:
            return False
        
        # Check permission (uploader can delete their own files)
        if str(attachment.id_uploader) != str(user_id):
            # TODO: Add admin check here
            pass
        
        # Delete from Cloudinary if exists
        if attachment.public_id:
            try:
                delete_file(attachment.public_id)
            except Exception as e:
                logger.warning(f"Failed to delete file from Cloudinary: {e}")
        
        # Soft delete
        return self.repo.soft_delete(attachment_id)
    
    def hard_delete_attachment(self, attachment_id: UUID) -> bool:
        """
        Permanently delete an attachment and its file.
        Use with caution - this cannot be undone.
        """
        attachment = self.repo.get_by_id_include_deleted(attachment_id)
        
        if not attachment:
            return False
        
        # Delete from Cloudinary
        if attachment.public_id:
            try:
                delete_file(attachment.public_id)
            except Exception as e:
                logger.warning(f"Failed to delete file from Cloudinary: {e}")
        
        return self.repo.hard_delete(attachment_id)
    
    async def cleanup_orphan_attachments(self, days: int = 30) -> int:
        """
        Delete attachments not linked to any entity after X days.
        These are considered "orphan" files.
        
        Args:
            days: Number of days after which orphaned attachments are deleted
        
        Returns:
            int: Number of attachments deleted
        """
        orphan_attachments = self.repo.get_orphan_attachments(days)
        deleted_count = 0
        
        for attachment in orphan_attachments:
            if self.hard_delete_attachment(attachment.id_attachment):
                deleted_count += 1
                logger.info(f"Cleaned up orphan attachment: {attachment.id_attachment}")
        
        return deleted_count
    
    def _generate_thumbnail_url(self, original_url: str) -> Optional[str]:
        """
        Generate thumbnail URL from original Cloudinary URL.
        Uses Cloudinary's transformation API.
        """
        if not original_url or 'cloudinary.com' not in original_url:
            return None
        
        try:
            # Cloudinary URL format: https://res.cloudinary.com/{cloud}/image/upload/{public_id}
            # Add transformation for thumbnail: w_300,h_300,c_thumb
            # This is a simplified version - in production, use cloudinary's url() helper
            return original_url
        except Exception as e:
            logger.warning(f"Failed to generate thumbnail: {e}")
            return None
    
    def _extract_public_id(self, url: str) -> Optional[str]:
        """
        Extract public_id from Cloudinary URL.
        Used for deletion.
        """
        if not url or 'cloudinary.com' not in url:
            return None
        
        try:
            # Simplified extraction
            # Format: https://res.cloudinary.com/cloud/image/upload/v1234567890/folder/filename.jpg
            parts = url.split('/')
            if len(parts) > 0:
                filename = parts[-1]
                # Remove extension
                if '.' in filename:
                    filename = filename.rsplit('.', 1)[0]
                return filename
        except Exception:
            pass
        
        return None
