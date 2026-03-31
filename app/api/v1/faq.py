from fastapi import APIRouter, Depends, HTTPException, Request, Query, Response
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.services.faqService import FAQService
from app.schemas.faqSchema import FAQCreate, FAQUpdate, FAQListOut, FAQDetailOut, FAQPublicOut, FAQPublicListResponse
from app.schemas.paginationSchema import PaginationMeta
from app.core.response import APIResponse
from app.api.dependencies import get_db, get_current_employee
from app.models.human import Employee

router = APIRouter(prefix="/faqs", tags=["FAQ Management"])

@router.post("", response_model=APIResponse[FAQDetailOut])
def create_faq(
        data: FAQCreate,
        current_employee: Employee = Depends(get_current_employee),
        db: Session = Depends(get_db)
):
    try:
        article = FAQService(db).create_article(data, current_employee.id)
        return APIResponse(status=True, code=201, message="Tạo bài viết về câu hỏi thành công!", data=article)
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)

@router.get("", response_model=APIResponse[List[FAQListOut]], dependencies=[Depends(get_current_employee)])
def get_all_faqs(db: Session = Depends(get_db)):
    articles = FAQService(db).get_all_articles()
    return APIResponse(status=True, code=200, message="Lấy toàn bộ danh sách thành công!", data=articles)

@router.get("/public", response_model=APIResponse[FAQPublicListResponse])
def get_public_faqs(
    article_id: Optional[UUID] = Query(None, description="Get single FAQ by ID"),
    category_id: Optional[UUID] = Query(None, description="Filter by category"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search in title/content"),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """
    Unified public FAQ endpoint.
    - If article_id provided: returns single FAQ detail (with view count increment)
    - Otherwise: returns paginated list of published FAQs (with content included)
    """
    faq_service = FAQService(db)

    # If article_id is provided, return single FAQ detail
    if article_id:
        try:
            client_ip = request.client.host if (request and request.client) else "unknown_ip"
            article = faq_service.get_public_article_detail(article_id, client_ip)
            return APIResponse(status=True, code=200, message="Lấy chi tiết FAQ thành công!", data=article)
        except HTTPException as e:
            return APIResponse(status=False, code=e.status_code, message=e.detail)

    # Otherwise, return paginated list
    articles, total = faq_service.get_public_articles_paginated(
        page=page,
        limit=limit,
        category_id=category_id,
        search=search
    )

    total_pages = (total + limit - 1) // limit if total > 0 else 0

    meta = PaginationMeta(
        page=page,
        limit=limit,
        total=total,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1
    )

    return APIResponse(
        status=True,
        code=200,
        message="Lấy danh sách FAQ công khai thành công!",
        data=FAQPublicListResponse(items=articles, meta=meta)
    )

@router.get("/private", response_model=APIResponse[List[FAQListOut]], dependencies=[Depends(get_current_employee)])
def get_private_faqs(db: Session = Depends(get_db)):
    articles = FAQService(db).get_private_articles()
    return APIResponse(status=True, code=200, message="Lấy danh sách private thành công!", data=articles)

@router.get("/{article_id}", response_model=APIResponse[FAQDetailOut], deprecated=True)
def read_faq_detail(
    article_id: UUID,
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    DEPRECATED: Use GET /faqs/public?article_id={article_id} instead.
    This endpoint will be removed in a future version.
    """
    response.headers["X-Deprecated"] = "true"
    try:
        client_ip = request.client.host if (request and request.client) else "unknown_ip"
        article = FAQService(db).read_article_detail(article_id, client_ip)
        return APIResponse(status=True, code=200, message="Lấy chi tiết thành công!", data=article)
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)

@router.patch("/{article_id}", response_model=APIResponse[FAQDetailOut], dependencies=[Depends(get_current_employee)])
def update_faq(
    article_id: UUID,
    data: FAQUpdate,
    db: Session = Depends(get_db)
):
    try:
        article = FAQService(db).update_article(article_id, data)
        return APIResponse(status=True, code=200, message="Cập nhật thành công!", data=article)
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)

@router.delete("/{article_id}", response_model=APIResponse, dependencies=[Depends(get_current_employee)])
def delete_faq(
    article_id: UUID,
    db: Session = Depends(get_db)
):
    try:
        FAQService(db).delete_article(article_id)
        return APIResponse(status=True, code=200, message="Xóa bài viết về câu hỏi thành công!")
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)
