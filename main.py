from fastapi import FastAPI
from app.api.v1 import roles, customerTypes, employees, customers, auth

app = FastAPI(title="Customer Feedback System")

# Đăng ký các router
app.include_router(auth.router, prefix="/api/v1")
app.include_router(roles.router, prefix="/api/v1")
app.include_router(customerTypes.router, prefix="/api/v1")
app.include_router(employees.router, prefix="/api/v1")
app.include_router(customers.router, prefix="/api/v1")
