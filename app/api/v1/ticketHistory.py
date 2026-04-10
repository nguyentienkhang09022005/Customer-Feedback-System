from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.services.ticketHistoryService import TicketHistoryService
from app.schemas.ticketHistorySchema import TicketHistoryListOut
from app.core.response import APIResponse
from app.api.dependencies import get_db, get_current_employee, get_current_user
from app.models.human import Human

router = APIRouter(prefix="/tickets/{ticket_id}/history", tags=["Ticket History"])


@router.get("", response_model=APIResponse[TicketHistoryListOut])
def get_ticket_history(
    ticket_id: UUID,
    current_user: Human = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lấy lịch sử của ticket - employee và customer đều xem được"""
    try:
        # Authorization: customer can only view history of their own tickets
        if current_user.type == "customer":
            from app.models.ticket import Ticket
            ticket = db.query(Ticket).filter(Ticket.id_ticket == ticket_id).first()
            if not ticket or ticket.id_customer != current_user.id:
                return APIResponse(
                    status=False, 
                    code=403, 
                    message="Bạn không có quyền xem lịch sử ticket này!"
                )
        
        histories = TicketHistoryService(db).get_ticket_history_with_actor_names(ticket_id)
        
        return APIResponse(
            status=True,
            code=200,
            message="Thành công",
            data=TicketHistoryListOut(items=histories, total=len(histories))
        )
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)
