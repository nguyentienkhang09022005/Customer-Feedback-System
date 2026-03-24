from fastapi import FastAPI
from app.api.v1 import roles, customerTypes, employees, customers, auth, user, ticketCategories, tickets, departments, \
    faq

app = FastAPI(title="Customer Feedback System")

# Đăng ký các router
app.include_router(auth.router, prefix="/api/v1")
app.include_router(user.router, prefix="/api/v1")
app.include_router(roles.router, prefix="/api/v1")
app.include_router(customerTypes.router, prefix="/api/v1")
app.include_router(employees.router, prefix="/api/v1")
app.include_router(customers.router, prefix="/api/v1")
app.include_router(ticketCategories.router, prefix="/api/v1")
app.include_router(tickets.router, prefix="/api/v1")
app.include_router(departments.router, prefix="/api/v1")
app.include_router(faq.router, prefix="/api/v1")