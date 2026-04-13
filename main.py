from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import socketio
import os
from app.api.v1 import roles, customerTypes, employees, customers, auth, user, ticketCategories, tickets, departments, \
    faq, chat, audit, sla, evaluate, notification, cloudinary_signatures, department_assignments, ticketComments, ticketHistory, \
    templates, chatbot
from app.socketio.manager import sio

app = FastAPI(title="Customer Feedback System")

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
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
app.include_router(templates.router, prefix="/api/v1")
app.include_router(ticketComments.router, prefix="/api/v1")
app.include_router(ticketHistory.router, prefix="/api/v1")
app.include_router(departments.router, prefix="/api/v1")
app.include_router(faq.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(cloudinary_signatures.router, prefix="/api/v1")
app.include_router(audit.router, prefix="/api/v1")
app.include_router(sla.router, prefix="/api/v1")
app.include_router(evaluate.router, prefix="/api/v1")
app.include_router(notification.router, prefix="/api/v1")
app.include_router(department_assignments.router, prefix="/api/v1")
app.include_router(chatbot.router, prefix="/api/v1")

socket_app = socketio.ASGIApp(sio, app)
app.mount("/socket.io", socket_app)