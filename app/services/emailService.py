import smtplib
import ssl
import logging
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List
from app.core.config import settings

logger = logging.getLogger(__name__)


# Template paths
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "..", "templates", "email")

def _load_template(template_name: str) -> Optional[str]:
    """Load email template from file."""
    template_path = os.path.join(TEMPLATE_DIR, template_name)
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        logger.warning(f"Template not found: {template_name}")
        return None


# Import template content
TEMPLATE_OTP_VERIFICATION_HTML = _load_template("otp_verification.html")
TEMPLATE_OTP_VERIFICATION_TXT = _load_template("otp_verification.txt")
TEMPLATE_PASSWORD_RESET_HTML = _load_template("password_reset.html")
TEMPLATE_PASSWORD_RESET_TXT = _load_template("password_reset.txt")
TEMPLATE_TICKET_NOTIFICATION_HTML = _load_template("ticket_notification.html")
TEMPLATE_TICKET_NOTIFICATION_TXT = _load_template("ticket_notification.txt")
TEMPLATE_CSAT_SURVEY_HTML = _load_template("csat_survey.html")


class EmailService:
    """
    Email Service supporting Gmail SMTP and SendGrid SMTP
    Uses STARTTLS on port 587 (recommended) or SSL on port 465
    """

    _instance: Optional['EmailService'] = None
    _smtp: Optional[smtplib.SMTP] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.host = settings.SMTP_HOST
        self.port = settings.SMTP_PORT
        self.user = settings.SMTP_USER
        self.password = settings.SMTP_PASSWORD
        self.from_name = settings.SMTP_FROM_NAME
        self.use_tls = settings.SMTP_USE_TLS
        self.email_provider = settings.EMAIL_PROVIDER
        self.sendgrid_api_key = settings.SENDGRID_API_KEY

    def _connect_smtp(self) -> smtplib.SMTP:
        """Establish SMTP connection based on email provider"""
        if self.email_provider == "sendgrid":
            return self._connect_sendgrid()
        else:
            return self._connect_gmail()

    def _connect_gmail(self) -> smtplib.SMTP:
        """Connect to Gmail SMTP"""
        try:
            smtp = smtplib.SMTP(self.host, self.port, timeout=30)
            smtp.ehlo()

            if self.use_tls:
                smtp.starttls(context=ssl.create_default_context())
                smtp.ehlo()

            smtp.login(self.user, self.password)
            logger.info(f"✅ Gmail SMTP connected to {self.host}:{self.port}")
            return smtp

        except smtplib.SMTPAuthenticationError:
            logger.error("❌ Gmail SMTP authentication failed - check credentials")
            raise
        except smtplib.SMTPConnectError:
            logger.error(f"❌ Failed to connect to Gmail SMTP {self.host}:{self.port}")
            raise
        except Exception as e:
            logger.error(f"❌ Gmail SMTP connection error: {e}")
            raise

    def _connect_sendgrid(self) -> smtplib.SMTP:
        """Connect to SendGrid SMTP"""
        try:
            smtp = smtplib.SMTP("smtp.sendgrid.net", 587, timeout=30)
            smtp.ehlo()
            smtp.starttls(context=ssl.create_default_context())
            smtp.ehlo()
            # SendGrid username is always "apikey"; password is the SG.* API key
            smtp.login("apikey", self.sendgrid_api_key)
            logger.info("✅ SendGrid SMTP connected")
            return smtp

        except smtplib.SMTPAuthenticationError:
            logger.error("❌ SendGrid authentication failed - check SENDGRID_API_KEY")
            raise
        except smtplib.SMTPConnectError:
            logger.error("❌ Failed to connect to SendGrid SMTP")
            raise
        except Exception as e:
            logger.error(f"❌ SendGrid SMTP connection error: {e}")
            raise
    
    def _disconnect(self):
        """Close SMTP connection"""
        if self._smtp:
            try:
                self._smtp.quit()
            except:
                pass
            self._smtp = None
    
    def _get_smtp(self) -> smtplib.SMTP:
        """Get or create SMTP connection"""
        if self._smtp is None:
            self._smtp = self._connect_smtp()
        return self._smtp
    
    def _send_with_retry(self, msg: MIMEMultipart, max_retries: int = 3) -> bool:
        """Send email with retry logic"""
        for attempt in range(max_retries):
            try:
                smtp = self._get_smtp()
                smtp.sendmail(self.user, msg['To'], msg.as_string())
                logger.info(f"✅ Email sent to {msg['To']}")
                return True
                
            except smtplib.SMTPServerDisconnected:
                logger.warning(f"⚠️ SMTP disconnected, reconnecting (attempt {attempt + 1}/{max_retries})")
                self._disconnect()
                self._smtp = self._connect_smtp()
                
            except smtplib.SMTPException as e:
                logger.error(f"❌ SMTP error: {e}")
                if attempt == max_retries - 1:
                    raise
                
        return False
    
    def send_email(
        self,
        to_email: str | List[str],
        subject: str,
        body: str,
        html: bool = False
    ) -> bool:
        """
        Send generic email
        
        Args:
            to_email: Recipient email(s)
            subject: Email subject
            body: Email body (plain text or HTML)
            html: If True, body is HTML
        
        Returns:
            bool: True if sent successfully
        """
        if not self.user:
            logger.error("❌ SMTP user (from email) not configured")
            return False

        if self.email_provider == "sendgrid" and not self.sendgrid_api_key:
            logger.error("❌ SENDGRID_API_KEY not configured")
            return False
        elif self.email_provider != "sendgrid" and not self.password:
            logger.error("❌ SMTP password not configured")
            return False

        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{self.from_name} <{self.user}>"
        
        if isinstance(to_email, str):
            msg['To'] = to_email
        else:
            msg['To'] = ', '.join(to_email)
        
        content_type = 'html' if html else 'plain'
        msg.attach(MIMEText(body, content_type, 'utf-8'))
        
        return self._send_with_retry(msg)
    
    def send_otp_email(self, to_email: str, otp_code: str) -> bool:
        """
        Send OTP verification email
        Template: app/templates/email/otp_verification.html, otp_verification.txt

        Args:
            to_email: Recipient email
            otp_code: 6-digit OTP code

        Returns:
            bool: True if sent successfully
        """
        subject = "Xac minh OTP - Ma xac minh dang nhap"

        # Use template if available, fallback to inline
        if TEMPLATE_OTP_VERIFICATION_HTML:
            body_html = TEMPLATE_OTP_VERIFICATION_HTML.replace("{otp_code}", otp_code)
        else:
            body_html = f"<html><body><h2>Xac minh OTP</h2><p>Ma cua ban: <strong>{otp_code}</strong></p></body></html>"

        if TEMPLATE_OTP_VERIFICATION_TXT:
            body_text = TEMPLATE_OTP_VERIFICATION_TXT.replace("{otp_code}", otp_code)
        else:
            body_text = f"Ma xac minh: {otp_code}"

        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{self.from_name} <{self.user}>"
        msg['To'] = to_email
        
        msg.attach(MIMEText(body_text, 'plain', 'utf-8'))
        msg.attach(MIMEText(body_html, 'html', 'utf-8'))
        
        return self._send_with_retry(msg)
    
    def send_password_reset_otp_email(self, to_email: str, otp_code: str) -> bool:
        """
        Send password reset OTP email
        Template: app/templates/email/password_reset.html, password_reset.txt

        Args:
            to_email: Recipient email
            otp_code: 6-digit OTP code

        Returns:
            bool: True if sent successfully
        """
        subject = "Dat lai mat khau - Ma xac minh"

        # Use template if available, fallback to inline
        if TEMPLATE_PASSWORD_RESET_HTML:
            body_html = TEMPLATE_PASSWORD_RESET_HTML.replace("{otp_code}", otp_code)
        else:
            body_html = f"<html><body><h2>Dat lai mat khau</h2><p>Ma cua ban: <strong>{otp_code}</strong></p></body></html>"

        if TEMPLATE_PASSWORD_RESET_TXT:
            body_text = TEMPLATE_PASSWORD_RESET_TXT.replace("{otp_code}", otp_code)
        else:
            body_text = f"Ma dat lai mat khau: {otp_code}"
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{self.from_name} <{self.user}>"
        msg['To'] = to_email
        
        msg.attach(MIMEText(body_text, 'plain', 'utf-8'))
        msg.attach(MIMEText(body_html, 'html', 'utf-8'))
        
        return self._send_with_retry(msg)
    
    def send_ticket_notification(
        self,
        to_email: str,
        ticket_id: str,
        event_type: str,
        additional_info: dict = None
    ) -> bool:
        """
        Send ticket notification email
        Template: app/templates/email/ticket_notification.html, ticket_notification.txt

        Args:
            to_email: Recipient email
            ticket_id: Ticket ID
            event_type: Type of event (created, assigned, updated, resolved, closed)
            additional_info: Additional ticket info

        Returns:
            bool: True if sent successfully
        """
        event_subjects = {
            'created': f"Ticket #{ticket_id} - Da tao moi",
            'assigned': f"Ticket #{ticket_id} - Da duoc phan cong",
            'updated': f"Ticket #{ticket_id} - Da duoc cap nhat",
            'resolved': f"Ticket #{ticket_id} - Da duoc giai quyet",
            'closed': f"Ticket #{ticket_id} - Da dong"
        }

        event_icons = {
            'created': "🎫",
            'assigned': "📋",
            'updated': "🔄",
            'resolved': "✅",
            'closed': "🔒"
        }

        event_messages = {
            'created': "Ticket cua ban da duoc tao thanh cong. Bo phan ho tro se phan hoi som.",
            'assigned': "Mot ticket moi da duoc phan cong cho ban. Vui long kiem tra va hanh dong.",
            'updated': "Trang thai hoac chi tiet ticket da duoc cap nhat.",
            'resolved': "Ticket da duoc giai quyet. Vui long kiem tra ket qua.",
            'closed': "Ticket da duoc dong."
        }

        subject = event_subjects.get(event_type, f"Ticket #{ticket_id} - Thong bao")
        event_icon = event_icons.get(event_type, "📌")
        event_message = event_messages.get(event_type, "Ban co thong bao ticket.")
        event_type_display = event_type.replace('_', ' ').title()

        # Build additional info block
        additional_info_block = ""
        additional_info_text = ""
        if additional_info:
            additional_info_block = f"<pre style='background: #21262d; padding: 12px; border-radius: 6px; font-size: 13px; color: #c9d1d9;'>{additional_info}</pre>"
            additional_info_text = f"Thong tin them: {additional_info}"

        # Use template if available
        if TEMPLATE_TICKET_NOTIFICATION_HTML:
            body_html = TEMPLATE_TICKET_NOTIFICATION_HTML
            body_html = body_html.replace("{ticket_id}", ticket_id)
            body_html = body_html.replace("{event_icon}", event_icon)
            body_html = body_html.replace("{event_type}", event_type_display)
            body_html = body_html.replace("{ticket_status}", event_type.replace('_', ' ').title())
            body_html = body_html.replace("{event_message}", event_message)
            body_html = body_html.replace("{additional_info_block}", additional_info_block)
        else:
            body_html = f"<html><body><h2>{event_icon} Thong bao Ticket</h2><p>Ticket #{ticket_id}<br>Su kien: {event_type_display}</p><p>{event_message}</p></body></html>"

        if TEMPLATE_TICKET_NOTIFICATION_TXT:
            body_text = TEMPLATE_TICKET_NOTIFICATION_TXT
            body_text = body_text.replace("{ticket_id}", ticket_id)
            body_text = body_text.replace("{event_type}", event_type_display)
            body_text = body_text.replace("{ticket_status}", event_type_display)
            body_text = body_text.replace("{event_message}", event_message)
            body_text = body_text.replace("{additional_info}", additional_info_text)
        else:
            body_text = f"Thong bao Ticket\nTicket #{ticket_id}\n{event_message}"
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{self.from_name} <{self.user}>"
        msg['To'] = to_email
        
        msg.attach(MIMEText(body_text, 'plain', 'utf-8'))
        msg.attach(MIMEText(body_html, 'html', 'utf-8'))
        
        return self._send_with_retry(msg)

    def send_csat_survey(
        self,
        to_email: str,
        ticket_id: str,
        ticket_title: str,
        ticket_status: str = None,
        ticket_severity: str = None
    ) -> bool:
        """
        Send CSAT survey email after ticket is resolved

        Args:
            to_email: Recipient email
            ticket_id: Ticket ID
            ticket_title: Title of the ticket
            ticket_status: Current status of the ticket
            ticket_severity: Severity level of the ticket

        Returns:
            bool: True if sent successfully
        """
        import os

        subject = "Khao sat muc do hai long"
        short_title = ticket_title[:60] + "..." if len(ticket_title) > 60 else ticket_title

        # Use pre-loaded template
        if TEMPLATE_CSAT_SURVEY_HTML:
            body_html = TEMPLATE_CSAT_SURVEY_HTML
            body_html = body_html.replace("{ticket_id}", ticket_id[:8])
            body_html = body_html.replace("{ticket_title}", short_title)
            body_html = body_html.replace("{ticket_status}", ticket_status or "N/A")
            body_html = body_html.replace("{ticket_severity}", ticket_severity or "N/A")
        else:
            body_html = f"<html><body><h2>Khao sat</h2><p>Ticket #{ticket_id[:8]} - {short_title}</p></body></html>"

        body_text = f"""
Khảo sát mức độ hài lòng - Ticket #{ticket_id[:8]}
================================================

Xin chào quý khách,

Ticket "{short_title}" đã được giải quyết.
Trạng thái: {ticket_status} | Mức độ: {ticket_severity}

Chúng tôi rất mong nhận được phản hồi từ bạn!

Vui lòng reply email này với số đánh giá (1-5):
- 5: Rất hài lòng
- 4: Hài lòng
- 3: Bình thường
- 2: Không hài lòng
- 1: Rất không hài lòng

Cảm ơn bạn!

Best regards,
{self.from_name}
        """

        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{self.from_name} <{self.user}>"
        msg['To'] = to_email

        msg.attach(MIMEText(body_text, 'plain', 'utf-8'))
        msg.attach(MIMEText(body_html, 'html', 'utf-8'))

        return self._send_with_retry(msg)


# Singleton instance
email_service = EmailService()
