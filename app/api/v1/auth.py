from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.api.dependencies import get_db, get_current_user
from app.schemas.authSchema import LoginRequest, TokenResponse, RefreshTokenRequest, RegisterRequest, MessageResponse, VerifyOTPRequest, ForgotPasswordRequest, ResetPasswordRequest
from app.services.authService import AuthService
from app.models.human import Human
from app.api.dependencies import security

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


@router.post("/verify-otp", response_model=TokenResponse)
def verify_otp(request: VerifyOTPRequest, db: Session = Depends(get_db)):
    """
    Verify OTP and activate account.
    Returns access token and refresh token on success.
    """
    service = AuthService(db)
    customer = service.verify_otp_and_activate(request.email, request.otp_code)

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mã OTP không hợp lệ hoặc đã hết hạn!"
        )

    access_token, refresh_token = service.create_tokens(customer)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/forgot-password", response_model=MessageResponse)
def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """
    Initiate password reset process.
    Sends OTP to email if email exists in system.
    Always returns success to prevent email enumeration.
    """
    service = AuthService(db)
    service.initiate_forgot_password(request.email)

    return MessageResponse(
        message="Nếu email tồn tại trong hệ thống, mã OTP đã được gửi (hiệu lực 5 phút)!")


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    """
    Reset password using valid OTP.
    """
    service = AuthService(db)
    success = service.reset_password_with_otp(
        request.email,
        request.otp_code,
        request.new_password
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mã OTP không hợp lệ hoặc đã hết hạn!"
        )

    return MessageResponse(
        message="Đặt lại mật khẩu thành công! Vui lòng đăng nhập với mật khẩu mới.")


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
    from app.core.security import decode_token_unsafe
    from app.services.tokenBlacklistService import TokenBlacklistService
    from datetime import datetime
    
    service = AuthService(db)
    
    # Decode old refresh token to get JTI for blacklisting
    old_payload = decode_token_unsafe(request.refresh_token)
    
    tokens = service.refresh_tokens(request.refresh_token)

    if not tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token không hợp lệ hoặc đã hết hạn. Vui lòng đăng nhập lại!"
        )

    # Blacklist old refresh token after successful refresh
    if old_payload:
        jti = old_payload.get("jti")
        exp = old_payload.get("exp")
        if jti and exp:
            expires_in = exp - int(datetime.utcnow().timestamp())
            if expires_in > 0:
                user_id = old_payload.get("sub")
                if user_id:
                    TokenBlacklistService.blacklist_refresh_token(
                        jti,
                        user_id,
                        expires_in
                    )

    access_token, refresh_token = tokens
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/logout")
def logout(
    current_user: Human = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Logout current user by blacklisting their access token.
    """
    from app.core.security import decode_token_unsafe
    from app.services.tokenBlacklistService import TokenBlacklistService
    from datetime import datetime
    
    token = credentials.credentials
    payload = decode_token_unsafe(token)
    
    if payload:
        jti = payload.get("jti")
        exp = payload.get("exp")
        if jti and exp:
            expires_in = exp - int(datetime.utcnow().timestamp())
            if expires_in > 0:
                TokenBlacklistService.blacklist_access_token(
                    jti, 
                    str(current_user.id), 
                    expires_in
                )
    
    return {"message": "Đăng xuất thành công!"}