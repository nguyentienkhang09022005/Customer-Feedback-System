from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.services.ticketService import TicketService
from app.schemas.ticketSchema import TicketCreate, TicketUpdate, TicketOut, TicketAssign, TicketResolve, TicketClose, TicketReopen, TicketListOut
from app.core.response import APIResponse
from app.core.pagination import paginate
from app.api.dependencies import get_db, get_current_user, get_current_employee, get_current_customer
from app.models.human import Human, Customer
from app.models.ticket import Ticket, TicketCategory

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


@router.get("/user", response_model=APIResponse[TicketListOut])
def get_all_tickets(
    current_user: Human = Depends(get_current_customer),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    query = (
        db.query(Ticket, TicketCategory.name.label('category_name'))
        .outerjoin(TicketCategory, Ticket.id_category == TicketCategory.id_category)
        .filter(
            Ticket.id_customer == current_user.id,
            Ticket.status != "Closed"
        )
        .order_by(Ticket.created_at.desc())
    )
    
    # Get total count efficiently
    total = query.count()
    total_pages = (total + limit - 1) // limit if total > 0 else 1
    
    # Apply database-level pagination with limit/offset
    skip = (page - 1) * limit
    results = query.offset(skip).limit(limit).all()
    
    tickets = []
    for ticket, category_name in results:
        ticket_dict = {
            "id_ticket": ticket.id_ticket,
            "title": ticket.title,
            "description": ticket.description,
            "status": ticket.status,
            "severity": ticket.severity,
            "expired_date": ticket.expired_date,
            "id_category": ticket.id_category,
            "id_employee": ticket.id_employee,
            "id_customer": ticket.id_customer,
            "created_at": ticket.created_at,
            "updated_at": ticket.updated_at,
            "category_name": category_name
        }
        tickets.append(ticket_dict)
    
    meta = {"page": page, "limit": limit, "total": total, "total_pages": total_pages, "has_next": page < total_pages, "has_prev": page > 1}
    return APIResponse(status=True, code=200, message="Thành công", data=TicketListOut(items=tickets, meta=meta))


@router.get("/user/closed", response_model=APIResponse[TicketListOut])
def get_my_closed_tickets_customer(
    current_user: Human = Depends(get_current_customer),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Lấy danh sách ticket đã closed của customer"""
    query = (
        db.query(Ticket, TicketCategory.name.label('category_name'))
        .outerjoin(TicketCategory, Ticket.id_category == TicketCategory.id_category)
        .filter(
            Ticket.id_customer == current_user.id,
            Ticket.status == "Closed"
        )
        .order_by(Ticket.updated_at.desc())
    )
    
    # Get total count efficiently
    total = query.count()
    total_pages = (total + limit - 1) // limit if total > 0 else 1
    
    # Apply database-level pagination with limit/offset
    skip = (page - 1) * limit
    results = query.offset(skip).limit(limit).all()
    
    tickets = []
    for ticket, category_name in results:
        ticket_dict = {
            "id_ticket": ticket.id_ticket,
            "title": ticket.title,
            "description": ticket.description,
            "status": ticket.status,
            "severity": ticket.severity,
            "expired_date": ticket.expired_date,
            "id_category": ticket.id_category,
            "id_employee": ticket.id_employee,
            "id_customer": ticket.id_customer,
            "created_at": ticket.created_at,
            "updated_at": ticket.updated_at,
            "category_name": category_name
        }
        tickets.append(ticket_dict)
    
    meta = {"page": page, "limit": limit, "total": total, "total_pages": total_pages, "has_next": page < total_pages, "has_prev": page > 1}
    return APIResponse(status=True, code=200, message="Thành công", data=TicketListOut(items=tickets, meta=meta))


@router.get("/unassigned", response_model=APIResponse[TicketListOut], dependencies=[Depends(get_current_employee)])
def get_unassigned_tickets(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    query = (
        db.query(Ticket, TicketCategory.name.label('category_name'))
        .outerjoin(TicketCategory, Ticket.id_category == TicketCategory.id_category)
        .filter(Ticket.id_employee == None)
        .order_by(Ticket.created_at.desc())
    )
    
    # Get total count efficiently
    total = query.count()
    total_pages = (total + limit - 1) // limit if total > 0 else 1
    
    # Apply database-level pagination with limit/offset
    skip = (page - 1) * limit
    results = query.offset(skip).limit(limit).all()
    
    tickets = []
    for ticket, category_name in results:
        ticket_dict = {
            "id_ticket": ticket.id_ticket,
            "title": ticket.title,
            "description": ticket.description,
            "status": ticket.status,
            "severity": ticket.severity,
            "expired_date": ticket.expired_date,
            "id_category": ticket.id_category,
            "id_employee": ticket.id_employee,
            "id_customer": ticket.id_customer,
            "created_at": ticket.created_at,
            "updated_at": ticket.updated_at,
            "category_name": category_name
        }
        tickets.append(ticket_dict)
    
    meta = {"page": page, "limit": limit, "total": total, "total_pages": total_pages, "has_next": page < total_pages, "has_prev": page > 1}
    return APIResponse(status=True, code=200, message="Thành công", data=TicketListOut(items=tickets, meta=meta))


@router.get("/department/{dept_id}", response_model=APIResponse[TicketListOut], dependencies=[Depends(get_current_employee)])
def get_tickets_by_department(
    dept_id: UUID,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    query = (
        db.query(Ticket, TicketCategory.name.label('category_name'))
        .outerjoin(TicketCategory, Ticket.id_category == TicketCategory.id_category)
        .filter(TicketCategory.id_department == dept_id)
        .order_by(Ticket.created_at.desc())
    )
    
    total = query.count()
    total_pages = (total + limit - 1) // limit if total > 0 else 1
    
    skip = (page - 1) * limit
    results = query.offset(skip).limit(limit).all()
    
    tickets = []
    for ticket, category_name in results:
        ticket_dict = {
            "id_ticket": ticket.id_ticket,
            "title": ticket.title,
            "description": ticket.description,
            "status": ticket.status,
            "severity": ticket.severity,
            "expired_date": ticket.expired_date,
            "id_category": ticket.id_category,
            "id_employee": ticket.id_employee,
            "id_customer": ticket.id_customer,
            "created_at": ticket.created_at,
            "updated_at": ticket.updated_at,
            "category_name": category_name
        }
        tickets.append(ticket_dict)
    
    meta = {"page": page, "limit": limit, "total": total, "total_pages": total_pages, "has_next": page < total_pages, "has_prev": page > 1}
    return APIResponse(status=True, code=200, message="Thành công", data=TicketListOut(items=tickets, meta=meta))


@router.get("/employee-tickets", response_model=APIResponse[TicketListOut], dependencies=[Depends(get_current_employee)])
def get_my_tickets(
    current_user: Human = Depends(get_current_employee),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    query = (
        db.query(Ticket, TicketCategory.name.label('category_name'))
        .outerjoin(TicketCategory, Ticket.id_category == TicketCategory.id_category)
        .filter(
            Ticket.id_employee == current_user.id,
            Ticket.status != "Closed"
        )
        .order_by(Ticket.created_at.desc())
    )
    
    # Get total count efficiently
    total = query.count()
    total_pages = (total + limit - 1) // limit if total > 0 else 1
    
    # Apply database-level pagination with limit/offset
    skip = (page - 1) * limit
    results = query.offset(skip).limit(limit).all()
    
    tickets = []
    for ticket, category_name in results:
        ticket_dict = {
            "id_ticket": ticket.id_ticket,
            "title": ticket.title,
            "description": ticket.description,
            "status": ticket.status,
            "severity": ticket.severity,
            "expired_date": ticket.expired_date,
            "id_category": ticket.id_category,
            "id_employee": ticket.id_employee,
            "id_customer": ticket.id_customer,
            "created_at": ticket.created_at,
            "updated_at": ticket.updated_at,
            "category_name": category_name
        }
        tickets.append(ticket_dict)
    
    meta = {"page": page, "limit": limit, "total": total, "total_pages": total_pages, "has_next": page < total_pages, "has_prev": page > 1}
    return APIResponse(status=True, code=200, message="Thành công", data=TicketListOut(items=tickets, meta=meta))


@router.get("/employee-tickets/closed", response_model=APIResponse[TicketListOut], dependencies=[Depends(get_current_employee)])
def get_my_closed_tickets(
    current_user: Human = Depends(get_current_employee),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Lấy danh sách ticket đã closed của employee"""
    query = (
        db.query(Ticket, TicketCategory.name.label('category_name'))
        .outerjoin(TicketCategory, Ticket.id_category == TicketCategory.id_category)
        .filter(
            Ticket.id_employee == current_user.id,
            Ticket.status == "Closed"
        )
        .order_by(Ticket.updated_at.desc())
    )
    
    # Get total count efficiently
    total = query.count()
    total_pages = (total + limit - 1) // limit if total > 0 else 1
    
    # Apply database-level pagination with limit/offset
    skip = (page - 1) * limit
    results = query.offset(skip).limit(limit).all()
    
    tickets = []
    for ticket, category_name in results:
        ticket_dict = {
            "id_ticket": ticket.id_ticket,
            "title": ticket.title,
            "description": ticket.description,
            "status": ticket.status,
            "severity": ticket.severity,
            "expired_date": ticket.expired_date,
            "id_category": ticket.id_category,
            "id_employee": ticket.id_employee,
            "id_customer": ticket.id_customer,
            "created_at": ticket.created_at,
            "updated_at": ticket.updated_at,
            "category_name": category_name
        }
        tickets.append(ticket_dict)
    
    meta = {"page": page, "limit": limit, "total": total, "total_pages": total_pages, "has_next": page < total_pages, "has_prev": page > 1}
    return APIResponse(status=True, code=200, message="Thành công", data=TicketListOut(items=tickets, meta=meta))


@router.get("/all", response_model=APIResponse[TicketListOut], dependencies=[Depends(get_current_employee)])
def get_all_tickets_admin(
    current_user: Human = Depends(get_current_employee),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get all tickets - for employee/admin use only"""
    query = (
        db.query(Ticket, TicketCategory.name.label('category_name'))
        .outerjoin(TicketCategory, Ticket.id_category == TicketCategory.id_category)
        .order_by(Ticket.created_at.desc())
    )
    
    # Get total count efficiently
    total = query.count()
    total_pages = (total + limit - 1) // limit if total > 0 else 1
    
    # Apply database-level pagination with limit/offset
    skip = (page - 1) * limit
    results = query.offset(skip).limit(limit).all()
    
    tickets = []
    for ticket, category_name in results:
        ticket_dict = {
            "id_ticket": ticket.id_ticket,
            "title": ticket.title,
            "description": ticket.description,
            "status": ticket.status,
            "severity": ticket.severity,
            "expired_date": ticket.expired_date,
            "id_category": ticket.id_category,
            "id_employee": ticket.id_employee,
            "id_customer": ticket.id_customer,
            "created_at": ticket.created_at,
            "updated_at": ticket.updated_at,
            "category_name": category_name
        }
        tickets.append(ticket_dict)
    
    meta = {"page": page, "limit": limit, "total": total, "total_pages": total_pages, "has_next": page < total_pages, "has_prev": page > 1}
    return APIResponse(status=True, code=200, message="Thành công", data=TicketListOut(items=tickets, meta=meta))


@router.get("/{ticket_id}", response_model=APIResponse[TicketOut])
def get_ticket(ticket_id: UUID, current_user: Human = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get ticket by ID - requires authentication and ticket access authorization"""
    try:
        service = TicketService(db)
        ticket = service.get_ticket_by_id(ticket_id)
        
        # Authorization check: user must be customer who owns ticket, employee assigned, or employee
        if current_user.type == 'customer' and ticket.id_customer != current_user.id:
            from app.core.response import APIResponse
            return APIResponse(status=False, code=403, message="Bạn không có quyền truy cập ticket này!")
        
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
        ticket = TicketService(db).assign_ticket(data.id_ticket, data)
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
    """
    Đóng ticket - customer đóng ticket của chính mình từ trạng thái Resolved.
    Employee cũng có thể đóng ticket.
    """
    try:
        # Verify ownership for customers
        if current_user.type == "customer":
            from app.models.ticket import Ticket
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
    """
    Mở lại ticket đã đóng - customer mở lại ticket của chính mình.
    Employee cũng có thể mở lại ticket.
    """
    try:
        # Verify ownership for customers
        if current_user.type == "customer":
            from app.models.ticket import Ticket
            ticket = db.query(Ticket).filter(Ticket.id_ticket == ticket_id).first()
            if not ticket or ticket.id_customer != current_user.id:
                return APIResponse(status=False, code=403, message="Bạn không có quyền mở lại ticket này!")
        
        ticket = TicketService(db).reopen_ticket(ticket_id, data.reason, current_user.id, current_user.type)
        return APIResponse(status=True, code=200, message="Mở lại ticket thành công", data=ticket)
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)
