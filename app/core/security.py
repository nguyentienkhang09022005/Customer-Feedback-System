import bcrypt
import jwt
import uuid
from datetime import datetime, timedelta
from typing import Optional, Any, Dict
from app.core.config import settings


def get_password_hash(password: str) -> str:
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    password_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def create_access_token(user: Any, expires_delta: Optional[timedelta] = None) -> tuple[str, str]:
    """
    Create access token with unique JTI (JWT ID).
    
    Returns:
        tuple: (token, jti)
    """
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    jti = str(uuid.uuid4())  # Unique token ID for blacklist tracking

    role = getattr(user, 'role_name', 'Customer') if user.type == 'employee' else 'Customer'

    to_encode = {
        "sub": str(user.id),
        "jti": jti,
        "email": user.email,
        "user_type": user.type,  # 'employee' hoặc 'customer'
        "role": role,
        "exp": expire,
        "type": "access"
    }
    token = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token, jti


def create_refresh_token(user: Any) -> tuple[str, str]:
    """
    Create refresh token with unique JTI (JWT ID).
    
    Returns:
        tuple: (token, jti)
    """
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    jti = str(uuid.uuid4())  # Unique token ID for blacklist tracking
    role = getattr(user, 'role_name', 'Customer') if user.type == 'employee' else 'Customer'

    to_encode = {
        "sub": str(user.id),
        "jti": jti,
        "email": user.email,
        "user_type": user.type,
        "role": role,
        "exp": expire,
        "type": "refresh"
    }
    token = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token, jti


def verify_token(token: str, expected_type: str = "access") -> Optional[Dict[str, Any]]:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("type") != expected_type:
            return None
        return payload
    except Exception:
        return None


def decode_token_unsafe(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode token without verification (for extracting JTI/exp).
    Used when checking blacklist before full verification.
    """
    try:
        # Decode without verification to get JTI and exp
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM], options={"verify_signature": False})
        return payload
    except Exception:
        return None