from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.dependencies import get_db, get_current_user
from app.schemas.authSchema import LoginRequest, TokenResponse, RefreshTokenRequest, RegisterRequest, MessageResponse
from app.services.authService import AuthService
from app.models.human import Human

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=MessageResponse)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    is_success = service.register_customer(request)

    if not is_success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username, email hoặc số điện thoại đã tồn tại trong hệ thống!"
        )

    return MessageResponse(
        message="Đăng ký bước 1 thành công. Vui lòng kiểm tra email để lấy mã OTP (hiệu lực 5 phút)!")


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    user = service.authenticate_user(request.username, request.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tài khoản hoặc mật khẩu không chính xác, hoặc tài khoản đang bị khóa!"
        )

    access_token, refresh_token = service.create_tokens(user)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
def refresh(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    tokens = service.refresh_tokens(request.refresh_token)

    if not tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token không hợp lệ hoặc đã hết hạn. Vui lòng đăng nhập lại!"
        )

    access_token, refresh_token = tokens
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/logout")
def logout(current_user: Human = Depends(get_current_user)):
    # Có thể kết hợp đưa token vào blacklist ở đây sau này
    return {"message": "Đăng xuất thành công!"}