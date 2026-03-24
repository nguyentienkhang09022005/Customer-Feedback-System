from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.services.faqService import FAQService
from app.schemas.faqSchema import FAQCreate, FAQUpdate, FAQListOut, FAQDetailOut
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

@router.get("/public", response_model=APIResponse[List[FAQListOut]])
def get_public_faqs(db: Session = Depends(get_db)):
    articles = FAQService(db).get_public_articles()
    return APIResponse(status=True, code=200, message="Lấy danh sách public thành công!", data=articles)

@router.get("/private", response_model=APIResponse[List[FAQListOut]], dependencies=[Depends(get_current_employee)])
def get_private_faqs(db: Session = Depends(get_db)):
    articles = FAQService(db).get_private_articles()
    return APIResponse(status=True, code=200, message="Lấy danh sách private thành công!", data=articles)

@router.get("/{article_id}", response_model=APIResponse[FAQDetailOut])
def read_faq_detail(article_id: UUID, request: Request, db: Session = Depends(get_db)):
    try:
        client_ip = request.client.host if request.client else "unknown_ip"
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