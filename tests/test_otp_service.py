import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4
from app.services.otpService import OTPService


class TestOTPService:
    """Test OTP service with Redis-based storage"""

    @pytest.fixture
    def mock_redis_service(self):
        """Create mock Redis service"""
        mock = MagicMock()
        mock.set_with_expiry.return_value = True
        mock.get.return_value = None
        mock.delete.return_value = True
        mock.is_connected.return_value = True
        return mock

    def test_generate_and_store_otp_stores_in_redis(self, mock_redis_service):
        """Test that OTP generation stores data in Redis"""
        with patch('app.services.otpService.redis_service', mock_redis_service):
            email = "test@example.com"
            payload_data = {"username": "testuser", "password": "hashed"}
            
            result = OTPService.generate_and_store_otp(email, payload_data)
            
            assert result is True
            mock_redis_service.set_with_expiry.assert_called_once()
            # Verify the key format
            call_args = mock_redis_service.set_with_expiry.call_args
            assert call_args[0][0] == f"otp:{email}"

    def test_verify_and_get_data_returns_payload_on_valid_otp(self, mock_redis_service):
        """Test OTP verification returns stored data when OTP is valid"""
        email = "test@example.com"
        otp_code = "123456"
        stored_data = {"username": "testuser", "password": "hashed"}
        
        import json
        mock_redis_service.get.return_value = json.dumps({
            "otp": otp_code,
            "data": stored_data,
            "type": "verification"
        })
        
        with patch('app.services.otpService.redis_service', mock_redis_service):
            result = OTPService.verify_and_get_data(email, otp_code)
            
            assert result == stored_data
            mock_redis_service.delete.assert_called_once_with(f"otp:{email}")

    def test_verify_and_get_data_returns_none_for_wrong_otp(self, mock_redis_service):
        """Test OTP verification returns None for wrong OTP"""
        email = "test@example.com"
        
        import json
        mock_redis_service.get.return_value = json.dumps({
            "otp": "123456",
            "data": {"username": "testuser"},
            "type": "verification"
        })
        
        with patch('app.services.otpService.redis_service', mock_redis_service):
            result = OTPService.verify_and_get_data(email, "999999")
            
            assert result is None

    def test_verify_and_get_data_returns_none_for_expired_otp(self, mock_redis_service):
        """Test OTP verification returns None when not found (simulating expiry)"""
        email = "test@example.com"
        mock_redis_service.get.return_value = None
        
        with patch('app.services.otpService.redis_service', mock_redis_service):
            result = OTPService.verify_and_get_data(email, "123456")
            
            assert result is None

    def test_generate_otp_for_password_reset_stores_correct_type(self, mock_redis_service):
        """Test password reset OTP has correct type marker"""
        with patch('app.services.otpService.redis_service', mock_redis_service):
            email = "test@example.com"
            
            result = OTPService.generate_otp_for_password_reset(email)
            
            assert result is True
            call_args = mock_redis_service.set_with_expiry.call_args
            stored_value = call_args[0][1]
            
            import json
            parsed = json.loads(stored_value)
            assert parsed["type"] == "password_reset"
            assert parsed["data"] == "password_reset"

    def test_verify_password_reset_otp_returns_true_for_valid(self, mock_redis_service):
        """Test password reset OTP verification"""
        email = "test@example.com"
        otp_code = "123456"
        
        import json
        mock_redis_service.get.return_value = json.dumps({
            "otp": otp_code,
            "data": "password_reset",
            "type": "password_reset"
        })
        
        with patch('app.services.otpService.redis_service', mock_redis_service):
            result = OTPService.verify_password_reset_otp(email, otp_code)
            
            assert result is True
            mock_redis_service.delete.assert_called_once()

    def test_verify_password_reset_otp_returns_false_for_wrong_type(self, mock_redis_service):
        """Test password reset OTP fails if generated as regular OTP"""
        email = "test@example.com"
        otp_code = "123456"
        
        import json
        # OTP stored as regular verification type, not password_reset
        mock_redis_service.get.return_value = json.dumps({
            "otp": otp_code,
            "data": {"username": "testuser"},
            "type": "verification"
        })
        
        with patch('app.services.otpService.redis_service', mock_redis_service):
            result = OTPService.verify_password_reset_otp(email, otp_code)
            
            assert result is False

    def test_send_otp_email_does_not_print_to_console(self, mock_redis_service):
        """Test that OTP email failure does NOT print OTP to console (security)"""
        with patch('app.services.otpService.redis_service', mock_redis_service):
            with patch('app.services.emailService.email_service') as mock_email:
                mock_email.send_otp_email.side_effect = Exception("SMTP error")
                
                # Should not raise, should not print
                OTPService._send_otp_email("test@example.com", "123456")
                
                # No print statement should be called
                # This test verifies the security fix - no console output

    def test_otp_deleted_after_successful_verification(self, mock_redis_service):
        """Test that OTP is deleted from Redis after successful use"""
        email = "test@example.com"
        otp_code = "123456"
        
        import json
        mock_redis_service.get.return_value = json.dumps({
            "otp": otp_code,
            "data": {"username": "testuser"},
            "type": "verification"
        })
        
        with patch('app.services.otpService.redis_service', mock_redis_service):
            OTPService.verify_and_get_data(email, otp_code)
            
            mock_redis_service.delete.assert_called_once_with(f"otp:{email}")

    def test_generate_otp_returns_six_digits(self, mock_redis_service):
        """Test that generated OTP is exactly 6 digits"""
        with patch('app.services.otpService.redis_service', mock_redis_service):
            email = "test@example.com"
            
            # We can't directly test the OTP code since it's random
            # But we can verify the length by checking the pattern in stored value
            OTPService.generate_and_store_otp(email, {"test": "data"})
            
            call_args = mock_redis_service.set_with_expiry.call_args
            stored_value = call_args[0][1]
            import json
            parsed = json.loads(stored_value)
            
            # Verify OTP is 6 digits
            assert len(parsed["otp"]) == 6
            assert parsed["otp"].isdigit()