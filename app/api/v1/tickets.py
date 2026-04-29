from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.services.ticketService import TicketService
from app.schemas.ticketSchema import (
    TicketOut,
    TicketAssign,
    TicketResolve,
    TicketClose,
    TicketReopen,
    TicketListOut,
    TicketFromTemplateCreate,
    TicketCustomerUpdate,
)
from app.core.response import APIResponse
from app.api.dependencies import get_db, get_current_user, get_current_employee, get_current_customer, get_current_manager, get_current_admin
from app.models.human import Human, Customer, Employee
from app.models.ticket import Ticket

router = APIRouter(prefix="/tickets", tags=["Ticket Management"])


def _build_meta(items: list) -> dict:
    total = len(items)
    return {
        "page": 1,
        "limit": total,
        "total": total,
        "total_pages": 1,
        "has_next": False,
        "has_prev": False
    }


@router.post("/from-template", response_model=APIResponse[TicketOut])
def create_ticket_from_template(
    data: TicketFromTemplateCreate,
    current_user: Human = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    try:
        customer = db.query(Customer).filter(Customer.id == current_user.id).first()
        ticket = TicketService(db).create_ticket_from_template(data, customer.id_customer)
        return APIResponse(status=True, code=201, message="Tạo ticket từ template thành công", data=ticket)
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)


@router.get("/user", response_model=APIResponse[TicketListOut])
def get_customer_tickets(
    current_user: Human = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    tickets = TicketService(db).get_tickets_by_customer(current_user.id)
    return APIResponse(status=True, code=200, message="Thành công", data={"items": tickets, "meta": _build_meta(tickets)})


@router.get("/user/closed", response_model=APIResponse[TicketListOut])
def get_customer_closed_tickets(
    current_user: Human = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    tickets = TicketService(db).get_tickets_by_customer(current_user.id, include_closed=True)
    closed = [t for t in tickets if t.status == "Closed"]
    return APIResponse(status=True, code=200, message="Thành công", data={"items": closed, "meta": _build_meta(closed)})


@router.get("/unassigned", response_model=APIResponse[TicketListOut])
def get_unassigned_tickets(
    current_user: Human = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    tickets = TicketService(db).get_unassigned_tickets()
    return APIResponse(status=True, code=200, message="Thành công", data={"items": tickets, "meta": _build_meta(tickets)})


@router.get("/department/{dept_id}", response_model=APIResponse[TicketListOut])
def get_tickets_by_department(
    dept_id: UUID,
    current_user: Human = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    tickets = TicketService(db).get_tickets_by_department(dept_id)
    return APIResponse(status=True, code=200, message="Thành công", data={"items": tickets, "meta": _build_meta(tickets)})


@router.get("/employee-tickets", response_model=APIResponse[TicketListOut])
def get_employee_tickets(
    current_user: Human = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    tickets = TicketService(db).get_tickets_by_employee(current_user.id)
    return APIResponse(status=True, code=200, message="Thành công", data={"items": tickets, "meta": _build_meta(tickets)})


@router.get("/employee-tickets/closed", response_model=APIResponse[TicketListOut])
def get_employee_closed_tickets(
    current_user: Human = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    tickets = TicketService(db).get_tickets_by_employee(current_user.id, include_closed=True)
    closed = [t for t in tickets if t.status == "Closed"]
    return APIResponse(status=True, code=200, message="Thành công", data={"items": closed, "meta": _build_meta(closed)})


@router.get("/all", response_model=APIResponse[TicketListOut])
def get_all_tickets(
    current_user: Human = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    tickets = TicketService(db).get_all_tickets()
    return APIResponse(status=True, code=200, message="Thành công", data={"items": tickets, "meta": _build_meta(tickets)})


@router.get("/{ticket_id}", response_model=APIResponse[TicketOut])
def get_ticket(ticket_id: UUID, current_user: Human = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        service = TicketService(db)
        ticket = service.get_ticket_by_id(ticket_id)
        
        if current_user.type == 'customer' and ticket.id_customer != current_user.id:
            return APIResponse(status=False, code=403, message="Bạn không có quyền truy cập ticket này!")
        
        return APIResponse(status=True, code=200, message="Thành công", data=ticket)
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)


@router.patch("/{ticket_id}/customer-update", response_model=APIResponse[TicketOut])
def customer_update_ticket(
    ticket_id: UUID,
    data: TicketCustomerUpdate,
    current_user: Human = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    try:
        customer = db.query(Customer).filter(Customer.id == current_user.id).first()
        ticket = TicketService(db).update_ticket_customer(ticket_id, data, customer.id_customer)
        return APIResponse(status=True, code=200, message="Cập nhật thành công", data=ticket)
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)


@router.patch("/{ticket_id}", response_model=APIResponse[TicketOut], dependencies=[Depends(get_current_employee)])
def update_ticket(ticket_id: UUID, data: dict, db: Session = Depends(get_db)):
    from app.schemas.ticketSchema import TicketUpdate
    try:
        from pydantic import BaseModel
        update_data = TicketUpdate(**data) if data else TicketUpdate()
        ticket = TicketService(db).update_ticket(ticket_id, update_data, actor_type="employee")
        return APIResponse(status=True, code=200, message="Cập nhật thành công", data=ticket)
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)


@router.delete("/{ticket_id}", response_model=APIResponse, dependencies=[Depends(get_current_employee)])
def delete_ticket(ticket_id: UUID, db: Session = Depends(get_db)):
    try:
        TicketService(db).delete_ticket(ticket_id)
        return APIResponse(status=True, code=200, message="Xóa ticket thành công")
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)


@router.post("/{ticket_id}/assign", response_model=APIResponse[TicketOut], dependencies=[Depends(get_current_employee)])
def assign_ticket(ticket_id: UUID, data: TicketAssign, db: Session = Depends(get_db)):
    try:
        ticket = TicketService(db).assign_ticket(ticket_id, data)
        return APIResponse(status=True, code=200, message="Giao ticket thành công", data=ticket)
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)


@router.post("/{ticket_id}/resolve", response_model=APIResponse[TicketOut], dependencies=[Depends(get_current_employee)])
def resolve_ticket_endpoint(ticket_id: UUID, data: TicketResolve, db: Session = Depends(get_db)):
    try:
        ticket = TicketService(db).resolve_ticket(ticket_id, data.resolution_note)
        return APIResponse(status=True, code=200, message="Giải quyết ticket thành công", data=ticket)
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)


@router.post("/{ticket_id}/close", response_model=APIResponse[TicketOut])
def close_ticket_endpoint(
    ticket_id: UUID, 
    data: TicketClose, 
    current_user: Human = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    try:
        if current_user.type == "customer":
            ticket = db.query(Ticket).filter(Ticket.id_ticket == ticket_id).first()
            if not ticket or ticket.id_customer != current_user.id:
                return APIResponse(status=False, code=403, message="Bạn không có quyền đóng ticket này!")
        
        ticket = TicketService(db).close_ticket(ticket_id, data.reason, current_user.id, current_user.type)
        return APIResponse(status=True, code=200, message="Đóng ticket thành công", data=ticket)
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)


@router.post("/{ticket_id}/reopen", response_model=APIResponse[TicketOut])
def reopen_ticket_endpoint(
    ticket_id: UUID, 
    data: TicketReopen, 
    current_user: Human = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    try:
        if current_user.type == "customer":
            ticket = db.query(Ticket).filter(Ticket.id_ticket == ticket_id).first()
            if not ticket or ticket.id_customer != current_user.id:
                return APIResponse(status=False, code=403, message="Bạn không có quyền mở lại ticket này!")
        
        ticket = TicketService(db).reopen_ticket(ticket_id, data.reason, current_user.id, current_user.type)
        return APIResponse(status=True, code=200, message="Mở lại ticket thành công", data=ticket)
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)


@router.get("/manager/department/{dept_id}", response_model=APIResponse[TicketListOut])
def get_manager_department_tickets(
    dept_id: UUID,
    current_user: Employee = Depends(get_current_manager),
    db: Session = Depends(get_db)
):
    """Manager: xem tất cả ticket trong phòng ban của mình"""
    # Verify manager owns this department
    if current_user.role_name != "Admin" and current_user.id_department != dept_id:
        return APIResponse(status=False, code=403, message="Bạn chỉ có quyền xem ticket trong phòng ban của mình!")

    tickets = TicketService(db).get_tickets_by_department(dept_id)
    return APIResponse(status=True, code=200, message="Thành công", data={"items": tickets, "meta": _build_meta(tickets)})


@router.post("/manager/assign/{ticket_id}", response_model=APIResponse[TicketOut])
def manager_assign_ticket(
    ticket_id: UUID,
    data: TicketAssign,
    current_user: Employee = Depends(get_current_manager),
    db: Session = Depends(get_db)
):
    """Manager: gán ticket cho nhân viên trong phòng ban"""
    # Verify ticket belongs to manager's department
    ticket = db.query(Ticket).filter(Ticket.id_ticket == ticket_id).first()
    if not ticket:
        return APIResponse(status=False, code=404, message="Ticket không tồn tại!")

    if current_user.role_name != "Admin" and ticket.id_department != current_user.id_department:
        return APIResponse(status=False, code=403, message="Bạn chỉ có quyền gán ticket trong phòng ban của mình!")

    ticket = TicketService(db).assign_ticket(ticket_id, data)
    return APIResponse(status=True, code=200, message="Giao ticket thành công", data=ticket)