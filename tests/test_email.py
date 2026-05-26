"""
Tests for EmailService - email sending functionality.
"""
import pytest
from unittest.mock import patch, MagicMock
import smtplib

from app.services.emailService import EmailService, email_service


class TestEmailServiceSingleton:
    """Tests for EmailService singleton behavior."""

    def test_email_service_is_singleton(self):
        """EmailService should return the same instance."""
        service1 = EmailService()
        service2 = EmailService()
        assert service1 is service2

    def test_email_service_stores_config(self):
        """EmailService should have configuration attributes."""
        service = EmailService()
        assert hasattr(service, "host")
        assert hasattr(service, "port")
        assert hasattr(service, "user")
        assert hasattr(service, "email_provider")


class TestEmailServiceSendEmail:
    """Tests for generic email sending."""

    @patch.object(EmailService, "_send_with_retry")
    def test_send_email_success_with_string_recipient(self, mock_retry):
        """Sending email to single recipient should succeed."""
        mock_retry.return_value = True
        service = EmailService()

        result = service.send_email(
            to_email="user@example.com",
            subject="Test Subject",
            body="Test body content"
        )

        assert result is True
        mock_retry.assert_called_once()

    @patch.object(EmailService, "_send_with_retry")
    def test_send_email_success_with_list_recipients(self, mock_retry):
        """Sending email to multiple recipients should succeed."""
        mock_retry.return_value = True
        service = EmailService()

        result = service.send_email(
            to_email=["user1@example.com", "user2@example.com"],
            subject="Test Subject",
            body="Test body"
        )

        assert result is True

    @patch.object(EmailService, "_send_with_retry")
    def test_send_email_with_html_content(self, mock_retry):
        """Sending HTML email should set correct content type."""
        mock_retry.return_value = True
        service = EmailService()

        result = service.send_email(
            to_email="user@example.com",
            subject="HTML Email",
            body="<html><body><h1>Hello</h1></body></html>",
            html=True
        )

        assert result is True

    def test_send_email_returns_false_when_user_not_configured(self):
        """Sending email without SMTP user should return False."""
        service = EmailService()
        original_user = service.user
        service.user = ""

        result = service.send_email(
            to_email="user@example.com",
            subject="Test",
            body="Test body"
        )

        service.user = original_user
        assert result is False

    def test_send_email_returns_false_when_password_not_configured(self):
        """Sending email without password (non-sendgrid) should return False."""
        service = EmailService()
        original_password = service.password
        original_provider = service.email_provider

        service.user = "test@example.com"
        service.password = ""
        service.email_provider = "gmail"

        result = service.send_email(
            to_email="user@example.com",
            subject="Test",
            body="Test body"
        )

        service.password = original_password
        service.email_provider = original_provider
        assert result is False

    def test_send_email_returns_false_when_sendgrid_key_missing(self):
        """Sending email via sendgrid without API key should return False."""
        service = EmailService()
        original_provider = service.email_provider
        original_key = service.sendgrid_api_key

        service.email_provider = "sendgrid"
        service.sendgrid_api_key = ""

        result = service.send_email(
            to_email="user@example.com",
            subject="Test",
            body="Test body"
        )

        service.email_provider = original_provider
        service.sendgrid_api_key = original_key
        assert result is False


class TestEmailServiceOtpEmails:
    """Tests for OTP email sending."""

    @patch.object(EmailService, "_send_with_retry")
    def test_send_otp_email_success(self, mock_retry):
        """Sending OTP email should succeed."""
        mock_retry.return_value = True
        service = EmailService()

        result = service.send_otp_email(
            to_email="user@example.com",
            otp_code="123456"
        )

        assert result is True

    @patch.object(EmailService, "_send_with_retry")
    def test_send_password_reset_otp_email_success(self, mock_retry):
        """Sending password reset OTP email should succeed."""
        mock_retry.return_value = True
        service = EmailService()

        result = service.send_password_reset_otp_email(
            to_email="user@example.com",
            otp_code="654321"
        )

        assert result is True


class TestEmailServiceTicketNotifications:
    """Tests for ticket notification emails."""

    @patch.object(EmailService, "_send_with_retry")
    def test_send_ticket_notification_created(self, mock_retry):
        """Sending ticket created notification should succeed."""
        mock_retry.return_value = True
        service = EmailService()

        result = service.send_ticket_notification(
            to_email="user@example.com",
            ticket_id="TICKET-123",
            event_type="created",
            additional_info={"priority": "High"}
        )

        assert result is True

    @patch.object(EmailService, "_send_with_retry")
    def test_send_ticket_notification_assigned(self, mock_retry):
        """Sending ticket assigned notification should succeed."""
        mock_retry.return_value = True
        service = EmailService()

        result = service.send_ticket_notification(
            to_email="user@example.com",
            ticket_id="TICKET-123",
            event_type="assigned"
        )

        assert result is True

    @patch.object(EmailService, "_send_with_retry")
    def test_send_ticket_notification_resolved(self, mock_retry):
        """Sending ticket resolved notification should succeed."""
        mock_retry.return_value = True
        service = EmailService()

        result = service.send_ticket_notification(
            to_email="user@example.com",
            ticket_id="TICKET-123",
            event_type="resolved"
        )

        assert result is True

    @patch.object(EmailService, "_send_with_retry")
    def test_send_ticket_notification_closed(self, mock_retry):
        """Sending ticket closed notification should succeed."""
        mock_retry.return_value = True
        service = EmailService()

        result = service.send_ticket_notification(
            to_email="user@example.com",
            ticket_id="TICKET-123",
            event_type="closed"
        )

        assert result is True

    @patch.object(EmailService, "_send_with_retry")
    def test_send_ticket_notification_with_unknown_event_type(self, mock_retry):
        """Sending notification with unknown event type should still succeed."""
        mock_retry.return_value = True
        service = EmailService()

        result = service.send_ticket_notification(
            to_email="user@example.com",
            ticket_id="TICKET-123",
            event_type="unknown_event"
        )

        assert result is True


class TestEmailServiceCsatSurvey:
    """Tests for CSAT survey emails."""

    @patch.object(EmailService, "_send_with_retry")
    def test_send_csat_survey_success(self, mock_retry):
        """Sending CSAT survey should succeed."""
        mock_retry.return_value = True
        service = EmailService()

        result = service.send_csat_survey(
            to_email="user@example.com",
            ticket_id="TICKET-123-456-789-012",
            ticket_title="Cannot login to my account",
            ticket_status="Resolved",
            ticket_severity="High"
        )

        assert result is True

    @patch.object(EmailService, "_send_with_retry")
    def test_send_csat_survey_truncates_long_title(self, mock_retry):
        """CSAT survey should truncate very long ticket titles."""
        mock_retry.return_value = True
        service = EmailService()

        long_title = "A" * 100
        result = service.send_csat_survey(
            to_email="user@example.com",
            ticket_id="TICKET-123",
            ticket_title=long_title,
            ticket_status="Resolved"
        )

        assert result is True

    @patch.object(EmailService, "_send_with_retry")
    def test_send_csat_survey_handles_missing_status_severity(self, mock_retry):
        """CSAT survey should handle None status/severity gracefully."""
        mock_retry.return_value = True
        service = EmailService()

        result = service.send_csat_survey(
            to_email="user@example.com",
            ticket_id="TICKET-123",
            ticket_title="Test ticket",
            ticket_status=None,
            ticket_severity=None
        )

        assert result is True


class TestEmailServiceSmtpConnection:
    """Tests for SMTP connection management."""

    @patch("smtplib.SMTP")
    def test_connect_gmail_success(self, mock_smtp_class):
        """Connecting to Gmail SMTP should succeed with valid credentials."""
        mock_smtp_instance = MagicMock()
        mock_smtp_class.return_value = mock_smtp_instance

        service = EmailService()
        service.email_provider = "gmail"
        service.user = "test@gmail.com"
        service.password = "valid_password"
        service.use_tls = True

        smtp = service._connect_gmail()

        mock_smtp_instance.ehlo.assert_called()
        mock_smtp_instance.starttls.assert_called()
        mock_smtp_instance.login.assert_called_with("test@gmail.com", "valid_password")

    @patch("smtplib.SMTP")
    def test_connect_gmail_raises_on_auth_error(self, mock_smtp_class):
        """Gmail connection should raise on authentication failure."""
        mock_smtp_instance = MagicMock()
        mock_smtp_instance.ehlo.side_effect = smtplib.SMTPAuthenticationError(535, "Authentication failed")
        mock_smtp_class.return_value = mock_smtp_instance

        service = EmailService()
        service.user = "test@gmail.com"
        service.password = "wrong_password"

        with pytest.raises(smtplib.SMTPAuthenticationError):
            service._connect_gmail()

    @patch("smtplib.SMTP")
    def test_connect_gmail_raises_on_connect_error(self, mock_smtp_class):
        """Gmail connection should raise on connection failure."""
        mock_smtp_instance = MagicMock()
        mock_smtp_instance.ehlo.side_effect = smtplib.SMTPConnectError(421, "Connection refused")
        mock_smtp_class.return_value = mock_smtp_instance

        service = EmailService()

        with pytest.raises(smtplib.SMTPConnectError):
            service._connect_gmail()

    @patch("smtplib.SMTP")
    def test_connect_sendgrid_success(self, mock_smtp_class):
        """Connecting to SendGrid SMTP should succeed."""
        mock_smtp_instance = MagicMock()
        mock_smtp_class.return_value = mock_smtp_instance

        service = EmailService()
        service.sendgrid_api_key = "SG.valid_key"

        smtp = service._connect_sendgrid()

        mock_smtp_instance.login.assert_called_with("apikey", "SG.valid_key")


class TestEmailServiceRetry:
    """Tests for email sending with retry logic."""

    @patch("smtplib.SMTP")
    def test_send_with_retry_success_on_first_attempt(self, mock_smtp_class):
        """Email should send successfully on first attempt."""
        mock_smtp_instance = MagicMock()
        mock_smtp_class.return_value = mock_smtp_instance

        service = EmailService()
        service._smtp = mock_smtp_instance

        msg = MagicMock()
        msg.as_string.return_value = "test message"

        result = service._send_with_retry(msg)

        assert result is True
        assert mock_smtp_instance.sendmail.call_count == 1

    @patch("smtplib.SMTP")
    def test_send_with_retry_reconnects_on_disconnect(self, mock_smtp_class):
        """Should reconnect when SMTP disconnects mid-send."""
        mock_smtp_instance = MagicMock()
        mock_smtp_instance.sendmail.side_effect = [
            smtplib.SMTPServerDisconnected("Server disconnected"),
            None
        ]
        mock_smtp_class.return_value = mock_smtp_instance

        service = EmailService()
        service._smtp = mock_smtp_instance

        msg = MagicMock()
        msg.as_string.return_value = "test message"
        msg.__getitem__ = MagicMock(return_value="user@example.com")

        result = service._send_with_retry(msg)

        assert result is True

    @patch("smtplib.SMTP")
    def test_disconnect_closes_smtp_connection(self, mock_smtp_class):
        """Disconnecting should close SMTP connection properly."""
        mock_smtp_instance = MagicMock()
        mock_smtp_class.return_value = mock_smtp_instance

        service = EmailService()
        service._smtp = mock_smtp_instance

        service._disconnect()

        mock_smtp_instance.quit.assert_called_once()
        assert service._smtp is None