import smtplib
import ssl
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List
from app.core.config import settings

logger = logging.getLogger(__name__)


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
        
        Args:
            to_email: Recipient email
            otp_code: 6-digit OTP code
        
        Returns:
            bool: True if sent successfully
        """
        subject = "🔐 Your OTP Verification Code"
        
        body_text = f"""
Your OTP Verification Code
==========================

Your verification code is: {otp_code}

This code will expire in 5 minutes.

If you did not request this code, please ignore this email.

Best regards,
{self.from_name}
        """
        
        body_html = f"""
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <h2>Your OTP Verification Code</h2>
    <div style="background-color: #f5f5f5; padding: 20px; border-radius: 8px; text-align: center;">
        <h1 style="color: #333; letter-spacing: 5px; margin: 0;">{otp_code}</h1>
    </div>
    <p style="color: #666; margin-top: 20px;">
        This code will expire in <strong>5 minutes</strong>.
    </p>
    <p style="color: #999; font-size: 12px;">
        If you did not request this code, please ignore this email.
    </p>
    <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
    <p style="color: #666; font-size: 14px;">
        Best regards,<br>
        <strong>{self.from_name}</strong>
    </p>
</body>
</html>
        """
        
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
        
        Args:
            to_email: Recipient email
            otp_code: 6-digit OTP code
        
        Returns:
            bool: True if sent successfully
        """
        subject = "🔑 Password Reset Request - OTP Code"
        
        body_text = f"""
Password Reset Request
=======================

Your password reset code is: {otp_code}

This code will expire in 5 minutes.

If you did not request this password reset, please ignore this email and your account remains secure.

Best regards,
{self.from_name}
        """
        
        body_html = f"""
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <h2>🔑 Password Reset Request</h2>
    <div style="background-color: #fff3cd; padding: 20px; border-radius: 8px; text-align: center; border: 1px solid #ffc107;">
        <h1 style="color: #333; letter-spacing: 5px; margin: 0;">{otp_code}</h1>
    </div>
    <p style="color: #666; margin-top: 20px;">
        This code will expire in <strong>5 minutes</strong>.
    </p>
    <p style="color: #666; margin-top: 20px;">
        If you did not request this password reset, please ignore this email and your account remains secure.
    </p>
    <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
    <p style="color: #666; font-size: 14px;">
        Best regards,<br>
        <strong>{self.from_name}</strong>
    </p>
</body>
</html>
        """
        
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
        
        Args:
            to_email: Recipient email
            ticket_id: Ticket ID
            event_type: Type of event (created, assigned, updated, resolved, closed)
            additional_info: Additional ticket info
        
        Returns:
            bool: True if sent successfully
        """
        event_subjects = {
            'created': f"🎫 Ticket #{ticket_id} Created",
            'assigned': f"📋 Ticket #{ticket_id} Assigned to You",
            'updated': f"🔄 Ticket #{ticket_id} Updated",
            'resolved': f"✅ Ticket #{ticket_id} Resolved",
            'closed': f"🔒 Ticket #{ticket_id} Closed"
        }
        
        subject = event_subjects.get(event_type, f"Ticket #{ticket_id} Notification")
        
        event_messages = {
            'created': "Your ticket has been created successfully. Our team will respond soon.",
            'assigned': "A new ticket has been assigned to you. Please review and take action.",
            'updated': "The ticket status or details have been updated.",
            'resolved': "The ticket has been resolved. Please review the resolution.",
            'closed': "The ticket has been closed."
        }
        
        body_text = f"""
Ticket Notification
===================

Ticket ID: {ticket_id}
Event: {event_type.replace('_', ' ').title()}

{event_messages.get(event_type, 'You have a ticket notification.')}

{"Additional Information:" + str(additional_info) if additional_info else ""}

Best regards,
{self.from_name}
        """
        
        body_html = f"""
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <h2>🎫 Ticket Notification</h2>
    <table style="width: 100%; border-collapse: collapse;">
        <tr>
            <td style="padding: 10px; border-bottom: 1px solid #eee;"><strong>Ticket ID</strong></td>
            <td style="padding: 10px; border-bottom: 1px solid #eee;">{ticket_id}</td>
        </tr>
        <tr>
            <td style="padding: 10px; border-bottom: 1px solid #eee;"><strong>Event</strong></td>
            <td style="padding: 10px; border-bottom: 1px solid #eee;">{event_type.replace('_', ' ').title()}</td>
        </tr>
    </table>
    <p style="margin-top: 20px; color: #333;">
        {event_messages.get(event_type, 'You have a ticket notification.')}
    </p>
    {"<pre style='background: #f5f5f5; padding: 10px;'>" + str(additional_info) + "</pre>" if additional_info else ""}
    <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
    <p style="color: #666; font-size: 14px;">
        Best regards,<br>
        <strong>{self.from_name}</strong>
    </p>
</body>
</html>
        """
        
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

        subject = f"📊 Khảo sát mức độ hài lòng"
        short_title = ticket_title[:60] + "..." if len(ticket_title) > 60 else ticket_title

        template_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "templates", "email", "csat_survey.html"
        )

        try:
            with open(template_path, "r", encoding="utf-8") as f:
                body_html = f.read()
            body_html = body_html.replace("{ticket_id}", ticket_id[:8])
            body_html = body_html.replace("{ticket_title}", short_title)
            body_html = body_html.replace("{ticket_status}", ticket_status or "N/A")
            body_html = body_html.replace("{ticket_severity}", ticket_severity or "N/A")
        except FileNotFoundError:
            body_html = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #0d1117; color: #c9d1d9;">
                <h2 style="color: #238636;">📊 Khảo sát mức độ hài lòng</h2>
                <p>Xin chào quý khách,</p>
                <p>Ticket <strong>#{ticket_id[:8]}</strong> - "{short_title}" đã được giải quyết.</p>
                <p>Trạng thái: {ticket_status} | Mức độ: {ticket_severity}</p>
                <p>Vui lòng reply email này với số đánh giá (1-5):</p>
                <ul>
                    <li>5 - Rất hài lòng</li>
                    <li>4 - Hài lòng</li>
                    <li>3 - Bình thường</li>
                    <li>2 - Không hài lòng</li>
                    <li>1 - Rất không hài lòng</li>
                </ul>
                <p>Best regards,<br>{self.from_name}</p>
            </body>
            </html>
            """

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
