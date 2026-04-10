import cloudinary
import cloudinary.uploader
from app.core.config import settings
from io import BytesIO
import time
import hashlib


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


def upload_file(file_obj, folder: str = "attachments") -> str:
    """
    Upload file to Cloudinary.
    
    Args:
        file_obj: File object (can be file-like or bytes)
        folder: Cloudinary folder to upload to
    
    Returns:
        str: Secure URL of uploaded file
    """
    init_cloudinary()
    
    # If file_obj is bytes, wrap in BytesIO
    if isinstance(file_obj, bytes):
        file_obj = BytesIO(file_obj)
    
    result = cloudinary.uploader.upload(
        file_obj, 
        folder=folder,
        resource_type="auto"  # Auto-detect resource type
    )
    return result["secure_url"]


def upload_image_with_thumbnail(file_obj, folder: str = "attachments") -> dict:
    """
    Upload image and generate thumbnail.
    
    Args:
        file_obj: Image file object (bytes or file-like)
        folder: Cloudinary folder
    
    Returns:
        dict: Contains 'url' and 'thumbnail_url'
    """
    init_cloudinary()
    
    if isinstance(file_obj, bytes):
        file_obj = BytesIO(file_obj)
    
    # Upload original with transformations
    result = cloudinary.uploader.upload(
        file_obj,
        folder=folder,
        resource_type="image",
        transformation=[
            {"width": 1200, "height": 1200, "crop": "limit"}
        ]
    )
    
    original_url = result["secure_url"]
    
    # Generate thumbnail URL using Cloudinary transformation
    # Format: https://res.cloudinary.com/{cloud}/image/upload/w_300,h_300,c_thumb/{public_id}
    thumbnail_url = cloudinary.CloudinaryImage(result["public_id"]).build_url(
        width=300,
        height=300,
        crop="thumb",
        gravity="auto"
    )
    
    return {
        "url": original_url,
        "thumbnail_url": thumbnail_url,
        "public_id": result["public_id"]
    }


def delete_file(public_id: str) -> bool:
    """
    Delete file from Cloudinary.
    
    Args:
        public_id: Cloudinary public ID of the file
    
    Returns:
        bool: True if deleted successfully
    """
    init_cloudinary()
    result = cloudinary.uploader.destroy(public_id, resource_type="auto")
    return result.get("result") == "ok"


def generate_upload_signature(filename: str, folder: str = "chat_attachments") -> dict:
    """
    Generate Cloudinary upload signature for frontend direct upload.
    
    Args:
        filename: Original filename for the upload
        folder: Cloudinary folder to upload to (default: chat_attachments)
    
    Returns:
        dict: Contains signature, timestamp, api_key, cloud_name, folder, upload_url
    """
    init_cloudinary()
    
    parsed = _parse_cloudinary_url(settings.CLOUDINARY_URL)
    cloud_name = parsed.get("cloud_name", "")
    api_key = parsed.get("api_key", "")
    api_secret = parsed.get("api_secret", "")
    
    timestamp = int(time.time())
    
    # Create signature payload
    params_to_sign = {
        "timestamp": timestamp,
        "folder": folder,
    }
    
    # Generate SHA256 HMAC signature
    def generate_signature(params: dict, secret: str) -> str:
        sorted_params = sorted(params.items())
        param_string = "&".join([f"{k}={v}" for k, v in sorted_params])
        return hashlib.sha256(f"{param_string}{secret}".encode()).hexdigest()
    
    signature = generate_signature(params_to_sign, api_secret)
    
    return {
        "signature": signature,
        "timestamp": timestamp,
        "api_key": api_key,
        "cloud_name": cloud_name,
        "folder": folder,
        "upload_url": f"https://api.cloudinary.com/v1_1/{cloud_name}/auto/upload"
    }