from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.services.ticketTemplateService import TicketTemplateService
from app.schemas.ticketCategorySchema import (
    TicketTemplateCreate,
    TicketTemplateUpdate,
    TicketTemplateOut,
    TicketTemplateDetailOut,
)
from app.core.response import APIResponse
from app.api.dependencies import get_db, get_current_admin, get_current_employee, get_current_user
from app.services.chatbotService import ChatbotService

router = APIRouter(prefix="/templates", tags=["Template Management"])


@router.get("", response_model=APIResponse[List[TicketTemplateOut]], dependencies=[Depends(get_current_user)])
def get_all_templates(db: Session = Depends(get_db)):
    try:
        service = TicketTemplateService(db)
        templates = service.get_all_templates()
        return APIResponse(status=True, code=200, message="Thành công", data=templates)
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)


@router.get("/category/{category_id}", response_model=APIResponse[List[TicketTemplateOut]], dependencies=[Depends(get_current_user)])
def get_templates_by_category(category_id: UUID, db: Session = Depends(get_db)):
    try:
        service = TicketTemplateService(db)
        templates = service.get_templates_by_category(category_id)
        return APIResponse(status=True, code=200, message="Thành công", data=templates)
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)


@router.get("/{template_id}", response_model=APIResponse[TicketTemplateOut], dependencies=[Depends(get_current_user)])
def get_template(template_id: UUID, version: int = None, db: Session = Depends(get_db)):
    try:
        service = TicketTemplateService(db)
        template = service.get_template(template_id, version)
        if not template:
            return APIResponse(status=False, code=404, message="Không tìm thấy template!")
        return APIResponse(status=True, code=200, message="Thành công", data=template)
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)


@router.get("/{template_id}/versions", response_model=APIResponse[List[TicketTemplateOut]], dependencies=[Depends(get_current_user)])
def get_template_versions(template_id: UUID, db: Session = Depends(get_db)):
    try:
        service = TicketTemplateService(db)
        versions = service.get_all_versions(template_id)
        return APIResponse(status=True, code=200, message="Thành công", data=versions)
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)


@router.post("", response_model=APIResponse[TicketTemplateOut], dependencies=[Depends(get_current_employee)])
def create_template(data: TicketTemplateCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_employee)):
    try:
        author_id = current_user.id if hasattr(current_user, 'id') else None
        service = TicketTemplateService(db)
        template = service.create_template(data, author_id)
        ChatbotService.invalidate_public_data_cache()
        return APIResponse(status=True, code=201, message="Tạo template thành công", data=template)
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)


@router.patch("/{template_id}", response_model=APIResponse[TicketTemplateOut], dependencies=[Depends(get_current_employee)])
def update_template(template_id: UUID, data: TicketTemplateUpdate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_employee)):
    try:
        author_id = current_user.id if hasattr(current_user, 'id') else None
        service = TicketTemplateService(db)
        template = service.update_template(template_id, data, author_id)
        ChatbotService.invalidate_public_data_cache()
        return APIResponse(status=True, code=200, message="Cập nhật template thành công", data=template)
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)


@router.delete("/{template_id}", response_model=APIResponse, dependencies=[Depends(get_current_admin)])
def delete_template(template_id: UUID, db: Session = Depends(get_db)):
    try:
        service = TicketTemplateService(db)
        service.delete_template(template_id)
        ChatbotService.invalidate_public_data_cache()
        return APIResponse(status=True, code=200, message="Xóa template thành công")
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)


@router.post("/{template_id}/activate", response_model=APIResponse[TicketTemplateOut], dependencies=[Depends(get_current_admin)])
def activate_template(template_id: UUID, db: Session = Depends(get_db)):
    try:
        service = TicketTemplateService(db)
        template = service.activate_template(template_id)
        ChatbotService.invalidate_public_data_cache()
        return APIResponse(status=True, code=200, message="Kích hoạt template thành công", data=template)
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)