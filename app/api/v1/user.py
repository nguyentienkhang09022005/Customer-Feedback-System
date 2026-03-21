from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from app.api.dependencies import get_db, get_current_user
from app.schemas.authSchema import UserResponse, ChangePasswordRequest, UserUpdateRequest
from app.services.authService import AuthService
from app.models.human import Human
from app.core.cloudinary import upload_file

router = APIRouter(prefix="/user", tags=["user"])

ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/gif", "image/webp"]

@router.get("/me", response_model=UserResponse)
def get_me(current_user: Human = Depends(get_current_user)):
    return current_user

@router.put("/me", response_model=UserResponse)
def update_profile(
    request: UserUpdateRequest,
    current_user: Human = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = AuthService(db)
    user = service.update_profile(str(current_user.id), request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@router.post("/change-password")
def change_password(
    request: ChangePasswordRequest,
    current_user: Human = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = AuthService(db)
    success = service.change_password(str(current_user.id), request.old_password, request.new_password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid old password"
        )
    return {"message": "Password changed successfully"}

@router.post("/avatar")
def upload_avatar(
    file: UploadFile = File(...),
    current_user: Human = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only image files are allowed (jpeg, png, gif, webp)"
        )
    
    url = upload_file(file.file, folder="avatars")
    
    service = AuthService(db)
    user = service.update_avatar(str(current_user.id), url)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"avatar_url": url}