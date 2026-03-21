from app.db.session import engine
from app.db.base import Base

# Import TẤT CẢ các model vào đây để SQLAlchemy xây dựng schema
from app.models.human import Role, CustomerType, Human, Employee, Customer
from app.models.ticket import TicketCategory, SLAPolicy, Ticket
from app.models.interaction import Message, Attachment, Evaluate, Notification
from app.models.system import AuditLog, FAQArticle

def init_db():
    print("⏳ Đang kết nối đến Neon Database và khởi tạo các bảng...")
    try:
        # print("🗑️ Đang xóa các bảng cũ (nếu có)...")
        # Base.metadata.drop_all(bind=engine)

        Base.metadata.create_all(bind=engine)
        print("✅ Thành công! Toàn bộ cấu trúc Database đã được tạo xong.")
    except Exception as e:
        print(f"❌ Có lỗi xảy ra: {e}")

if __name__ == "__main__":
    init_db()