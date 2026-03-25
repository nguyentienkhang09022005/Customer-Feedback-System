from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import socketio
from app.api.v1 import roles, customerTypes, employees, customers, auth, user, ticketCategories, tickets, departments, \
    faq, chat, audit, sla
from app.socketio.manager import sio

app = FastAPI(title="Customer Feedback System")

app.add_middleware(
    CORSMiddleware,
    allow_origins="*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
app.include_router(chat.router, prefix="/api/v1")
app.include_router(audit.router, prefix="/api/v1")
app.include_router(sla.router, prefix="/api/v1")

socket_app = socketio.ASGIApp(sio, app)
app.mount("/socket.io", socket_app)