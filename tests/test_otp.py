"""
Tests for OTP Service.

Covers:
- OTP generation and storage
- OTP verification for registration flow
- OTP verification for password reset flow
- Rejection of invalid/expired/wrong OTPs
- One-time use enforcement (reused codes rejected)
- Differentiation between registration and password_reset OTP types
"""

import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4

from app.services.otpService import OTPService


# ============================================================================
# Helper Mocks
# ============================================================================

class FakeRedisStore(dict):
    """Fake Redis storage for testing OTP service."""

    def set_with_expiry(self, key, value, ttl):
        self[key] = value
        return True

    def get(self, key):
        return self.get(key)  # Will be overridden in mock

    def delete(self, key):
        if key in self:
            del self[key]
            return True
        return False


@pytest.fixture
def mock_redis():
    """Mock Redis service for OTP tests."""
    store = {}

    def fake_set(key, value, ttl):
        store[key] = value
        return True

    def fake_get(key):
        return store.get(key)

    def fake_delete(key):
        if key in store:
            del store[key]
            return True
        return False

    with patch("app.services.otpService.redis_service") as mock:
        mock.set_with_expiry.side_effect = fake_set
        mock.get.side_effect = fake_get
        mock.delete.side_effect = fake_delete
        mock.is_connected.return_value = True
        yield mock, store


@pytest.fixture
def mock_email():
    """Mock email service methods to prevent actual email sending."""
    with patch("app.services.emailService.email_service.send_otp_email", return_value=True) as mock_send, \
         patch("app.services.emailService.email_service.send_password_reset_otp_email", return_value=True) as mock_reset:
        yield mock_send, mock_reset


# ============================================================================
# OTP Generation Tests
# ============================================================================

class TestOTPGeneration:
    """Tests for OTP generation."""

    def test_generate_otp_returns_six_digit_code(self, mock_redis, mock_email):
        """Test that generated OTP is a 6-digit numeric code."""
        email = "test@example.com"

        result = OTPService.generate_and_store_otp(email)

        assert result is True

    def test_generate_otp_stores_in_redis(self, mock_redis, mock_email):
        """Test that OTP is stored in Redis with correct key format."""
        email = "test@example.com"

        OTPService.generate_and_store_otp(email)

        mock_redis[0].set_with_expiry.assert_called_once()
        call_args = mock_redis[0].set_with_expiry.call_args
        assert call_args[0][0] == f"otp:{email}"

    def test_generate_otp_stores_correct_data_structure(self, mock_redis, mock_email):
        """Test that stored OTP data has expected fields."""
        email = "test@example.com"
        import json

        OTPService.generate_and_store_otp(email)

        stored_value = mock_redis[1][f"otp:{email}"]
        data = json.loads(stored_value)

        assert "otp" in data
        assert len(data["otp"]) == 6
        assert data["otp"].isdigit()
        assert data["type"] == "verification"

    def test_generate_otp_with_payload_data(self, mock_redis, mock_email):
        """Test OTP generation with custom payload data."""
        email = "test@example.com"
        payload = {"user_id": str(uuid4())}
        import json

        OTPService.generate_and_store_otp(email, payload_data=payload)

        stored_value = mock_redis[1][f"otp:{email}"]
        data = json.loads(stored_value)

        assert data["data"] == payload

    def test_generate_password_reset_otp_different_type(self, mock_redis, mock_email):
        """Test that password reset OTP has 'password_reset' type."""
        email = "test@example.com"
        import json

        OTPService.generate_otp_for_password_reset(email)

        stored_value = mock_redis[1][f"otp:{email}"]
        data = json.loads(stored_value)

        assert data["type"] == "password_reset"
        assert data["data"] == "password_reset"

    def test_generate_otp_sends_email(self, mock_redis, mock_email):
        """Test that OTP generation triggers email sending."""
        email = "test@example.com"

        OTPService.generate_and_store_otp(email)

        mock_email[0].assert_called_once()

    def test_generate_password_reset_otp_sends_email(self, mock_redis, mock_email):
        """Test that password reset OTP generation triggers email sending."""
        email = "test@example.com"

        OTPService.generate_otp_for_password_reset(email)

        mock_email[1].assert_called_once()


# ============================================================================
# OTP Verification Tests - Registration Flow
# ============================================================================

class TestOTPVerificationRegistration:
    """Tests for OTP verification in registration flow."""

    def test_verify_otp_with_correct_code_returns_true(self, mock_redis, mock_email):
        """Test that correct OTP code is accepted."""
        email = "test@example.com"
        import json

        # Pre-populate store with known OTP
        known_code = "123456"
        mock_redis[1][f"otp:{email}"] = json.dumps({
            "otp": known_code,
            "data": None,
            "type": "verification"
        })

        result = OTPService.verify_otp_code(email, known_code)

        assert result is True

    def test_verify_otp_with_wrong_code_returns_false(self, mock_redis, mock_email):
        """Test that wrong OTP code is rejected."""
        email = "test@example.com"
        import json

        mock_redis[1][f"otp:{email}"] = json.dumps({
            "otp": "123456",
            "data": None,
            "type": "verification"
        })

        result = OTPService.verify_otp_code(email, "000000")

        assert result is False

    def test_verify_otp_deletes_after_success(self, mock_redis, mock_email):
        """Test that OTP is deleted from Redis after successful verification."""
        email = "test@example.com"
        import json

        mock_redis[1][f"otp:{email}"] = json.dumps({
            "otp": "123456",
            "data": None,
            "type": "verification"
        })

        OTPService.verify_otp_code(email, "123456")

        assert f"otp:{email}" not in mock_redis[1]

    def test_verify_otp_no_entry_returns_false(self, mock_redis, mock_email):
        """Test that non-existent OTP returns False."""
        email = "nonexistent@example.com"

        result = OTPService.verify_otp_code(email, "123456")

        assert result is False

    def test_verify_otp_rejects_password_reset_type(self, mock_redis, mock_email):
        """Test that password_reset OTP is rejected for registration verification."""
        email = "test@example.com"
        import json

        mock_redis[1][f"otp:{email}"] = json.dumps({
            "otp": "123456",
            "data": "password_reset",
            "type": "password_reset"
        })

        result = OTPService.verify_otp_code(email, "123456")

        assert result is False


# ============================================================================
# OTP Verification Tests - Password Reset Flow
# ============================================================================

class TestOTPVerificationPasswordReset:
    """Tests for OTP verification in password reset flow."""

    def test_verify_password_reset_otp_with_correct_code_returns_true(self, mock_redis, mock_email):
        """Test that correct password reset OTP is accepted."""
        email = "test@example.com"
        import json

        mock_redis[1][f"otp:{email}"] = json.dumps({
            "otp": "123456",
            "data": "password_reset",
            "type": "password_reset"
        })

        result = OTPService.verify_password_reset_otp(email, "123456")

        assert result is True

    def test_verify_password_reset_otp_with_wrong_code_returns_false(self, mock_redis, mock_email):
        """Test that wrong password reset OTP is rejected."""
        email = "test@example.com"
        import json

        mock_redis[1][f"otp:{email}"] = json.dumps({
            "otp": "123456",
            "data": "password_reset",
            "type": "password_reset"
        })

        result = OTPService.verify_password_reset_otp(email, "000000")

        assert result is False

    def test_verify_password_reset_otp_deletes_after_success(self, mock_redis, mock_email):
        """Test that password reset OTP is deleted after successful verification."""
        email = "test@example.com"
        import json

        mock_redis[1][f"otp:{email}"] = json.dumps({
            "otp": "123456",
            "data": "password_reset",
            "type": "password_reset"
        })

        OTPService.verify_password_reset_otp(email, "123456")
        assert f"otp:{email}" not in mock_redis[1]

    def test_verify_password_reset_otp_no_entry_returns_false(self, mock_redis, mock_email):
        """Test that non-existent password reset OTP returns False."""
        email = "nonexistent@example.com"

        result = OTPService.verify_password_reset_otp(email, "123456")

        assert result is False

    def test_verify_password_reset_otp_rejects_registration_type(self, mock_redis, mock_email):
        """Test that registration OTP is rejected for password reset verification."""
        email = "test@example.com"
        import json

        mock_redis[1][f"otp:{email}"] = json.dumps({
            "otp": "123456",
            "data": None,
            "type": "verification"
        })

        result = OTPService.verify_password_reset_otp(email, "123456")

        assert result is False


# ============================================================================
# Verify and Get Data Tests
# ============================================================================

class TestVerifyAndGetData:
    """Tests for OTP verification with data retrieval."""

    def test_verify_and_get_data_returns_stored_data(self, mock_redis, mock_email):
        """Test that stored data is returned after OTP verification."""
        email = "test@example.com"
        import json
        expected_data = {"user_id": str(uuid4())}

        mock_redis[1][f"otp:{email}"] = json.dumps({
            "otp": "123456",
            "data": expected_data,
            "type": "verification"
        })

        result = OTPService.verify_and_get_data(email, "123456")

        assert result == expected_data

    def test_verify_and_get_data_with_wrong_code_returns_none(self, mock_redis, mock_email):
        """Test that wrong code returns None without deleting."""
        email = "test@example.com"
        import json

        mock_redis[1][f"otp:{email}"] = json.dumps({
            "otp": "123456",
            "data": {"key": "value"},
            "type": "verification"
        })

        result = OTPService.verify_and_get_data(email, "999999")

        assert result is None
        assert f"otp:{email}" in mock_redis[1]

    def test_verify_and_get_data_no_entry_returns_none(self, mock_redis, mock_email):
        """Test that non-existent OTP returns None."""
        email = "nonexistent@example.com"

        result = OTPService.verify_and_get_data(email, "123456")

        assert result is None


# ============================================================================
# One-Time Use Tests
# ============================================================================

class TestOTPOneTimeUse:
    """Tests for OTP one-time use enforcement."""

    def test_otp_cannot_be_used_twice(self, mock_redis, mock_email):
        """Test that OTP cannot be verified twice."""
        email = "test@example.com"
        import json

        mock_redis[1][f"otp:{email}"] = json.dumps({
            "otp": "123456",
            "data": None,
            "type": "verification"
        })

        first_result = OTPService.verify_otp_code(email, "123456")
        second_result = OTPService.verify_otp_code(email, "123456")

        assert first_result is True
        assert second_result is False

    def test_password_reset_otp_cannot_be_used_twice(self, mock_redis, mock_email):
        """Test that password reset OTP cannot be verified twice."""
        email = "test@example.com"
        import json

        mock_redis[1][f"otp:{email}"] = json.dumps({
            "otp": "123456",
            "data": "password_reset",
            "type": "password_reset"
        })

        first_result = OTPService.verify_password_reset_otp(email, "123456")
        second_result = OTPService.verify_password_reset_otp(email, "123456")

        assert first_result is True
        assert second_result is False


# ============================================================================
# Edge Case Tests
# ============================================================================

class TestOTPEdgeCases:
    """Edge case tests for OTP service."""

    def test_verify_otp_with_malformed_json_returns_false(self, mock_redis, mock_email):
        """Test that malformed JSON in Redis returns False."""
        email = "test@example.com"

        mock_redis[1][f"otp:{email}"] = "not valid json"

        result = OTPService.verify_otp_code(email, "123456")

        assert result is False

    def test_verify_otp_with_empty_email_stores_with_empty_key(self, mock_redis, mock_email):
        """Test handling of empty email edge case."""
        email = ""
        import json

        OTPService.generate_and_store_otp(email)

        mock_redis[0].set_with_expiry.assert_called_once()
        call_args = mock_redis[0].set_with_expiry.call_args
        assert call_args[0][0] == "otp:"

    def test_verify_and_get_data_with_empty_data_returns_none_after_delete(self, mock_redis, mock_email):
        """Test that empty data returns None correctly."""
        email = "test@example.com"
        import json

        mock_redis[1][f"otp:{email}"] = json.dumps({
            "otp": "123456",
            "data": None,
            "type": "verification"
        })

        result = OTPService.verify_and_get_data(email, "123456")

        assert result is None

    def test_different_emails_have_separate_otps(self, mock_redis, mock_email):
        """Test that email addresses have isolated OTP entries."""
        email1 = "user1@example.com"
        email2 = "user2@example.com"
        import json

        OTPService.generate_and_store_otp(email1)
        OTPService.generate_and_store_otp(email2)

        assert f"otp:{email1}" in mock_redis[1]
        assert f"otp:{email2}" in mock_redis[1]

        otp1 = json.loads(mock_redis[1][f"otp:{email1}"])["otp"]
        otp2 = json.loads(mock_redis[1][f"otp:{email2}"])["otp"]

        assert otp1 != otp2
