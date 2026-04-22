from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from uuid import UUID

from app.services.appointmentService import AppointmentService
from app.schemas.appointmentSchema import (
    AppointmentCreate,
    AppointmentOut,
    AppointmentAccept,
    AppointmentReject,
    AppointmentCancel,
    AppointmentListOut,
)
from app.core.response import APIResponse
from app.api.dependencies import get_db, get_current_user, get_current_customer, get_current_employee
from app.models.human import Human, Customer


router = APIRouter(prefix="/appointments", tags=["Appointment"])


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


@router.post("", response_model=APIResponse[AppointmentOut])
def create_appointment(
    data: AppointmentCreate,
    current_user: Human = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    try:
        customer = db.query(Customer).filter(Customer.id == current_user.id).first()
        appointment = AppointmentService(db).create_appointment(data, customer.id_customer)
        return APIResponse(status=True, code=201, message="Đặt lịch hẹn thành công!", data=appointment)
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)


@router.get("/ticket/{ticket_id}", response_model=APIResponse[AppointmentListOut])
def get_appointments_by_ticket(
    ticket_id: UUID,
    current_user: Human = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        appointments = AppointmentService(db).get_appointments_by_ticket(ticket_id)
        return APIResponse(status=True, code=200, message="Thành công", data=AppointmentListOut(items=appointments, meta=_build_meta(appointments)))
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)


@router.get("/employee", response_model=APIResponse[AppointmentListOut])
def get_employee_appointments(
    current_user: Human = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    try:
        appointments = AppointmentService(db).get_appointments_by_employee(current_user.id)
        return APIResponse(status=True, code=200, message="Thành công", data=AppointmentListOut(items=appointments, meta=_build_meta(appointments)))
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)


@router.get("/employee/pending", response_model=APIResponse[AppointmentListOut])
def get_employee_pending_appointments(
    current_user: Human = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    try:
        appointments = AppointmentService(db).get_pending_appointments_by_employee(current_user.id)
        return APIResponse(status=True, code=200, message="Thành công", data=AppointmentListOut(items=appointments, meta=_build_meta(appointments)))
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)


@router.get("/{appointment_id}", response_model=APIResponse[AppointmentOut])
def get_appointment(
    appointment_id: UUID,
    current_user: Human = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        appointment = AppointmentService(db).get_appointment_by_id(appointment_id)

        if current_user.type == "customer" and appointment.id_customer != current_user.id:
            return APIResponse(status=False, code=403, message="Bạn không có quyền xem lịch hẹn này!")
        if current_user.type == "employee" and appointment.id_employee != current_user.id:
            return APIResponse(status=False, code=403, message="Bạn không có quyền xem lịch hẹn này!")

        return APIResponse(status=True, code=200, message="Thành công", data=appointment)
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)


@router.patch("/{appointment_id}/accept", response_model=APIResponse[AppointmentOut])
def accept_appointment(
    appointment_id: UUID,
    current_user: Human = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    try:
        appointment = AppointmentService(db).accept_appointment(appointment_id, current_user.id)
        return APIResponse(status=True, code=200, message="Chấp nhận lịch hẹn thành công!", data=appointment)
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)


@router.patch("/{appointment_id}/reject", response_model=APIResponse[AppointmentOut])
def reject_appointment(
    appointment_id: UUID,
    data: AppointmentReject,
    current_user: Human = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    try:
        appointment = AppointmentService(db).reject_appointment(
            appointment_id,
            current_user.id,
            data.rejection_reason
        )
        return APIResponse(status=True, code=200, message="Từ chối lịch hẹn thành công!", data=appointment)
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)


@router.patch("/{appointment_id}/cancel", response_model=APIResponse[AppointmentOut])
def cancel_appointment(
    appointment_id: UUID,
    data: AppointmentCancel,
    current_user: Human = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    try:
        customer = db.query(Customer).filter(Customer.id == current_user.id).first()
        appointment = AppointmentService(db).cancel_appointment(appointment_id, customer.id_customer)
        return APIResponse(status=True, code=200, message="Hủy lịch hẹn thành công!", data=appointment)
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)


from fastapi import HTTPException