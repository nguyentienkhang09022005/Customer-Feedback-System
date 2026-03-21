"""
DEPRECATED: Chỉ dùng để initial setup 1 lần.
Sau khi có Alembic, dùng: alembic upgrade head

Để khởi tạo database mới hoàn toàn (xóa và tạo lại):
1. alembic downgrade base
2. alembic upgrade head

Hoặc chạy trực tiếp: python create_db.py
"""
import subprocess
import sys


def init_db():
    print("⚠️ DEPRECATED: Khuyến nghị dùng 'alembic upgrade head'")
    print("⏳ Kiểm tra database connection...")
    
    try:
        from app.core.config import settings
        print(f"📍 Database: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'local'}")
    except Exception as e:
        print(f"❌ Lỗi kết nối: {e}")
        return False
    
    print("\n🔧 Để tạo migration mới: alembic revision --autogenerate -m 'description'")
    print("🔧 Để apply migration: alembic upgrade head")
    print("🔧 Để xem status: alembic current")
    
    response = input("\n❓ Bạn có muốn chạy 'alembic upgrade head' không? (y/n): ")
    if response.lower() == 'y':
        result = subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"])
        return result.returncode == 0
    
    return True


if __name__ == "__main__":
    success = init_db()
    sys.exit(0 if success else 1)