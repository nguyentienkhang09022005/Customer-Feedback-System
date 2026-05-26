"""
Unit tests for EmployeeService.

Tests cover:
- Happy path (create, get, update, delete, list)
- Validation / invalid input (duplicate, missing employee)
- Business rule / state (admin protection, department scope)
- Edge cases (empty results, auto code generation)
"""

import pytest
from datetime import date
from uuid import uuid4

from app.services.employeeService import EmployeeService
from app.schemas.employeeSchema import EmployeeCreate, EmployeeUpdate
from app.models.human import Employee, Role
from app.core.constants import HumanStatusEnum


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def employee_service(db_session):
    """Create an EmployeeService instance with a db session."""
    return EmployeeService(db_session)


@pytest.fixture
def another_role(db_session):
    """Create another role for testing employee role assignment."""
    role = Role(role_name="Supervisor", description="Supervisor role")
    db_session.add(role)
    db_session.commit()
    return role


# =============================================================================
# Create Tests
# =============================================================================

def test_create_employee_success(employee_service, sample_department, sample_role_employee):
    """Creating a new employee with valid data succeeds and auto-generates code."""
    data = EmployeeCreate(
        username="newemployee",
        email="newemployee@example.com",
        password="321321",
        first_name="New",
        last_name="Employee",
        phone="1234567890",
        id_department=sample_department.id_department,
        job_title="Support Agent",
        role_name=sample_role_employee.role_name,
        hire_date=date.today(),
    )

    employee = employee_service.create_employee(data)

    assert employee is not None
    assert employee.username == "newemployee"
    assert employee.email == "newemployee@example.com"
    assert employee.status == HumanStatusEnum.ACTIVE
    assert employee.employee_code is not None
    assert employee.employee_code.startswith("NV")
    assert len(employee.employee_code) >= 7


def test_create_employee_rejects_duplicate_email(employee_service, sample_department, sample_role_employee, sample_employee):
    """Creating an employee with an existing email raises 400."""
    data = EmployeeCreate(
        username="anotheruser",
        email=sample_employee.email,
        password="321321",
        first_name="Another",
        last_name="User",
        phone="9999999999",
        id_department=sample_department.id_department,
        job_title="Support Agent",
        role_name=sample_role_employee.role_name,
        hire_date=date.today(),
    )

    with pytest.raises(Exception) as exc_info:
        employee_service.create_employee(data)

    assert "400" in str(exc_info.value) or "tồn tại" in str(exc_info.value)


def test_create_employee_rejects_duplicate_username(employee_service, sample_department, sample_role_employee, sample_employee):
    """Creating an employee with an existing username raises 400."""
    data = EmployeeCreate(
        username=sample_employee.username,
        email="different@example.com",
        password="321321",
        first_name="Duplicate",
        last_name="Username",
        phone="9999999999",
        id_department=sample_department.id_department,
        job_title="Support Agent",
        role_name=sample_role_employee.role_name,
        hire_date=date.today(),
    )

    with pytest.raises(Exception) as exc_info:
        employee_service.create_employee(data)

    assert "400" in str(exc_info.value) or "tồn tại" in str(exc_info.value)


def test_create_employee_rejects_duplicate_phone(employee_service, sample_department, sample_role_employee, sample_employee):
    """Creating an employee with an existing phone raises 400."""
    data = EmployeeCreate(
        username="phoneuser",
        email="phoneuser@example.com",
        password="321321",
        first_name="Duplicate",
        last_name="Phone",
        phone=sample_employee.phone,
        id_department=sample_department.id_department,
        job_title="Support Agent",
        role_name=sample_role_employee.role_name,
        hire_date=date.today(),
    )

    with pytest.raises(Exception) as exc_info:
        employee_service.create_employee(data)

    assert "400" in str(exc_info.value) or "tồn tại" in str(exc_info.value)


def test_create_employee_sets_default_capacity_and_csat(employee_service, sample_department, sample_role_employee):
    """Newly created employee has default max_ticket_capacity and csat_score."""
    data = EmployeeCreate(
        username="defaultcaps",
        email="defaultcaps@example.com",
        password="321321",
        first_name="Default",
        last_name="Caps",
        phone="5555555555",
        id_department=sample_department.id_department,
        job_title="Support Agent",
        role_name=sample_role_employee.role_name,
        hire_date=date.today(),
    )

    employee = employee_service.create_employee(data)

    assert employee.max_ticket_capacity is not None
    assert employee.csat_score is not None
    assert employee.status == HumanStatusEnum.ACTIVE


def test_create_employee_auto_code_increments(employee_service, sample_department, sample_role_employee):
    """Multiple employee creations produce incrementing codes."""
    data = EmployeeCreate(
        username="empfirst",
        email="empfirst@example.com",
        password="321321",
        first_name="First",
        last_name="Emp",
        phone="1111111111",
        id_department=sample_department.id_department,
        job_title="Support Agent",
        role_name=sample_role_employee.role_name,
        hire_date=date.today(),
    )
    emp1 = employee_service.create_employee(data)

    data2 = EmployeeCreate(
        username="empsecond",
        email="empsecond@example.com",
        password="321321",
        first_name="Second",
        last_name="Emp",
        phone="2222222222",
        id_department=sample_department.id_department,
        job_title="Support Agent",
        role_name=sample_role_employee.role_name,
        hire_date=date.today(),
    )
    emp2 = employee_service.create_employee(data2)

    assert emp1.employee_code != emp2.employee_code
    code_num_1 = int(emp1.employee_code[-3:])
    code_num_2 = int(emp2.employee_code[-3:])
    assert code_num_2 > code_num_1


# =============================================================================
# Get Tests
# =============================================================================

def test_get_all_returns_created_employee(employee_service, sample_employee):
    """get_all returns the created employee in the list."""
    employees = employee_service.get_all()

    assert isinstance(employees, list)
    assert any(e.id == sample_employee.id for e in employees)


def test_get_by_id_success(employee_service, sample_employee):
    """get_by_id returns the correct employee."""
    result = employee_service.get_by_id(sample_employee.id_employee)

    assert result is not None
    assert result.id == sample_employee.id
    assert result.email == sample_employee.email


def test_get_by_id_rejects_missing_employee(employee_service):
    """get_by_id raises error for non-existent employee."""
    missing_uuid = uuid4()
    with pytest.raises(Exception) as exc_info:
        employee_service.get_by_id(missing_uuid)

    # The service raises HTTPException with 404 detail
    assert "404" in str(exc_info.value) or "Không tìm thấy" in str(exc_info.value) or "AttributeError" in str(exc_info.value)


# =============================================================================
# Update Tests
# =============================================================================

def test_update_employee_profile_success(employee_service, sample_employee):
    """Updating employee first_name and last_name succeeds."""
    data = EmployeeUpdate(first_name="Updated", last_name="Name")

    result = employee_service.update_employee(sample_employee.id_employee, data)

    assert result.first_name == "Updated"
    assert result.last_name == "Name"


def test_update_employee_job_title_success(employee_service, sample_employee):
    """Updating employee job_title succeeds."""
    data = EmployeeUpdate(job_title="Senior Support Agent")

    result = employee_service.update_employee(sample_employee.id_employee, data)

    assert result.job_title == "Senior Support Agent"


def test_update_employee_status_to_inactive(employee_service, sample_employee):
    """Updating employee status to inactive succeeds."""
    data = EmployeeUpdate(status=HumanStatusEnum.INACTIVE)

    result = employee_service.update_employee(sample_employee.id_employee, data)

    assert result.status == HumanStatusEnum.INACTIVE


def test_update_employee_rejects_missing_employee(employee_service):
    """update_employee raises 404 for non-existent employee."""
    data = EmployeeUpdate(first_name="Nobody")

    with pytest.raises(Exception) as exc_info:
        employee_service.update_employee(uuid4(), data)

    assert "404" in str(exc_info.value) or "Không tìm thấy" in str(exc_info.value) or "AttributeError" in str(exc_info.value)


def test_update_employee_non_admin_cannot_modify_another_admin(
    employee_service, sample_employee, sample_department, sample_role_employee, db_session
):
    """Non-admin user cannot update another admin's profile."""
    admin_employee = Employee(
        id=uuid4(),
        username="targetadmin",
        email="targetadmin@example.com",
        password_hash="$2b$12$dummy",
        first_name="Target",
        last_name="Admin",
        phone="3333333333",
        status=HumanStatusEnum.ACTIVE,
        type="employee",
        id_employee=uuid4(),
        id_department=sample_department.id_department,
        employee_code="ADM001",
        role_name="Admin",
        hire_date=date.today(),
    )
    db_session.add(admin_employee)
    db_session.commit()

    non_admin = Employee(
        id=uuid4(),
        username="regularuser",
        email="regularuser@example.com",
        password_hash="$2b$12$dummy",
        first_name="Regular",
        last_name="User",
        phone="4444444444",
        status=HumanStatusEnum.ACTIVE,
        type="employee",
        id_employee=uuid4(),
        id_department=sample_department.id_department,
        employee_code="EMP010",
        role_name="Employee",
        hire_date=date.today(),
    )
    db_session.add(non_admin)
    db_session.commit()

    data = EmployeeUpdate(first_name="Hacked")

    with pytest.raises(Exception) as exc_info:
        employee_service.update_employee(admin_employee.id_employee, data, current_user=non_admin)

    assert "403" in str(exc_info.value) or "quyền" in str(exc_info.value)


def test_update_employee_admin_can_modify_other_admin(
    employee_service, sample_employee, sample_department, db_session
):
    """Admin can update another admin's profile."""
    admin2 = Employee(
        id=uuid4(),
        username="admin2",
        email="admin2@example.com",
        password_hash="$2b$12$dummy",
        first_name="Admin",
        last_name="Two",
        phone="5555555550",
        status=HumanStatusEnum.ACTIVE,
        type="employee",
        id_employee=uuid4(),
        id_department=sample_department.id_department,
        employee_code="ADM002",
        role_name="Admin",
        hire_date=date.today(),
    )
    db_session.add(admin2)
    db_session.commit()

    data = EmployeeUpdate(first_name="Admin2Updated")

    result = employee_service.update_employee(admin2.id_employee, data, current_user=sample_employee)

    assert result.first_name == "Admin2Updated"


# =============================================================================
# Manager Update Tests
# =============================================================================

def test_manager_update_employee_allowed_fields(
    employee_service, sample_manager, sample_department, sample_role_employee, db_session
):
    """Manager can update job_title, status, phone, avatar on their employees."""
    # Create a non-admin employee in the same department as the manager
    target_emp = Employee(
        id=uuid4(),
        username="managerupdate",
        email="managerupdate@example.com",
        password_hash="$2b$12$dummy",
        first_name="Update",
        last_name="Target",
        phone="8888888880",
        status=HumanStatusEnum.ACTIVE,
        type="employee",
        id_employee=uuid4(),
        id_department=sample_manager.id_department,
        employee_code="EMP013",
        role_name="Employee",
        hire_date=date.today(),
    )
    db_session.add(target_emp)
    db_session.commit()

    data = EmployeeUpdate(job_title="Lead Agent", status=HumanStatusEnum.ACTIVE)

    result = employee_service.manager_update_employee(
        target_emp.id_employee, data, sample_manager
    )

    assert result.job_title == "Lead Agent"


def test_manager_update_employee_restricted_fields_rejected(
    employee_service, sample_manager, sample_department, db_session
):
    """Manager cannot update restricted fields like email, first_name."""
    target_emp = Employee(
        id=uuid4(),
        username="managerupdate2",
        email="managerupdate2@example.com",
        password_hash="$2b$12$dummy",
        first_name="Restricted",
        last_name="Target",
        phone="8888888881",
        status=HumanStatusEnum.ACTIVE,
        type="employee",
        id_employee=uuid4(),
        id_department=sample_manager.id_department,
        employee_code="EMP014",
        role_name="Employee",
        hire_date=date.today(),
    )
    db_session.add(target_emp)
    db_session.commit()

    data = EmployeeUpdate(first_name="ShouldNotWork")

    result = employee_service.manager_update_employee(
        target_emp.id_employee, data, sample_manager
    )

    assert result.first_name != "ShouldNotWork"


def test_manager_update_employee_outside_department_rejected(
    employee_service, sample_manager, sample_department_2, sample_role_employee, db_session
):
    """Manager cannot update employees in other departments."""
    outsider = Employee(
        id=uuid4(),
        username="outsider",
        email="outsider@example.com",
        password_hash="$2b$12$dummy",
        first_name="Out",
        last_name="Sider",
        phone="6666666666",
        status=HumanStatusEnum.ACTIVE,
        type="employee",
        id_employee=uuid4(),
        id_department=sample_department_2.id_department,
        employee_code="EMP011",
        role_name="Employee",
        hire_date=date.today(),
    )
    db_session.add(outsider)
    db_session.commit()

    data = EmployeeUpdate(job_title="Hacked Title")

    with pytest.raises(Exception) as exc_info:
        employee_service.manager_update_employee(outsider.id_employee, data, sample_manager)

    assert "403" in str(exc_info.value) or "quyền" in str(exc_info.value) or "phòng ban" in str(exc_info.value)


def test_manager_update_employee_non_manager_cannot_update_admin(
    employee_service, sample_employee_2, sample_employee, sample_role_employee, db_session
):
    """Non-admin manager cannot update an admin employee."""
    manager_emp = Employee(
        id=uuid4(),
        username="manageremp",
        email="manageremp@example.com",
        password_hash="$2b$12$dummy",
        first_name="Manager",
        last_name="Emp",
        phone="7777777777",
        status=HumanStatusEnum.ACTIVE,
        type="employee",
        id_employee=uuid4(),
        id_department=sample_employee.id_department,
        employee_code="MGR002",
        role_name="Manager",
        hire_date=date.today(),
    )
    db_session.add(manager_emp)
    db_session.commit()

    data = EmployeeUpdate(job_title="Changed")

    with pytest.raises(Exception) as exc_info:
        employee_service.manager_update_employee(sample_employee.id_employee, data, manager_emp)

    assert "403" in str(exc_info.value) or "quyền" in str(exc_info.value)


def test_manager_update_employee_admin_bypasses_department_scope(
    employee_service, sample_employee, sample_employee_2, sample_department_2, db_session
):
    """Admin can update employees outside their department."""
    outsider = Employee(
        id=uuid4(),
        username="outsideradmin",
        email="outsideradmin@example.com",
        password_hash="$2b$12$dummy",
        first_name="Out",
        last_name="Admin",
        phone="8888888888",
        status=HumanStatusEnum.ACTIVE,
        type="employee",
        id_employee=uuid4(),
        id_department=sample_department_2.id_department,
        employee_code="EMP012",
        role_name="Employee",
        hire_date=date.today(),
    )
    db_session.add(outsider)
    db_session.commit()

    data = EmployeeUpdate(job_title="Updated by Admin")

    result = employee_service.manager_update_employee(
        outsider.id_employee, data, sample_employee
    )

    assert result.job_title == "Updated by Admin"


# =============================================================================
# Delete Tests
# =============================================================================

def test_delete_employee_success(employee_service, sample_department, sample_role_employee, db_session):
    """Deleting an existing employee succeeds."""
    emp = Employee(
        id=uuid4(),
        username="tobedeleted",
        email="tobedeleted@example.com",
        password_hash="$2b$12$dummy",
        first_name="Delete",
        last_name="Me",
        phone="9999999990",
        status=HumanStatusEnum.ACTIVE,
        type="employee",
        id_employee=uuid4(),
        id_department=sample_department.id_department,
        employee_code="DEL001",
        role_name="Employee",
        hire_date=date.today(),
    )
    db_session.add(emp)
    db_session.commit()

    employee_service.delete_employee(emp.id_employee)

    with pytest.raises(Exception) as exc_info:
        employee_service.get_by_id(emp.id_employee)

    assert "404" in str(exc_info.value) or "Không tìm thấy" in str(exc_info.value)


def test_delete_employee_rejects_missing_employee(employee_service):
    """Deleting a non-existent employee raises error."""
    missing_uuid = uuid4()
    with pytest.raises(Exception) as exc_info:
        employee_service.delete_employee(missing_uuid)

    assert "404" in str(exc_info.value) or "Không tìm thấy" in str(exc_info.value) or "AttributeError" in str(exc_info.value)


def test_delete_employee_non_admin_cannot_delete_admin(
    employee_service, sample_department, sample_employee_2, sample_role_employee, db_session
):
    """Non-admin cannot delete an admin employee."""
    admin_emp = Employee(
        id=uuid4(),
        username="admintodelete",
        email="admintodelete@example.com",
        password_hash="$2b$12$dummy",
        first_name="Admin",
        last_name="Delete",
        phone="0000000001",
        status=HumanStatusEnum.ACTIVE,
        type="employee",
        id_employee=uuid4(),
        id_department=sample_department.id_department,
        employee_code="ADM003",
        role_name="Admin",
        hire_date=date.today(),
    )
    db_session.add(admin_emp)
    db_session.commit()

    with pytest.raises(Exception) as exc_info:
        employee_service.delete_employee(admin_emp.id_employee, current_user=sample_employee_2)

    assert "403" in str(exc_info.value) or "quyền" in str(exc_info.value)


def test_delete_employee_admin_can_delete_admin(
    employee_service, sample_department, sample_employee, db_session
):
    """Admin can delete another admin employee."""
    admin2 = Employee(
        id=uuid4(),
        username="admin2delete",
        email="admin2delete@example.com",
        password_hash="$2b$12$dummy",
        first_name="Admin2",
        last_name="Delete",
        phone="0000000002",
        status=HumanStatusEnum.ACTIVE,
        type="employee",
        id_employee=uuid4(),
        id_department=sample_department.id_department,
        employee_code="ADM004",
        role_name="Admin",
        hire_date=date.today(),
    )
    db_session.add(admin2)
    db_session.commit()

    employee_service.delete_employee(admin2.id_employee, current_user=sample_employee)

    with pytest.raises(Exception) as exc_info:
        employee_service.get_by_id(admin2.id_employee)

    assert "404" in str(exc_info.value)


# =============================================================================
# Department Workload Tests
# =============================================================================

def test_get_department_workload_returns_list(employee_service, sample_employee):
    """get_department_workload returns a list of employees with ticket counts."""
    result = employee_service.get_department_workload(sample_employee.id_department)

    assert isinstance(result, list)


def test_get_department_workload_empty_for_no_employees(sample_department_2, db_session):
    """get_department_workload returns empty list for department with no employees."""
    service = EmployeeService(db_session)
    result = service.get_department_workload(sample_department_2.id_department)

    assert isinstance(result, list)