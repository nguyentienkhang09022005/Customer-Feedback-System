import cloudinary
import cloudinary.uploader
from app.core.config import settings


def _parse_cloudinary_url(url: str) -> dict:
    if not url or "@" not in url:
        return {"cloud_name": None, "api_key": None, "api_secret": None}
    
    url = url.replace("CLOUDINARY_URL=", "")
    
    parts = url.split("@")
    if len(parts) != 2:
        return {"cloud_name": None, "api_key": None, "api_secret": None}
    
    credentials, cloud_name = parts
    credentials = credentials.replace("cloudinary://", "")
    
    cred_parts = credentials.split(":")
    if len(cred_parts) != 2:
        return {"cloud_name": None, "api_key": None, "api_secret": None}
    
    api_key, api_secret = cred_parts
    
    return {
        "cloud_name": cloud_name,
        "api_key": api_key,
        "api_secret": api_secret
    }


def init_cloudinary():
    parsed = _parse_cloudinary_url(settings.CLOUDINARY_URL)
    if parsed["cloud_name"]:
        cloudinary.config(
            cloud_name=parsed["cloud_name"],
            api_key=parsed["api_key"],
            api_secret=parsed["api_secret"]
        )


def upload_file(file_obj, folder: str = "avatars") -> str:
    init_cloudinary()
    result = cloudinary.uploader.upload(file_obj, folder=folder)
    return result["secure_url"]


def delete_file(public_id: str) -> bool:
    init_cloudinary()
    result = cloudinary.uploader.destroy(public_id)
    return result.get("result") == "ok"