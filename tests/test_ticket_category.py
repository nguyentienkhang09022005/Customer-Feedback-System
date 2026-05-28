"""
Tests for ticketCategoryService.
Covers CRUD operations, uniqueness constraints, and business rules.
"""

import pytest
from uuid import uuid4

from app.services.ticketCategoryService import TicketCategoryService
from app.schemas.ticketCategorySchema import TicketCategoryCreate, TicketCategoryUpdate

pytestmark = [pytest.mark.unit]


class TestCreateCategory:
    """Tests for creating ticket categories."""

    def test_create_category_success(self, db_session, sample_department):
        """Happy path: creating a category with valid data succeeds."""
        data = TicketCategoryCreate(
            name="Billing Support",
            description="Billing and payment support",
            id_department=sample_department.id_department,
            auto_assign=True,
        )

        category = TicketCategoryService(db_session).create_category(data)

        assert category.name == "Billing Support"
        assert category.description == "Billing and payment support"
        assert category.id_department == sample_department.id_department
        assert category.is_active is True
        assert category.auto_assign is True
        assert category.is_deleted is False
        assert category.id_category is not None

    def test_create_category_with_minimal_fields(self, db_session, sample_department):
        """Creating a category with only required fields succeeds."""
        data = TicketCategoryCreate(
            name="Technical Support",
            id_department=sample_department.id_department,
        )

        category = TicketCategoryService(db_session).create_category(data)

        assert category.name == "Technical Support"
        assert category.description is None
        assert category.is_active is True
        assert category.auto_assign is True

    def test_create_category_rejects_duplicate_name(self, db_session, sample_department):
        """Business rule: duplicate category name raises HTTPException."""
        data = TicketCategoryCreate(
            name="Billing Support",
            id_department=sample_department.id_department,
        )
        TicketCategoryService(db_session).create_category(data)

        with pytest.raises(Exception) as exc_info:
            TicketCategoryService(db_session).create_category(
                TicketCategoryCreate(
                    name="Billing Support",
                    id_department=sample_department.id_department,
                )
            )
        assert "đã tồn tại" in str(exc_info.value.detail)

    def test_create_category_allows_different_case_same_name(self, db_session, sample_department):
        """The service does not enforce case-insensitive uniqueness."""
        data = TicketCategoryCreate(
            name="Billing Support",
            id_department=sample_department.id_department,
        )
        TicketCategoryService(db_session).create_category(data)

        second = TicketCategoryService(db_session).create_category(
            TicketCategoryCreate(
                name="billing support",
                id_department=sample_department.id_department,
            )
        )
        assert second.name == "billing support"


class TestGetCategory:
    """Tests for retrieving ticket categories."""

    def test_get_all_returns_created_categories(self, db_session, sample_department):
        """get_all returns all categories including inactive."""
        data1 = TicketCategoryCreate(
            name="Category One",
            id_department=sample_department.id_department,
        )
        data2 = TicketCategoryCreate(
            name="Category Two",
            id_department=sample_department.id_department,
            is_active=False,
        )
        TicketCategoryService(db_session).create_category(data1)
        TicketCategoryService(db_session).create_category(data2)

        categories = TicketCategoryService(db_session).get_all()

        assert len(categories) == 2
        names = {cat.name for cat in categories}
        assert "Category One" in names
        assert "Category Two" in names

    def test_get_active_all_returns_only_active(self, db_session, sample_department):
        """get_active_all returns only active categories."""
        data1 = TicketCategoryCreate(
            name="Active Category",
            id_department=sample_department.id_department,
            is_active=True,
        )
        data2 = TicketCategoryCreate(
            name="Inactive Category",
            id_department=sample_department.id_department,
            is_active=False,
        )
        TicketCategoryService(db_session).create_category(data1)
        TicketCategoryService(db_session).create_category(data2)

        active_categories = TicketCategoryService(db_session).get_active_all()

        assert len(active_categories) == 1
        assert active_categories[0].name == "Active Category"

    def test_get_by_id_returns_category(self, db_session, sample_department):
        """get_by_id returns the correct category."""
        data = TicketCategoryCreate(
            name="Find Me",
            description="Should be found",
            id_department=sample_department.id_department,
        )
        created = TicketCategoryService(db_session).create_category(data)

        found = TicketCategoryService(db_session).get_by_id(created.id_category)

        assert found is not None
        assert found.id_category == created.id_category
        assert found.name == "Find Me"

    def test_get_by_id_returns_none_for_missing_category(self, db_session):
        """get_by_id returns None when category does not exist."""
        result = TicketCategoryService(db_session).get_by_id(uuid4())

        assert result is None


class TestUpdateCategory:
    """Tests for updating ticket categories."""

    def test_update_category_success(self, db_session, sample_department):
        """Happy path: updating category fields succeeds."""
        data = TicketCategoryCreate(
            name="Original Name",
            description="Original description",
            id_department=sample_department.id_department,
            auto_assign=True,
        )
        category = TicketCategoryService(db_session).create_category(data)

        update_data = TicketCategoryUpdate(
            name="Updated Name",
            description="Updated description",
            auto_assign=False,
        )
        updated = TicketCategoryService(db_session).update_category(
            category.id_category, update_data
        )

        assert updated.name == "Updated Name"
        assert updated.description == "Updated description"
        assert updated.auto_assign is False

    def test_update_category_partial_update(self, db_session, sample_department):
        """Updating some fields preserves others."""
        data = TicketCategoryCreate(
            name="Keep Me",
            description="Keep this too",
            id_department=sample_department.id_department,
        )
        category = TicketCategoryService(db_session).create_category(data)

        update_data = TicketCategoryUpdate(description="Only this changes")
        updated = TicketCategoryService(db_session).update_category(
            category.id_category, update_data
        )

        assert updated.name == "Keep Me"
        assert updated.description == "Only this changes"

    def test_update_category_to_existing_name_succeeds(self, db_session, sample_department):
        """The service allows updating to a different case variant of existing name."""
        data1 = TicketCategoryCreate(
            name="Category A",
            id_department=sample_department.id_department,
        )
        data2 = TicketCategoryCreate(
            name="Category B",
            id_department=sample_department.id_department,
        )
        cat_b = TicketCategoryService(db_session).create_category(data1)
        TicketCategoryService(db_session).create_category(data2)

        update_data = TicketCategoryUpdate(name="CATEGORY A")
        updated = TicketCategoryService(db_session).update_category(
            cat_b.id_category, update_data
        )
        assert updated.name == "CATEGORY A"

    def test_update_category_allows_same_name(self, db_session, sample_department):
        """Business rule: updating with current name succeeds."""
        data = TicketCategoryCreate(
            name="Same Name",
            id_department=sample_department.id_department,
        )
        category = TicketCategoryService(db_session).create_category(data)

        update_data = TicketCategoryUpdate(name="Same Name")
        updated = TicketCategoryService(db_session).update_category(
            category.id_category, update_data
        )

        assert updated.name == "Same Name"

    def test_update_category_not_found(self, db_session):
        """Updating non-existent category raises HTTPException."""
        update_data = TicketCategoryUpdate(name="Should Fail")
        with pytest.raises(Exception) as exc_info:
            TicketCategoryService(db_session).update_category(uuid4(), update_data)
        assert "Không tìm thấy" in str(exc_info.value.detail)


class TestDeleteCategory:
    """Tests for deleting ticket categories."""

    def test_delete_category_success(self, db_session, sample_department):
        """Soft delete marks category as deleted."""
        data = TicketCategoryCreate(
            name="To Be Deleted",
            id_department=sample_department.id_department,
        )
        category = TicketCategoryService(db_session).create_category(data)

        TicketCategoryService(db_session).delete_category(category.id_category)

        db_session.refresh(category)
        assert category.is_deleted is True
        assert category.deleted_at is not None

    def test_delete_category_not_found(self, db_session):
        """Deleting non-existent category raises HTTPException."""
        with pytest.raises(Exception) as exc_info:
            TicketCategoryService(db_session).delete_category(uuid4())
        assert "Không tìm thấy" in str(exc_info.value.detail)

    def test_deleted_category_not_in_active_list(self, db_session, sample_department):
        """Deleted category does not appear in active list."""
        data = TicketCategoryCreate(
            name="Will Be Deleted",
            id_department=sample_department.id_department,
        )
        category = TicketCategoryService(db_session).create_category(data)

        TicketCategoryService(db_session).delete_category(category.id_category)

        active_categories = TicketCategoryService(db_session).get_active_all()
        active_names = {cat.name for cat in active_categories}
        assert "Will Be Deleted" not in active_names
