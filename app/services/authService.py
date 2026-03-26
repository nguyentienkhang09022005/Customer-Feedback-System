from typing import Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session

from app.core.constants import HumanStatusEnum, MembershipTierEnum
from app.repositories.humanRepository import HumanRepository
from app.repositories.customerRepository import CustomerRepository
from app.core.security import verify_password, create_access_token, create_refresh_token, verify_token, get_password_hash
from app.models.human import Human, Customer
from app.schemas.authSchema import RegisterRequest, UserUpdateRequest
from app.services.otpService import OTPService

class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = HumanRepository(db)
        self.customer_repo = CustomerRepository(db)

    def _generate_customer_code(self) -> str:
        prefix_year = f"KH{datetime.utcnow().strftime('%y')}"
        latest = self.customer_repo.get_latest_code(prefix_year)
        new_num = int(latest[0][-3:]) + 1 if (latest and latest[0]) else 1
        return f"{prefix_year}{new_num:03d}"

    def register_customer(self, data: RegisterRequest) -> bool:
        if self.customer_repo.check_human_exists(data.email, data.username, data.phone):
            return False

        return OTPService.generate_and_store_otp(data.email, data)

    def verify_otp_and_activate(self, email: str, otp_code: str) -> Optional[Customer]:
        data: RegisterRequest = OTPService.verify_and_get_data(email, otp_code)

        if not data:
            return None

        new_customer = Customer(
            username=data.username,
            email=data.email,
            password_hash=get_password_hash(data.password),
            first_name=data.first_name,
            last_name=data.last_name,
            phone=data.phone or "",
            address=data.address or "",
            timezone=data.timezone,
            customer_type=data.customer_type,
            status=HumanStatusEnum.ACTIVE,
            customer_code=self._generate_customer_code(),
            membership_tier=MembershipTierEnum.STANDARD
        )
        return self.customer_repo.create(new_customer)

    def authenticate_user(self, username: str, password: str) -> Optional[Human]:
        user = self.repo.get_by_username(username)
        if not user or not verify_password(password, user.password_hash):
            return None
        if user.status != HumanStatusEnum.ACTIVE:
            return None
        return user

    def create_tokens(self, user: Human) -> Tuple[str, str]:
        access_token, _ = create_access_token(user)
        refresh_token, _ = create_refresh_token(user)
        return access_token, refresh_token

    def verify_access_token(self, token: str) -> Optional[str]:
        return verify_token(token, "access")

    def verify_refresh_token(self, token: str) -> Optional[str]:
        return verify_token(token, "refresh")

    def refresh_tokens(self, refresh_token: str) -> Optional[Tuple[str, str]]:
        payload = self.verify_refresh_token(refresh_token)
        if not payload:
            return None

        user_id = payload.get("sub")
        user = self.repo.get_by_id(user_id)

        if not user:
            return None

        return self.create_tokens(user)

    def change_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        user = self.repo.get_by_id(user_id)
        if not user:
            return False
        if not verify_password(old_password, user.password_hash):
            return False
        user.password_hash = get_password_hash(new_password)
        self.db.commit()
        self.db.refresh(user)
        return True

    def update_profile(self, user_id: str, data: UserUpdateRequest) -> Optional[Human]:
        user = self.repo.get_by_id(user_id)
        if not user:
            return None
        if data.first_name is not None:
            user.first_name = data.first_name
        if data.last_name is not None:
            user.last_name = data.last_name
        if data.phone is not None:
            user.phone = data.phone
        if data.address is not None:
            user.address = data.address
        self.db.commit()
        self.db.refresh(user)
        return user

    def update_avatar(self, user_id: str, avatar_url: str) -> Optional[Human]:
        user = self.repo.get_by_id(user_id)
        if not user:
            return None
        user.avatar = avatar_url
        self.db.commit()
        self.db.refresh(user)
        return user

    def initiate_forgot_password(self, email: str) -> bool:
        """
        Initiate password reset process for a user.
        Returns True if email exists and OTP was sent.
        Always returns True to prevent email enumeration.
        """
        # Check if email exists in the system
        user = self.repo.get_by_email(email)
        if not user:
            # Return True anyway to prevent email enumeration
            # (attacker can't tell if email exists)
            return True
        
        # Generate and send OTP for password reset
        OTPService.generate_otp_for_password_reset(email)
        return True

    def reset_password_with_otp(self, email: str, otp_code: str, new_password: str) -> bool:
        """
        Reset password using OTP verification.
        Returns True if OTP is valid and password was reset.
        """
        # Verify the OTP first
        if not OTPService.verify_password_reset_otp(email, otp_code):
            return False
        
        # Get user by email
        user = self.repo.get_by_email(email)
        if not user:
            return False
        
        # Update password
        user.password_hash = get_password_hash(new_password)
        self.db.commit()
        return True