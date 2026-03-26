from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.api.dependencies import get_db, get_current_user
from app.models.human import Human
from app.schemas.attachmentSchema import (
    AttachmentResponse,
    AttachmentUploadResponse,
    AttachmentDeleteResponse,
    AttachmentListResponse,
    AttachmentCleanupResponse
)
from app.services.attachmentService import AttachmentService
from app.services.fileService import FileValidationError

router = APIRouter(prefix="/attachments", tags=["Attachments"])


@router.post("/upload", response_model=AttachmentUploadResponse)
async def upload_attachment(
    file: UploadFile = File(...),
    reference_type: str = Form(...),
    reference_id: str = Form(...),
    current_user: Human = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload a single file attachment.
    
    - **file**: File to upload (max 10MB)
    - **reference_type**: Type of reference ('ticket', 'message')
    - **reference_id**: ID of the reference entity
    """
    service = AttachmentService(db)
    
    try:
        attachment = await service.upload_attachment(
            file=file,
            reference_type=reference_type,
            reference_id=UUID(reference_id),
            uploader_id=current_user.id
        )
        
        return AttachmentUploadResponse(
            id_attachment=attachment.id_attachment,
            attach_name=attachment.attach_name,
            url=attachment.url,
            thumbnail_url=attachment.thumbnail_url,
            file_size=attachment.file_size,
            message="File uploaded successfully"
        )
        
    except FileValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )


@router.post("/upload-multiple", response_model=List[AttachmentUploadResponse])
async def upload_multiple_attachments(
    files: List[UploadFile] = File(...),
    reference_type: str = Form(...),
    reference_id: str = Form(...),
    current_user: Human = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload multiple file attachments.
    
    - **files**: List of files to upload (max 10MB each)
    - **reference_type**: Type of reference ('ticket', 'message')
    - **reference_id**: ID of the reference entity
    """
    service = AttachmentService(db)
    
    try:
        attachments = await service.upload_multiple_attachments(
            files=files,
            reference_type=reference_type,
            reference_id=UUID(reference_id),
            uploader_id=current_user.id
        )
        
        return [
            AttachmentUploadResponse(
                id_attachment=att.id_attachment,
                attach_name=att.attach_name,
                url=att.url,
                thumbnail_url=att.thumbnail_url,
                file_size=att.file_size,
                message="File uploaded successfully"
            )
            for att in attachments
        ]
        
    except FileValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )


@router.get("/{attachment_id}", response_model=AttachmentResponse)
async def get_attachment(
    attachment_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get attachment details by ID.
    """
    service = AttachmentService(db)
    attachment = service.get_attachment(attachment_id)
    
    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attachment not found"
        )
    
    return attachment


@router.get("/reference/{reference_type}/{reference_id}", response_model=AttachmentListResponse)
async def list_attachments(
    reference_type: str,
    reference_id: UUID,
    db: Session = Depends(get_db)
):
    """
    List all attachments for a specific ticket or message.
    """
    service = AttachmentService(db)
    attachments = service.get_attachments_for_reference(reference_type, reference_id)
    
    return AttachmentListResponse(
        attachments=attachments,
        total=len(attachments)
    )


@router.delete("/{attachment_id}", response_model=AttachmentDeleteResponse)
async def delete_attachment(
    attachment_id: UUID,
    current_user: Human = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete an attachment.
    Only the uploader can delete their own attachments.
    """
    service = AttachmentService(db)
    success = service.delete_attachment(attachment_id, current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attachment not found or permission denied"
        )
    
    return AttachmentDeleteResponse(
        id_attachment=attachment_id,
        message="Attachment deleted successfully"
    )


@router.post("/cleanup", response_model=AttachmentCleanupResponse)
async def cleanup_orphan_attachments(
    days: int = 30,
    current_user: Human = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Cleanup orphaned attachments (admin only).
    Deletes attachments that are not linked to any entity after X days.
    """
    # TODO: Add admin check
    # if current_user.type != 'employee' or current_user.role_name != 'Admin':
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Admin access required"
    #     )
    
    service = AttachmentService(db)
    deleted_count = await service.cleanup_orphan_attachments(days)
    
    return AttachmentCleanupResponse(
        deleted_count=deleted_count,
        message=f"Cleanup completed. Deleted {deleted_count} orphan attachments."
    )
