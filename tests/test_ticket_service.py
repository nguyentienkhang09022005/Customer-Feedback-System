import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4
from app.services.ticketService import TicketService
from app.schemas.ticketSchema import TicketCreate


class TestTicketService:
    def test_create_ticket_auto_assigns_when_employee_available(self):
        db = MagicMock()
        
        category_id = uuid4()
        customer_id = uuid4()
        employee_id = uuid4()
        dept_id = uuid4()
        
        mock_category = MagicMock()
        mock_category.id_category = category_id
        mock_category.id_department = dept_id
        mock_category.is_active = True
        mock_category.auto_assign = True
        
        mock_employee = MagicMock()
        mock_employee.id_employee = employee_id
        
        mock_ticket = MagicMock()
        mock_ticket.id_ticket = uuid4()
        mock_ticket.id_employee = employee_id
        
        mock_repo = MagicMock()
        mock_repo.create.return_value = mock_ticket
        mock_repo.assign_to_employee.return_value = mock_ticket
        mock_repo.update.return_value = mock_ticket
        
        mock_category_repo = MagicMock()
        mock_category_repo.get_by_id.return_value = mock_category
        
        mock_load_balancer = MagicMock()
        mock_load_balancer.get_best_employee_for_department.return_value = mock_employee
        
        service = TicketService.__new__(TicketService)
        service.db = db
        service.repo = mock_repo
        service.category_repo = mock_category_repo
        service.load_balancer = mock_load_balancer
        
        data = TicketCreate(
            title="Test Ticket",
            description="Test",
            severity="Medium",
            id_category=category_id
        )
        result = service.create_ticket(data, customer_id)
        
        mock_repo.assign_to_employee.assert_called_once()

    def test_create_ticket_stays_unassigned_when_no_employee_available(self):
        db = MagicMock()
        
        category_id = uuid4()
        customer_id = uuid4()
        dept_id = uuid4()
        
        mock_category = MagicMock()
        mock_category.id_category = category_id
        mock_category.id_department = dept_id
        mock_category.is_active = True
        mock_category.auto_assign = True
        
        mock_ticket = MagicMock()
        mock_ticket.id_ticket = uuid4()
        mock_ticket.id_employee = None
        
        mock_repo = MagicMock()
        mock_repo.create.return_value = mock_ticket
        
        mock_category_repo = MagicMock()
        mock_category_repo.get_by_id.return_value = mock_category
        
        mock_load_balancer = MagicMock()
        mock_load_balancer.get_best_employee_for_department.return_value = None
        
        service = TicketService.__new__(TicketService)
        service.db = db
        service.repo = mock_repo
        service.category_repo = mock_category_repo
        service.load_balancer = mock_load_balancer
        
        data = TicketCreate(
            title="Test Ticket",
            description="Test",
            severity="Medium",
            id_category=category_id
        )
        result = service.create_ticket(data, customer_id)
        
        assert result.id_employee is None
        mock_repo.assign_to_employee.assert_not_called()

    def test_create_ticket_no_auto_assign_when_disabled(self):
        db = MagicMock()
        
        category_id = uuid4()
        customer_id = uuid4()
        dept_id = uuid4()
        
        mock_category = MagicMock()
        mock_category.id_category = category_id
        mock_category.id_department = dept_id
        mock_category.is_active = True
        mock_category.auto_assign = False
        
        mock_ticket = MagicMock()
        mock_ticket.id_ticket = uuid4()
        mock_ticket.id_employee = None
        
        mock_repo = MagicMock()
        mock_repo.create.return_value = mock_ticket
        
        mock_category_repo = MagicMock()
        mock_category_repo.get_by_id.return_value = mock_category
        
        mock_load_balancer = MagicMock()
        
        service = TicketService.__new__(TicketService)
        service.db = db
        service.repo = mock_repo
        service.category_repo = mock_category_repo
        service.load_balancer = mock_load_balancer
        
        data = TicketCreate(
            title="Test Ticket",
            description="Test",
            severity="Medium",
            id_category=category_id
        )
        result = service.create_ticket(data, customer_id)
        
        assert result.id_employee is None
        mock_load_balancer.get_best_employee_for_department.assert_not_called()

    def test_create_ticket_raises_error_when_category_not_found(self):
        db = MagicMock()
        
        category_id = uuid4()
        customer_id = uuid4()
        
        mock_repo = MagicMock()
        mock_category_repo = MagicMock()
        mock_category_repo.get_by_id.return_value = None
        
        service = TicketService.__new__(TicketService)
        service.db = db
        service.repo = mock_repo
        service.category_repo = mock_category_repo
        
        data = TicketCreate(
            title="Test Ticket",
            description="Test",
            severity="Medium",
            id_category=category_id
        )
        with pytest.raises(Exception) as exc_info:
            service.create_ticket(data, customer_id)
            
        assert "Không tìm thấy danh mục" in str(exc_info.value)

    def test_create_ticket_raises_error_when_category_inactive(self):
        db = MagicMock()
        
        category_id = uuid4()
        customer_id = uuid4()
        
        mock_category = MagicMock()
        mock_category.id_category = category_id
        mock_category.is_active = False
        
        mock_repo = MagicMock()
        mock_category_repo = MagicMock()
        mock_category_repo.get_by_id.return_value = mock_category
        
        service = TicketService.__new__(TicketService)
        service.db = db
        service.repo = mock_repo
        service.category_repo = mock_category_repo
        
        data = TicketCreate(
            title="Test Ticket",
            description="Test",
            severity="Medium",
            id_category=category_id
        )
        with pytest.raises(Exception) as exc_info:
            service.create_ticket(data, customer_id)
            
        assert "Danh mục không hoạt động" in str(exc_info.value)
