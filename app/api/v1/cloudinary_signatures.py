from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Literal

from app.core.cloudinary import generate_upload_signature
from app.core.response import APIResponse
from app.api.dependencies import get_current_user
from app.models.human import Human

router = APIRouter(prefix="/chat", tags=["Chat - Cloudinary"])


class UploadSignatureRequest(BaseModel):
    filename: str
    file_type: Literal["image", "file"]


ALLOWED_IMAGE_TYPES = {"png", "jpeg", "jpg", "gif", "webp"}
ALLOWED_FILE_TYPES = {"pdf", "doc", "docx", "xls", "xlsx", "zip"}


def get_extension(filename: str) -> str:
    """Extract file extension from filename."""
    if "." in filename:
        return filename.rsplit(".", 1)[-1].lower()
    return ""


@router.post("/upload-signature", response_model=APIResponse[dict])
def get_upload_signature(
    data: UploadSignatureRequest,
    current_user: Human = Depends(get_current_user)
):
    """
    Generate a signed URL for direct Cloudinary upload from frontend.
    
    This endpoint validates the file type and returns the necessary parameters
    for the frontend to upload directly to Cloudinary using a signed upload.
    """
    file_ext = get_extension(data.filename)
    
    if data.file_type == "image":
        if file_ext not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid image type. Allowed types: {', '.join(ALLOWED_IMAGE_TYPES)}"
            )
    elif data.file_type == "file":
        if file_ext not in ALLOWED_FILE_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed types: {', '.join(ALLOWED_FILE_TYPES)}"
            )
    
    try:
        signature_data = generate_upload_signature(
            filename=data.filename,
            folder="chat_attachments"
        )
        
        return APIResponse(
            status=True,
            code=200,
            message="Success",
            data=signature_data
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate upload signature: {str(e)}")
