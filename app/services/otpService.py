import random
import string
import time
from typing import Any, Optional, Dict

OTP_CACHE: Dict[str, Dict[str, Any]] = {}
SPAM_COOLDOWN = 300  # Hết hạn sau 5 phút

class OTPService:
    @staticmethod
    def _send_otp_email(email: str, otp: str):
        try:
            from app.services.emailService import email_service
            email_service.send_otp_email(email, otp)
        except Exception as e:
            # Fallback to console print if email fails
            print(f"\n=====================================================")
            print(f"📧 EMAIL FAILED - PRINTING TO CONSOLE:")
            print(f"📧 ĐANG GỬI EMAIL ĐẾN: {email}")
            print(f"🔑 MÃ OTP XÁC NHẬN CỦA BẠN LÀ: {otp}")
            print(f"=====================================================\n")
    
    @staticmethod
    def _send_password_reset_otp_email(email: str, otp: str):
        """Send password reset OTP via email"""
        try:
            from app.services.emailService import email_service
            email_service.send_password_reset_otp_email(email, otp)
        except Exception as e:
            # Fallback to console print if email fails
            print(f"\n=====================================================")
            print(f"📧 PASSWORD RESET - EMAIL FAILED - PRINTING TO CONSOLE:")
            print(f"📧 ĐANG GỬI EMAIL ĐẾN: {email}")
            print(f"🔑 MÃ OTP ĐẶT LẠI MẬT KHẨU: {otp}")
            print(f"=====================================================\n")

    @staticmethod
    def generate_and_store_otp(email: str, payload_data: Any) -> bool:
        otp_code = ''.join(random.choices(string.digits, k=6))
        expire_time = time.time() + SPAM_COOLDOWN

        # Lưu vào Cache
        OTP_CACHE[email] = {
            "otp": otp_code,
            "expire": expire_time,
            "data": payload_data
        }

        OTPService._send_otp_email(email, otp_code)
        return True
    
    @staticmethod
    def generate_otp_for_password_reset(email: str) -> bool:
        """Generate OTP specifically for password reset (no payload, just mark for password reset)"""
        # Check if there's already an OTP for this email
        existing = OTP_CACHE.get(email)
        if existing:
            # If existing OTP hasn't expired, allow reuse but still send new one
            if time.time() < existing["expire"]:
                # Just update with new OTP but keep the "password_reset" type
                pass
        
        otp_code = ''.join(random.choices(string.digits, k=6))
        expire_time = time.time() + SPAM_COOLDOWN

        # Store with special "password_reset" marker
        OTP_CACHE[email] = {
            "otp": otp_code,
            "expire": expire_time,
            "data": "password_reset"
        }

        OTPService._send_password_reset_otp_email(email, otp_code)
        return True
    
    @staticmethod
    def verify_password_reset_otp(email: str, otp_code: str) -> bool:
        """Verify OTP for password reset - returns True if valid"""
        cache_entry = OTP_CACHE.get(email)

        if not cache_entry:
            return False

        if time.time() > cache_entry["expire"]:
            del OTP_CACHE[email]
            return False

        if cache_entry["otp"] != otp_code:
            return False

        # Check if this OTP was generated for password reset
        if cache_entry.get("data") != "password_reset":
            return False

        # Delete OTP after successful verification (one-time use)
        del OTP_CACHE[email]
        return True

    @staticmethod
    def verify_and_get_data(email: str, otp_code: str) -> Optional[Any]:
        cache_entry = OTP_CACHE.get(email)

        if not cache_entry:
            return None

        if time.time() > cache_entry["expire"]:
            del OTP_CACHE[email]
            return None

        if cache_entry["otp"] != otp_code:
            return None

        data = cache_entry["data"]
        del OTP_CACHE[email]
        return data