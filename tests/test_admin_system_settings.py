"""
Tests for admin system settings service.
"""

import pytest

from app.services.admin.systemSettingsService import SystemSettingsService
from app.schemas.admin.systemSettings import SystemSettingsUpdate


class TestGetSettings:
    """Tests for get_settings method."""

    def test_get_settings_returns_existing_settings(self, db_session):
        """Happy path: returns existing default settings."""
        service = SystemSettingsService(db_session)

        settings = service.get_settings()

        assert settings is not None
        assert settings.id == SystemSettingsService.DEFAULT_SETTINGS_ID

    def test_get_settings_creates_default_if_not_exists(self, db_session):
        """Business rule: get_settings auto-creates default settings on first access."""
        service = SystemSettingsService(db_session)

        settings = service.get_settings()

        # Should be created and persisted
        assert settings is not None
        assert settings.id == SystemSettingsService.DEFAULT_SETTINGS_ID

        # second call should return same instance (not create duplicate)
        second = service.get_settings()
        assert second.id == settings.id


class TestUpdateSettings:
    """Tests for update_settings method."""

    def test_update_settings_changes_company_name(self, db_session):
        """Happy path: update company_name."""
        service = SystemSettingsService(db_session)
        service.get_settings()  # ensure defaults exist

        updated = service.update_settings(
            SystemSettingsUpdate(company_name="Acme Corp")
        )

        assert updated.company_name == "Acme Corp"

    def test_update_settings_changes_multiple_fields(self, db_session):
        """Happy path: update multiple fields in one call."""
        service = SystemSettingsService(db_session)
        service.get_settings()  # ensure defaults exist

        updated = service.update_settings(
            SystemSettingsUpdate(
                company_name="New Company",
                support_email="support@newco.com",
                support_phone="+1-800-NEW-CORP",
                maintenance_mode=True
            )
        )

        assert updated.company_name == "New Company"
        assert updated.support_email == "support@newco.com"
        assert updated.support_phone == "+1-800-NEW-CORP"
        assert updated.maintenance_mode is True

    def test_update_settings_allows_false_maintenance_mode(self, db_session):
        """Edge case: explicitly set maintenance_mode to False."""
        service = SystemSettingsService(db_session)
        service.get_settings()

        updated = service.update_settings(
            SystemSettingsUpdate(maintenance_mode=False)
        )

        assert updated.maintenance_mode is False

    def test_update_settings_allows_none_for_optional_fields(self, db_session):
        """Edge case: setting optional string fields to None (no change)."""
        service = SystemSettingsService(db_session)
        service.get_settings()

        updated = service.update_settings(
            SystemSettingsUpdate(company_name=None, support_email=None)
        )

        # Should not raise, fields remain unchanged
        assert updated.id is not None

    def test_update_settings_allows_registration_flag(self, db_session):
        """Business rule: allow_customer_registration can be toggled."""
        service = SystemSettingsService(db_session)
        service.get_settings()

        updated = service.update_settings(
            SystemSettingsUpdate(allow_customer_registration=False)
        )

        assert updated.allow_customer_registration is False

    def test_update_settings_preserves_unmodified_fields(self, db_session):
        """Business rule: updating one field preserves others."""
        service = SystemSettingsService(db_session)
        service.update_settings(
            SystemSettingsUpdate(company_name="First Company")
        )
        service.update_settings(
            SystemSettingsUpdate(support_email="test@example.com")
        )

        # Re-read settings to verify both fields are set
        settings = service.get_settings()

        assert settings.company_name == "First Company"
        assert settings.support_email == "test@example.com"

    def test_update_settings_with_all_fields(self, db_session):
        """Edge case: update with all available fields."""
        service = SystemSettingsService(db_session)
        service.get_settings()

        updated = service.update_settings(
            SystemSettingsUpdate(
                company_name="Full Corp",
                company_logo="https://logo.example.com/logo.png",
                support_email="support@fullcorp.com",
                support_phone="+1-800-555-0100",
                maintenance_mode=True,
                allow_customer_registration=False,
                default_customer_type="Enterprise"
            )
        )

        assert updated.company_name == "Full Corp"
        assert updated.company_logo == "https://logo.example.com/logo.png"
        assert updated.support_email == "support@fullcorp.com"
        assert updated.support_phone == "+1-800-555-0100"
        assert updated.maintenance_mode is True
        assert updated.allow_customer_registration is False
        assert updated.default_customer_type == "Enterprise"


class TestGetAllSettings:
    """Tests for get_all_settings method."""

    def test_get_all_settings_returns_list(self, db_session):
        """Happy path: get_all_settings returns a list."""
        service = SystemSettingsService(db_session)
        service.get_settings()  # ensure at least one settings record

        all_settings = service.get_all_settings()

        assert isinstance(all_settings, list)
        assert len(all_settings) >= 1
        assert all(hasattr(attrs, "id") for attrs in all_settings)

    def test_get_all_settings_returns_empty_when_no_settings(self, db_session):
        """Edge case: no settings records — returns empty list."""
        # Remove any existing settings first if present
        from app.models.systemSettings import SystemSettings
        db_session.query(SystemSettings).delete()
        db_session.commit()

        all_settings = SystemSettingsService(db_session).get_all_settings()

        assert all_settings == []
