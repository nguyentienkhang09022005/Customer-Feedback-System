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
    Gmail SMTP Email Service
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
    
    def _connect_smtp(self) -> smtplib.SMTP:
        """Establish SMTP connection with TLS"""
        try:
            smtp = smtplib.SMTP(self.host, self.port, timeout=30)
            smtp.ehlo()
            
            if self.use_tls:
                smtp.starttls(context=ssl.create_default_context())
                smtp.ehlo()
            
            smtp.login(self.user, self.password)
            logger.info(f"✅ SMTP connected to {self.host}:{self.port}")
            return smtp
            
        except smtplib.SMTPAuthenticationError:
            logger.error("❌ SMTP authentication failed - check credentials")
            raise
        except smtplib.SMTPConnectError:
            logger.error(f"❌ Failed to connect to SMTP server {self.host}:{self.port}")
            raise
        except Exception as e:
            logger.error(f"❌ SMTP connection error: {e}")
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
        if not self.user or not self.password:
            logger.error("❌ SMTP credentials not configured")
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


# Singleton instance
email_service = EmailService()
