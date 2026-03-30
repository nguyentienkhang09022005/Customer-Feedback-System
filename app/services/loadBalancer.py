from sqlalchemy.orm import Session
from app.repositories.employeeRepository import EmployeeRepository
from app.repositories.ticketRepository import TicketRepository
from app.models.human import Employee
from typing import Optional
from contextlib import contextmanager
import uuid
import redis
from app.core.config import settings


class LoadBalancer:
    def __init__(self, db: Session):
        self.db = db
        self.employee_repo = EmployeeRepository(db)
        self.ticket_repo = TicketRepository(db)
        # Redis connection for distributed lock
        self._redis_client = None
    
    @property
    def redis_client(self) -> redis.Redis:
        """Lazy initialization of Redis client"""
        if self._redis_client is None:
            self._redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
        return self._redis_client
    
    @contextmanager
    def _acquire_department_lock(self, dept_id: uuid.UUID, timeout: int = 10):
        """Acquire a distributed lock for department assignment"""
        lock_key = f"lock:dept_assignment:{dept_id}"
        lock = self.redis_client.lock(lock_key, timeout=timeout)
        acquired = lock.acquire(blocking=True, blocking_timeout=5)
        try:
            yield acquired
        finally:
            if acquired:
                try:
                    lock.release()
                except redis.redis.exceptions.LockError:
                    # Lock may have expired or already released
                    pass
    
    def get_best_employee_for_department(self, dept_id: uuid.UUID) -> Optional[Employee]:
        """Get best employee for department (read-only, no lock)"""
        results = self.employee_repo.get_available_employees_with_ticket_counts(dept_id)
        
        if not results:
            return None
        
        best_employee = None
        best_csat = -1
        
        for emp, ticket_count in results:
            if ticket_count < emp.max_ticket_capacity:
                if emp.csat_score > best_csat:
                    best_csat = emp.csat_score
                    best_employee = emp
        
        return best_employee
    
    def assign_ticket_with_lock(self, ticket_id: uuid.UUID, dept_id: uuid.UUID) -> Optional[Employee]:
        """Assign a ticket to best employee with distributed lock to prevent race conditions"""
        with self._acquire_department_lock(dept_id) as acquired:
            if not acquired:
                # Could not acquire lock - return None due to contention
                # Caller should handle retry or failure
                return None
            
            # Re-check employee counts while holding lock
            results = self.employee_repo.get_available_employees_with_ticket_counts(dept_id)
            
            best_employee = None
            best_csat = -1
            
            for emp, ticket_count in results:
                if ticket_count < emp.max_ticket_capacity:
                    if emp.csat_score > best_csat:
                        best_csat = emp.csat_score
                        best_employee = emp
            
            if best_employee:
                self.ticket_repo.assign_to_employee(ticket_id, best_employee.id_employee)
            
            return best_employee
