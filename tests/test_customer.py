"""
Tests for CustomerService.

Covers: create, retrieve, update, delete, filter, membership tier updates,
duplicate detection, and not-found scenarios.
"""

import pytest
import uuid
from uuid import uuid4

from app.services.customerService import CustomerService
from app.schemas.customerSchema import CustomerCreate, CustomerUpdate
from app.core.constants import MembershipTierEnum


class TestCustomerServiceCreate:
    """Test customer creation."""

    def test_create_customer_success(self, db_session, sample_customer_type):
        """Happy path: create a new customer with all required fields."""
        data = CustomerCreate(
            username="newcustomer",
            email="newcustomer@example.com",
            password="321321",
            first_name="New",
            last_name="Customer",
            phone="9998887777",
            address="123 New St",
            timezone="Asia/Ho_Chi_Minh",
            customer_type=sample_customer_type.type_name,
        )
        service = CustomerService(db_session)
        customer = service.create_customer(data)

        assert customer is not None
        assert customer.username == "newcustomer"
        assert customer.email == "newcustomer@example.com"
        assert customer.membership_tier == "Standard"
        assert customer.status == "Active"
        assert customer.customer_code is not None
        assert customer.customer_code.startswith("KH")

    def test_create_customer_generates_incremental_code(self, db_session, sample_customer_type):
        """Verify customer codes are sequential within the same year prefix."""
        data1 = CustomerCreate(
            username="firstcustomer",
            email="first@example.com",
            password="321321",
            first_name="First",
            last_name="Customer",
            phone="1111111111",
            timezone="Asia/Ho_Chi_Minh",
            customer_type=sample_customer_type.type_name,
        )
        data2 = CustomerCreate(
            username="secondcustomer",
            email="second@example.com",
            password="321321",
            first_name="Second",
            last_name="Customer",
            phone="2222222222",
            timezone="Asia/Ho_Chi_Minh",
            customer_type=sample_customer_type.type_name,
        )
        service = CustomerService(db_session)
        c1 = service.create_customer(data1)
        c2 = service.create_customer(data2)

        # Second code should be one higher than first
        num1 = int(c1.customer_code[-3:])
        num2 = int(c2.customer_code[-3:])
        assert num2 == num1 + 1

    def test_create_customer_rejects_duplicate_email(self, db_session, sample_customer_type, sample_customer):
        """Business rule: email uniqueness across all humans."""
        data = CustomerCreate(
            username="anothercustomer",
            email=sample_customer.email,  # duplicate email
            password="321321",
            first_name="Another",
            last_name="Customer",
            phone="3333333333",
            timezone="Asia/Ho_Chi_Minh",
            customer_type=sample_customer_type.type_name,
        )
        service = CustomerService(db_session)

        with pytest.raises(Exception) as exc_info:
            service.create_customer(data)
        assert "đã tồn tại" in str(exc_info.value.detail)

    def test_create_customer_rejects_duplicate_username(self, db_session, sample_customer_type, sample_customer):
        """Business rule: username uniqueness across all humans."""
        data = CustomerCreate(
            username=sample_customer.username,  # duplicate username
            email="unique_email@example.com",
            password="321321",
            first_name="Another",
            last_name="Customer",
            phone="3333333333",
            timezone="Asia/Ho_Chi_Minh",
            customer_type=sample_customer_type.type_name,
        )
        service = CustomerService(db_session)

        with pytest.raises(Exception) as exc_info:
            service.create_customer(data)
        assert "đã tồn tại" in str(exc_info.value.detail)

    def test_create_customer_rejects_duplicate_phone(self, db_session, sample_customer_type, sample_customer):
        """Business rule: phone uniqueness across all humans."""
        data = CustomerCreate(
            username="unique_username",
            email="unique_email@example.com",
            password="321321",
            first_name="Another",
            last_name="Customer",
            phone=sample_customer.phone,  # duplicate phone
            timezone="Asia/Ho_Chi_Minh",
            customer_type=sample_customer_type.type_name,
        )
        service = CustomerService(db_session)

        with pytest.raises(Exception) as exc_info:
            service.create_customer(data)
        assert "đã tồn tại" in str(exc_info.value.detail)


class TestCustomerServiceRetrieve:
    """Test customer retrieval."""

    def test_get_all_returns_created_customer(self, db_session, sample_customer_type, sample_customer):
        """Happy path: get_all includes previously created customers."""
        service = CustomerService(db_session)
        all_customers = service.get_all()

        assert len(all_customers) >= 1
        assert any(c.id_customer == sample_customer.id_customer for c in all_customers)

    def test_get_all_returns_empty_list_when_no_customers(self, db_session):
        """Edge case: no customers exist."""
        service = CustomerService(db_session)
        all_customers = service.get_all()

        assert all_customers == []


class TestCustomerServiceUpdate:
    """Test customer update operations."""

    def test_update_customer_membership_tier_success(self, db_session, sample_customer):
        """Happy path: update membership tier."""
        service = CustomerService(db_session)
        data = CustomerUpdate(membership_tier=MembershipTierEnum.GOLD)
        updated = service.update_customer(sample_customer.id_customer, data)

        assert updated.membership_tier == MembershipTierEnum.GOLD

    def test_update_customer_multiple_fields(self, db_session, sample_customer):
        """Update multiple fields in one call."""
        service = CustomerService(db_session)
        data = CustomerUpdate(
            first_name="UpdatedFirst",
            last_name="UpdatedLast",
            phone="5555555555",
        )
        updated = service.update_customer(sample_customer.id_customer, data)

        assert updated.first_name == "UpdatedFirst"
        assert updated.last_name == "UpdatedLast"
        assert updated.phone == "5555555555"

    def test_update_customer_rejects_not_found(self, db_session):
        """Validation: update target does not exist."""
        service = CustomerService(db_session)
        data = CustomerUpdate(first_name="Should Fail")
        fake_id = str(uuid4())

        with pytest.raises(Exception):
            service.update_customer(fake_id, data)

    def test_update_customer_ignores_unset_fields(self, db_session, sample_customer):
        """Partial update: only provided fields change."""
        original_first = sample_customer.first_name
        service = CustomerService(db_session)
        data = CustomerUpdate(membership_tier=MembershipTierEnum.PLATINUM)
        updated = service.update_customer(sample_customer.id_customer, data)

        assert updated.first_name == original_first
        assert updated.membership_tier == MembershipTierEnum.PLATINUM


class TestCustomerServiceDelete:
    """Test customer deletion."""

    def test_delete_customer_success(self, db_session, sample_customer):
        """Happy path: delete an existing customer."""
        service = CustomerService(db_session)
        service.delete_customer(sample_customer.id_customer)

        # Verify it's gone
        from app.models.human import Customer
        found = db_session.query(Customer).filter(
            Customer.id_customer == sample_customer.id_customer
        ).first()
        assert found is None

    def test_delete_customer_rejects_not_found(self, db_session):
        """Validation: delete target does not exist."""
        service = CustomerService(db_session)
        fake_id = str(uuid4())

        with pytest.raises(Exception):
            service.delete_customer(fake_id)


class TestCustomerServiceEdgeCases:
    """Edge cases and boundary conditions."""

    def test_update_customer_with_invalid_tier(self, db_session, sample_customer):
        """Invalid input: membership_tier accepts valid enum values only."""
        from pydantic import ValidationError
        service = CustomerService(db_session)

        # Invalid enum value should raise validation error at schema level
        with pytest.raises(ValidationError):
            CustomerUpdate(membership_tier="InvalidTier")

    def test_update_customer_status_to_pending(self, db_session, sample_customer):
        """Update customer status to a different valid status."""
        from app.core.constants import HumanStatusEnum
        service = CustomerService(db_session)
        data = CustomerUpdate(status=HumanStatusEnum.PENDING)
        updated = service.update_customer(sample_customer.id_customer, data)

        assert updated.status == HumanStatusEnum.PENDING

    def test_create_customer_with_optional_address(self, db_session, sample_customer_type):
        """Edge case: address is optional."""
        data = CustomerCreate(
            username="noaddresscustomer",
            email="noaddress@example.com",
            password="321321",
            first_name="No",
            last_name="Address",
            phone="7777777777",
            timezone="Asia/Ho_Chi_Minh",
            customer_type=sample_customer_type.type_name,
            address=None,
        )
        service = CustomerService(db_session)
        customer = service.create_customer(data)

        assert customer is not None
        assert customer.address is None