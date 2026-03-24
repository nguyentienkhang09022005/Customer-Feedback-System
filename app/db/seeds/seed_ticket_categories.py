import uuid
from datetime import datetime, timezone
from app.db.session import SessionLocal
from app.models.ticket import TicketCategory
from app.models.department import Department


DEPARTMENTS = {
    "Finance": "73044748-c595-4892-bd30-9edc2b2f1e8d",
    "HR": "fdfe2b16-07bd-40c2-b9fc-994fe73e6667",
    "IT": "2a55f1e3-aa8f-4d06-b83b-6aead44fb8e5",
    "Support": "87faf75c-49ea-4023-acd5-27fa4fba97b1",
    "Sales": "1a33ba9e-ee6f-4f26-b67f-3ad77f083380",
}

TICKET_CATEGORIES = [
    {
        "name": "Bug Report",
        "description": "Báo lỗi hệ thống",
        "id_department": DEPARTMENTS["IT"],
        "auto_assign": True,
    },
    {
        "name": "Feature Request",
        "description": "Yêu cầu tính năng mới",
        "id_department": DEPARTMENTS["IT"],
        "auto_assign": True,
    },
    {
        "name": "General Inquiry",
        "description": "Câu hỏi chung",
        "id_department": DEPARTMENTS["Support"],
        "auto_assign": True,
    },
    {
        "name": "Complaint",
        "description": "Khiếu nại",
        "id_department": DEPARTMENTS["Support"],
        "auto_assign": True,
    },
    {
        "name": "Question",
        "description": "Hỏi đáp",
        "id_department": DEPARTMENTS["Support"],
        "auto_assign": True,
    },
    {
        "name": "Feedback",
        "description": "Góp ý",
        "id_department": DEPARTMENTS["Sales"],
        "auto_assign": True,
    },
    {
        "name": "HR Related",
        "description": "Nhân sự",
        "id_department": DEPARTMENTS["HR"],
        "auto_assign": True,
    },
    {
        "name": "Finance Inquiry",
        "description": "Câu hỏi tài chính",
        "id_department": DEPARTMENTS["Finance"],
        "auto_assign": True,
    },
]


def seed_ticket_categories():
    db = SessionLocal()
    try:
        categories_created = 0
        for cat_data in TICKET_CATEGORIES:
            existing = db.query(TicketCategory).filter(
                TicketCategory.name == cat_data["name"]
            ).first()
            if existing:
                print(f"Skipped (already exists): {cat_data['name']}")
                continue

            category = TicketCategory(
                id_category=uuid.uuid4(),
                name=cat_data["name"],
                description=cat_data["description"],
                id_department=cat_data["id_department"],
                auto_assign=cat_data["auto_assign"],
                is_active=True,
                created_at=datetime.now(timezone.utc),
            )
            db.add(category)
            categories_created += 1
            print(f"Added: {cat_data['name']}")

        db.commit()
        print(f"\n✅ Successfully seeded {categories_created} ticket categories")
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_ticket_categories()
