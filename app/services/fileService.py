import os
import re
import uuid
import magic
from fastapi import UploadFile, HTTPException
from app.core.config import settings


class FileValidationError(Exception):
    """Custom exception for file validation errors"""
    pass


class FileService:
    """
    File validation and handling service.
    Validates file type, size, and sanitizes filenames.
    """
    
    # Allowed MIME types by category
    ALLOWED_MIME_TYPES = {
        'image': ['image/jpeg', 'image/png', 'image/gif', 'image/webp'],
        'document': [
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        ],
        'archive': ['application/zip', 'application/x-rar-compressed']
    }
    
    # All allowed MIME types
    ALL_ALLOWED_TYPES = (
        ALLOWED_MIME_TYPES['image'] + 
        ALLOWED_MIME_TYPES['document'] + 
        ALLOWED_MIME_TYPES['archive']
    )
    
    @staticmethod
    def get_file_extension(filename: str) -> str:
        """Extract file extension from filename"""
        if '.' in filename:
            return filename.rsplit('.', 1)[1].lower()
        return ''
    
    @staticmethod
    def is_image(mime_type: str) -> bool:
        """Check if file is an image based on MIME type"""
        return mime_type in FileService.ALLOWED_MIME_TYPES['image']
    
    @staticmethod
    def is_document(mime_type: str) -> bool:
        """Check if file is a document"""
        return mime_type in FileService.ALLOWED_MIME_TYPES['document']
    
    @staticmethod
    def is_archive(mime_type: str) -> bool:
        """Check if file is an archive"""
        return mime_type in FileService.ALLOWED_MIME_TYPES['archive']
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename by removing dangerous characters.
        Preserves extension but removes special chars.
        """
        # Remove path components
        filename = os.path.basename(filename)
        
        # Remove special characters but keep extension
        name, ext = os.path.splitext(filename)
        
        # Replace spaces and special chars with underscore
        name = re.sub(r'[^\w\s-]', '', name)
        name = re.sub(r'[-\s]+', '_', name)
        
        # Limit length
        name = name[:100]
        
        return f"{name}{ext}"
    
    @staticmethod
    def generate_unique_filename(original_filename: str) -> str:
        """
        Generate unique filename with UUID to prevent collisions.
        Preserves original extension.
        """
        ext = FileService.get_file_extension(original_filename)
        unique_id = str(uuid.uuid4())
        
        if ext:
            return f"{unique_id}.{ext}"
        return unique_id
    
    @staticmethod
    async def validate_file(file: UploadFile) -> dict:
        """
        Validate file type and size.
        Returns dict with file info if valid.
        Raises FileValidationError if invalid.
        """
        # Get file content type (MIME type)
        content_type = file.content_type or 'application/octet-stream'
        
        # Check file extension
        ext = FileService.get_file_extension(file.filename or 'unknown')
        
        if ext not in settings.ALLOWED_FILE_TYPES:
            raise FileValidationError(
                f"File type .{ext} is not allowed. "
                f"Allowed types: {', '.join(settings.ALLOWED_FILE_TYPES)}"
            )
        
        # Check MIME type matches extension (basic security)
        if content_type == 'application/octet-stream':
            # Try to detect from extension
            mime_from_ext = FileService._get_mime_from_extension(ext)
            if mime_from_ext not in FileService.ALL_ALLOWED_TYPES:
                raise FileValidationError(
                    f"File type .{ext} is not allowed"
                )
        
        # Read file to check size and get actual content
        content = await file.read()
        file_size = len(content)
        
        # Check size
        if file_size > settings.MAX_FILE_SIZE_BYTES:
            raise FileValidationError(
                f"File size ({file_size / 1024 / 1024:.2f}MB) exceeds "
                f"maximum allowed size ({settings.MAX_FILE_SIZE_MB}MB)"
            )
        
        if file_size == 0:
            raise FileValidationError("File is empty")
        
        # Reset file position for subsequent reads
        await file.seek(0)
        
        # Detect actual MIME type from content (magic bytes)
        try:
            mime_detected = magic.from_buffer(content[:1024], mime=True)
            if mime_detected not in FileService.ALL_ALLOWED_TYPES:
                raise FileValidationError(
                    f"File content type ({mime_detected}) is not allowed"
                )
        except Exception:
            # If magic detection fails, rely on content type header
            if content_type not in FileService.ALL_ALLOWED_TYPES:
                raise FileValidationError(
                    f"File type ({content_type}) is not allowed"
                )
        
        return {
            'filename': file.filename,
            'content_type': content_type,
            'extension': ext,
            'size': file_size,
            'is_image': FileService.is_image(content_type)
        }
    
    @staticmethod
    def _get_mime_from_extension(ext: str) -> str:
        """Get MIME type from file extension"""
        mime_map = {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'webp': 'image/webp',
            'pdf': 'application/pdf',
            'doc': 'application/msword',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'xls': 'application/vnd.ms-excel',
            'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'zip': 'application/zip',
        }
        return mime_map.get(ext.lower(), 'application/octet-stream')
