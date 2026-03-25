import socketio
from typing import Dict, Optional
from app.core.security import verify_token
from app.socketio.config import CORS_ALLOWED_ORIGINS, CHAT_NAMESPACE

sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=CORS_ALLOWED_ORIGINS,
    always_connect=True
)

chat_namespace = CHAT_NAMESPACE


@sio.on('connect', namespace=chat_namespace)
async def on_connect(sid, environ):
    auth_token = environ.get('HTTP_AUTHORIZATION', '')
    if auth_token.startswith('Bearer '):
        token = auth_token[7:]
        user_id = verify_token(token, "access")
        if not user_id:
            return False
        return True
    return False


@sio.on('disconnect', namespace=chat_namespace)
async def on_disconnect(sid):
    pass


@sio.on('join_ticket', namespace=chat_namespace)
async def on_join_ticket(sid, data):
    ticket_id = data.get('ticket_id')
    user_id = data.get('user_id')
    if not ticket_id or not user_id:
        return
    
    room = f"ticket_{ticket_id}"
    await sio.enter_room(sid, room)
    await sio.to(room).emit('user_joined', {
        'ticket_id': ticket_id,
        'user_id': user_id,
        'sid': sid
    })


@sio.on('leave_ticket', namespace=chat_namespace)
async def on_leave_ticket(sid, data):
    ticket_id = data.get('ticket_id')
    user_id = data.get('user_id')
    if not ticket_id:
        return
    
    room = f"ticket_{ticket_id}"
    await sio.leave_room(sid, room)
    await sio.to(room).emit('user_left', {
        'ticket_id': ticket_id,
        'user_id': user_id,
        'sid': sid
    })


@sio.on('send_message', namespace=chat_namespace)
async def on_send_message(sid, data):
    ticket_id = data.get('ticket_id')
    user_id = data.get('user_id')
    content = data.get('content')
    message_type = data.get('type', 'text')
    
    if not all([ticket_id, user_id, content]):
        return
    
    room = f"ticket_{ticket_id}"
    await sio.to(room).emit('new_message', {
        'ticket_id': ticket_id,
        'user_id': user_id,
        'content': content,
        'type': message_type,
        'sid': sid
    })


async def broadcast_to_ticket(ticket_id: str, event: str, data: dict):
    room = f"ticket_{ticket_id}"
    await sio.to(room).emit(event, data)


@sio.on('typing_start', namespace=chat_namespace)
async def on_typing_start(sid, data):
    ticket_id = data.get('ticket_id')
    user_id = data.get('user_id')
    if not ticket_id:
        return
    room = f"ticket_{ticket_id}"
    await sio.to(room).emit('user_typing', {
        'ticket_id': ticket_id,
        'user_id': user_id,
        'is_typing': True
    })


@sio.on('typing_stop', namespace=chat_namespace)
async def on_typing_stop(sid, data):
    ticket_id = data.get('ticket_id')
    user_id = data.get('user_id')
    if not ticket_id:
        return
    room = f"ticket_{ticket_id}"
    await sio.to(room).emit('user_typing', {
        'ticket_id': ticket_id,
        'user_id': user_id,
        'is_typing': False
    })