import os


def get_cors_allowed_origins():
    """Get allowed origins, defaulting to common frontend ports for development."""
    env_origins = os.getenv("CORS_ALLOWED_ORIGINS", "")
    if env_origins:
        return [o.strip() for o in env_origins.split(",") if o.strip()]
    # Development defaults
    return ["http://localhost:3000", "http://127.0.0.1:3000"]


CORS_ALLOWED_ORIGINS = get_cors_allowed_origins()

CHAT_NAMESPACE = "/chat"

JWT_ALGORITHM = "HS256"