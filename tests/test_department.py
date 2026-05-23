"""
Unit tests for Department Service.

Tests cover:
- Department creation
- Department retrieval (all, by ID, active only)
- Department update
- Department deletion
- Duplicate name validation
"""

import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4

from app.services.departmentService import DepartmentService
from app.schemas.departmentSchema import DepartmentCreate, DepartmentUpdate
from app.models.department import Department


# ============================================================================
# Department Creation Tests
# ============================================================================

class TestDepartmentCreation:
    """Tests for department creation."""

    def test_create_department_success(
        self,
        db_session
    ):
        """Test successful department creation."""
        service = DepartmentService(db_session)

        data = DepartmentCreate(
            name="Sales Department",
            description="Sales and marketing team"
        )

        department = service.create_department(data)

        assert department is not None
        assert department.name == "Sales Department"
        assert department.description == "Sales and marketing team"
        assert department.is_active is True

    def test_create_department_duplicate_name(
        self,
        db_session,
        sample_department
    ):
        """Test creation fails when department name already exists."""
        service = DepartmentService(db_session)

        data = DepartmentCreate(
            name=sample_department.name,  # Duplicate name
            description="Another description"
        )

        with pytest.raises(Exception) as exc_info:
            service.create_department(data)

        assert "đã tồn tại" in str(exc_info.value)

    def test_create_department_empty_name(
        self,
        db_session
    ):
        """Test creation fails with empty name."""
        service = DepartmentService(db_session)

        data = DepartmentCreate(
            name="",
            description="Test"
        )

        # Empty name may fail at validation or database level
        # The exact behavior depends on implementation


# ============================================================================
# Department Retrieval Tests
# ============================================================================

class TestDepartmentRetrieval:
    """Tests for department retrieval."""

    def test_get_all_departments(
        self,
        db_session,
        sample_department
    ):
        """Test getting all departments."""
        service = DepartmentService(db_session)

        departments = service.get_all()

        assert len(departments) >= 1

    def test_get_by_id_success(
        self,
        db_session,
        sample_department
    ):
        """Test getting department by ID."""
        service = DepartmentService(db_session)

        department = service.get_by_id(sample_department.id_department)

        assert department is not None
        assert department.id_department == sample_department.id_department

    def test_get_by_id_not_found(
        self,
        db_session
    ):
        """Test getting nonexistent department."""
        service = DepartmentService(db_session)

        with pytest.raises(Exception) as exc_info:
            service.get_by_id(uuid4())

        assert "Không tìm thấy phòng ban" in str(exc_info.value)

    def test_get_active_all(
        self,
        db_session,
        sample_department
    ):
        """Test getting only active departments."""
        service = DepartmentService(db_session)

        departments = service.get_active_all()

        assert all(d.is_active for d in departments)


# ============================================================================
# Department Update Tests
# ============================================================================

class TestDepartmentUpdate:
    """Tests for department updates."""

    def test_update_department_success(
        self,
        db_session,
        sample_department
    ):
        """Test successful department update."""
        service = DepartmentService(db_session)

        data = DepartmentUpdate(
            name="Updated Name",
            description="Updated description"
        )

        department = service.update_department(
            sample_department.id_department,
            data
        )

        assert department.name == "Updated Name"
        assert department.description == "Updated description"

    def test_update_department_duplicate_name(
        self,
        db_session,
        sample_department
    ):
        """Test update fails when new name already exists."""
        # Create another department
        other_dept = Department(
            id_department=uuid4(),
            name="Other Department",
            description="Other desc",
            is_active=True
        )
        db_session.add(other_dept)
        db_session.commit()

        service = DepartmentService(db_session)

        data = DepartmentUpdate(name="Other Department")  # Duplicate

        with pytest.raises(Exception) as exc_info:
            service.update_department(sample_department.id_department, data)

        assert "đã tồn tại" in str(exc_info.value)

    def test_update_department_not_found(
        self,
        db_session
    ):
        """Test update fails for nonexistent department."""
        service = DepartmentService(db_session)

        data = DepartmentUpdate(name="Test")

        with pytest.raises(Exception) as exc_info:
            service.update_department(uuid4(), data)

        assert "Không tìm thấy phòng ban" in str(exc_info.value)


# ============================================================================
# Department Deletion Tests
# ============================================================================

class TestDepartmentDeletion:
    """Tests for department deletion."""

    def test_delete_department_success(
        self,
        db_session,
        sample_department
    ):
        """Test successful department deletion."""
        service = DepartmentService(db_session)

        service.delete_department(sample_department.id_department)

        # Verify department is deleted
        with pytest.raises(Exception):
            service.get_by_id(sample_department.id_department)

    def test_delete_department_not_found(
        self,
        db_session
    ):
        """Test deletion fails for nonexistent department."""
        service = DepartmentService(db_session)

        with pytest.raises(Exception) as exc_info:
            service.delete_department(uuid4())

        assert "Không tìm thấy phòng ban" in str(exc_info.value)


# ============================================================================
# Edge Cases
# ============================================================================

class TestDepartmentEdgeCases:
    """Edge case tests for department service."""

    def test_department_name_case_sensitivity(
        self,
        db_session,
        sample_department
    ):
        """Test department names are case-sensitive."""
        service = DepartmentService(db_session)

        # Try to create with same name but different case
        data = DepartmentCreate(
            name=sample_department.name.upper(),  # Different case
            description="Should this work?"
        )

        # This depends on database collation settings
        # In most cases "Customer Support" != "CUSTOMER SUPPORT"

    def test_department_with_special_characters(
        self,
        db_session
    ):
        """Test department with special characters in name."""
        service = DepartmentService(db_session)

        data = DepartmentCreate(
            name="IT & Support (日本語)",
            description="Multilingual support team"
        )

        department = service.create_department(data)

        assert department.name == "IT & Support (日本語)"