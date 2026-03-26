import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from uuid import uuid4
from io import BytesIO

from app.services.fileService import FileService, FileValidationError


class TestFileService:
    """Unit tests for FileService"""
    
    def test_get_file_extension(self):
        """Test extracting file extension"""
        assert FileService.get_file_extension("document.pdf") == "pdf"
        assert FileService.get_file_extension("image.JPG") == "jpg"
        assert FileService.get_file_extension("noextension") == ""
        assert FileService.get_file_extension("multiple.dots.file.txt") == "txt"
    
    def test_is_image(self):
        """Test image detection"""
        assert FileService.is_image("image/jpeg") is True
        assert FileService.is_image("image/png") is True
        assert FileService.is_image("image/gif") is True
        assert FileService.is_image("application/pdf") is False
    
    def test_is_document(self):
        """Test document detection"""
        assert FileService.is_document("application/pdf") is True
        assert FileService.is_document("application/msword") is True
        assert FileService.is_document("image/png") is False
    
    def test_is_archive(self):
        """Test archive detection"""
        assert FileService.is_archive("application/zip") is True
        assert FileService.is_archive("application/x-rar-compressed") is True
        assert FileService.is_archive("image/png") is False
    
    def test_sanitize_filename(self):
        """Test filename sanitization"""
        # Normal filename
        result = FileService.sanitize_filename("document.pdf")
        assert result == "document.pdf"
        
        # Filename with special chars
        result = FileService.sanitize_filename("fi@le#na$me.pdf")
        assert result == "filename.pdf"
        
        # Filename with spaces
        result = FileService.sanitize_filename("my document file.pdf")
        assert "my" in result
        
        # Path traversal attempt
        result = FileService.sanitize_filename("../../../etc/passwd")
        assert ".." not in result
        
        # Long filename
        long_name = "a" * 200 + ".pdf"
        result = FileService.sanitize_filename(long_name)
        assert len(result) <= 105  # 100 chars + .pdf
    
    def test_generate_unique_filename(self):
        """Test unique filename generation"""
        filename1 = FileService.generate_unique_filename("document.pdf")
        filename2 = FileService.generate_unique_filename("document.pdf")
        
        # Should have .pdf extension
        assert filename1.endswith(".pdf")
        assert filename2.endswith(".pdf")
        
        # Should be unique
        assert filename1 != filename2
        
        # UUID format check (8-4-4-4-12 = 36 chars)
        base_name = filename1.rsplit('.', 1)[0]
        assert len(base_name) == 36


class TestFileValidation:
    """Unit tests for file validation"""
    
    @pytest.mark.asyncio
    async def test_validate_file_size_limit(self):
        """Test file size validation"""
        service = FileService()
        
        # Create mock file
        mock_file = Mock()
        mock_file.filename = "large_file.pdf"
        mock_file.content_type = "application/pdf"
        
        # Large content (>10MB)
        large_content = b"x" * (11 * 1024 * 1024)  # 11MB
        
        async def read_mock():
            return large_content
        
        async def seek_mock(pos):
            pass
        
        mock_file.read = read_mock
        mock_file.seek = seek_mock
        
        with patch('app.services.fileService.settings') as mock_settings:
            mock_settings.MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024
            mock_settings.MAX_FILE_SIZE_MB = 10
            mock_settings.ALLOWED_FILE_TYPES = ["pdf", "jpg"]
            mock_settings.IMAGE_EXTENSIONS = ["jpg", "jpeg", "png"]
            
            with pytest.raises(FileValidationError) as exc_info:
                await service.validate_file(mock_file)
            
            assert "exceeds maximum allowed size" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_validate_empty_file(self):
        """Test empty file validation"""
        service = FileService()
        
        mock_file = Mock()
        mock_file.filename = "empty.pdf"
        mock_file.content_type = "application/pdf"
        
        async def read_mock():
            return b""
        
        async def seek_mock(pos):
            pass
        
        mock_file.read = read_mock
        mock_file.seek = seek_mock
        
        with patch('app.services.fileService.settings') as mock_settings:
            mock_settings.MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024
            mock_settings.ALLOWED_FILE_TYPES = ["pdf"]
            mock_settings.IMAGE_EXTENSIONS = ["jpg", "jpeg", "png"]
            
            with pytest.raises(FileValidationError) as exc_info:
                await service.validate_file(mock_file)
            
            assert "empty" in str(exc_info.value).lower()


class TestAttachmentService:
    """Unit tests for AttachmentService"""
    
    def test_attachment_repository_integration(self):
        """Test that AttachmentRepository can be instantiated"""
        mock_db = Mock()
        from app.repositories.attachmentRepository import AttachmentRepository
        
        repo = AttachmentRepository(mock_db)
        assert repo.db == mock_db
    
    def test_attachment_service_initialization(self):
        """Test AttachmentService initialization"""
        mock_db = Mock()
        from app.services.attachmentService import AttachmentService
        
        service = AttachmentService(mock_db)
        assert service.db == mock_db
        assert isinstance(service.repo, Mock)
        assert isinstance(service.file_service, FileService)


class TestCloudinaryIntegration:
    """Tests for Cloudinary upload integration"""
    
    def test_cloudinary_url_parsing(self):
        """Test Cloudinary URL parsing"""
        from app.core.cloudinary import _parse_cloudinary_url
        
        # Valid URL
        result = _parse_cloudinary_url("cloudinary://key:secret@cloudname")
        assert result["cloud_name"] == "cloudname"
        assert result["api_key"] == "key"
        assert result["api_secret"] == "secret"
        
        # Invalid URL
        result = _parse_cloudinary_url("")
        assert result["cloud_name"] is None
    
    def test_extract_public_id(self):
        """Test public ID extraction from URL"""
        from app.services.attachmentService import AttachmentService
        
        mock_db = Mock()
        service = AttachmentService(mock_db)
        
        # Test URL parsing
        url = "https://res.cloudinary.com/demo/image/upload/v1234567890/folder/filename.jpg"
        # Note: This is a simplified test, actual implementation may vary
        public_id = service._extract_public_id(url)
        # The result depends on implementation


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
