from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.services.ticketCategoryService import TicketCategoryService
from app.services.ticketTemplateService import TicketTemplateService
from app.schemas.ticketCategorySchema import (
    TicketCategoryCreate,
    TicketCategoryUpdate,
    TicketCategoryOut,
    TicketCategoryWithTemplatesOut,
    TicketTemplateOut,
)
from app.core.response import APIResponse
from app.api.dependencies import get_db, get_current_employee, get_current_user, get_current_admin
from app.services.chatbotService import ChatbotService

router = APIRouter(prefix="/ticket-categories", tags=["Ticket Categories Management"])


@router.get("", response_model=APIResponse[List[TicketCategoryOut]], dependencies=[Depends(get_current_user)])
def get_categories(active_only: bool = Query(True), db: Session = Depends(get_db)):
    service = TicketCategoryService(db)
    if active_only:
        categories = service.get_active_all()
    else:
        categories = service.get_all()
    return APIResponse(status=True, code=200, message="Thành công", data=categories)


@router.post("", response_model=APIResponse[TicketCategoryOut], dependencies=[Depends(get_current_employee)])
def create_category(data: TicketCategoryCreate, db: Session = Depends(get_db)):
    try:
        category = TicketCategoryService(db).create_category(data)
        ChatbotService.invalidate_public_data_cache()
        return APIResponse(status=True, code=201, message="Tạo danh mục thành công", data=category)
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)


@router.get("/{cat_id}", response_model=APIResponse[TicketCategoryOut], dependencies=[Depends(get_current_user)])
def get_category(cat_id: UUID, db: Session = Depends(get_db)):
    try:
        service = TicketCategoryService(db)
        category = service.get_by_id(str(cat_id))
        if not category:
            return APIResponse(status=False, code=404, message="Không tìm thấy danh mục!")
        return APIResponse(status=True, code=200, message="Thành công", data=category)
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)


@router.get("/{cat_id}/templates", response_model=APIResponse[List[TicketTemplateOut]], dependencies=[Depends(get_current_user)])
def get_category_templates(cat_id: UUID, db: Session = Depends(get_db)):
    try:
        service = TicketTemplateService(db)
        templates = service.get_templates_by_category(cat_id)
        return APIResponse(status=True, code=200, message="Thành công", data=templates)
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)


@router.patch("/{cat_id}", response_model=APIResponse[TicketCategoryOut], dependencies=[Depends(get_current_employee)])
def update_category(cat_id: UUID, data: TicketCategoryUpdate, db: Session = Depends(get_db)):
    try:
        category = TicketCategoryService(db).update_category(str(cat_id), data)
        ChatbotService.invalidate_public_data_cache()
        return APIResponse(status=True, code=200, message="Cập nhật thành công", data=category)
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)


@router.delete("/{cat_id}", response_model=APIResponse, dependencies=[Depends(get_current_admin)])
def delete_category(cat_id: UUID, hard_delete: bool = Query(False), db: Session = Depends(get_db)):
    try:
        service = TicketCategoryService(db)
        if hard_delete:
            service.hard_delete_category(str(cat_id))
        else:
            service.delete_category(str(cat_id))
        ChatbotService.invalidate_public_data_cache()
        return APIResponse(status=True, code=200, message="Xóa danh mục thành công")
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)