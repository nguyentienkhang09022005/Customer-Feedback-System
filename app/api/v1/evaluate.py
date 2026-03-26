from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.services.evaluateService import EvaluateService
from app.schemas.evaluateSchema import EvaluateCreate, EvaluateUpdate, EvaluateOut
from app.core.response import APIResponse
from app.api.dependencies import get_db, get_current_customer
from app.models.human import Customer

router = APIRouter(prefix="/evaluates", tags=["Evaluate Management"])

@router.post("", response_model=APIResponse[EvaluateOut])
def create_evaluate(
    data: EvaluateCreate,
    current_customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    try:
        evaluate = EvaluateService(db).create_evaluate(data, current_customer.id_customer)
        return APIResponse(status=True, code=201, message="Đánh giá ticket thành công!", data=evaluate)
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)

@router.get("/ticket/{ticket_id}", response_model=APIResponse[List[EvaluateOut]])
def get_evaluates_by_ticket(ticket_id: UUID, db: Session = Depends(get_db)):
    evaluates = EvaluateService(db).get_evaluates_by_ticket(ticket_id)
    return APIResponse(status=True, code=200, message="Lấy danh sách đánh giá thành công!", data=evaluates)

@router.patch("/{evaluate_id}", response_model=APIResponse[EvaluateOut])
def update_evaluate(
    evaluate_id: UUID,
    data: EvaluateUpdate,
    current_customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    try:
        evaluate = EvaluateService(db).update_evaluate(evaluate_id, data, current_customer.id_customer)
        return APIResponse(status=True, code=200, message="Cập nhật đánh giá thành công!", data=evaluate)
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)

@router.delete("/{evaluate_id}", response_model=APIResponse)
def delete_evaluate(
    evaluate_id: UUID,
    current_customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    try:
        EvaluateService(db).delete_evaluate(evaluate_id, current_customer.id_customer)
        return APIResponse(status=True, code=200, message="Xóa đánh giá thành công!")
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)