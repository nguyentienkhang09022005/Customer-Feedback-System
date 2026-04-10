from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.repositories.ticketCommentRepository import TicketCommentRepository
from app.repositories.ticketRepository import TicketRepository
from app.models.ticketComment import TicketComment
from app.models.human import Human
from app.schemas.ticketCommentSchema import CommentCreate, CommentUpdate
from app.schemas.notificationSchema import NotificationCreate
from app.services.notificationService import NotificationService
from typing import List
import uuid
import logging

logger = logging.getLogger(__name__)


class TicketCommentService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = TicketCommentRepository(db)
        self.ticket_repo = TicketRepository(db)

    def create_comment(
        self, 
        ticket_id: uuid.UUID, 
        data: CommentCreate, 
        author_id: uuid.UUID, 
        author_type: str
    ) -> TicketComment:
        """Tạo comment mới cho ticket"""
        # Verify ticket exists
        ticket = self.ticket_repo.get_by_id(ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Không tìm thấy ticket!")
        
        # If is_internal, only employee can create internal notes
        if data.is_internal and author_type != "employee":
            raise HTTPException(
                status_code=403, 
                detail="Chỉ nhân viên mới có thể tạo ghi chú nội bộ!"
            )
        
        comment = TicketComment(
            id_ticket=ticket_id,
            id_author=author_id,
            author_type=author_type,
            content=data.content,
            is_internal=data.is_internal
        )
        
        created_comment = self.repo.create(comment)
        
        # Send notification about new comment
        self._notify_about_new_comment(ticket, created_comment, author_type)
        
        return created_comment

    def get_comments(
        self, 
        ticket_id: uuid.UUID, 
        is_employee: bool = False
    ) -> List[TicketComment]:
        """Lấy comments của ticket - employee thấy internal, customer không"""
        ticket = self.ticket_repo.get_by_id(ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Không tìm thấy ticket!")
        
        # Employee sees all, customer only sees non-internal
        include_internal = is_employee
        return self.repo.get_by_ticket(ticket_id, include_internal=include_internal)

    def update_comment(
        self, 
        comment_id: uuid.UUID, 
        data: CommentUpdate, 
        user_id: uuid.UUID
    ) -> TicketComment:
        """Cập nhật comment - chỉ author mới được sửa"""
        comment = self.repo.get_by_id(comment_id)
        if not comment:
            raise HTTPException(status_code=404, detail="Không tìm thấy comment!")
        
        if comment.id_author != user_id:
            raise HTTPException(status_code=403, detail="Bạn không có quyền sửa comment này!")
        
        if data.content:
            comment.content = data.content
        
        return self.repo.update(comment)

    def delete_comment(self, comment_id: uuid.UUID, user_id: uuid.UUID, is_admin: bool = False):
        """Xóa comment - chỉ author hoặc admin mới được xóa"""
        comment = self.repo.get_by_id(comment_id)
        if not comment:
            raise HTTPException(status_code=404, detail="Không tìm thấy comment!")
        
        if not is_admin and comment.id_author != user_id:
            raise HTTPException(status_code=403, detail="Bạn không có quyền xóa comment này!")
        
        self.repo.delete(comment)

    def _notify_about_new_comment(self, ticket, comment, author_type):
        """Gửi notification khi có comment mới"""
        try:
            noti_service = NotificationService(self.db)
            short_content = comment.content[:50] + "..." if len(comment.content) > 50 else comment.content
            
            if author_type == "customer":
                # Notify assigned employee (if any)
                if ticket.id_employee:
                    noti_data = NotificationCreate(
                        title=f"Bình luận mới từ khách hàng",
                        content=f"Khách hàng bình luận trên ticket #{str(ticket.id_ticket)[:8]}: {short_content}",
                        notification_type="NEW_COMMENT",
                        id_reference=ticket.id_ticket,
                        id_receiver=ticket.id_employee
                    )
                    noti_service.create_and_send(noti_data)
            else:
                # Employee comment - notify customer
                noti_data = NotificationCreate(
                    title=f"Nhân viên phản hồi",
                    content=f"Nhân viên bình luận trên ticket #{str(ticket.id_ticket)[:8]}: {short_content}",
                    notification_type="NEW_COMMENT",
                    id_reference=ticket.id_ticket,
                    id_receiver=ticket.id_customer
                )
                noti_service.create_and_send(noti_data)
                
        except Exception as e:
            logger.warning(f"Failed to notify about new comment: {e}")
