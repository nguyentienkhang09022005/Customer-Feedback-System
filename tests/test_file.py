"""
Tests for FileService - file validation and handling.
"""
import pytest
import os
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi import UploadFile

# Patch magic import before importing fileService
with patch.dict('sys.modules', {'magic': MagicMock()}):
    from app.services.fileService import FileService, FileValidationError


class TestFileServiceExtensions:
    """Tests for file extension utilities."""

    def test_get_file_extension_returns_correct_extension(self):
        assert FileService.get_file_extension("document.pdf") == "pdf"
        assert FileService.get_file_extension("image.PNG") == "png"
        assert FileService.get_file_extension("file.docx") == "docx"
        assert FileService.get_file_extension("archive.ZIP") == "zip"

    def test_get_file_extension_returns_empty_for_no_extension(self):
        assert FileService.get_file_extension("filename") == ""

    def test_get_file_extension_returns_last_extension_for_multiple_dots(self):
        assert FileService.get_file_extension("file.backup.tar") == "tar"


class TestFileServiceMimeTypeChecks:
    """Tests for MIME type categorization."""

    def test_is_image_returns_true_for_allowed_image_types(self):
        assert FileService.is_image("image/jpeg") is True
        assert FileService.is_image("image/png") is True
        assert FileService.is_image("image/gif") is True
        assert FileService.is_image("image/webp") is True

    def test_is_image_returns_false_for_non_image_types(self):
        assert FileService.is_image("application/pdf") is False
        assert FileService.is_image("text/plain") is False

    def test_is_document_returns_true_for_allowed_document_types(self):
        assert FileService.is_document("application/pdf") is True
        assert FileService.is_document("application/msword") is True

    def test_is_document_returns_false_for_non_document_types(self):
        assert FileService.is_document("image/jpeg") is False
        assert FileService.is_document("text/plain") is False

    def test_is_archive_returns_true_for_allowed_archive_types(self):
        assert FileService.is_archive("application/zip") is True
        assert FileService.is_archive("application/x-rar-compressed") is True

    def test_is_archive_returns_false_for_non_archive_types(self):
        assert FileService.is_archive("application/pdf") is False


class TestFileServiceSanitizeFilename:
    """Tests for filename sanitization."""

    def test_sanitize_filename_preserves_extension(self):
        result = FileService.sanitize_filename("document.pdf")
        assert result.endswith(".pdf")

    def test_sanitize_filename_removes_path_components(self):
        result = FileService.sanitize_filename("/path/to/file.pdf")
        assert "/" not in result

    def test_sanitize_filename_replaces_special_characters(self):
        result = FileService.sanitize_filename("file@name#test.pdf")
        assert "@" not in result
        assert "#" not in result

    def test_sanitize_filename_replaces_spaces_with_underscores(self):
        result = FileService.sanitize_filename("my document file.pdf")
        assert " " not in result
        assert "_" in result

    def test_sanitize_filename_limits_length(self):
        long_name = "a" * 150 + ".pdf"
        result = FileService.sanitize_filename(long_name)
        assert len(result) <= 105  # 100 chars + .pdf

    def test_sanitize_filename_handles_multiple_special_chars(self):
        result = FileService.sanitize_filename("file@name#with$special%chars.pdf")
        assert "@" not in result
        assert "#" not in result
        assert "$" not in result
        assert "%" not in result


class TestFileServiceUniqueFilename:
    """Tests for unique filename generation."""

    def test_generate_unique_filename_preserves_extension(self):
        result = FileService.generate_unique_filename("document.pdf")
        assert result.endswith(".pdf")
        assert len(result.split(".")) == 2

    def test_generate_unique_filename_returns_different_ids(self):
        result1 = FileService.generate_unique_filename("doc.pdf")
        result2 = FileService.generate_unique_filename("doc.pdf")
        # Results should be different UUIDs (not the same filename)
        assert result1 != result2

    def test_generate_unique_filename_handles_no_extension(self):
        result = FileService.generate_unique_filename("noextension")
        # Should just return a UUID without extension
        assert len(result) == 36  # UUID format

    def test_generate_unique_filename_handles_uppercase_extension(self):
        result = FileService.generate_unique_filename("document.PDF")
        assert result.endswith(".pdf")  # Lowercased


class TestFileServiceMimeFromExtension:
    """Tests for MIME type lookup from extension."""

    def test_get_mime_from_extension_returns_correct_types(self):
        assert FileService._get_mime_from_extension("jpg") == "image/jpeg"
        assert FileService._get_mime_from_extension("jpeg") == "image/jpeg"
        assert FileService._get_mime_from_extension("png") == "image/png"
        assert FileService._get_mime_from_extension("gif") == "image/gif"
        assert FileService._get_mime_from_extension("webp") == "image/webp"
        assert FileService._get_mime_from_extension("pdf") == "application/pdf"
        assert FileService._get_mime_from_extension("doc") == "application/msword"
        assert FileService._get_mime_from_extension("docx") == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        assert FileService._get_mime_from_extension("xls") == "application/vnd.ms-excel"
        assert FileService._get_mime_from_extension("xlsx") == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        assert FileService._get_mime_from_extension("zip") == "application/zip"

    def test_get_mime_from_extension_case_insensitive(self):
        assert FileService._get_mime_from_extension("PDF") == "application/pdf"
        assert FileService._get_mime_from_extension("DOCX") == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    def test_get_mime_from_extension_returns_octet_stream_for_unknown(self):
        assert FileService._get_mime_from_extension("unknown") == "application/octet-stream"
        assert FileService._get_mime_from_extension("exe") == "application/octet-stream"


class TestFileServiceValidateFile:
    """Tests for file validation logic."""

    @pytest.mark.asyncio
    async def test_validate_file_rejects_empty_content_type(self):
        """File with no content type should fail validation."""
        mock_file = MagicMock(spec=UploadFile)
        mock_file.content_type = None
        mock_file.filename = "test.pdf"

        # This will use 'application/octet-stream' which will be checked
        with pytest.raises(FileValidationError):
            await FileService.validate_file(mock_file)

    @pytest.mark.asyncio
    async def test_validate_file_rejects_unknown_extension(self):
        """File with disallowed extension should fail validation."""
        mock_file = MagicMock(spec=UploadFile)
        mock_file.content_type = "application/octet-stream"
        mock_file.filename = "test.exe"

        with pytest.raises(FileValidationError):
            await FileService.validate_file(mock_file)

    @pytest.mark.asyncio
    async def test_validate_file_accepts_valid_content_type(self):
        """File with allowed MIME type should pass content type check."""
        mock_file = MagicMock(spec=UploadFile)
        mock_file.content_type = "application/pdf"
        mock_file.filename = "document.pdf"

        # The file.read() will be called, returning a small valid PDF-like content
        mock_file.read = AsyncMock(return_value=b"%PDF-1.4 test content here"[:1024])
        mock_file.seek = AsyncMock()

        result = await FileService.validate_file(mock_file)
        assert result["filename"] == "document.pdf"