from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.services.ticketCategoryService import TicketCategoryService
from app.schemas.ticketCategorySchema import TicketCategoryCreate, TicketCategoryUpdate, TicketCategoryOut
from app.core.response import APIResponse
from app.api.dependencies import get_db, get_current_employee

router = APIRouter(prefix="/ticket-categories", tags=["Ticket Categories Management"])

@router.get("", response_model=APIResponse[List[TicketCategoryOut]], dependencies=[Depends(get_current_employee)])
def get_categories(db: Session = Depends(get_db)):
    categories = TicketCategoryService(db).get_all()
    return APIResponse(status=True, code=200, message="Thành công", data=categories)

@router.post("", response_model=APIResponse[TicketCategoryOut], dependencies=[Depends(get_current_employee)])
def create_category(data: TicketCategoryCreate, db: Session = Depends(get_db)):
    try:
        category = TicketCategoryService(db).create_category(data)
        return APIResponse(status=True, code=201, message="Tạo danh mục thành công", data=category)
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)

@router.patch("/{cat_id}", response_model=APIResponse[TicketCategoryOut], dependencies=[Depends(get_current_employee)])
def update_category(cat_id: str, data: TicketCategoryUpdate, db: Session = Depends(get_db)):
    try:
        category = TicketCategoryService(db).update_category(cat_id, data)
        return APIResponse(status=True, code=200, message="Cập nhật thành công", data=category)
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)

@router.delete("/{cat_id}", response_model=APIResponse, dependencies=[Depends(get_current_employee)])
def delete_category(cat_id: str, db: Session = Depends(get_db)):
    try:
        TicketCategoryService(db).delete_category(cat_id)
        return APIResponse(status=True, code=200, message="Xóa danh mục thành công")
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)