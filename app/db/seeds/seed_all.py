import uuid
from datetime import datetime, timezone
from app.db.session import SessionLocal
from app.models.department import Department
from app.models.human import Human, Employee, Customer, Role, CustomerType
from app.models.ticket import TicketCategory, SLAPolicy, Ticket
from app.models.interaction import Message, Evaluate, Attachment, Notification
from app.models.system import FAQArticle, AuditLog


DEPARTMENTS = {
    "Finance": "73044748-c595-4892-bd30-9edc2b2f1e8d",
    "HR": "fdfe2b16-07bd-40c2-b9fc-994fe73e6667",
    "IT": "2a55f1e3-aa8f-4d06-b83b-6aead44fb8e5",
    "Support": "87faf75c-49ea-4023-acd5-27fa4fba97b1",
    "Sales": "1a33ba9e-ee6f-4f26-b67f-3ad77f083380",
}

EMPLOYEE_DATA = [
    {
        "username": "admin",
        "email": "admin@company.com",
        "first_name": "System",
        "last_name": "Admin",
        "password_hash": "password123",
        "id_department": DEPARTMENTS["IT"],
        "role_name": "Admin",
        "job_title": "System Administrator",
    },
    {
        "username": "employee1",
        "email": "employee1@company.com",
        "first_name": "Nguyen",
        "last_name": "Agent One",
        "password_hash": "password123",
        "id_department": DEPARTMENTS["Support"],
        "role_name": "Employee",
        "job_title": "Support Agent",
    },
    {
        "username": "employee2",
        "email": "employee2@company.com",
        "first_name": "Tran",
        "last_name": "Agent Two",
        "password_hash": "password123",
        "id_department": DEPARTMENTS["Support"],
        "role_name": "Employee",
        "job_title": "Support Agent",
    },
    {
        "username": "employee3",
        "email": "employee3@company.com",
        "first_name": "Le",
        "last_name": "HR Staff",
        "password_hash": "password123",
        "id_department": DEPARTMENTS["HR"],
        "role_name": "Employee",
        "job_title": "HR Specialist",
    },
    {
        "username": "employee4",
        "email": "employee4@company.com",
        "first_name": "Pham",
        "last_name": "IT Staff",
        "password_hash": "password123",
        "id_department": DEPARTMENTS["IT"],
        "role_name": "Employee",
        "job_title": "IT Technician",
    },
]

CUSTOMER_DATA = [
    {
        "username": "customer1",
        "email": "cust1@email.com",
        "first_name": "John",
        "last_name": "Doe",
        "password_hash": "password123",
        "customer_type": "Individual",
        "membership_tier": "Silver",
    },
    {
        "username": "customer2",
        "email": "cust2@email.com",
        "first_name": "Jane",
        "last_name": "Smith",
        "password_hash": "password123",
        "customer_type": "Corporate",
        "membership_tier": "Gold",
    },
    {
        "username": "customer3",
        "email": "cust3@email.com",
        "first_name": "Bob",
        "last_name": "Wilson",
        "password_hash": "password123",
        "customer_type": "VIP",
        "membership_tier": "Platinum",
    },
    {
        "username": "customer4",
        "email": "cust4@email.com",
        "first_name": "Alice",
        "last_name": "Brown",
        "password_hash": "password123",
        "customer_type": "Individual",
        "membership_tier": "Bronze",
    },
    {
        "username": "customer5",
        "email": "cust5@email.com",
        "first_name": "Charlie",
        "last_name": "Davis",
        "password_hash": "password123",
        "customer_type": "Corporate",
        "membership_tier": "Silver",
    },
]

TICKET_CATEGORIES = [
    "Bug Report",
    "Feature Request",
    "General Inquiry",
    "Complaint",
    "Question",
    "Feedback",
    "HR Related",
    "Finance Inquiry",
]

TICKET_DATA = [
    {
        "title": "Cannot login to system",
        "description": "I am getting an error when trying to login",
        "status": "New",
        "severity": "High",
        "category_name": "Bug Report",
    },
    {
        "title": "Request new dashboard feature",
        "description": "Please add analytics dashboard",
        "status": "New",
        "severity": "Medium",
        "category_name": "Feature Request",
    },
    {
        "title": "How to reset password?",
        "description": "I forgot my password, how do I reset it?",
        "status": "New",
        "severity": "Low",
        "category_name": "Question",
    },
    {
        "title": "Slow response time",
        "description": "The system is running very slowly today",
        "status": "In Progress",
        "severity": "Medium",
        "category_name": "Complaint",
    },
    {
        "title": "Billing question",
        "description": "I have a question about my invoice",
        "status": "In Progress",
        "severity": "Low",
        "category_name": "Finance Inquiry",
    },
    {
        "title": "Add dark mode",
        "description": "Would be nice to have dark mode option",
        "status": "In Progress",
        "severity": "Low",
        "category_name": "Feedback",
    },
    {
        "title": "Email notification not working",
        "description": "Not receiving email notifications",
        "status": "Resolved",
        "severity": "High",
        "category_name": "Bug Report",
    },
    {
        "title": "Request API access",
        "description": "Need API access for integration",
        "status": "Resolved",
        "severity": "Medium",
        "category_name": "Feature Request",
    },
    {
        "title": "General feedback on service",
        "description": "Great service overall!",
        "status": "Resolved",
        "severity": "Low",
        "category_name": "Feedback",
    },
    {
        "title": "Product inquiry",
        "description": "Do you offer enterprise plans?",
        "status": "Closed",
        "severity": "Low",
        "category_name": "General Inquiry",
    },
    {
        "title": "Complaint about support",
        "description": "Long wait time for support",
        "status": "Closed",
        "severity": "Medium",
        "category_name": "Complaint",
    },
    {
        "title": "HR policy question",
        "description": "Question about vacation policy",
        "status": "Closed",
        "severity": "Low",
        "category_name": "HR Related",
    },
]

SLA_POLICIES = [
    {"policy_name": "Critical SLA", "severity": "Critical", "max_resolution_minutes": 30},
    {"policy_name": "High SLA", "severity": "High", "max_resolution_minutes": 120},
    {"policy_name": "Medium SLA", "severity": "Medium", "max_resolution_minutes": 480},
    {"policy_name": "Low SLA", "severity": "Low", "max_resolution_minutes": 1440},
]

FAQ_ARTICLES = [
    {
        "title": "How to reset your password",
        "content": "Click on 'Forgot Password' on the login page and follow the instructions.",
        "id_category": "Question",
    },
    {
        "title": "How to contact support",
        "content": "You can contact support via email at support@company.com or call our hotline.",
        "id_category": "General Inquiry",
    },
    {
        "title": "Billing and payments",
        "content": "We accept credit cards, bank transfers, and PayPal. Invoices are sent monthly.",
        "id_category": "Finance Inquiry",
    },
    {
        "title": "How to upgrade your plan",
        "content": "Go to Settings > Subscription > Upgrade Plan to see available options.",
        "id_category": "General Inquiry",
    },
]


def seed_all():
    db = SessionLocal()
    try:
        print("=" * 50)
        print("SEEDING DATABASE")
        print("=" * 50)

        seed_roles(db)
        seed_customer_types(db)
        seed_departments(db)
        seed_humans_and_employees(db)
        seed_humans_and_customers(db)
        seed_ticket_categories(db)
        seed_sla_policies(db)
        seed_tickets(db)
        seed_messages(db)
        seed_evaluates(db)
        seed_faq_articles(db)

        db.commit()
        print("\n" + "=" * 50)
        print("✅ SEEDING COMPLETED SUCCESSFULLY")
        print("=" * 50)
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error: {e}")
        raise
    finally:
        db.close()


def seed_roles(db):
    print("\n[1/11] Seeding roles...")
    roles = [
        {"role_name": "Admin", "description": "Quản trị hệ thống"},
        {"role_name": "Employee", "description": "Nhân viên hỗ trợ"},
        {"role_name": "Customer", "description": "Khách hàng"},
    ]
    count = 0
    for r in roles:
        existing = db.query(Role).filter(Role.role_name == r["role_name"]).first()
        if existing:
            print(f"  Skipped (exists): {r['role_name']}")
            continue
        role = Role(role_name=r["role_name"], description=r["description"])
        db.add(role)
        count += 1
        print(f"  Added: {r['role_name']}")
    db.flush()
    print(f"  → {count} roles added")


def seed_customer_types(db):
    print("\n[2/11] Seeding customer types...")
    types = [
        {"type_name": "Individual", "description": "Khách hàng cá nhân"},
        {"type_name": "Corporate", "description": "Khách hàng doanh nghiệp"},
        {"type_name": "VIP", "description": "Khách hàng VIP"},
    ]
    count = 0
    for t in types:
        existing = db.query(CustomerType).filter(CustomerType.type_name == t["type_name"]).first()
        if existing:
            print(f"  Skipped (exists): {t['type_name']}")
            continue
        ct = CustomerType(type_name=t["type_name"], description=t["description"])
        db.add(ct)
        count += 1
        print(f"  Added: {t['type_name']}")
    db.flush()
    print(f"  → {count} customer types added")


def seed_departments(db):
    print("\n[3/11] Seeding departments...")
    departments = [
        {"name": "IT", "description": "Phòng Công Nghệ Thông Tin"},
        {"name": "HR", "description": "Phòng Nhân Sự"},
        {"name": "Finance", "description": "Phòng Tài Chính"},
        {"name": "Support", "description": "Phòng Hỗ Trợ Khách Hàng"},
        {"name": "Sales", "description": "Phòng Kinh Doanh"},
    ]
    count = 0
    for d in departments:
        existing = db.query(Department).filter(Department.name == d["name"]).first()
        if existing:
            print(f"  Skipped (exists): {d['name']}")
            continue
        dept = Department(
            id_department=uuid.UUID(DEPARTMENTS[d["name"]]),
            name=d["name"],
            description=d["description"],
            is_active=True,
        )
        db.add(dept)
        count += 1
        print(f"  Added: {d['name']}")
    db.flush()
    print(f"  → {count} departments added")


def seed_humans_and_employees(db):
    print("\n[4/11] Seeding employees...")
    count = 0
    employee_ids = {}
    for emp_data in EMPLOYEE_DATA:
        existing = db.query(Human).filter(Human.username == emp_data["username"]).first()
        if existing:
            print(f"  Skipped (exists): {emp_data['username']}")
            emp = db.query(Employee).filter(Employee.id_employee == existing.id).first()
            if emp:
                employee_ids[emp_data["username"]] = emp.id_employee
            continue

        emp_id = uuid.uuid4()
        employee = Employee(
            id_employee=emp_id,
            username=emp_data["username"],
            email=emp_data["email"],
            first_name=emp_data["first_name"],
            last_name=emp_data["last_name"],
            password_hash=emp_data["password_hash"],
            status="Active",
            type="employee",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            id_department=uuid.UUID(emp_data["id_department"]),
            role_name=emp_data["role_name"],
            job_title=emp_data["job_title"],
            max_ticket_capacity=5,
            csat_score=0.0,
        )
        db.add(employee)
        employee_ids[emp_data["username"]] = emp_id
        count += 1
        print(f"  Added: {emp_data['username']}")
    db.flush()
    print(f"  → {count} employees added")
    return employee_ids


def seed_humans_and_customers(db):
    print("\n[5/11] Seeding customers...")
    count = 0
    customer_ids = {}
    for cust_data in CUSTOMER_DATA:
        existing = db.query(Human).filter(Human.username == cust_data["username"]).first()
        if existing:
            print(f"  Skipped (exists): {cust_data['username']}")
            cust = db.query(Customer).filter(Customer.id_customer == existing.id).first()
            if cust:
                customer_ids[cust_data["username"]] = cust.id_customer
            continue

        cust_id = uuid.uuid4()
        customer = Customer(
            id_customer=cust_id,
            username=cust_data["username"],
            email=cust_data["email"],
            first_name=cust_data["first_name"],
            last_name=cust_data["last_name"],
            password_hash=cust_data["password_hash"],
            status="Active",
            type="customer",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            customer_type=cust_data["customer_type"],
            membership_tier=cust_data["membership_tier"],
        )
        db.add(customer)
        customer_ids[cust_data["username"]] = cust_id
        count += 1
        print(f"  Added: {cust_data['username']}")
    db.flush()
    print(f"  → {count} customers added")
    return customer_ids


def seed_ticket_categories(db):
    print("\n[6/11] Seeding ticket categories...")
    categories = [
        {"name": "Bug Report", "description": "Báo lỗi hệ thống", "id_department": DEPARTMENTS["IT"]},
        {"name": "Feature Request", "description": "Yêu cầu tính năng mới", "id_department": DEPARTMENTS["IT"]},
        {"name": "General Inquiry", "description": "Câu hỏi chung", "id_department": DEPARTMENTS["Support"]},
        {"name": "Complaint", "description": "Khiếu nại", "id_department": DEPARTMENTS["Support"]},
        {"name": "Question", "description": "Hỏi đáp", "id_department": DEPARTMENTS["Support"]},
        {"name": "Feedback", "description": "Góp ý", "id_department": DEPARTMENTS["Sales"]},
        {"name": "HR Related", "description": "Nhân sự", "id_department": DEPARTMENTS["HR"]},
        {"name": "Finance Inquiry", "description": "Câu hỏi tài chính", "id_department": DEPARTMENTS["Finance"]},
    ]
    count = 0
    for cat in categories:
        existing = db.query(TicketCategory).filter(TicketCategory.name == cat["name"]).first()
        if existing:
            print(f"  Skipped (exists): {cat['name']}")
            continue
        tc = TicketCategory(
            id_category=uuid.uuid4(),
            name=cat["name"],
            description=cat["description"],
            id_department=uuid.UUID(cat["id_department"]),
            auto_assign=True,
            is_active=True,
        )
        db.add(tc)
        count += 1
        print(f"  Added: {cat['name']}")
    db.flush()
    print(f"  → {count} ticket categories added")


def seed_sla_policies(db):
    print("\n[7/11] Seeding SLA policies...")
    count = 0
    for sla in SLA_POLICIES:
        existing = db.query(SLAPolicy).filter(
            SLAPolicy.policy_name == sla["policy_name"]
        ).first()
        if existing:
            print(f"  Skipped (exists): {sla['policy_name']}")
            continue
        policy = SLAPolicy(
            id_policy=uuid.uuid4(),
            policy_name=sla["policy_name"],
            severity=sla["severity"],
            max_resolution_minutes=sla["max_resolution_minutes"],
            is_active=True,
        )
        db.add(policy)
        count += 1
        print(f"  Added: {sla['policy_name']}")
    db.flush()
    print(f"  → {count} SLA policies added")


def seed_tickets(db):
    print("\n[8/11] Seeding tickets...")
    employee_ids = [e[0] for e in db.query(Employee.id_employee).all()]
    customer_ids = [c[0] for c in db.query(Customer.id_customer).all()]
    categories = db.query(TicketCategory).all()
    cat_map = {c.name: c.id_category for c in categories}

    count = 0
    ticket_ids = []
    for i, t_data in enumerate(TICKET_DATA):
        ticket = Ticket(
            id_ticket=uuid.uuid4(),
            title=t_data["title"],
            description=t_data["description"],
            status=t_data["status"],
            severity=t_data["severity"],
            version=1,
            id_category=cat_map.get(t_data["category_name"]),
            id_employee=employee_ids[i % len(employee_ids)] if employee_ids else None,
            id_customer=customer_ids[i % len(customer_ids)],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(ticket)
        ticket_ids.append(ticket.id_ticket)
        count += 1
        print(f"  Added: {t_data['title'][:40]}...")
    db.flush()
    print(f"  → {count} tickets added")
    return ticket_ids


def seed_messages(db):
    print("\n[9/11] Seeding messages...")
    tickets = db.query(Ticket).all()
    humans = db.query(Human).all()
    human_ids = [h.id for h in humans]

    if not tickets or not human_ids:
        print("  Skipped: no tickets or humans found")
        return

    messages_data = [
        "Thank you for contacting us. We will assist you shortly.",
        "Could you please provide more details about your issue?",
        "We are working on resolving your request.",
        "Your issue has been escalated to our technical team.",
        "Is there anything else we can help you with?",
    ]

    count = 0
    for i, ticket in enumerate(tickets[:6]):
        msg = Message(
            id_message=uuid.uuid4(),
            message=messages_data[i % len(messages_data)],
            is_deleted=False,
            id_ticket=ticket.id_ticket,
            id_sender=human_ids[i % len(human_ids)],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(msg)
        count += 1
        print(f"  Added message for ticket: {ticket.title[:30]}...")
    db.flush()
    print(f"  → {count} messages added")


def seed_evaluates(db):
    print("\n[10/11] Seeding evaluations...")
    tickets = db.query(Ticket).filter(Ticket.status.in_(["Resolved", "Closed"])).all()
    customer_ids = [c[0] for c in db.query(Customer.id_customer).all()]

    if not tickets or not customer_ids:
        print("  Skipped: no resolved/closed tickets or customers found")
        return

    comments = [
        "Great service!",
        "Issue was resolved quickly.",
        "Could be better.",
        "Excellent support team.",
        "Satisfied with the resolution.",
    ]

    count = 0
    for i, ticket in enumerate(tickets[:6]):
        eval = Evaluate(
            id_evaluate=uuid.uuid4(),
            star=(i % 5) + 1,
            comment=comments[i % len(comments)],
            id_ticket=ticket.id_ticket,
            id_customer=customer_ids[i % len(customer_ids)],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(eval)
        count += 1
        print(f"  Added evaluation for ticket: {ticket.title[:30]}...")
    db.flush()
    print(f"  → {count} evaluations added")


def seed_faq_articles(db):
    print("\n[11/11] Seeding FAQ articles...")
    employees = db.query(Employee).all()
    categories = db.query(TicketCategory).all()
    cat_map = {c.name: c.id_category for c in categories}

    if not employees:
        print("  Skipped: no employees found")
        return

    count = 0
    for faq in FAQ_ARTICLES:
        article = FAQArticle(
            id_article=uuid.uuid4(),
            title=faq["title"],
            content=faq["content"],
            view_count=0,
            is_published=True,
            id_category=cat_map.get(faq.get("id_category")),
            id_author=employees[0].id_employee if employees else None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(article)
        count += 1
        print(f"  Added: {faq['title']}")
    db.flush()
    print(f"  → {count} FAQ articles added")


if __name__ == "__main__":
    seed_all()
