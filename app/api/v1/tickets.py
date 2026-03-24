from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.services.ticketService import TicketService
from app.schemas.ticketSchema import TicketCreate, TicketUpdate, TicketOut, TicketAssign
from app.core.response import APIResponse
from app.api.dependencies import get_db, get_current_user, get_current_employee, get_current_customer
from app.models.human import Human, Customer

router = APIRouter(prefix="/tickets", tags=["Ticket Management"])


@router.post("", response_model=APIResponse[TicketOut])
def create_ticket(
    data: TicketCreate,
    current_user: Human = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    try:
        customer = db.query(Customer).filter(Customer.id == current_user.id).first()
        ticket = TicketService(db).create_ticket(data, customer.id_customer)
        return APIResponse(status=True, code=201, message="Tạo ticket thành công", data=ticket)
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)


@router.get("", response_model=APIResponse[List[TicketOut]])
def get_all_tickets(
    current_user: Human = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    tickets = TicketService(db).get_all_tickets()
    return APIResponse(status=True, code=200, message="Thành công", data=tickets)


@router.get("/unassigned", response_model=APIResponse[List[TicketOut]], dependencies=[Depends(get_current_employee)])
def get_unassigned_tickets(db: Session = Depends(get_db)):
    tickets = TicketService(db).get_unassigned_tickets()
    return APIResponse(status=True, code=200, message="Thành công", data=tickets)


@router.get("/department/{department}", response_model=APIResponse[List[TicketOut]], dependencies=[Depends(get_current_employee)])
def get_tickets_by_department(department: str, db: Session = Depends(get_db)):
    tickets = TicketService(db).get_tickets_by_department(department)
    return APIResponse(status=True, code=200, message="Thành công", data=tickets)


@router.get("/my-tickets", response_model=APIResponse[List[TicketOut]], dependencies=[Depends(get_current_employee)])
def get_my_tickets(
    current_user: Human = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    tickets = TicketService(db).get_tickets_by_employee(current_user.id)
    return APIResponse(status=True, code=200, message="Thành công", data=tickets)


@router.get("/{ticket_id}", response_model=APIResponse[TicketOut])
def get_ticket(ticket_id: UUID, db: Session = Depends(get_db)):
    try:
        ticket = TicketService(db).get_ticket_by_id(ticket_id)
        return APIResponse(status=True, code=200, message="Thành công", data=ticket)
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)


@router.patch("/{ticket_id}", response_model=APIResponse[TicketOut], dependencies=[Depends(get_current_employee)])
def update_ticket(ticket_id: UUID, data: TicketUpdate, db: Session = Depends(get_db)):
    try:
        ticket = TicketService(db).update_ticket(ticket_id, data)
        return APIResponse(status=True, code=200, message="Cập nhật thành công", data=ticket)
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)


@router.post("/assign", response_model=APIResponse[TicketOut], dependencies=[Depends(get_current_employee)])
def assign_ticket(data: TicketAssign, db: Session = Depends(get_db)):
    try:
        ticket = TicketService(db).assign_ticket(data.id_employee, data)
        return APIResponse(status=True, code=200, message="Giao ticket thành công", data=ticket)
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)


@router.delete("/{ticket_id}", response_model=APIResponse, dependencies=[Depends(get_current_employee)])
def delete_ticket(ticket_id: UUID, db: Session = Depends(get_db)):
    try:
        TicketService(db).delete_ticket(ticket_id)
        return APIResponse(status=True, code=200, message="Xóa ticket thành công")
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)
