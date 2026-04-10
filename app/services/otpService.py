import random
import string
import json
import logging
from typing import Any, Optional
from app.services.redisService import redis_service

logger = logging.getLogger(__name__)

SPAM_COOLDOWN = 300  # 5 minutes expiry

class OTPService:
    @staticmethod
    def _send_otp_email(email: str, otp: str):
        """Send OTP email - fail silently, do not print to console"""
        try:
            from app.services.emailService import email_service
            email_service.send_otp_email(email, otp)
        except Exception as e:
            logger.error(f"❌ Failed to send OTP email to {email}: {e}")
            # Never print OTP to console - security risk
    
    @staticmethod
    def _send_password_reset_otp_email(email: str, otp: str):
        """Send password reset OTP via email"""
        try:
            from app.services.emailService import email_service
            email_service.send_password_reset_otp_email(email, otp)
        except Exception as e:
            logger.error(f"❌ Failed to send password reset OTP email to {email}: {e}")
            # Never print OTP to console - security risk

    @staticmethod
    def _get_redis():
        """Get Redis service instance"""
        return redis_service

    @staticmethod
    def _store_otp(email: str, otp_code: str, data: Any, otp_type: str = "verification") -> bool:
        """Store OTP in Redis with TTL"""
        redis = OTPService._get_redis()
        key = f"otp:{email}"
        value = json.dumps({
            "otp": otp_code,
            "data": data,
            "type": otp_type
        })
        return redis.set_with_expiry(key, value, SPAM_COOLDOWN)

    @staticmethod
    def _get_otp_data(email: str) -> Optional[dict]:
        """Retrieve OTP data from Redis"""
        redis = OTPService._get_redis()
        key = f"otp:{email}"
        value = redis.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return None
        return None

    @staticmethod
    def _delete_otp(email: str) -> bool:
        """Delete OTP from Redis (one-time use)"""
        redis = OTPService._get_redis()
        key = f"otp:{email}"
        return redis.delete(key)

    @staticmethod
    def generate_and_store_otp(email: str, payload_data: Any) -> bool:
        otp_code = ''.join(random.choices(string.digits, k=6))
        
        # Store in Redis instead of in-memory dict
        stored = OTPService._store_otp(email, otp_code, payload_data, "verification")
        
        # Send email (do not fall back to console)
        OTPService._send_otp_email(email, otp_code)
        return stored
    
    @staticmethod
    def generate_otp_for_password_reset(email: str) -> bool:
        """Generate OTP specifically for password reset"""
        otp_code = ''.join(random.choices(string.digits, k=6))
        
        # Store with special "password_reset" marker
        stored = OTPService._store_otp(email, otp_code, "password_reset", "password_reset")
        
        OTPService._send_password_reset_otp_email(email, otp_code)
        return stored
    
    @staticmethod
    def verify_password_reset_otp(email: str, otp_code: str) -> bool:
        """Verify OTP for password reset - returns True if valid"""
        cache_entry = OTPService._get_otp_data(email)

        if not cache_entry:
            return False

        if cache_entry["otp"] != otp_code:
            return False

        # Check if this OTP was generated for password reset
        if cache_entry.get("type") != "password_reset":
            return False

        # Delete OTP after successful verification (one-time use)
        OTPService._delete_otp(email)
        return True

    @staticmethod
    def verify_and_get_data(email: str, otp_code: str) -> Optional[Any]:
        cache_entry = OTPService._get_otp_data(email)

        if not cache_entry:
            return None

        if cache_entry["otp"] != otp_code:
            return None

        data = cache_entry["data"]
        # Delete OTP after successful verification (one-time use)
        OTPService._delete_otp(email)
        return data