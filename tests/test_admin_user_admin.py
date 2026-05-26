"""
Tests for admin user admin service.
"""

import pytest
from uuid import uuid4
from typing import Any

from app.services.admin.userAdminService import UserAdminService
from app.core.constants import HumanStatusEnum


class TestUpdateUserStatus:
    """Tests for update_user_status method."""

    def test_update_employee_status_to_inactive(self, db_session, sample_employee):
        """Happy path: update employee status from Active to Inactive."""
        service = UserAdminService(db_session)

        result = service.update_user_status(
            "employee",
            sample_employee.id_employee,
            HumanStatusEnum.INACTIVE.value
        )

        assert result["user_type"] == "employee"
        assert str(result["user_id"]) == str(sample_employee.id_employee)
        assert result["status"] == HumanStatusEnum.INACTIVE.value

        db_session.refresh(sample_employee)
        assert sample_employee.status == HumanStatusEnum.INACTIVE.value

    def test_update_employee_status_to_banned(self, db_session, sample_employee):
        """Business rule: ban an employee."""
        service = UserAdminService(db_session)

        result = service.update_user_status(
            "employee",
            sample_employee.id_employee,
            HumanStatusEnum.BANNED.value
        )

        assert str(result["status"]) == HumanStatusEnum.BANNED.value
        db_session.refresh(sample_employee)
        assert sample_employee.status == HumanStatusEnum.BANNED.value

    def test_update_customer_status_to_inactive(self, db_session, sample_customer):
        """Happy path: update customer status from Active to Inactive."""
        service = UserAdminService(db_session)

        result = service.update_user_status(
            "customer",
            sample_customer.id_customer,
            HumanStatusEnum.INACTIVE.value
        )

        assert result["user_type"] == "customer"
        db_session.refresh(sample_customer)
        assert sample_customer.status == HumanStatusEnum.INACTIVE.value

    def test_update_user_status_rejects_invalid_status_for_employee(
        self, db_session, sample_employee
    ):
        """Validation: invalid status value raises HTTPException."""
        service = UserAdminService(db_session)

        with pytest.raises(Exception) as exc_info:
            service.update_user_status(
                "employee",
                sample_employee.id_employee,
                "NotAValidStatus"
            )

        assert "400" in str(exc_info.value) or "Invalid status" in str(exc_info.value)

    def test_update_user_status_rejects_invalid_status_for_customer(
        self, db_session, sample_customer
    ):
        """Validation: invalid status value raises HTTPException for customer."""
        service = UserAdminService(db_session)

        with pytest.raises(Exception) as exc_info:
            service.update_user_status(
                "customer",
                sample_customer.id_customer,
                "BadStatus"
            )

        assert "400" in str(exc_info.value) or "Invalid status" in str(exc_info.value)

    def test_update_user_status_rejects_invalid_user_type(
        self, db_session, sample_employee
    ):
        """Validation: invalid user_type raises HTTPException 400."""
        service = UserAdminService(db_session)

        with pytest.raises(Exception) as exc_info:
            service.update_user_status(
                "unknown_user",
                sample_employee.id_employee,
                HumanStatusEnum.ACTIVE.value
            )

        assert "400" in str(exc_info.value) or "Invalid user_type" in str(exc_info.value)

    def test_update_user_status_rejects_missing_employee(self, db_session):
        """Validation: missing employee ID raises HTTPException 404."""
        service = UserAdminService(db_session)

        with pytest.raises(Exception) as exc_info:
            service.update_user_status(
                "employee",
                uuid4(),
                HumanStatusEnum.ACTIVE.value
            )

        assert "404" in str(exc_info.value) or "not found" in str(exc_info.value).lower()

    def test_update_user_status_rejects_missing_customer(self, db_session):
        """Validation: missing customer ID raises HTTPException 404."""
        service = UserAdminService(db_session)

        with pytest.raises(Exception) as exc_info:
            service.update_user_status(
                "customer",
                uuid4(),
                HumanStatusEnum.ACTIVE.value
            )

        assert "404" in str(exc_info.value) or "not found" in str(exc_info.value).lower()


class TestResetPassword:
    """Tests for reset_password method."""

    def test_reset_password_for_employee(self, db_session, sample_employee):
        """Happy path: reset password for an employee."""
        service = UserAdminService(db_session)
        old_hash = sample_employee.password_hash

        result = service.reset_password(
            "employee",
            sample_employee.id_employee,
            "newStrongPass99"
        )

        assert result["user_type"] == "employee"
        assert str(result["user_id"]) == str(sample_employee.id_employee)
        assert "password reset successfully" in result["message"].lower()

        db_session.refresh(sample_employee)
        assert sample_employee.password_hash != old_hash

    def test_reset_password_for_customer(self, db_session, sample_customer):
        """Happy path: reset password for a customer."""
        service = UserAdminService(db_session)
        old_hash = sample_customer.password_hash

        result = service.reset_password(
            "customer",
            sample_customer.id_customer,
            "newCustomerPass88"
        )

        assert result["user_type"] == "customer"
        db_session.refresh(sample_customer)
        assert sample_customer.password_hash != old_hash

    def test_reset_password_rejects_short_password(self, db_session, sample_employee):
        """Validation: password shorter than 6 chars raises HTTPException."""
        service = UserAdminService(db_session)

        with pytest.raises(Exception) as exc_info:
            service.reset_password(
                "employee",
                sample_employee.id_employee,
                "12345"
            )

        assert "400" in str(exc_info.value) or "must be at least 6" in str(exc_info.value).lower()

    def test_reset_password_rejects_empty_password(self, db_session, sample_employee):
        """Validation: empty password raises HTTPException."""
        service = UserAdminService(db_session)

        with pytest.raises(Exception) as exc_info:
            service.reset_password(
                "employee",
                sample_employee.id_employee,
                ""
            )

        assert "400" in str(exc_info.value) or "Password" in str(exc_info.value)

    def test_reset_password_rejects_invalid_user_type(self, db_session, sample_customer):
        """Validation: invalid user_type raises HTTPException 400."""
        service = UserAdminService(db_session)

        with pytest.raises(Exception) as exc_info:
            service.reset_password(
                "unknown",
                sample_customer.id_customer,
                "validPassword123"
            )

        assert "400" in str(exc_info.value) or "Invalid user_type" in str(exc_info.value)

    def test_reset_password_rejects_missing_employee(self, db_session):
        """Validation: missing employee ID raises HTTPException 404."""
        service = UserAdminService(db_session)

        with pytest.raises(Exception) as exc_info:
            service.reset_password(
                "employee",
                uuid4(),
                "validPassword123"
            )

        assert "404" in str(exc_info.value) or "not found" in str(exc_info.value).lower()

    def test_reset_password_rejects_missing_customer(self, db_session):
        """Validation: missing customer ID raises HTTPException 404."""
        service = UserAdminService(db_session)

        with pytest.raises(Exception) as exc_info:
            service.reset_password(
                "customer",
                uuid4(),
                "validPassword123"
            )

        assert "404" in str(exc_info.value) or "not found" in str(exc_info.value).lower()

    def test_reset_password_hash_is_valid_bcrypt(self, db_session, sample_employee):
        """Business rule: reset password produces a valid bcrypt hash."""
        import bcrypt

        service = UserAdminService(db_session)
        new_password = "validPassword456"

        service.reset_password(
            "employee",
            sample_employee.id_employee,
            new_password
        )

        db_session.refresh(sample_employee)
        # bcrypt check
        assert bcrypt.checkpw(
            new_password.encode("utf-8"),
            sample_employee.password_hash.encode("utf-8")
        )
