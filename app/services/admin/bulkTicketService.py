from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.repositories.ticketRepository import TicketRepository
from app.schemas.admin.ticketBulk import BulkUpdateStatus, BulkAssignTicket, BulkDelete
from app.core.constants import TicketStatusConstants
from typing import List
from uuid import UUID
from datetime import datetime


class BulkTicketService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = TicketRepository(db)

    def bulk_update_status(self, data: BulkUpdateStatus) -> dict:
        if data.status not in TicketStatusConstants.VALID_STATUSES:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {TicketStatusConstants.VALID_STATUSES}")

        updated_count = self.repo.update_status_bulk(data.ticket_ids, data.status)
        return {"updated_count": updated_count}

    def bulk_assign(self, data: BulkAssignTicket) -> dict:
        assigned_count = self.repo.assign_employee_bulk(data.ticket_ids, data.employee_id)
        return {"assigned_count": assigned_count}

    def bulk_delete(self, data: BulkDelete) -> dict:
        deleted_count = self.repo.delete_bulk(data.ticket_ids)
        return {"deleted_count": deleted_count}