from pydantic import BaseModel, Field, EmailStr, model_validator
from typing import Optional
from uuid import UUID

class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    password: str
    email: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    address: Optional[str] = None
    timezone: str = "Asia/Ho_Chi_Minh"
    customer_type: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=6)
    confirm_password: str = Field(..., min_length=6)
    
    @model_validator(mode='after')
    def passwords_match(self):
        if self.new_password != self.confirm_password:
            raise ValueError('New password and confirm password do not match')
        return self

class UserUpdateRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None

class UserResponse(BaseModel):
    id: UUID
    username: str
    email: str
    first_name: str
    last_name: str
    phone: Optional[str]
    address: Optional[str]
    status: str
    type: Optional[str]
    avatar: Optional[str]
    class Config:
        from_attributes = True

class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp_code: str = Field(..., min_length=6, max_length=6)

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp_code: str = Field(..., min_length=6, max_length=6)
    new_password: str = Field(..., min_length=6)
    confirm_password: str = Field(..., min_length=6)
    
    @model_validator(mode='after')
    def passwords_match(self):
        if self.new_password != self.confirm_password:
            raise ValueError('New password and confirm password do not match')
        return self

class MessageResponse(BaseModel):
    message: str

class LogoutRequest(BaseModel):
    refresh_token: Optional[str] = None