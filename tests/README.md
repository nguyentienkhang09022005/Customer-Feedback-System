# Customer Feedback System - Test Suite

## Overview

This test suite provides comprehensive unit testing for all modules in the Customer Feedback System built with FastAPI.

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and test configuration
├── test_auth.py            # Authentication module tests
├── test_ticket.py          # Ticket management tests
├── test_chat.py            # Chat/messaging tests
├── test_appointment.py     # Appointment scheduling tests
├── test_evaluate.py        # Evaluation/CSAT tests
├── test_chatbot.py         # AI chatbot tests
├── test_load_balancer.py   # Load balancer tests
├── test_api_integration.py # API endpoint integration tests
└── README.md               # This file
```

## Running Tests

### Run All Tests
```bash
pytest tests/ -v
```

### Run Specific Test Module
```bash
pytest tests/test_auth.py -v
```

### Run with Coverage
```bash
pytest tests/ --cov=app --cov-report=html
```

### Run Specific Test Class
```bash
pytest tests/test_auth.py::TestAuthentication -v
```

## Test Modules

### 1. Authentication (`test_auth.py`)
Tests for user registration, OTP verification, login, logout, token refresh, and password management.

### 2. Ticket Management (`test_ticket.py`)
Tests for ticket creation, retrieval, update, assignment, status transitions, and deletion.

### 3. Chat/Messaging (`test_chat.py`)
Tests for message sending, chat history, read/unread tracking, and message management.

### 4. Appointments (`test_appointment.py`)
Tests for appointment creation, acceptance, rejection, cancellation, and validation.

### 5. Evaluation/CSAT (`test_evaluate.py`)
Tests for creating, retrieving, updating, and deleting customer satisfaction evaluations.

### 6. AI Chatbot (`test_chatbot.py`)
Tests for chatbot messaging, session management, context building, and cache operations.

### 7. Load Balancer (`test_load_balancer.py`)
Tests for employee selection, ticket assignment, and distributed locking.

### 8. API Integration (`test_api_integration.py`)
Tests for HTTP endpoints using FastAPI TestClient.

## Test Credentials

The test suite uses fixtures with the following test accounts:

| Role | Username | Password |
|------|----------|----------|
| Admin | khangnguyen | 321321 |
| Manager | string | 321321 |
| Employee | employee2 | 321321 |
| Customer | antran | 321321 |

## Test Configuration

- **Database**: Uses in-memory SQLite for fast, isolated testing
- **Mocking**: External services (Redis, Email, Groq) are mocked
- **Fixtures**: Shared fixtures in `conftest.py` for reusability

## Writing New Tests

### Basic Test Structure
```python
class TestModuleName:
    """Tests for module functionality."""

    def test_successful_operation(
        self,
        db_session,
        sample_fixture
    ):
        """Test description."""
        service = ServiceClass(db_session)
        result = service.method()
        assert result is not None

    def test_failure_case(
        self,
        db_session
    ):
        """Test error handling."""
        service = ServiceClass(db_session)
        with pytest.raises(Exception) as exc_info:
            service.method_that_fails()
        assert "Expected error" in str(exc_info.value)
```

### Using Fixtures
```python
def test_with_customer(
    self,
    db_session,
    sample_customer,  # Auto-provided fixture
    mock_redis_service  # Mocked external dependency
):
    """Test using customer fixture."""
    # Use sample_customer for testing
    assert sample_customer.email is not None
```

## Notes

- All tests use an in-memory SQLite database for isolation
- External services (Redis, SMTP, Groq API) are mocked
- Each test is independent and can run in parallel
- Use `db_session` fixture for database operations
- Use `mock_*` fixtures for external service mocking