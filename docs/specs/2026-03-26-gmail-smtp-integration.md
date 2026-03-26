# Gmail SMTP Email Integration Spec

## Status
- [x] Architecture approved
- [ ] Implementation pending
- [ ] Testing pending

---

## 1. Overview

**Change**: Switch from Gmail API to Gmail SMTP for email sending
**Reason**: Simpler setup, no OAuth flow required
**Scope**: Replace all email sending with SMTP-based service

---

## 2. Environment Variables

| Variable | Value | Description |
|----------|-------|-------------|
| `SMTP_HOST` | `smtp.gmail.com` | Gmail SMTP server |
| `SMTP_PORT` | `587` | STARTTLS port (recommended) |
| `SMTP_USER` | `your-email@gmail.com` | Sender email |
| `SMTP_PASSWORD` | `app-password` | Gmail App Password (16 chars) |

### ⚠️ Note: Gmail requires App Password, not your login password
- Enable 2FA on Google Account
- Generate App Password at: myaccount.google.com → Security → App passwords

---

## 3. New Files

### `app/services/emailService.py`
```python
class EmailService:
    - connect_smtp()      # Create SMTP session with SSL/TLS
    - disconnect()        # Close SMTP session
    - send_email()        # Generic send method
    - send_otp()          # Send OTP email
    - send_ticket_notification()  # Ticket events
```

### Features:
- Singleton pattern for connection reuse
- STARTTLS on port 587 (recommended by Google)
- SSL on port 465 (alternative)
- Connection timeout: 30 seconds
- Auto-reconnect on failure
- HTML email templates support

---

## 4. Files to Modify

| File | Changes |
|------|---------|
| [`app/core/config.py`](app/core/config.py) | Add SMTP_* settings |
| [`app/services/otpService.py:11`](app/services/otpService.py:11) | Replace `_send_otp_email()` print with EmailService |
| [`app/services/ticketService.py`](app/services/ticketService.py) | Add notification hooks (optional) |

---

## 5. SMTP Configuration

```
Host: smtp.gmail.com
Port: 587 (STARTTLS) - RECOMMENDED
Port: 465 (SSL) - Alternative

Security:
  - Port 587: STARTTLS (upgrade plain to encrypted)
  - Port 465: Implicit SSL (connect encrypted from start)
```

---

## 6. Error Handling

| Error | Handling |
|-------|----------|
| Connection timeout | Retry 3 times with exponential backoff |
| Authentication failed | Log error, raise exception |
| Invalid recipient | Validate email format before sending |
| SMTP session expired | Auto-reconnect and retry |

---

## 7. Email Templates

### OTP Email:
```
Subject: Your OTP Code
Body: Your verification code is: {otp}
Expiry: 5 minutes
```

### Ticket Created (to customer):
```
Subject: Ticket #{ticket_id} Created
Body: Your ticket has been received...
```

### Ticket Assigned (to employee):
```
Subject: New Ticket Assigned
Body: Ticket #{ticket_id} has been assigned to you...
```

---

## 8. Implementation Order

1. Update `app/core/config.py` with SMTP settings
2. Create `app/services/emailService.py`
3. Update `app/services/otpService.py` to use EmailService
4. Update `app/services/ticketService.py` with notification hooks (optional)
5. Add `.env` template documentation
6. Test with dry-run mode

---

## 9. Testing

- Unit test EmailService with mocked SMTP
- Integration test with real Gmail account (use test recipients)
- Verify email deliverability and spam score
