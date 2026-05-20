# Chat & Chatbot

## 1. Tổng quan

| Module | Mục đích |
|--------|----------|
| **Chat** | Nhắn tin real-time giữa Customer và Employee thông qua Ticket |
| **Chatbot** | Trợ lý AI tự động trả lời khách hàng, sử dụng Groq LLM |

---

## 2. Database Schema

### Messages (`messages`)
| Cột | Kiểu | Mô tả |
|-----|------|--------|
| id_message | UUID, PK | ID tin nhắn |
| message | Text | Nội dung |
| message_type | String(20) | text / image / file |
| is_read | Boolean | Đã đọc |
| is_deleted | Boolean | Soft delete |
| id_ticket | UUID, FK→tickets | Ticket chứa tin nhắn |
| id_sender | UUID, FK→humans | Người gửi |
| created_at / updated_at | DateTime | Timestamps |

### ChatSession (`chat_sessions`)
| Cột | Kiểu | Mô tả |
|-----|------|--------|
| id_session | UUID, PK | ID phiên |
| customer_id | UUID, FK, UNIQUE | Mỗi customer 1 session |
| created_at / updated_at | DateTime | Timestamps |

### ChatMessage (`chat_messages`)
| Cột | Kiểu | Mô tả |
|-----|------|--------|
| id_message | UUID, PK | ID |
| session_id | UUID, FK→chat_sessions | Phiên chat |
| role | String(20) | "user" / "assistant" |
| content | Text | Nội dung |
| created_at | DateTime | Timestamps |

---

## 3. API Endpoints

### Chat (`/api/v1/chat`)

| Method | Path | Quyền | Mô tả |
|--------|------|-------|--------|
| GET | `/tickets/{ticket_id}/messages` | User | Lịch sử chat (phân trang) |
| POST | `/tickets/{ticket_id}/messages` | User | Gửi tin nhắn (ưu tiên dùng Socket.IO) |
| PATCH | `/tickets/{ticket_id}/read` | User | Đánh dấu đã đọc |
| GET | `/tickets/{ticket_id}/unread-count` | User | Đếm tin chưa đọc |
| GET | `/conversations` | User | Danh sách cuộc hội thoại |
| DELETE | `/tickets/{id}/messages/{msg_id}` | Employee | Xóa tin nhắn |
| PUT | `/tickets/{id}/messages/{msg_id}` | Employee | Sửa tin nhắn |

### Chatbot (`/api/v1/chatbot`)

| Method | Path | Quyền | Mô tả |
|--------|------|-------|--------|
| POST | `/message` | Customer | Gửi tin nhắn cho AI, nhận phản hồi |
| GET | `/session` | Customer | Lịch sử phiên chat AI |
| DELETE | `/session` | Customer | Xóa phiên chat AI |

**Rate Limiting**: 10 tin nhắn/phút mỗi customer (Redis).

---

## 4. Socket.IO Real-time

### Cấu hình
- **Namespace**: `/chat`
- **Auth**: JWT token

### Events (Client → Server)

| Event | Data | Mô tả |
|-------|------|--------|
| `connect` | token | Xác thực JWT, join room `user_{id}` |
| `join_ticket` | {ticket_id, user_id} | Vào phòng ticket |
| `leave_ticket` | {ticket_id, user_id} | Rời phòng ticket |
| `send_message` | {ticket_id, user_id, content, type} | Gửi tin nhắn |
| `typing_start` | {ticket_id, user_id} | Báo đang gõ |
| `typing_stop` | {ticket_id, user_id} | Báo ngừng gõ |
| `mark_read` | {ticket_id, user_id} | Đánh dấu đã đọc |

### Events (Server → Client)

| Event | Mô tả |
|-------|--------|
| `user_joined` | User vào phòng |
| `user_left` | User rời phòng |
| `new_message` | Tin nhắn mới (kèm sender info) |
| `message_error` | Lỗi (VD: ticket closed) |
| `user_typing` | Trạng thái đang gõ |
| `messages_read` | Thông báo đã đọc |

### Room Strategy
- `user_{user_id}`: Room cá nhân (notification, error)
- `ticket_{ticket_id}`: Room theo ticket (messages, typing, read)

---

## 5. Chatbot AI Integration

### Luồng xử lý
```
Customer → POST /chatbot/message
  → Rate limit check (Redis, 10 msg/min)
  → Get/Create ChatSession (1 per customer)
  → Lưu tin nhắn user
  → Build context:
      ├── Customer profile (cached)
      ├── Customer tickets (cached)
      ├── Public FAQ (cached 10 min)
      ├── Departments, Customer types
      ├── Ticket categories, Templates, SLA
  → Build messages (system prompt + context + last 10 messages)
  → Gọi GroqService.chat(messages)
  → Lưu phản hồi AI
  → Trả về response
```

### System Prompt
- AI chỉ trả lời dựa trên context được cung cấp
- Không truy cập thông tin customer khác
- Không bịa thông tin

### Caching Strategy

| Loại | Cache Key | TTL |
|------|-----------|-----|
| Public data (FAQ, dept...) | `chatbot:public_data` | 10 phút |
| Customer profile | `chatbot:customer:{id}:profile` | = token expiry |
| Customer tickets | `chatbot:customer:{id}:tickets` | = token expiry |
| Rate limit | `ratelimit:chatbot:{id}` | 60 giây |

---

## 6. Service Layer

### ChatService
- `send_message()`: Validate participant → Tạo message → Notification
- `validate_participant()`: Kiểm tra user thuộc ticket (403 nếu không)
- `mark_messages_read()`: Đánh dấu tất cả tin từ người khác đã đọc
- `delete_message()`: Soft delete + audit log
- `update_message()`: Cập nhật nội dung + audit log

### ChatbotService
- `send_message()`: Get/create session → Lưu → Build context → Gọi AI → Lưu response
- `_build_context()`: Xây dựng ngữ cảnh cá nhân hóa
- `_get_public_data()`: Cache Redis 10 phút
- `_preload_customer_data()`: Preload cache khi login (retry + exponential backoff)
- `invalidate_public_data_cache()`: Xóa cache khi admin cập nhật FAQ/Department

---

## 7. Kiến trúc

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│  Frontend   │────▶│  Socket.IO   │────▶│  ChatService    │──▶ DB (messages)
│             │     │  /chat ns    │     │  + Notification │
└─────────────┘     └──────────────┘     └─────────────────┘
       │
       │ REST API
       ▼
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│  /chatbot/* │────▶│ChatbotService│────▶│  Groq LLM API   │
│  (REST)     │     │  + Redis     │     │  (AI Response)  │
└─────────────┘     └──────────────┘     └─────────────────┘
```
