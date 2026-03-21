from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.dependencies import get_db, get_current_user
from app.schemas.authSchema import LoginRequest, TokenResponse, RefreshTokenRequest, RegisterRequest, ChangePasswordRequest, UserResponse
from app.services.authService import AuthService
from app.models.human import Human

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register", response_model=TokenResponse)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    customer = service.register_customer(request)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username, email hoặc phone đã tồn tại"
        )
    access_token, refresh_token = service.create_tokens(str(customer.id))
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)

@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    user = service.authenticate_user(request.username, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    access_token, refresh_token = service.create_tokens(str(user.id))
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)

@router.post("/refresh", response_model=TokenResponse)
def refresh(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    tokens = service.refresh_tokens(request.refresh_token)
    if not tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    access_token, refresh_token = tokens
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)

@router.post("/logout")
def logout(current_user: Human = Depends(get_current_user)):
    return {"message": "Successfully logged out"}

@router.get("/me", response_model=UserResponse)
def get_me(current_user: Human = Depends(get_current_user)):
    return current_user

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