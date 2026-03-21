from fastapi import FastAPI
from app.api.v1 import roles, customerTypes, employees, customers

app = FastAPI(title="Customer Feedback System")

# Đăng ký các router
app.include_router(roles.router, prefix="/api/v1")
app.include_router(customerTypes.router, prefix="/api/v1")
app.include_router(employees.router, prefix="/api/v1")
app.include_router(customers.router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"message": "Welcome to Customer Feedback System API"}