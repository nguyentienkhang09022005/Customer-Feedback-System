from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.services.ticketCommentService import TicketCommentService
from app.schemas.ticketCommentSchema import CommentCreate, CommentUpdate, CommentOut, CommentListOut
from app.core.response import APIResponse
from app.api.dependencies import get_db, get_current_user, get_current_employee, get_current_customer
from app.models.human import Human

router = APIRouter(prefix="/tickets/{ticket_id}/comments", tags=["Ticket Comments"])


def _get_author_info(current_user: Human) -> tuple:
    """Get author_id and author_type from current user"""
    if current_user.type == "customer":
        return current_user.id, "customer"
    elif current_user.type == "employee":
        return current_user.id, "employee"
    else:
        raise HTTPException(status_code=403, detail="Không xác định được loại người dùng!")


@router.post("", response_model=APIResponse[CommentOut])
def create_comment(
    ticket_id: UUID,
    data: CommentCreate,
    current_user: Human = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Tạo comment mới cho ticket"""
    try:
        author_id, author_type = _get_author_info(current_user)
        comment = TicketCommentService(db).create_comment(
            ticket_id=ticket_id,
            data=data,
            author_id=author_id,
            author_type=author_type
        )
        
        # Get author name for response
        author_name = f"{current_user.first_name} {current_user.last_name}".strip()
        comment_out = CommentOut(
            id_comment=comment.id_comment,
            id_ticket=comment.id_ticket,
            id_author=comment.id_author,
            author_name=author_name,
            author_type=comment.author_type,
            content=comment.content,
            is_internal=comment.is_internal,
            created_at=comment.created_at,
            updated_at=comment.updated_at
        )
        
        return APIResponse(status=True, code=201, message="Tạo bình luận thành công", data=comment_out)
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)


@router.get("", response_model=APIResponse[CommentListOut])
def get_comments(
    ticket_id: UUID,
    current_user: Human = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lấy comments của ticket"""
    try:
        is_employee = current_user.type == "employee"
        comments = TicketCommentService(db).get_comments(ticket_id, is_employee)
        
        # Get author names
        comment_outs = []
        for comment in comments:
            # Query author to get name
            author = db.query(Human).filter(Human.id == comment.id_author).first()
            author_name = None
            if author:
                author_name = f"{author.first_name} {author.last_name}".strip()
            
            comment_outs.append(CommentOut(
                id_comment=comment.id_comment,
                id_ticket=comment.id_ticket,
                id_author=comment.id_author,
                author_name=author_name,
                author_type=comment.author_type,
                content=comment.content,
                is_internal=comment.is_internal,
                created_at=comment.created_at,
                updated_at=comment.updated_at
            ))
        
        return APIResponse(
            status=True, 
            code=200, 
            message="Thành công", 
            data=CommentListOut(items=comment_outs, total=len(comment_outs))
        )
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)


@router.patch("/{comment_id}", response_model=APIResponse[CommentOut])
def update_comment(
    ticket_id: UUID,
    comment_id: UUID,
    data: CommentUpdate,
    current_user: Human = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cập nhật comment - chỉ author mới được sửa"""
    try:
        comment = TicketCommentService(db).update_comment(comment_id, data, current_user.id)
        
        author_name = f"{current_user.first_name} {current_user.last_name}".strip()
        comment_out = CommentOut(
            id_comment=comment.id_comment,
            id_ticket=comment.id_ticket,
            id_author=comment.id_author,
            author_name=author_name,
            author_type=comment.author_type,
            content=comment.content,
            is_internal=comment.is_internal,
            created_at=comment.created_at,
            updated_at=comment.updated_at
        )
        
        return APIResponse(status=True, code=200, message="Cập nhật thành công", data=comment_out)
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)


@router.delete("/{comment_id}", response_model=APIResponse)
def delete_comment(
    ticket_id: UUID,
    comment_id: UUID,
    current_user: Human = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Xóa comment - chỉ author hoặc admin mới được xóa"""
    try:
        # Check if user is admin (simplified - in real app would check role)
        is_admin = current_user.type == "employee"  # Could enhance to check specific admin role
        
        TicketCommentService(db).delete_comment(comment_id, current_user.id, is_admin)
        return APIResponse(status=True, code=200, message="Xóa bình luận thành công")
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)
