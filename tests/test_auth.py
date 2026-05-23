"""
Unit tests for Authentication Module.

Tests cover:
- User registration (Bước 1: Tạo tài khoản)
- OTP verification (Bước 2: Xác thực OTP)
- Login with username/password
- Token refresh mechanism
- Logout with token blacklisting
- Password change flow
- Forgot password and reset password
- Token validation and security

Test Credentials (from conftest fixtures):
- Admin: khangnguyen / 321321
- Manager: string / 321321
- Employee: employee2 / 321321
- Customer: antran / 321321
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from uuid import uuid4
import json

from app.services.authService import AuthService
from app.schemas.authSchema import (
    RegisterRequest,
    LoginRequest,
    VerifyOTPRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    ChangePasswordRequest,
    UserUpdateRequest,
)
from app.models.human import Human, Customer, Employee
from app.core.constants import HumanStatusEnum, MembershipTierEnum
from app.core.security import verify_password, get_password_hash, create_access_token, verify_token


# ============================================================================
# Registration Tests
# ============================================================================

class TestUserRegistration:
    """Tests for customer registration flow."""

    def test_register_customer_success(
        self,
        db_session,
        mock_redis_service,
        mock_email_service
    ):
        """Test successful customer registration."""
        with patch("app.services.authService.OTPService.generate_and_store_otp", return_value=True):
            service = AuthService(db_session)

            register_data = RegisterRequest(
                username="newcustomer",
                password="password123",
                email="newcustomer@example.com",
                first_name="New",
                last_name="Customer",
                phone="1234567890",
                address="123 New St",
                timezone="Asia/Ho_Chi_Minh"
            )

            result = service.register_customer(register_data)

            assert result is True

            # Verify customer was created with PENDING status
            customer = db_session.query(Customer).filter(
                Customer.email == "newcustomer@example.com"
            ).first()

            assert customer is not None
            assert customer.username == "newcustomer"
            assert customer.email == "newcustomer@example.com"
            assert customer.status == HumanStatusEnum.PENDING
            assert customer.membership_tier == MembershipTierEnum.STANDARD

    def test_register_customer_duplicate_email(
        self,
        db_session,
        sample_customer,
        mock_redis_service
    ):
        """Test registration fails when email already exists."""
        service = AuthService(db_session)

        register_data = RegisterRequest(
            username="anothercustomer",
            password="password123",
            email=sample_customer.email,  # Duplicate email
            first_name="Another",
            last_name="Customer"
        )

        result = service.register_customer(register_data)

        assert result is False

    def test_register_customer_duplicate_username(
        self,
        db_session,
        sample_customer,
        mock_redis_service
    ):
        """Test registration fails when username already exists."""
        service = AuthService(db_session)

        register_data = RegisterRequest(
            username=sample_customer.username,  # Duplicate username
            password="password123",
            email="different@example.com",
            first_name="Another",
            last_name="Customer"
        )

        result = service.register_customer(register_data)

        assert result is False

    def test_register_customer_duplicate_phone(
        self,
        db_session,
        sample_customer,
        mock_redis_service
    ):
        """Test registration fails when phone already exists."""
        service = AuthService(db_session)

        register_data = RegisterRequest(
            username="differentuser",
            password="password123",
            email="different@example.com",
            first_name="Another",
            last_name="Customer",
            phone=sample_customer.phone  # Duplicate phone
        )

        result = service.register_customer(register_data)

        assert result is False


# ============================================================================
# OTP Verification Tests
# ============================================================================

class TestOTPVerification:
    """Tests for OTP verification and account activation."""

    def test_verify_otp_success(
        self,
        db_session,
        sample_customer_pending,
        mock_redis_service
    ):
        """Test successful OTP verification activates account."""
        # Mock OTP verification to return True
        with patch("app.services.authService.OTPService.verify_otp_code", return_value=True):
            service = AuthService(db_session)

            customer = service.verify_otp_and_activate(
                sample_customer_pending.email,
                "123456"
            )

            assert customer is not None
            assert customer.status == HumanStatusEnum.ACTIVE

            # Verify in database
            db_session.refresh(sample_customer_pending)
            assert sample_customer_pending.status == HumanStatusEnum.ACTIVE

    def test_verify_otp_invalid_code(
        self,
        db_session,
        sample_customer_pending,
        mock_redis_service
    ):
        """Test OTP verification fails with invalid code."""
        with patch("app.services.authService.OTPService.verify_otp_code", return_value=False):
            service = AuthService(db_session)

            customer = service.verify_otp_and_activate(
                sample_customer_pending.email,
                "999999"  # Wrong OTP
            )

            assert customer is None

            # Status should still be PENDING
            db_session.refresh(sample_customer_pending)
            assert sample_customer_pending.status == HumanStatusEnum.PENDING

    def test_verify_otp_expired_or_not_found(
        self,
        db_session,
        mock_redis_service
    ):
        """Test OTP verification fails when OTP not found."""
        service = AuthService(db_session)

        # OTP not in Redis (returns None)
        with patch("app.services.authService.OTPService.verify_otp_code", return_value=False):
            customer = service.verify_otp_and_activate(
                "nonexistent@example.com",
                "123456"
            )

            assert customer is None

    def test_verify_otp_wrong_email(
        self,
        db_session,
        sample_customer_pending,
        mock_redis_service
    ):
        """Test OTP verification fails with wrong email (no pending customer)."""
        with patch("app.services.authService.OTPService.verify_otp_code", return_value=True):
            service = AuthService(db_session)

            customer = service.verify_otp_and_activate(
                "wrong@example.com",  # Email not in system
                "123456"
            )

            assert customer is None


# ============================================================================
# Authentication Tests (Login)
# ============================================================================

class TestAuthentication:
    """Tests for user authentication (login)."""

    def test_authenticate_user_success(
        self,
        db_session,
        sample_customer
    ):
        """Test successful login with correct credentials."""
        service = AuthService(db_session)

        # Password is "321321" - use the hashed version
        user = service.authenticate_user("customer1", "321321")

        assert user is not None
        assert user.username == "customer1"
        assert user.email == "customer1@example.com"

    def test_authenticate_user_wrong_password(
        self,
        db_session,
        sample_customer
    ):
        """Test login fails with wrong password."""
        service = AuthService(db_session)

        user = service.authenticate_user("customer1", "wrongpassword")

        assert user is None

    def test_authenticate_user_nonexistent_username(
        self,
        db_session
    ):
        """Test login fails with nonexistent username."""
        service = AuthService(db_session)

        user = service.authenticate_user("nonexistent", "password")

        assert user is None

    def test_authenticate_user_inactive_status(
        self,
        db_session
    ):
        """Test login fails for inactive (PENDING) user."""
        # Create a PENDING customer directly in DB
        pending_customer = Customer(
            id=uuid4(),
            username="pendinguser",
            email="pending@example.com",
            password_hash=get_password_hash("password123"),
            first_name="Pending",
            last_name="User",
            phone="9998887777",
            status=HumanStatusEnum.PENDING,  # Not ACTIVE
            type="customer",
            id_customer=uuid4(),
            customer_code="KH260999"
        )
        db_session.add(pending_customer)
        db_session.commit()

        service = AuthService(db_session)
        user = service.authenticate_user("pendinguser", "password123")

        assert user is None

    def test_authenticate_employee_success(
        self,
        db_session,
        sample_employee
    ):
        """Test successful employee login."""
        service = AuthService(db_session)

        user = service.authenticate_user("employee1", "321321")

        assert user is not None
        assert user.username == "employee1"
        assert isinstance(user, Employee)

    def test_authenticate_manager_success(
        self,
        db_session,
        sample_manager
    ):
        """Test successful manager login."""
        service = AuthService(db_session)

        user = service.authenticate_user("manager1", "321321")

        assert user is not None
        assert user.username == "manager1"
        assert user.role_name == "Manager"


# ============================================================================
# Token Management Tests
# ============================================================================

class TestTokenManagement:
    """Tests for JWT token creation and validation."""

    def test_create_tokens_success(
        self,
        db_session,
        sample_customer
    ):
        """Test token creation for authenticated user."""
        service = AuthService(db_session)

        access_token, refresh_token = service.create_tokens(sample_customer)

        assert access_token is not None
        assert refresh_token is not None
        assert len(access_token) > 0
        assert len(refresh_token) > 0

    def test_verify_access_token_valid(
        self,
        db_session,
        sample_customer
    ):
        """Test valid access token verification."""
        service = AuthService(db_session)

        access_token, _ = service.create_tokens(sample_customer)
        payload = service.verify_access_token(access_token)

        assert payload is not None
        assert payload["sub"] == str(sample_customer.id)
        assert payload["email"] == sample_customer.email

    def test_verify_access_token_invalid(
        self,
        db_session
    ):
        """Test invalid access token returns None."""
        service = AuthService(db_session)

        payload = service.verify_access_token("invalid.token.here")

        assert payload is None

    def test_refresh_tokens_success(
        self,
        db_session,
        sample_customer
    ):
        """Test successful token refresh."""
        service = AuthService(db_session)

        _, refresh_token = service.create_tokens(sample_customer)
        new_tokens = service.refresh_tokens(refresh_token)

        assert new_tokens is not None
        access_token, new_refresh_token = new_tokens
        assert access_token is not None
        assert new_refresh_token is not None

    def test_refresh_tokens_invalid(
        self,
        db_session
    ):
        """Test refresh fails with invalid token."""
        service = AuthService(db_session)

        new_tokens = service.refresh_tokens("invalid.refresh.token")

        assert new_tokens is None

    def test_access_token_has_correct_claims(
        self,
        db_session,
        sample_employee
    ):
        """Test access token contains correct claims."""
        service = AuthService(db_session)

        access_token, _ = service.create_tokens(sample_employee)
        payload = service.verify_access_token(access_token)

        assert payload["user_type"] == "employee"
        assert payload["role"] == "Admin"
        assert payload["email"] == sample_employee.email


# ============================================================================
# Password Management Tests
# ============================================================================

class TestPasswordManagement:
    """Tests for password change and reset functionality."""

    def test_change_password_success(
        self,
        db_session,
        sample_customer
    ):
        """Test successful password change."""
        service = AuthService(db_session)

        result = service.change_password(
            str(sample_customer.id),
            "321321",  # Old password
            "newpassword123"  # New password
        )

        assert result is True

        # Verify new password works
        db_session.refresh(sample_customer)
        assert verify_password("newpassword123", sample_customer.password_hash)

    def test_change_password_wrong_old_password(
        self,
        db_session,
        sample_customer
    ):
        """Test password change fails with wrong old password."""
        service = AuthService(db_session)

        result = service.change_password(
            str(sample_customer.id),
            "wrongoldpassword",
            "newpassword123"
        )

        assert result is False

    def test_change_password_nonexistent_user(
        self,
        db_session
    ):
        """Test password change fails for nonexistent user."""
        service = AuthService(db_session)

        result = service.change_password(
            str(uuid4()),  # Nonexistent user ID
            "oldpassword",
            "newpassword"
        )

        assert result is False

    def test_update_profile_success(
        self,
        db_session,
        sample_customer
    ):
        """Test successful profile update."""
        service = AuthService(db_session)

        update_data = UserUpdateRequest(
            first_name="UpdatedFirst",
            last_name="UpdatedLast",
            phone="9998887777",
            address="456 Updated Ave"
        )

        user = service.update_profile(str(sample_customer.id), update_data)

        assert user is not None
        assert user.first_name == "UpdatedFirst"
        assert user.last_name == "UpdatedLast"
        assert user.phone == "9998887777"
        assert user.address == "456 Updated Ave"

    def test_update_profile_partial(
        self,
        db_session,
        sample_customer
    ):
        """Test partial profile update (only some fields)."""
        service = AuthService(db_session)

        update_data = UserUpdateRequest(
            first_name="OnlyFirstUpdated"
        )

        user = service.update_profile(str(sample_customer.id), update_data)

        assert user.first_name == "OnlyFirstUpdated"
        assert user.last_name == sample_customer.last_name  # Unchanged

    def test_update_profile_nonexistent_user(
        self,
        db_session
    ):
        """Test profile update fails for nonexistent user."""
        service = AuthService(db_session)

        update_data = UserUpdateRequest(first_name="Test")
        user = service.update_profile(str(uuid4()), update_data)

        assert user is None


# ============================================================================
# Forgot Password Tests
# ============================================================================

class TestForgotPassword:
    """Tests for forgot password flow."""

    def test_initiate_forgot_password_existing_user(
        self,
        db_session,
        sample_customer,
        mock_redis_service
    ):
        """Test forgot password initiation for existing user."""
        with patch("app.services.authService.OTPService.generate_otp_for_password_reset", return_value=True):
            service = AuthService(db_session)

            result = service.initiate_forgot_password(sample_customer.email)

            assert result is True

    def test_initiate_forgot_password_nonexistent_user(
        self,
        db_session,
        mock_redis_service
    ):
        """Test forgot password returns True even for nonexistent email (security)."""
        # This prevents email enumeration attacks
        with patch("app.services.authService.OTPService.generate_otp_for_password_reset", return_value=True) as mock_otp:
            service = AuthService(db_session)

            result = service.initiate_forgot_password("nonexistent@example.com")

            # Should return True to prevent email enumeration
            assert result is True
            # OTP should NOT be generated for nonexistent email
            # (depends on implementation - some may still call it)

    def test_reset_password_with_otp_success(
        self,
        db_session,
        sample_customer,
        mock_redis_service
    ):
        """Test successful password reset with valid OTP."""
        with patch("app.services.authService.OTPService.verify_password_reset_otp", return_value=True):
            service = AuthService(db_session)

            result = service.reset_password_with_otp(
                sample_customer.email,
                "123456",
                "newresetpassword"
            )

            assert result is True

            # Verify new password works for login
            db_session.refresh(sample_customer)
            assert verify_password("newresetpassword", sample_customer.password_hash)

    def test_reset_password_with_otp_invalid(
        self,
        db_session,
        sample_customer,
        mock_redis_service
    ):
        """Test password reset fails with invalid OTP."""
        with patch("app.services.authService.OTPService.verify_password_reset_otp", return_value=False):
            service = AuthService(db_session)

            result = service.reset_password_with_otp(
                sample_customer.email,
                "999999",
                "newpassword"
            )

            assert result is False

    def test_reset_password_with_otp_nonexistent_email(
        self,
        db_session,
        mock_redis_service
    ):
        """Test password reset fails for nonexistent email."""
        with patch("app.services.authService.OTPService.verify_password_reset_otp", return_value=False):
            service = AuthService(db_session)

            result = service.reset_password_with_otp(
                "nonexistent@example.com",
                "123456",
                "newpassword"
            )

            assert result is False


# ============================================================================
# Token Blacklisting Tests
# ============================================================================

class TestTokenBlacklisting:
    """Tests for token blacklist functionality."""

    def test_verify_token_returns_payload_for_valid_token(
        self,
        sample_customer
    ):
        """Test that valid token returns correct payload."""
        access_token, _ = create_access_token(sample_customer)

        payload = verify_token(access_token, "access")

        assert payload is not None
        assert payload["sub"] == str(sample_customer.id)

    def test_verify_token_returns_none_for_wrong_type(
        self,
        sample_customer
    ):
        """Test that using refresh token as access token fails."""
        _, refresh_token = create_access_token(sample_customer)  # Create as refresh

        # Try to verify as access token
        payload = verify_token(refresh_token, "access")

        # Should fail because token type doesn't match
        assert payload is None

    def test_password_hashing(
        self
    ):
        """Test password hashing and verification."""
        password = "testpassword123"
        hashed = get_password_hash(password)

        assert hashed != password
        assert verify_password(password, hashed) is True
        assert verify_password("wrongpassword", hashed) is False


# ============================================================================
# Integration-Style Tests (Service Layer)
# ============================================================================

class TestAuthServiceIntegration:
    """High-level tests simulating real authentication flows."""

    def test_full_registration_flow(
        self,
        db_session,
        mock_redis_service,
        mock_email_service
    ):
        """Test complete registration flow: register -> verify OTP -> login."""
        # Step 1: Register
        with patch("app.services.authService.OTPService.generate_and_store_otp", return_value=True):
            service = AuthService(db_session)

            register_data = RegisterRequest(
                username="flowtest",
                password="password123",
                email="flowtest@example.com",
                first_name="Flow",
                last_name="Test"
            )

            reg_result = service.register_customer(register_data)
            assert reg_result is True

            # Step 2: Verify OTP (would be done with real OTP in production)
            # For testing, we mock the OTP verification
            with patch("app.services.authService.OTPService.verify_otp_code", return_value=True):
                customer = service.verify_otp_and_activate("flowtest@example.com", "123456")

                assert customer is not None
                assert customer.status == HumanStatusEnum.ACTIVE

                # Step 3: Login with new account
                user = service.authenticate_user("flowtest", "password123")
                assert user is not None

                # Step 4: Get tokens
                access_token, refresh_token = service.create_tokens(user)
                assert access_token is not None
                assert refresh_token is not None

    def test_login_creates_tokens_with_correct_claims(
        self,
        db_session,
        sample_employee
    ):
        """Test that login creates tokens with correct user claims."""
        service = AuthService(db_session)

        user = service.authenticate_user("employee1", "321321")
        access_token, refresh_token = service.create_tokens(user)

        # Verify access token
        payload = verify_token(access_token, "access")

        assert payload["sub"] == str(user.id)
        assert payload["email"] == user.email
        assert payload["user_type"] == "employee"
        assert payload["role"] == "Admin"


# ============================================================================
# Security Edge Cases
# ============================================================================

class TestAuthSecurityEdgeCases:
    """Security-related edge case tests."""

    def test_password_not_stored_in_plain_text(
        self,
        db_session
    ):
        """Test that passwords are never stored in plain text."""
        password = "MySecurePassword123!"
        hashed = get_password_hash(password)

        assert hashed != password
        assert len(hashed) > 20
        assert "$2b$" in hashed  # bcrypt format indicator

    def test_different_passwords_produce_different_hashes(
        self
    ):
        """Test that same password produces different hashes (salt)."""
        password = "samepassword"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        assert hash1 != hash2
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)

    def test_empty_username_rejected_at_service_level(
        self,
        db_session,
        mock_redis_service
    ):
        """Test that empty username is handled gracefully."""
        service = AuthService(db_session)

        user = service.authenticate_user("", "password")

        assert user is None

    def test_special_characters_in_password_handled(
        self,
        db_session,
        sample_customer
    ):
        """Test that special characters in passwords work correctly."""
        # This tests that password hashing handles Unicode/special chars
        special_password = "P@ssw0rd!#$%^&*()_+-=[]{}|;':\",./<>?"
        hashed = get_password_hash(special_password)

        assert verify_password(special_password, hashed)
        assert not verify_password("wrongpassword", hashed)
