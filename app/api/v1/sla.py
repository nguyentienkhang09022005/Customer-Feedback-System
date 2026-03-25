from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.services.slaService import SLAService
from app.schemas.slaSchema import SLACreate, SLAUpdate, SLAOut
from app.core.response import APIResponse
from app.api.dependencies import get_db, get_current_employee, get_current_admin

router = APIRouter(prefix="/sla-policies", tags=["SLA Policies"])


@router.get("", response_model=APIResponse[List[SLAOut]], dependencies=[Depends(get_current_employee)])
def get_all_sla_policies(db: Session = Depends(get_db)):
    service = SLAService(db)
    policies = service.get_all_policies()
    return APIResponse(
        status=True,
        code=200,
        message="Lấy danh sách SLA thành công!",
        data=policies
    )


@router.post("", response_model=APIResponse[SLAOut], dependencies=[Depends(get_current_admin)])
def create_sla_policy(
        data: SLACreate,
        db: Session = Depends(get_db)
):
    try:
        service = SLAService(db)
        policy = service.create_policy(data)
        return APIResponse(
            status=True,
            code=201,
            message="Tạo chính sách SLA thành công!",
            data=policy
        )
    except Exception as e:
        return APIResponse(status=False, code=400, message=str(e))


@router.put("/{policy_id}", response_model=APIResponse[SLAOut], dependencies=[Depends(get_current_admin)])
def update_sla_policy(
        policy_id: UUID,
        data: SLAUpdate,
        db: Session = Depends(get_db)
):
    try:
        service = SLAService(db)
        policy = service.update_policy(policy_id, data)
        return APIResponse(
            status=True,
            code=200,
            message="Cập nhật chính sách SLA thành công!",
            data=policy
        )
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)


@router.patch("/{policy_id}/toggle", response_model=APIResponse[SLAOut], dependencies=[Depends(get_current_admin)])
def toggle_sla_policy(
        policy_id: UUID,
        db: Session = Depends(get_db)
):
    try:
        service = SLAService(db)
        policy = service.toggle_policy(policy_id)

        status_msg = "đã BẬT" if policy.is_active else "đã TẮT"

        return APIResponse(
            status=True,
            code=200,
            message=f"Chính sách SLA {status_msg} thành công!",
            data=policy
        )
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)