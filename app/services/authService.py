from typing import Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from app.repositories.humanRepository import HumanRepository
from app.repositories.customerRepository import CustomerRepository
from app.core.security import verify_password, create_access_token, create_refresh_token, verify_token, get_password_hash
from app.models.human import Human, Customer
from app.schemas.authSchema import RegisterRequest
from app.core.constants import HumanStatusEnum, MembershipTierEnum

class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = HumanRepository(db)
        self.customer_repo = CustomerRepository(db)

    def authenticate_user(self, username: str, password: str) -> Optional[Human]:
        user = self.repo.get_by_username(username)
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        if user.status != "Active":
            return None
        return user

    def _generate_customer_code(self) -> str:
        prefix_year = f"KH{datetime.utcnow().strftime('%y')}"
        latest = self.customer_repo.get_latest_code(prefix_year)
        new_num = int(latest[0][-3:]) + 1 if (latest and latest[0]) else 1
        return f"{prefix_year}{new_num:03d}"

    def register_customer(self, data: RegisterRequest) -> Optional[Customer]:
        if self.customer_repo.check_human_exists(data.email, data.username, data.phone):
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

    def create_tokens(self, user_id: str) -> Tuple[str, str]:
        access_token = create_access_token(user_id)
        refresh_token = create_refresh_token(user_id)
        return access_token, refresh_token

    def verify_access_token(self, token: str) -> Optional[str]:
        return verify_token(token, "access")

    def verify_refresh_token(self, token: str) -> Optional[str]:
        return verify_token(token, "refresh")

    def refresh_tokens(self, refresh_token: str) -> Optional[Tuple[str, str]]:
        user_id = self.verify_refresh_token(refresh_token)
        if not user_id:
            return None
        return self.create_tokens(user_id)

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