# Gmail SMTP Implementation Plan

## 1. Update `app/core/config.py`

**Task**: Add SMTP configuration settings
```python
SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER: str = os.getenv("SMTP_USER", "")
SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM_NAME: str = os.getenv("SMTP_FROM_NAME", "Customer Feedback System")
```

## 2. Create `app/services/emailService.py`

**Task**: Implement EmailService class with:
- Singleton pattern for connection reuse
- `_connect_smtp()` - establish SMTP connection with STARTTLS
- `_disconnect()` - close SMTP session
- `send_email(to, subject, body, html=False)` - generic send
- `send_otp_email(to_email, otp_code)` - OTP template
- `send_ticket_email(to_email, ticket_id, event_type)` - ticket notifications
- Error handling with retry (3 attempts)
- Connection timeout: 30 seconds

## 3. Update `app/services/otpService.py`

**Task**: Replace `_send_otp_email()` method
```python
# OLD (line 11-15):
def _send_otp_email(email: str, otp: str):
    print(f"📧 ĐANG GỬI EMAIL ĐẾN: {email}...")

# NEW:
def _send_otp_email(email: str, otp: str):
    from app.services.emailService import email_service
    email_service.send_otp_email(email, otp)
```

## 4. (Optional) Update `app/services/ticketService.py`

**Task**: Add email notifications for ticket events:
- `create_ticket()` → notify customer
- `assign_ticket()` → notify employee

## 5. Update `.env` or `.env.example`

**Add**:
```
# Gmail SMTP Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-16-char-app-password
SMTP_FROM_NAME=Customer Feedback System
```

## Implementation Order

1. `app/core/config.py` - Add SMTP settings
2. `app/services/emailService.py` - Create service
3. `app/services/otpService.py` - Update to use EmailService
4. `app/services/ticketService.py` - Add notifications (optional)
5. Update `.env` with credentials
6. Test send email

## Dependencies

None - using Python's built-in `smtplib` and `ssl` libraries.

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Gmail blocks less secure apps | Use App Password (16 chars) |
| SMTP connection timeout | Retry 3x with exponential backoff |
| Email goes to spam | Use proper From headers and SPF |
| Wrong credentials | Validate on startup |
