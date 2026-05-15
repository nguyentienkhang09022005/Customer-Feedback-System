from pydantic import BaseModel, Field
from typing import List
from uuid import UUID


class BulkUpdateStatus(BaseModel):
    ticket_ids: List[UUID]
    status: str = Field(..., description="New status for the tickets")


class BulkAssignTicket(BaseModel):
    ticket_ids: List[UUID]
    employee_id: UUID = Field(..., description="Employee ID to assign tickets to")


class BulkDelete(BaseModel):
    ticket_ids: List[UUID]