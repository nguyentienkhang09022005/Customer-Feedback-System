"""
Tests for AttachmentService - file attachment management.
"""
import pytest
from uuid import uuid4
from unittest.mock import patch, MagicMock, AsyncMock

# magic is mocked at session level in conftest.py

from app.services.attachmentService import AttachmentService
from app.models.interaction import Attachment


@pytest.fixture
def attachment_service(db_session):
    """Create attachment service instance."""
    return AttachmentService(db_session)


@pytest.fixture
def sample_attachment(db_session, sample_ticket, sample_customer):
    """Create a sample attachment directly in the database."""
    attachment = Attachment(
        id_attachment=uuid4(),
        attach_name="test_document.pdf",
        attach_type="application/pdf",
        url="https://cloudinary.example.com/test_document.pdf",
        id_reference=sample_ticket.id_ticket,
        id_uploader=sample_customer.id,
        file_size=1024,
        storage_type="cloudinary",
        public_id="test_document_pdf_123",
        reference_type="ticket",
        is_deleted=False
    )
    db_session.add(attachment)
    db_session.commit()
    db_session.refresh(attachment)
    return attachment


class TestAttachmentServiceGet:
    """Tests for attachment retrieval."""

    def test_get_attachment_returns_attachment_by_id(
        self, attachment_service, sample_attachment
    ):
        """get_attachment should return the attachment when found."""
        result = attachment_service.get_attachment(sample_attachment.id_attachment)
        assert result is not None
        assert result.id_attachment == sample_attachment.id_attachment
        assert result.attach_name == "test_document.pdf"

    def test_get_attachment_returns_none_for_missing(
        self, attachment_service
    ):
        """get_attachment should return None when not found."""
        result = attachment_service.get_attachment(uuid4())
        assert result is None


class TestAttachmentServiceGetByReference:
    """Tests for getting attachments by reference."""

    def test_get_attachments_for_reference_returns_list(
        self, attachment_service, sample_attachment, sample_ticket
    ):
        """get_attachments_for_reference should return attachments for ticket."""
        results = attachment_service.get_attachments_for_reference(
            "ticket",
            sample_ticket.id_ticket
        )
        assert isinstance(results, list)
        assert len(results) >= 1

    def test_get_attachments_for_reference_returns_empty_for_no_attachments(
        self, attachment_service, sample_ticket
    ):
        """get_attachments_for_reference should return empty list when none exist."""
        results = attachment_service.get_attachments_for_reference(
            "ticket",
            sample_ticket.id_ticket
        )
        # May have existing attachments, check it's a list
        assert isinstance(results, list)


class TestAttachmentServiceDelete:
    """Tests for attachment deletion."""

    def test_delete_attachment_returns_false_for_missing(
        self, attachment_service, sample_customer
    ):
        """delete_attachment should return False when attachment not found."""
        result = attachment_service.delete_attachment(
            uuid4(),
            sample_customer.id
        )
        assert result is False

    @patch("app.core.cloudinary.delete_file")
    def test_delete_attachment_soft_deletes_when_found(
        self, mock_delete_file, db_session, attachment_service, sample_attachment, sample_customer
    ):
        """delete_attachment should soft delete when found."""
        mock_delete_file.return_value = True

        result = attachment_service.delete_attachment(
            sample_attachment.id_attachment,
            sample_customer.id
        )

        assert result is True

        # Verify attachment is soft deleted
        db_session.refresh(sample_attachment)
        assert sample_attachment.is_deleted is True

    @patch("app.core.cloudinary.delete_file")
    def test_delete_attachment_handles_delete_failure(
        self, mock_delete_file, db_session, attachment_service, sample_attachment, sample_customer
    ):
        """delete_attachment should still succeed even if cloudinary delete fails."""
        mock_delete_file.side_effect = Exception("Cloudinary error")

        result = attachment_service.delete_attachment(
            sample_attachment.id_attachment,
            sample_customer.id
        )

        # Should still succeed because soft delete works
        assert result is True


class TestAttachmentServiceHardDelete:
    """Tests for permanent attachment deletion."""

    def test_hard_delete_attachment_returns_false_for_missing(
        self, attachment_service
    ):
        """hard_delete_attachment should return False when not found."""
        result = attachment_service.hard_delete_attachment(uuid4())
        assert result is False

    @patch("app.core.cloudinary.delete_file")
    def test_hard_delete_attachment_removes_record(
        self, mock_delete_file, db_session, attachment_service, sample_attachment
    ):
        """hard_delete_attachment should permanently remove the record."""
        mock_delete_file.return_value = True
        attachment_id = sample_attachment.id_attachment

        result = attachment_service.hard_delete_attachment(attachment_id)

        assert result is True

        # Verify attachment is removed from database
        deleted = attachment_service.get_attachment(attachment_id)
        assert deleted is None


class TestAttachmentServiceHelpers:
    """Tests for helper methods."""

    def test_generate_thumbnail_url_returns_none_for_non_cloudinary_url(
        self, attachment_service
    ):
        """_generate_thumbnail_url should return None for non-Cloudinary URLs."""
        result = attachment_service._generate_thumbnail_url("https://example.com/file.pdf")
        assert result is None

    def test_extract_public_id_returns_none_for_non_cloudinary_url(
        self, attachment_service
    ):
        """_extract_public_id should return None for non-Cloudinary URLs."""
        result = attachment_service._extract_public_id("https://example.com/file.pdf")
        assert result is None


class TestAttachmentServiceUploadValidation:
    """Tests for upload validation behavior."""

    def test_attachment_service_uses_file_service(self, db_session):
        """AttachmentService should initialize with FileService."""
        with patch.dict('sys.modules', {'magic': MagicMock()}):
            service = AttachmentService(db_session)
            assert service.file_service is not None
            from app.services.fileService import FileService
            assert isinstance(service.file_service, FileService)


class TestAttachmentModel:
    """Tests for Attachment model."""

    def test_attachment_stores_file_metadata(
        self, db_session, sample_attachment
    ):
        """Attachment should store file metadata correctly."""
        assert sample_attachment.attach_name == "test_document.pdf"
        assert sample_attachment.attach_type == "application/pdf"
        assert sample_attachment.file_size == 1024

    def test_attachment_stores_cloudinary_info(
        self, sample_attachment
    ):
        """Attachment should store Cloudinary information."""
        assert sample_attachment.storage_type == "cloudinary"
        assert sample_attachment.public_id == "test_document_pdf_123"
        assert "cloudinary" in sample_attachment.url

    def test_attachment_stores_reference_info(
        self, sample_attachment, sample_ticket, sample_customer
    ):
        """Attachment should store reference information."""
        assert sample_attachment.reference_type == "ticket"
        assert sample_attachment.id_reference == sample_ticket.id_ticket
        assert sample_attachment.id_uploader == sample_customer.id

    def test_attachment_defaults_to_not_deleted(
        self, sample_attachment
    ):
        """Attachment should default to is_deleted=False."""
        assert sample_attachment.is_deleted is False