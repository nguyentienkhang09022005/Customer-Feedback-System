import os
from typing import Optional, List
from dotenv import load_dotenv

load_dotenv()

class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    
    JWT_SECRET: str = os.getenv("JWT_SECRET", "")
    # Validate JWT_SECRET in production - fail fast if not configured
    if not JWT_SECRET and os.getenv("ENVIRONMENT", "development") == "production":
        raise ValueError("JWT_SECRET environment variable must be set in production")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    
    CLOUDINARY_URL: str = os.getenv("CLOUDINARY_LINK", "")
    
    # Email Provider Configuration
    # Set to "sendgrid" to use SendGrid SMTP; anything else uses Gmail
    EMAIL_PROVIDER: str = os.getenv("EMAIL_PROVIDER", "gmail").lower()

    # Gmail SMTP Configuration
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM_NAME: str = os.getenv("SMTP_FROM_NAME", "Customer Feedback System")
    SMTP_USE_TLS: bool = os.getenv("SMTP_USE_TLS", "true").lower() == "true"

    # SendGrid-specific (only used when EMAIL_PROVIDER="sendgrid")
    SENDGRID_API_KEY: str = os.getenv("SEND_GRID_API_KEY", "")
    
    # Redis Configuration
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD", None)
    REDIS_ENABLED: bool = os.getenv("REDIS_ENABLED", "true").lower() == "true"

    # Groq API Configuration (supports multiple keys for fallback)
    GROQ_API_KEYS: List[str] = [k for k in [
        os.getenv("GROQ_API_KEY_1"),
        os.getenv("GROQ_API_KEY_2"),
        os.getenv("GROQ_API_KEY_3"),
    ] if k]
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    
    # File Upload Configuration
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
    MAX_FILE_SIZE_BYTES: int = MAX_FILE_SIZE_MB * 1024 * 1024
    ALLOWED_FILE_TYPES: List[str] = os.getenv("ALLOWED_FILE_TYPES", "jpg,jpeg,png,gif,pdf,doc,docx,xls,xlsx,zip").split(",")
    IMAGE_EXTENSIONS: List[str] = ["jpg", "jpeg", "png", "gif", "webp"]
    THUMBNAIL_SIZE: tuple = (300, 300)
    ATTACHMENT_CLEANUP_DAYS: int = int(os.getenv("ATTACHMENT_CLEANUP_DAYS", "30"))

settings = Settings()