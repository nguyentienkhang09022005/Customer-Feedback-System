"""
Tests for CustomerTypeService.

Covers: create, retrieve, update, delete, duplicate detection,
and not-found scenarios for customer type management.
"""

import pytest
import uuid
from uuid import uuid4

from app.services.customerTypeService import CustomerTypeService
from app.schemas.customerTypeSchema import CustomerTypeCreate, CustomerTypeUpdate

pytestmark = [pytest.mark.unit]


class TestCustomerTypeServiceCreate:
    """Test customer type creation."""

    def test_create_customer_type_success(self, db_session):
        """Happy path: create a new customer type."""
        data = CustomerTypeCreate(
            type_name="Enterprise",
            description="Enterprise tier for large businesses",
        )
        service = CustomerTypeService(db_session)
        customer_type = service.create(data)

        assert customer_type is not None
        assert customer_type.type_name == "Enterprise"
        assert customer_type.description == "Enterprise tier for large businesses"

    def test_create_customer_type_without_description(self, db_session):
        """Edge case: description is optional."""
        data = CustomerTypeCreate(type_name="Basic")
        service = CustomerTypeService(db_session)
        customer_type = service.create(data)

        assert customer_type.type_name == "Basic"
        assert customer_type.description is None

    def test_create_customer_type_rejects_duplicate_name(self, db_session):
        """Business rule: type_name uniqueness."""
        data1 = CustomerTypeCreate(type_name="VIP", description="First VIP")
        service = CustomerTypeService(db_session)
        service.create(data1)

        data2 = CustomerTypeCreate(type_name="VIP", description="Duplicate VIP")
        with pytest.raises(Exception) as exc_info:
            service.create(data2)
        assert "đã tồn tại" in str(exc_info.value.detail)

    def test_create_customer_type_rejects_duplicate_name_same_case(self, db_session):
        """Business rule: type_name must be unique, same case."""
        data1 = CustomerTypeCreate(type_name="PremiumTier", description="First")
        service = CustomerTypeService(db_session)
        service.create(data1)

        # Same name, same case should be rejected
        data2 = CustomerTypeCreate(type_name="PremiumTier", description="Duplicate")
        with pytest.raises(Exception):
            service.create(data2)


class TestCustomerTypeServiceRetrieve:
    """Test customer type retrieval."""

    def test_get_all_returns_created_types(self, db_session):
        """Happy path: get_all includes previously created types."""
        data1 = CustomerTypeCreate(type_name="Type1")
        data2 = CustomerTypeCreate(type_name="Type2")
        service = CustomerTypeService(db_session)
        service.create(data1)
        service.create(data2)

        all_types = service.get_all()

        assert len(all_types) >= 2
        type_names = [t.type_name for t in all_types]
        assert "Type1" in type_names
        assert "Type2" in type_names

    def test_get_all_returns_empty_list_when_no_types(self, db_session):
        """Edge case: no customer types exist."""
        service = CustomerTypeService(db_session)
        all_types = service.get_all()

        assert all_types == []


class TestCustomerTypeServiceUpdate:
    """Test customer type update operations."""

    def test_update_customer_type_success(self, db_session):
        """Happy path: update description of existing type."""
        data = CustomerTypeCreate(type_name="Standard", description="Original desc")
        service = CustomerTypeService(db_session)
        created = service.create(data)

        update_data = CustomerTypeUpdate(description="Updated description")
        updated = service.update("Standard", update_data)

        assert updated.type_name == "Standard"
        assert updated.description == "Updated description"

    def test_update_customer_type_only_description(self, db_session):
        """Partial update: only description field changes, type_name stays same."""
        data = CustomerTypeCreate(type_name="Basic", description="Old desc")
        service = CustomerTypeService(db_session)
        service.create(data)

        update_data = CustomerTypeUpdate(description="New desc")
        updated = service.update("Basic", update_data)

        assert updated.type_name == "Basic"
        assert updated.description == "New desc"

    def test_update_customer_type_rejects_not_found(self, db_session):
        """Validation: update target does not exist."""
        service = CustomerTypeService(db_session)
        update_data = CustomerTypeUpdate(description="Should fail")

        with pytest.raises(Exception) as exc_info:
            service.update("NonExistentType", update_data)
        assert "Không tìm thấy" in str(exc_info.value.detail)

    def test_update_customer_type_ignores_unset_fields(self, db_session):
        """Partial update: only provided fields change."""
        data = CustomerTypeCreate(type_name="Minimal", description="Original")
        service = CustomerTypeService(db_session)
        service.create(data)

        # Update with no fields set (empty update)
        update_data = CustomerTypeUpdate()
        updated = service.update("Minimal", update_data)

        # Description should remain unchanged
        assert updated.description == "Original"


class TestCustomerTypeServiceDelete:
    """Test customer type deletion."""

    def test_delete_customer_type_success(self, db_session):
        """Happy path: delete an existing customer type."""
        data = CustomerTypeCreate(type_name="ToDelete")
        service = CustomerTypeService(db_session)
        created = service.create(data)

        service.delete("ToDelete")

        # Verify it's gone
        from app.models.human import CustomerType
        found = db_session.query(CustomerType).filter(
            CustomerType.type_name == "ToDelete"
        ).first()
        assert found is None

    def test_delete_customer_type_rejects_not_found(self, db_session):
        """Validation: delete target does not exist."""
        service = CustomerTypeService(db_session)

        with pytest.raises(Exception) as exc_info:
            service.delete("NonExistentType")
        assert "Không tìm thấy" in str(exc_info.value.detail)


class TestCustomerTypeServiceEdgeCases:
    """Edge cases and boundary conditions."""

    def test_update_customer_type_with_empty_description(self, db_session):
        """Edge case: clear description by setting empty string."""
        data = CustomerTypeCreate(type_name="HasDesc", description="Some text")
        service = CustomerTypeService(db_session)
        service.create(data)

        update_data = CustomerTypeUpdate(description="")
        updated = service.update("HasDesc", update_data)

        assert updated.description == ""

    def test_create_multiple_different_types(self, db_session):
        """Stress test: create many distinct customer types."""
        service = CustomerTypeService(db_session)
        created_types = []
        for i in range(5):
            data = CustomerTypeCreate(type_name=f"Type{i}", description=f"Desc {i}")
            created = service.create(data)
            created_types.append(created)

        all_types = service.get_all()
        assert len(all_types) >= 5

    def test_update_then_delete_customer_type(self, db_session):
        """Integration: update then delete a customer type."""
        data = CustomerTypeCreate(type_name="UpdateDelete", description="Original")
        service = CustomerTypeService(db_session)
        service.create(data)

        # Update first
        update_data = CustomerTypeUpdate(description="Updated")
        updated = service.update("UpdateDelete", update_data)
        assert updated.description == "Updated"

        # Then delete
        service.delete("UpdateDelete")

        # Verify deletion
        from app.models.human import CustomerType
        found = db_session.query(CustomerType).filter(
            CustomerType.type_name == "UpdateDelete"
        ).first()
        assert found is None