# Cách Chạy Test Riêng Lẻ

Tài liệu này hướng dẫn cách chạy test theo từng module riêng lẻ cho repo `Customer-Feedback-System`.

## 1. Chạy Từng File Test Đơn Lẻ

```bash
# Authentication
.venv/bin/python -m pytest tests/test_auth.py -q

# Appointment
.venv/bin/python -m pytest tests/test_appointment.py -q

# Chat
.venv/bin/python -m pytest tests/test_chat.py -q

# Chatbot
.venv/bin/python -m pytest tests/test_chatbot.py -q

# Customer
.venv/bin/python -m pytest tests/test_customer.py -q

# Customer Type
.venv/bin/python -m pytest tests/test_customer_type.py -q

# Department
.venv/bin/python -m pytest tests/test_department.py -q

# Department Assignment
.venv/bin/python -m pytest tests/test_department_assignment.py -q

# Email
.venv/bin/python -m pytest tests/test_email.py -q

# Employee
.venv/bin/python -m pytest tests/test_employee.py -q

# Escalation
.venv/bin/python -m pytest tests/test_escalation.py -q

# Evaluate (CSAT)
.venv/bin/python -m pytest tests/test_evaluate.py -q

# FAQ
.venv/bin/python -m pytest tests/test_faq.py -q

# File
.venv/bin/python -m pytest tests/test_file.py -q

# Groq
.venv/bin/python -m pytest tests/test_groq.py -q

# Load Balancer
.venv/bin/python -m pytest tests/test_load_balancer.py -q

# Notification
.venv/bin/python -m pytest tests/test_notification.py -q

# OTP
.venv/bin/python -m pytest tests/test_otp.py -q

# Redis
.venv/bin/python -m pytest tests/test_redis.py -q

# Role
.venv/bin/python -m pytest tests/test_role.py -q

# Sentiment
.venv/bin/python -m pytest tests/test_sentiment.py -q

# SLA
.venv/bin/python -m pytest tests/test_sla.py -q

# Ticket
.venv/bin/python -m pytest tests/test_ticket.py -q

# Ticket Category
.venv/bin/python -m pytest tests/test_ticket_category.py -q

# Ticket Comment
.venv/bin/python -m pytest tests/test_ticket_comment.py -q

# Ticket History
.venv/bin/python -m pytest tests/test_ticket_history.py -q

# Ticket Template
.venv/bin/python -m pytest tests/test_ticket_template.py -q

# Token Blacklist
.venv/bin/python -m pytest tests/test_token_blacklist.py -q

# Audit Log
.venv/bin/python -m pytest tests/test_audit_log.py -q
```

## 2. Chạy Nhiều Files Cùng Lúc

```bash
# Auth + Appointment
.venv/bin/python -m pytest tests/test_auth.py tests/test_appointment.py -q

# Chat + Chatbot
.venv/bin/python -m pytest tests/test_chat.py tests/test_chatbot.py -q

# Ticket related
.venv/bin/python -m pytest tests/test_ticket.py tests/test_ticket_template.py tests/test_ticket_category.py -q

# Customer related
.venv/bin/python -m pytest tests/test_customer.py tests/test_customer_type.py tests/test_department_assignment.py -q

# Admin services
.venv/bin/python -m pytest tests/test_admin_bulk_ticket.py tests/test_admin_escalation_rule.py tests/test_admin_system_settings.py tests/test_admin_user_admin.py tests/test_admin_workload_report.py -q
```

## 3. Chạy Một Class Trong File

```bash
# Chỉ chạy class TestAppointmentCreation trong test_appointment.py
.venv/bin/python -m pytest tests/test_appointment.py::TestAppointmentCreation -v

# Chỉ chạy class TestAuth trong test_auth.py
.venv/bin/python -m pytest tests/test_auth.py::TestAuth -v

# Chỉ chạy class TestChatbotCache trong test_chatbot.py
.venv/bin/python -m pytest tests/test_chatbot.py::TestChatbotCache -v

# Chỉ chạy class TestTicketCreation trong test_ticket.py
.venv/bin/python -m pytest tests/test_ticket.py::TestTicketCreation -v
```

## 4. Chạy Một Test Cụ Thể

```bash
# Chỉ chạy test_create_appointment_success
.venv/bin/python -m pytest tests/test_appointment.py::TestAppointmentCreation::test_create_appointment_success -v

# Chỉ chạy test_login_success
.venv/bin/python -m pytest tests/test_auth.py::TestAuth::test_login_success -v

# Chỉ chạy test_send_message_creates_notification
.venv/bin/python -m pytest tests/test_chat.py::TestMessageSending::test_send_message_creates_notification -v

# Chỉ chạy test_invalidate_customer_cache
.venv/bin/python -m pytest tests/test_chatbot.py::TestChatbotCache::test_invalidate_customer_cache -v
```

## 5. Chạy Theo Keyword Filter

```bash
# Tất cả test có chữ "appointment"
.venv/bin/python -m pytest tests/ -k "appointment" -q

# Tất cả test có chữ "auth" hoặc "login"
.venv/bin/python -m pytest tests/ -k "auth or login" -q

# Tất cả test có chữ "ticket" nhưng không phải "template"
.venv/bin/python -m pytest tests/ -k "ticket and not template" -q

# Tất cả test bắt đầu bằng "test_create"
.venv/bin/python -m pytest tests/ -k "test_create" -v

# Tất cả test có chữ "rate_limit"
.venv/bin/python -m pytest tests/ -k "rate_limit" -q

# Bỏ slow tests
.venv/bin/python -m pytest tests/ -k "not slow" -q
```

## 6. Chạy Theo Marker

```bash
# Chỉ unit tests
.venv/bin/python -m pytest tests/ -m "unit" -q

# Chỉ integration tests
.venv/bin/python -m pytest tests/ -m "integration" -q

# Chỉ system tests
.venv/bin/python -m pytest tests/ -m "system" -q

# Unit tests nhưng bỏ slow
.venv/bin/python -m pytest tests/ -m "unit and not slow" -q

# Auth marker
.venv/bin/python -m pytest tests/ -m "auth" -q

# Chatbot marker
.venv/bin/python -m pytest tests/ -m "chatbot" -q

# Ticket marker
.venv/bin/python -m pytest tests/ -m "ticket" -q
```

## 7. Chạy Integration và System Test Files

```bash
# Integration tests
.venv/bin/python -m pytest tests/test_api_integration.py -q
.venv/bin/python -m pytest tests/test_integration_critical_flows.py -q

# System/E2E tests (CHẠY RIÊNG để tránh ordering issue)
.venv/bin/python -m pytest tests/test_system_e2e.py -q
```

## 8. Chạy Layers Giống CI

```bash
# Layer 1: Unit tests (bỏ integration và system)
.venv/bin/python -m pytest tests/ \
  --ignore=tests/test_api_integration.py \
  --ignore=tests/test_integration_critical_flows.py \
  --ignore=tests/test_system_e2e.py \
  -q --tb=short

# Layer 2: Integration tests
.venv/bin/python -m pytest \
  tests/test_api_integration.py \
  tests/test_integration_critical_flows.py \
  -q --tb=short

# Layer 3: System/E2E tests (chạy cuối)
.venv/bin/python -m pytest tests/test_system_e2e.py -q --tb=short
```

## 9. Chạy với PostgreSQL

```bash
# Bật PostgreSQL container
docker compose -f docker-compose.test.yml up -d postgres

# Chạy một file với PostgreSQL
TEST_DATABASE_URL="postgresql://testuser:testpass@localhost:5433/testdb" \
.venv/bin/python -m pytest tests/test_appointment.py -q --tb=short

# Chạy toàn bộ suite với PostgreSQL
TEST_DATABASE_URL="postgresql://testuser:testpass@localhost:5433/testdb" \
.venv/bin/python -m pytest tests/ -q --tb=short

# Tắt PostgreSQL khi xong
docker compose -f docker-compose.test.yml down
```

## 10. Chạy Coverage Cho Một File

```bash
# Coverage cho một file
.venv/bin/python -m pytest tests/test_appointment.py --cov=app --cov-report=term-missing -v

# Coverage cho nhiều files
.venv/bin/python -m pytest tests/test_auth.py tests/test_appointment.py --cov=app --cov-report=term-missing -v

# Coverage cho toàn bộ tests
.venv/bin/python -m pytest tests/ --cov=app --cov-report=term-missing --cov-report=xml -q
```

## 11. Các Lệnh Tiện Ích

```bash
# Xem tất cả tests trong một file (không chạy)
.venv/bin/python -m pytest tests/test_appointment.py --collect-only -q

# Xem tất cả tests có marker nào đó
.venv/bin/python -m pytest tests/ -m "unit" --collect-only -q

# Chạy với verbose output
.venv/bin/python -m pytest tests/test_appointment.py -v

# Chạy với short traceback
.venv/bin/python -m pytest tests/test_appointment.py -q --tb=short

# Chạy và hiện reason cho skipped tests
.venv/bin/python -m pytest tests/ -q -rs

# Chạy với stdout/stderr capture bị bỏ
.venv/bin/python -m pytest tests/test_appointment.py -q --disable-warnings

# Dừng ở first failure
.venv/bin/python -m pytest tests/test_appointment.py -x -v

# Chạy lại failed tests từ lần trước
.venv/bin/python -m pytest tests/ --lf -v
```

## 12. Tóm Tắt Nhanh

| Mục đích | Lệnh |
|----------|------|
| Một file | `.venv/bin/python -m pytest tests/test_xxx.py -q` |
| Nhiều files | `.venv/bin/python -m pytest tests/test_a.py tests/test_b.py -q` |
| Một class | `.venv/bin/python -m pytest tests/test_xxx.py::ClassName -v` |
| Một test | `.venv/bin/python -m pytest tests/test_xxx.py::ClassName::test_name -v` |
| Filter keyword | `.venv/bin/python -m pytest tests/ -k "keyword" -q` |
| Theo marker | `.venv/bin/python -m pytest tests/ -m "marker_name" -q` |
| System/E2E (riêng) | `.venv/bin/python -m pytest tests/test_system_e2e.py -q` |

## Lưu Ý Quan Trọng

- **`test_system_e2e.py`** nên chạy riêng hoặc cuối cùng để tránh test ordering issues
- Nếu gặp lỗi `module not found`, đảm bảo đang dùng `.venv/bin/python`
- Dùng `-q` để quiet output, `-v` để verbose
- Dùng `--tb=short` để xem ngắn gọn lỗi