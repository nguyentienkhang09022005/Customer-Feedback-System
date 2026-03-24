import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4
from app.services.loadBalancer import LoadBalancer
from app.models.human import Employee


class TestLoadBalancer:
    def test_get_best_employee_returns_employee_with_highest_csat(self):
        db = MagicMock()
        load_balancer = LoadBalancer(db)
        
        dept_id = uuid4()
        
        emp1 = MagicMock(spec=Employee)
        emp1.id_employee = "emp1"
        emp1.id_department = dept_id
        emp1.csat_score = 4.5
        emp1.max_ticket_capacity = 5
        
        emp2 = MagicMock(spec=Employee)
        emp2.id_employee = "emp2"
        emp2.id_department = dept_id
        emp2.csat_score = 4.8
        emp2.max_ticket_capacity = 5
        
        with patch.object(load_balancer.employee_repo, 'get_available_employees_by_department', return_value=[emp1, emp2]):
            with patch.object(load_balancer.ticket_repo, 'get_active_ticket_count', return_value=2):
                result = load_balancer.get_best_employee_for_department(dept_id)
                
        assert result == emp2

    def test_get_best_employee_returns_none_when_no_capacity(self):
        db = MagicMock()
        load_balancer = LoadBalancer(db)
        
        dept_id = uuid4()
        
        emp1 = MagicMock(spec=Employee)
        emp1.id_employee = "emp1"
        emp1.id_department = dept_id
        emp1.csat_score = 4.5
        emp1.max_ticket_capacity = 3
        
        with patch.object(load_balancer.employee_repo, 'get_available_employees_by_department', return_value=[emp1]):
            with patch.object(load_balancer.ticket_repo, 'get_active_ticket_count', return_value=3):
                result = load_balancer.get_best_employee_for_department(dept_id)
                
        assert result is None

    def test_get_best_employee_returns_none_when_no_employees(self):
        db = MagicMock()
        load_balancer = LoadBalancer(db)
        
        dept_id = uuid4()
        
        with patch.object(load_balancer.employee_repo, 'get_available_employees_by_department', return_value=[]):
            result = load_balancer.get_best_employee_for_department(dept_id)
            
        assert result is None

    def test_get_best_employee_skips_employee_over_capacity(self):
        db = MagicMock()
        load_balancer = LoadBalancer(db)
        
        dept_id = uuid4()
        
        emp1 = MagicMock(spec=Employee)
        emp1.id_employee = "emp1"
        emp1.id_department = dept_id
        emp1.csat_score = 4.5
        emp1.max_ticket_capacity = 3
        
        emp2 = MagicMock(spec=Employee)
        emp2.id_employee = "emp2"
        emp2.id_department = dept_id
        emp2.csat_score = 4.0
        emp2.max_ticket_capacity = 5
        
        with patch.object(load_balancer.employee_repo, 'get_available_employees_by_department', return_value=[emp1, emp2]):
            with patch.object(load_balancer.ticket_repo, 'get_active_ticket_count', side_effect=[3, 1]):
                result = load_balancer.get_best_employee_for_department(dept_id)
                
        assert result == emp2
