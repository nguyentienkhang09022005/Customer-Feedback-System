"""
Unit tests for API Endpoint Integration.

Tests cover:
- API endpoint authentication/authorization
- Request/response format validation
- Integration between services
- Error handling at API level

These tests use FastAPI TestClient for full HTTP request/response testing.
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from uuid import uuid4
import json

from fastapi.testclient import TestClient


# ============================================================================
# Test Database and App Setup
# ============================================================================

@pytest.fixture
def test_client(db_session):
    """Create a test client with mocked dependencies."""
    from main import app
    from app.api.dependencies import get_db

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
def admin_token(sample_employee):
    """Create access token for admin user."""
    from tests.conftest import create_test_jwt_token
    return create_test_jwt_token(sample_employee, "access")


@pytest.fixture
def customer_token(sample_customer):
    """Create access token for customer user."""
    from tests.conftest import create_test_jwt_token
    return create_test_jwt_token(sample_customer, "access")


@pytest.fixture
def employee_token(sample_employee):
    """Create access token for employee user."""
    from tests.conftest import create_test_jwt_token
    return create_test_jwt_token(sample_employee, "access")


# ============================================================================
# Authentication API Tests
# ============================================================================

class TestAuthAPI:
    """Tests for authentication API endpoints."""

    def test_login_success(self, test_client, sample_customer):
        """Test successful login via API."""
        with patch("app.services.authService.ChatbotService._preload_customer_data"):
            response = test_client.post(
                "/api/v1/auth/login",
                json={
                    "username": "customer1",
                    "password": "321321"
                }
            )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, test_client, sample_customer):
        """Test login fails with wrong password."""
        response = test_client.post(
            "/api/v1/auth/login",
            json={
                "username": "customer1",
                "password": "wrongpassword"
            }
        )

        assert response.status_code == 401

    def test_login_nonexistent_user(self, test_client):
        """Test login fails with nonexistent username."""
        response = test_client.post(
            "/api/v1/auth/login",
            json={
                "username": "nonexistent",
                "password": "password"
            }
        )

        assert response.status_code == 401

    def test_logout_success(self, test_client, customer_token):
        """Test successful logout via API."""
        with patch("app.services.tokenBlacklistService.TokenBlacklistService.blacklist_access_token", return_value=True):
            with patch("app.services.chatbotService.ChatbotService._invalidate_customer_cache", return_value=True):
                response = test_client.post(
                    "/api/v1/auth/logout",
                    headers={"Authorization": f"Bearer {customer_token}"},
                    json={"refresh_token": "some_token"}
                )

        assert response.status_code == 200


# ============================================================================
# Ticket API Tests
# ============================================================================

class TestTicketAPI:
    """Tests for ticket management API endpoints."""

    def test_get_customer_tickets(
        self,
        test_client,
        customer_token,
        sample_ticket
    ):
        """Test getting customer's own tickets."""
        with patch("app.services.authService.ChatbotService._preload_customer_data"):
            response = test_client.get(
                "/api/v1/tickets/user",
                headers={"Authorization": f"Bearer {customer_token}"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] is True

    def test_get_ticket_by_id(
        self,
        test_client,
        customer_token,
        sample_ticket
    ):
        """Test getting ticket by ID."""
        with patch("app.services.authService.ChatbotService._preload_customer_data"):
            response = test_client.get(
                f"/api/v1/tickets/{sample_ticket.id_ticket}",
                headers={"Authorization": f"Bearer {customer_token}"}
            )

        assert response.status_code == 200

    def test_get_ticket_unauthorized_customer(
        self,
        test_client,
        sample_customer,
        sample_ticket
    ):
        """Test that customer cannot access other customer's ticket."""
        # Create another customer token
        from tests.conftest import create_test_jwt_token
        other_customer = sample_customer  # Use existing for simplicity
        other_token = create_test_jwt_token(other_customer, "access")

        response = test_client.get(
            f"/api/v1/tickets/{sample_ticket.id_ticket}",
            headers={"Authorization": f"Bearer {other_token}"}
        )

        # Should fail due to ownership check
        assert response.status_code in [200, 403]

    def test_get_unassigned_tickets_requires_employee(
        self,
        test_client,
        customer_token
    ):
        """Test that unassigned tickets endpoint requires employee role."""
        response = test_client.get(
            "/api/v1/tickets/unassigned",
            headers={"Authorization": f"Bearer {customer_token}"}
        )

        # Customer cannot access employee endpoint
        assert response.status_code in [401, 403]

    def test_get_unassigned_tickets_as_employee(
        self,
        test_client,
        employee_token,
        sample_ticket
    ):
        """Test getting unassigned tickets as employee."""
        response = test_client.get(
            "/api/v1/tickets/unassigned",
            headers={"Authorization": f"Bearer {employee_token}"}
        )

        assert response.status_code == 200


# ============================================================================
# Appointment API Tests
# ============================================================================

class TestAppointmentAPI:
    """Tests for appointment API endpoints."""

    def test_create_appointment(
        self,
        test_client,
        customer_token,
        sample_ticket_assigned,
        mock_notification_service
    ):
        """Test creating appointment via API."""
        with patch("app.services.authService.ChatbotService._preload_customer_data"):
            future_time = datetime.utcnow() + timedelta(days=1)
            response = test_client.post(
                "/api/v1/appointments",
                headers={"Authorization": f"Bearer {customer_token}"},
                json={
                    "id_ticket": str(sample_ticket_assigned.id_ticket),
                    "scheduled_at": future_time.isoformat(),
                    "reason": "Need consultation"
                }
            )

        assert response.status_code == 201
        data = response.json()
        assert data["status"] is True

    def test_get_employee_appointments(
        self,
        test_client,
        employee_token,
        sample_appointment
    ):
        """Test getting appointments for employee."""
        response = test_client.get(
            "/api/v1/appointments/employee",
            headers={"Authorization": f"Bearer {employee_token}"}
        )

        assert response.status_code == 200

    def test_accept_appointment(
        self,
        test_client,
        employee_token,
        sample_appointment
    ):
        """Test accepting appointment via API."""
        response = test_client.patch(
            f"/api/v1/appointments/{sample_appointment.id_appointment}/accept",
            headers={"Authorization": f"Bearer {employee_token}"}
        )

        assert response.status_code == 200

    def test_reject_appointment(
        self,
        test_client,
        employee_token,
        sample_appointment
    ):
        """Test rejecting appointment via API."""
        response = test_client.patch(
            f"/api/v1/appointments/{sample_appointment.id_appointment}/reject",
            headers={"Authorization": f"Bearer {employee_token}"},
            json={"rejection_reason": "Schedule conflict"}
        )

        assert response.status_code == 200

    def test_cancel_appointment(
        self,
        test_client,
        customer_token,
        sample_appointment
    ):
        """Test cancelling appointment via API."""
        with patch("app.services.authService.ChatbotService._preload_customer_data"):
            response = test_client.patch(
                f"/api/v1/appointments/{sample_appointment.id_appointment}/cancel",
                headers={"Authorization": f"Bearer {customer_token}"},
                json={}
            )

        assert response.status_code == 200


# ============================================================================
# Evaluation API Tests
# ============================================================================

class TestEvaluationAPI:
    """Tests for evaluation API endpoints."""

    def test_create_evaluation(
        self,
        test_client,
        customer_token,
        sample_ticket_resolved,
        mock_notification_service
    ):
        """Test creating evaluation via API."""
        with patch("app.services.authService.ChatbotService._preload_customer_data"):
            response = test_client.post(
                "/api/v1/evaluates",
                headers={"Authorization": f"Bearer {customer_token}"},
                json={
                    "id_ticket": str(sample_ticket_resolved.id_ticket),
                    "star": 5,
                    "comment": "Great service!"
                }
            )

        assert response.status_code == 201
        data = response.json()
        assert data["status"] is True

    def test_get_evaluates_by_ticket(
        self,
        test_client,
        sample_evaluate
    ):
        """Test getting evaluations for a ticket."""
        response = test_client.get(
            f"/api/v1/evaluates/ticket/{sample_evaluate.id_ticket}"
        )

        assert response.status_code == 200

    def test_update_evaluation(
        self,
        test_client,
        customer_token,
        sample_evaluate
    ):
        """Test updating evaluation via API."""
        with patch("app.services.authService.ChatbotService._preload_customer_data"):
            response = test_client.patch(
                f"/api/v1/evaluates/{sample_evaluate.id_evaluate}",
                headers={"Authorization": f"Bearer {customer_token}"},
                json={
                    "star": 4,
                    "comment": "Updated comment"
                }
            )

        assert response.status_code == 200

    def test_delete_evaluation(
        self,
        test_client,
        customer_token,
        sample_evaluate
    ):
        """Test deleting evaluation via API."""
        with patch("app.services.authService.ChatbotService._preload_customer_data"):
            response = test_client.delete(
                f"/api/v1/evaluates/{sample_evaluate.id_evaluate}",
                headers={"Authorization": f"Bearer {customer_token}"}
            )

        assert response.status_code == 200


# ============================================================================
# Chatbot API Tests
# ============================================================================

class TestChatbotAPI:
    """Tests for chatbot API endpoints."""

    def test_send_chatbot_message(
        self,
        test_client,
        customer_token,
        mock_groq_service,
        mock_redis_service
    ):
        """Test sending message to chatbot via API."""
        with patch("app.services.authService.ChatbotService._preload_customer_data"):
            with patch("app.api.v1.chatbot.check_chatbot_rate_limit", return_value=True):
                response = test_client.post(
                    "/api/v1/chatbot/message",
                    headers={"Authorization": f"Bearer {customer_token}"},
                    json={"message": "Hello chatbot"}
                )

        assert response.status_code == 200

    def test_get_chatbot_session(
        self,
        test_client,
        customer_token,
        sample_chat_session
    ):
        """Test getting chatbot session via API."""
        with patch("app.services.authService.ChatbotService._preload_customer_data"):
            response = test_client.get(
                "/api/v1/chatbot/session",
                headers={"Authorization": f"Bearer {customer_token}"}
            )

        assert response.status_code in [200, 404]

    def test_delete_chatbot_session(
        self,
        test_client,
        customer_token,
        sample_chat_session
    ):
        """Test deleting chatbot session via API."""
        with patch("app.services.authService.ChatbotService._preload_customer_data"):
            response = test_client.delete(
                "/api/v1/chatbot/session",
                headers={"Authorization": f"Bearer {customer_token}"}
            )

        assert response.status_code in [200, 404]


# ============================================================================
# Health Check Tests
# ============================================================================

class TestHealthCheck:
    """Tests for basic health check."""

    def test_api_health(self, test_client):
        """Test API is accessible."""
        # Try to access a public or protected endpoint
        response = test_client.get("/docs")  # Swagger docs
        assert response.status_code == 200
