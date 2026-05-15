from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.services.admin.bulkTicketService import BulkTicketService
from app.schemas.admin.ticketBulk import BulkUpdateStatus, BulkAssignTicket, BulkDelete
from app.core.response import APIResponse
from app.api.dependencies import get_db, get_current_admin

router = APIRouter(prefix="/admin/tickets", tags=["Admin Ticket Management"])


@router.post("/bulk-status", response_model=APIResponse[dict], dependencies=[Depends(get_current_admin)])
def bulk_update_status(data: BulkUpdateStatus, db: Session = Depends(get_db)):
    try:
        result = BulkTicketService(db).bulk_update_status(data)
        return APIResponse(status=True, code=200, message="Bulk status update completed", data=result)
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)


@router.post("/bulk-assign", response_model=APIResponse[dict], dependencies=[Depends(get_current_admin)])
def bulk_assign(data: BulkAssignTicket, db: Session = Depends(get_db)):
    try:
        result = BulkTicketService(db).bulk_assign(data)
        return APIResponse(status=True, code=200, message="Bulk assign completed", data=result)
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)


@router.post("/bulk-delete", response_model=APIResponse[dict], dependencies=[Depends(get_current_admin)])
def bulk_delete(data: BulkDelete, db: Session = Depends(get_db)):
    try:
        result = BulkTicketService(db).bulk_delete(data)
        return APIResponse(status=True, code=200, message="Bulk delete completed", data=result)
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)