"""
Tests for ticketTemplateService.
Covers CRUD operations, versioning, validation, and business rules.
"""

import pytest
from uuid import uuid4

from app.services.ticketTemplateService import TicketTemplateService
from app.schemas.ticketCategorySchema import TicketTemplateCreate, TicketTemplateUpdate


class TestCreateTemplate:
    """Tests for creating ticket templates."""

    def test_create_template_success(self, db_session, sample_ticket_category, sample_employee):
        """Happy path: creating a template with valid data succeeds."""
        data = TicketTemplateCreate(
            name="Bug Report Template",
            description="Template for bug reports",
            id_category=sample_ticket_category.id_category,
            fields_config={
                "fields": [
                    {"name": "steps_to_reproduce", "type": "text", "required": True},
                    {"name": "severity", "type": "select", "options": ["Low", "High"]},
                ]
            },
        )

        template = TicketTemplateService(db_session).create_template(
            data, author_id=sample_employee.id_employee
        )

        assert template.name == "Bug Report Template"
        assert template.description == "Template for bug reports"
        assert template.id_category == sample_ticket_category.id_category
        assert template.version == 1
        assert template.is_active is True
        assert template.is_deleted is False
        assert template.id_author == sample_employee.id_employee
        assert "fields" in template.fields_config

    def test_create_template_without_category(self, db_session):
        """Creating a template without category succeeds."""
        data = TicketTemplateCreate(
            name="General Template",
            description="General purpose template",
            id_category=None,
            fields_config={
                "fields": [
                    {"name": "description", "type": "textarea", "required": True},
                ]
            },
        )

        template = TicketTemplateService(db_session).create_template(data)

        assert template.name == "General Template"
        assert template.id_category is None

    def test_create_template_rejects_invalid_category(self, db_session):
        """Creating with non-existent category raises HTTPException."""
        data = TicketTemplateCreate(
            name="Broken Template",
            id_category=uuid4(),
            fields_config={"fields": []},
        )

        with pytest.raises(Exception) as exc_info:
            TicketTemplateService(db_session).create_template(data)
        assert "Không tìm thấy danh mục" in str(exc_info.value.detail)

    def test_create_template_rejects_deleted_category(self, db_session, sample_ticket_category, sample_employee):
        """Creating template for deleted category raises HTTPException."""
        # Soft delete the category via service
        from app.services.ticketCategoryService import TicketCategoryService
        from app.schemas.ticketCategorySchema import TicketCategoryCreate

        cat_data = TicketCategoryCreate(
            name="Will Delete",
            id_department=sample_ticket_category.id_department,
        )
        cat_service = TicketCategoryService(db_session)
        cat = cat_service.create_category(cat_data)
        cat_service.delete_category(cat.id_category)

        template_data = TicketTemplateCreate(
            name="Should Fail",
            id_category=cat.id_category,
            fields_config={"fields": []},
        )

        with pytest.raises(Exception) as exc_info:
            TicketTemplateService(db_session).create_template(
                template_data, author_id=sample_employee.id_employee
            )
        # Category not found in active records (soft-deleted)
        assert "Không tìm thấy" in str(exc_info.value.detail)

    def test_create_template_default_is_active(self, db_session):
        """New template is active by default."""
        data = TicketTemplateCreate(
            name="Default Active",
            fields_config={"fields": []},
        )

        template = TicketTemplateService(db_session).create_template(data)

        assert template.is_active is True


class TestGetTemplate:
    """Tests for retrieving ticket templates."""

    def test_get_template_returns_latest_by_default(self, db_session, sample_ticket_template):
        """get_template returns latest version when no version specified."""
        result = TicketTemplateService(db_session).get_template(
            sample_ticket_template.id_template
        )

        assert result.id_template == sample_ticket_template.id_template

    def test_get_template_by_specific_version(self, db_session, sample_ticket_template):
        """get_template returns exact version when specified."""
        result = TicketTemplateService(db_session).get_template(
            sample_ticket_template.id_template,
            version=sample_ticket_template.version,
        )

        assert result is not None
        assert result.version == sample_ticket_template.version

    def test_get_template_returns_none_for_missing(self, db_session):
        """get_template returns None for non-existent template."""
        result = TicketTemplateService(db_session).get_template(uuid4())

        assert result is None

    def test_get_templates_by_category(self, db_session, sample_ticket_category):
        """get_templates_by_category returns only matching category."""
        # Create two categories and templates
        from app.services.ticketCategoryService import TicketCategoryService
        from app.schemas.ticketCategorySchema import TicketCategoryCreate

        cat_data = TicketCategoryCreate(
            name="Another Category",
            id_department=sample_ticket_category.id_department,
        )
        cat2 = TicketCategoryService(db_session).create_category(cat_data)

        data1 = TicketTemplateCreate(
            name="Template for Cat1",
            id_category=sample_ticket_category.id_category,
            fields_config={"fields": []},
        )
        data2 = TicketTemplateCreate(
            name="Template for Cat2",
            id_category=cat2.id_category,
            fields_config={"fields": []},
        )
        TicketTemplateService(db_session).create_template(data1)
        TicketTemplateService(db_session).create_template(data2)

        templates = TicketTemplateService(db_session).get_templates_by_category(
            sample_ticket_category.id_category
        )

        assert len(templates) == 1
        assert templates[0].name == "Template for Cat1"

    def test_get_all_templates_returns_non_deleted(self, db_session, sample_ticket_template):
        """get_all_templates returns all non-deleted templates, regardless of is_active."""
        # Create an inactive template
        inactive_data = TicketTemplateCreate(
            name="Inactive Template",
            id_category=sample_ticket_template.id_category,
            is_active=False,
            fields_config={"fields": []},
        )
        TicketTemplateService(db_session).create_template(inactive_data)

        all_templates = TicketTemplateService(db_session).get_all_templates()

        names = {t.name for t in all_templates}
        # Service returns all non-deleted, is_active filtering is caller's responsibility
        assert "Inactive Template" in names

    def test_get_all_versions(self, db_session, sample_ticket_template):
        """get_all_versions returns all versions of a template."""
        # Update to create a new version
        update_data = TicketTemplateUpdate(
            fields_config={
                "fields": [
                    {"name": "new_field", "type": "text"},
                ]
            }
        )
        TicketTemplateService(db_session).update_template(
            sample_ticket_template.id_template, update_data
        )

        versions = TicketTemplateService(db_session).get_all_versions(
            sample_ticket_template.id_template
        )

        assert len(versions) == 2
        version_nums = {v.version for v in versions}
        assert version_nums == {1, 2}


class TestUpdateTemplate:
    """Tests for updating ticket templates."""

    def test_update_template_success_no_version_change(self, db_session, sample_ticket_template):
        """Updating only name/description/active status does not create new version."""
        update_data = TicketTemplateUpdate(
            name="Updated Template Name",
            description="Updated description",
        )

        updated = TicketTemplateService(db_session).update_template(
            sample_ticket_template.id_template, update_data
        )

        assert updated.name == "Updated Template Name"
        assert updated.description == "Updated description"
        assert updated.version == sample_ticket_template.version

    def test_update_template_with_fields_config_creates_new_version(
        self, db_session, sample_ticket_template
    ):
        """Updating fields_config creates a new version."""
        original_version = sample_ticket_template.version
        update_data = TicketTemplateUpdate(
            fields_config={
                "fields": [
                    {"name": "new_field", "type": "text"},
                ]
            }
        )

        updated = TicketTemplateService(db_session).update_template(
            sample_ticket_template.id_template, update_data
        )

        assert updated.version == original_version + 1
        assert "fields" in updated.fields_config

    def test_update_template_deactivates_previous_version(
        self, db_session, sample_ticket_template
    ):
        """When new version is created, previous version becomes inactive."""
        update_data = TicketTemplateUpdate(
            fields_config={
                "fields": [
                    {"name": "new_field", "type": "text"},
                ]
            }
        )
        TicketTemplateService(db_session).update_template(
            sample_ticket_template.id_template, update_data
        )

        db_session.refresh(sample_ticket_template)

        assert sample_ticket_template.is_active is False

    def test_update_deleted_template_rejects_operation(self, db_session, sample_ticket_template):
        """Updating a deleted template raises HTTPException."""
        # Soft delete via service call
        TicketTemplateService(db_session).delete_template(
            sample_ticket_template.id_template
        )

        update_data = TicketTemplateUpdate(name="Should Fail")

        with pytest.raises(Exception) as exc_info:
            TicketTemplateService(db_session).update_template(
                sample_ticket_template.id_template, update_data
            )
        # Soft-deleted template is not found in active queries
        assert "Không tìm thấy" in str(exc_info.value.detail)

    def test_update_template_not_found_returns_404(self, db_session):
        """Updating non-existent template raises HTTPException."""
        update_data = TicketTemplateUpdate(name="Should Fail")

        with pytest.raises(Exception) as exc_info:
            TicketTemplateService(db_session).update_template(uuid4(), update_data)
        assert "Không tìm thấy template" in str(exc_info.value.detail)


class TestDeleteTemplate:
    def test_delete_template_success(self, db_session, sample_ticket_template):
        """Soft delete marks all versions as deleted."""
        template_id = sample_ticket_template.id_template

        TicketTemplateService(db_session).delete_template(template_id)

        db_session.refresh(sample_ticket_template)
        assert sample_ticket_template.is_deleted is True

    def test_delete_template_not_found(self, db_session):
        """Deleting non-existent template raises HTTPException."""
        with pytest.raises(Exception) as exc_info:
            TicketTemplateService(db_session).delete_template(uuid4())
        assert "Không tìm thấy template" in str(exc_info.value.detail)


class TestActivateTemplate:
    """Tests for activating templates."""

    def test_activate_template_success(self, db_session, sample_ticket_template):
        """Activating a template sets is_active to True."""
        # First deactivate
        sample_ticket_template.is_active = False
        db_session.commit()

        activated = TicketTemplateService(db_session).activate_template(
            sample_ticket_template.id_template
        )

        assert activated.is_active is True

    def test_activate_template_not_found(self, db_session):
        """Activating non-existent template raises HTTPException."""
        with pytest.raises(Exception) as exc_info:
            TicketTemplateService(db_session).activate_template(uuid4())
        assert "Không tìm thấy template" in str(exc_info.value.detail)


class TestValidateFieldsConfig:
    """Tests for fields_config validation."""

    def test_validate_fields_config_valid(self, db_session):
        """Valid fields_config returns True."""
        fields_config = {
            "fields": [
                {"name": "email", "type": "email"},
                {"name": "description", "type": "textarea"},
                {"name": "priority", "type": "select", "options": ["Low", "High"]},
            ]
        }

        result = TicketTemplateService(db_session).validate_fields_config(fields_config)

        assert result is True

    def test_validate_fields_config_missing_fields_key(self, db_session):
        """fields_config without 'fields' key returns False."""
        fields_config = {"severity": "High"}

        result = TicketTemplateService(db_session).validate_fields_config(fields_config)

        assert result is False

    def test_validate_fields_config_missing_field_name(self, db_session):
        """Field without 'name' returns False."""
        fields_config = {
            "fields": [
                {"type": "text"},
            ]
        }

        result = TicketTemplateService(db_session).validate_fields_config(fields_config)

        assert result is False

    def test_validate_fields_config_missing_field_type(self, db_session):
        """Field without 'type' returns False."""
        fields_config = {
            "fields": [
                {"name": "field1"},
            ]
        }

        result = TicketTemplateService(db_session).validate_fields_config(fields_config)

        assert result is False

    def test_validate_fields_config_unsupported_type(self, db_session):
        """Field with unsupported type returns False."""
        fields_config = {
            "fields": [
                {"name": "field1", "type": "unsupported_type"},
            ]
        }

        result = TicketTemplateService(db_session).validate_fields_config(fields_config)

        assert result is False

    def test_validate_fields_config_empty_fields(self, db_session):
        """Empty fields list is valid."""
        fields_config = {"fields": []}

        result = TicketTemplateService(db_session).validate_fields_config(fields_config)

        assert result is True
