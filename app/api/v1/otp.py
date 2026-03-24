from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.dependencies import get_db
from app.schemas.authSchema import TokenResponse, VerifyOTPRequest
from app.services.authService import AuthService

router = APIRouter(prefix="/otp", tags=["OTP Verification"])


@router.post("/verify-registration", response_model=TokenResponse)
def verify_registration_otp(request: VerifyOTPRequest, db: Session = Depends(get_db)):
    service = AuthService(db)

    customer = service.verify_otp_and_activate(request.email, request.otp_code)

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mã OTP không chính xác, đã hết hạn hoặc email chưa đăng ký!"
        )

    # Tạo token khi OTP đúng
    access_token, refresh_token = service.create_tokens(customer)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)