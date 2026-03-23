import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    
    JWT_SECRET: str = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 100
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    CLOUDINARY_URL: str = os.getenv("CLOUDINARY_LINK", "")

settings = Settings()