import socketio
from typing import Dict, Optional
from app.core.security import verify_token
from app.socketio.config import CORS_ALLOWED_ORIGINS, CHAT_NAMESPACE
from app.db.session import SessionLocal
from app.schemas.chatSchema import MessageType
import uuid

sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=CORS_ALLOWED_ORIGINS,
    always_connect=True
)

chat_namespace = CHAT_NAMESPACE


def get_ticket_status(ticket_id: str) -> Optional[str]:
    """Get ticket status by ID"""
    from app.db.session import SessionLocal
    from app.models.ticket import Ticket
    import uuid as uuid_lib
    db = SessionLocal()
    try:
        ticket = db.query(Ticket).filter(Ticket.id_ticket == uuid_lib.UUID(ticket_id)).first()
        return ticket.status if ticket else None
    finally:
        db.close()


def save_message_to_db(ticket_id: str, sender_id: str, content: str, message_type: str = 'text'):
    """Helper function to save message to database via ChatService"""
    # Import here to avoid circular import
    from app.services.chatService import ChatService
    
    db = SessionLocal()
    try:
        service = ChatService(db)
        message = service.send_message(
            ticket_id=uuid.UUID(ticket_id),
            sender_id=uuid.UUID(sender_id),
            content=content,
            message_type=MessageType(message_type)
        )
        return message
    finally:
        db.close()


@sio.on('connect', namespace=chat_namespace)
async def on_connect(sid, environ, data=None):
    token = None
    
    # Method 1: If data is a string (direct token)
    if isinstance(data, str) and data:
        token = data
    # Method 2: If data is a dict with token key
    elif isinstance(data, dict):
        token = data.get('token')
    # Method 3: Check environ for socketio auth (nested structure)
    elif isinstance(environ.get('socketio'), dict):
        socketio_auth = environ.get('socketio', {}).get('auth', {})
        if isinstance(socketio_auth, dict):
            token = socketio_auth.get('token')
    
    # Method 4: Fallback to Authorization header
    if not token:
        auth_header = environ.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
    
    if not token:
        print(f"Connection rejected: No token for sid={sid}")
        return False
    
    user_id = verify_token(token, "access")
    if not user_id:
        print(f"Connection rejected: Invalid token for sid={sid}")
        return False
    
    # Store user_id in session
    await sio.save_session(sid, {'user_id': str(user_id)}, namespace=chat_namespace)
    
    room_name = f"user_{user_id}"
    await sio.enter_room(sid, room_name, namespace=chat_namespace)
    return True


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
    await sio.enter_room(sid, room, namespace=chat_namespace)
    await sio.emit('user_joined', {
        'ticket_id': ticket_id,
        'user_id': user_id,
        'sid': sid
    }, to=room, namespace=chat_namespace)


@sio.on('leave_ticket', namespace=chat_namespace)
async def on_leave_ticket(sid, data):
    ticket_id = data.get('ticket_id')
    user_id = data.get('user_id')
    if not ticket_id:
        return

    room = f"ticket_{ticket_id}"
    await sio.leave_room(sid, room, namespace=chat_namespace)
    await sio.emit('user_left', {
        'ticket_id': ticket_id,
        'user_id': user_id,
        'sid': sid
    }, to=room, namespace=chat_namespace)


@sio.on('send_message', namespace=chat_namespace)
async def on_send_message(sid, data):
    ticket_id = data.get('ticket_id')
    user_id = data.get('user_id')
    content = data.get('content')
    message_type = data.get('type', 'text')

    if not all([ticket_id, user_id, content]):
        return

    # Check if ticket is closed
    ticket_status = get_ticket_status(ticket_id)
    if ticket_status == "Closed":
        await sio.emit('message_error', {
            'error': 'Ticket is closed. Cannot send messages.',
            'ticket_id': ticket_id,
            'code': 'TICKET_CLOSED'
        }, to=f"user_{user_id}", namespace=chat_namespace)
        return

    # Save message to database
    try:
        message_out = save_message_to_db(ticket_id, user_id, content, message_type)
    except Exception as e:
        # Emit error back to sender
        await sio.emit('message_error', {
            'error': str(e),
            'ticket_id': ticket_id
        }, room=f"user_{user_id}")
        return

    room = f"ticket_{ticket_id}"
    await sio.emit('new_message', {
        'ticket_id': ticket_id,
        'user_id': user_id,
        'content': message_out.message,
        'type': str(message_out.message_type.value),
        'id_message': str(message_out.id_message),
        'created_at': message_out.created_at.isoformat() if message_out.created_at else None,
        'sender': {
            'id': str(message_out.sender.id) if message_out.sender else None,
            'first_name': message_out.sender.first_name if message_out.sender else None,
            'last_name': message_out.sender.last_name if message_out.sender else None,
            'avatar': message_out.sender.avatar if message_out.sender else None,
        }
    }, to=room, namespace=chat_namespace)


async def broadcast_to_ticket(ticket_id: str, event: str, data: dict):
    room = f"ticket_{ticket_id}"
    await sio.emit(event, data, to=room, namespace=chat_namespace)


@sio.on('typing_start', namespace=chat_namespace)
async def on_typing_start(sid, data):
    ticket_id = data.get('ticket_id')
    user_id = data.get('user_id')
    if not ticket_id:
        return
    room = f"ticket_{ticket_id}"
    await sio.emit('user_typing', {
        'ticket_id': ticket_id,
        'user_id': user_id,
        'is_typing': True
    }, to=room, namespace=chat_namespace)


@sio.on('typing_stop', namespace=chat_namespace)
async def on_typing_stop(sid, data):
    ticket_id = data.get('ticket_id')
    user_id = data.get('user_id')
    if not ticket_id:
        return
    room = f"ticket_{ticket_id}"
    await sio.emit('user_typing', {
        'ticket_id': ticket_id,
        'user_id': user_id,
        'is_typing': False
    }, to=room, namespace=chat_namespace)


@sio.on('mark_read', namespace=chat_namespace)
async def on_mark_read(sid, data):
    """Handle mark messages as read via Socket.IO"""
    ticket_id = data.get('ticket_id')
    user_id = data.get('user_id')
    
    if not ticket_id or not user_id:
        return
    
    # Import here to avoid circular import
    from app.services.chatService import ChatService
    
    db = SessionLocal()
    try:
        service = ChatService(db)
        service.mark_messages_read(uuid.UUID(ticket_id), uuid.UUID(user_id))
    except Exception:
        pass  # Silently handle - read status is not critical
    finally:
        db.close()
    
    # Emit read status change to other users in the ticket room
    room = f"ticket_{ticket_id}"
    await sio.emit('messages_read', {
        'ticket_id': ticket_id,
        'user_id': user_id,
        'read_by': user_id
    }, to=room, namespace=chat_namespace)