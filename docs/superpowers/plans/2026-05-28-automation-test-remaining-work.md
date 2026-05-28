# Automation Test - Remaining Work Implementation Plan

**Goal:** Bring the automation test suite to full coverage by fixing 38 failing tests, adding missing service tests, completing integration flows, stabilizing PostgreSQL/Redis layers, and validating CI.

**Architecture:** Work is decomposed into 7 sequential phases. Each phase focuses on one area. Phases are independent but ordered so infrastructure phases come before their dependent test phases.

**Tech Stack:** FastAPI, SQLAlchemy, pytest, pytest-asyncio, pytest-cov, SQLite (default), PostgreSQL (opt-in), Redis (for caching), GitHub Actions CI.

---

## Phase A: Fix 38 Failing Tests

### Target: Reduce failing tests from 38 to near-zero.

**Files to modify:**
- `tests/conftest.py` — fix fixtures causing failures
- `tests/test_api_integration.py` — fix API integration test failures
- `tests/test_ticket_template.py` — fix SQLite composite PK collision
- `tests/test_appointment.py` — fix appointment state transition tests
- `tests/test_chatbot.py` — fix chatbot mock/error tests
- `tests/test_chat.py` — fix chat notification test
- `tests/test_system_e2e.py` — fix E2E tests (largest group)

### A.1: Fix `test_api_integration.py` (11 failures)

The primary issue is `AttributeError` — tests reference `app` or `client` that is None due to fixture lifetime.

- [ ] **Step 1: Read `tests/conftest.py`** — Find the `app` fixture and `get_client()` helper. Identify why `TestClient` is not persisting across tests in `test_api_integration.py`.

- [ ] **Step 2: Run one failing test with full traceback**

```
.venv/bin/python -m pytest tests/test_api_integration.py::TestAuthAPI::test_login_success -v --tb=short
```

Expected: `AttributeError: 'NoneType' object has no attribute 'post'`

- [ ] **Step 3: Fix the `client` fixture in `conftest.py`**

The `client` fixture creates a fresh `TestClient` per test but `test_api_integration.py` uses a class-based `TestAuthAPI` with `setup_method` that calls `get_client()`. The problem is `get_client()` references `app` which may not be initialized. Replace class-level `client` usage with module-level fixture injection.

```python
# In tests/conftest.py, ensure this pattern works:
@pytest.fixture
def client(app):
    with TestClient(app) as c:
        yield c
```

- [ ] **Step 4: Run all 11 failing tests**

```
.venv/bin/python -m pytest tests/test_api_integration.py -v --tb=short -x
```

Expected: First test passes, stop at next failure. Fix each failure's root cause.

- [ ] **Step 5: Verify all `test_api_integration.py` tests pass**

```
.venv/bin/python -m pytest tests/test_api_integration.py -q --tb=no
```

Expected: `38 passed` (all pass, 0 failures)

### A.2: Fix `test_ticket_template.py` (3 failures — SQLite composite PK)

Root cause: When creating version 2 of a template, SQLite enforces uniqueness on `id_template` alone because `id_template` is the primary key. The model comment says composite PK `(id_template, version)` but the actual column definition only uses `id_template` as PK.

- [ ] **Step 1: Read `app/models/ticket.py` lines 35-62** — Check if `version` is part of the primary key in the model definition.

- [ ] **Step 2: Run failing test to confirm error**

```
.venv/bin/python -m pytest tests/test_ticket_template.py::TestGetTemplate::test_get_all_versions -v --tb=short
```

Expected: `UNIQUE constraint failed: ticket_templates.id_template`

- [ ] **Step 3: Fix the model to use composite PK**

Add `PrimaryKeyConstraint` on both `id_template` AND `version`:

```python
from sqlalchemy import PrimaryKeyConstraint

__table_args__ = (
    PrimaryKeyConstraint(id_template, version, name="pk_ticket_template"),
    UniqueConstraint(id_template, version, name="uq_ticket_template_id_version"),
)
```

Also ensure `version_id_col` mapper args is NOT set on `TicketTemplate` (only `Ticket` has it).

- [ ] **Step 4: Run all 3 failing tests**

```
.venv/bin/python -m pytest tests/test_ticket_template.py::TestGetTemplate::test_get_all_versions tests/test_ticket_template.py::TestUpdateTemplate::test_update_template_with_fields_config_creates_new_version tests/test_ticket_template.py::TestUpdateTemplate::test_update_template_deactivates_previous_version -v --tb=short
```

Expected: All 3 pass

- [ ] **Step 5: Verify all `test_ticket_template.py` tests pass**

```
.venv/bin/python -m pytest tests/test_ticket_template.py -q --tb=no
```

Expected: `26 passed, 0 failed`

### A.3: Fix `test_appointment.py` (4 failures)

Root cause: Tests expect certain appointment state transitions to fail but the service allows them.

- [ ] **Step 1: Run the failing appointment tests**

```
.venv/bin/python -m pytest tests/test_appointment.py -v --tb=short 2>&1 | grep -A10 "FAILED"
```

- [ ] **Step 2: Read `tests/test_appointment.py`** — Find `test_create_appointment_existing_pending`, `test_cancel_rejected_appointment_fails`, `test_cancel_completed_appointment_fails`.

- [ ] **Step 3: Read `app/services/appointmentService.py`** — Understand `create_appointment` and `cancel_appointment` methods. Determine if service correctly prevents duplicate pending appointments or if test expectations are wrong.

- [ ] **Step 4: Fix the service or the test**

If the service allows creating a pending appointment when one already exists (bug), fix the service:

```python
def create_appointment(self, db, employee_id, customer_id, ...):
    existing = db.query(Appointment).filter(
        Appointment.id_customer == customer_id,
        Appointment.status == "pending"
    ).first()
    if existing:
        raise ValueError("Customer already has a pending appointment")
```

If the service already has this check and the test doesn't match the actual logic, update the test assertion.

- [ ] **Step 5: Run all appointment tests**

```
.venv/bin/python -m pytest tests/test_appointment.py -q --tb=no
```

Expected: `0 failed` (all pass)

### A.4: Fix `test_chatbot.py` (4 failures)

Root cause: Mock setup issues — tests mock `groqService` but the actual code path doesn't use the mocked version.

- [ ] **Step 1: Run failing chatbot tests**

```
.venv/bin/python -m pytest tests/test_chatbot.py -v --tb=short 2>&1 | grep -A5 "FAILED"
```

- [ ] **Step 2: Read `tests/test_chatbot.py` lines 150-300** — Find the failing tests: `test_send_message_groq_error`, `test_invalidate_customer_cache`, `test_rate_limit_blocks_excessive_requests`.

- [ ] **Step 3: Read `app/services/chatbotService.py`** — Trace how `groqService` is called. The mock needs to patch the right import path.

- [ ] **Step 4: Fix mock patch paths**

```python
# Wrong:
@patch('app.services.chatbotService.groq_service')
# Correct (depends on how groq_service is imported in chatbotService):
@patch('app.services.groqService.GroqService')
# or
@patch('app.services.chatbotService.GroqService')
```

- [ ] **Step 5: Run all chatbot tests**

```
.venv/bin/python -m pytest tests/test_chatbot.py -q --tb=no
```

Expected: `0 failed`

### A.5: Fix `test_chat.py` (1 failure)

- [ ] **Step 1: Run `test_send_message_creates_notification`**

```
.venv/bin/python -m pytest tests/test_chat.py::TestMessageSending::test_send_message_creates_notification -v --tb=short
```

- [ ] **Step 2: Read `tests/test_chat.py`** — Find the notification assertion.

- [ ] **Step 3: Read `app/services/chatService.py`** — Find `send_message` and check if it creates a notification.

- [ ] **Step 4: Fix test assertion or service** — If the service doesn't create notification, either add it or fix the test to not expect it.

- [ ] **Step 5: Verify pass**

```
.venv/bin/python -m pytest tests/test_chat.py -q --tb=no
```

### A.6: Fix `test_system_e2e.py` (19 failures — largest group)

Root cause: Multiple causes — token blacklist, ticket from template, ticket reopen, customer access control, CSAT evaluation, rate limiting, template validation, appointments.

- [ ] **Step 1: Run all system E2E tests to get full failure list**

```
.venv/bin/python -m pytest tests/test_system_e2e.py -v --tb=no 2>&1 | grep "FAILED"
```

- [ ] **Step 2: Categorize failures into groups:**
   - Auth/logout token blacklist (1 failure)
   - Ticket from template (1 failure)
   - Ticket reopen (2 failures)
   - Customer access control (2 failures)
   - CSAT evaluation (3 failures)
   - Rate limiting (2 failures)
   - Template validation (3 failures)
   - Appointment (1 failure)

- [ ] **Step 3: Run each failure with full traceback, fix category-by-category**

Common fixes:
- Token blacklist: `app` not initialized before `client` in fixture
- Ticket from template: Template service returns None or version mismatch
- Customer access: Role check logic differs between test expectation and actual RBAC
- CSAT: Survey already sent or ticket not in correct status
- Rate limiting: Redis not available in test environment
- Template validation: Template deleted/inactive state check missing in service
- Appointment: Session/app fixture issue

- [ ] **Step 4: Verify all system E2E tests pass**

```
.venv/bin/python -m pytest tests/test_system_e2e.py -q --tb=no
```

Expected: `0 failed` (or minimal failures that are known/acceptable)

---

## Phase B: Add Missing Service Tests

### Target: Ensure all 30 services have at least basic test coverage.

**Files to create:**
- `tests/test_audit_log.py` — for `auditLogService`
- `tests/test_customer_type.py` — for `customerTypeService`
- `tests/test_department_assignment.py` — for `departmentAssignmentService`
- `tests/test_ticket_category.py` — for `ticketCategoryService`
- `tests/test_ticket_comment.py` — for `ticketCommentService`
- `tests/test_ticket_history.py` — for `ticketHistoryService`
- `tests/test_token_blacklist.py` — for `tokenBlacklistService`

### B.1: Create `tests/test_audit_log.py`

- [ ] **Step 1: Read `app/services/auditLogService.py`** — Identify public methods: `log_action`, `get_logs`, `get_logs_by_user`, `get_logs_by_entity`.

- [ ] **Step 2: Create test file with basic tests**

```python
import pytest
from datetime import datetime, timezone, timedelta
from app.services.auditLogService import AuditLogService

class TestAuditLogCreation:
    def test_log_action_creates_audit_record(self, db_session):
        result = AuditLogService.log_action(
            db_session,
            user_id="uuid-employee",
            action="CREATE_TICKET",
            entity_type="ticket",
            entity_id="uuid-ticket",
            metadata={"title": "Test"}
        )
        assert result is not None
        assert result.action == "CREATE_TICKET"

    def test_log_action_with_minimal_fields(self, db_session):
        result = AuditLogService.log_action(
            db_session, user_id="uuid", action="LOGIN"
        )
        assert result is not None

class TestAuditLogRetrieval:
    def test_get_logs_by_user_returns_records(self, db_session):
        AuditLogService.log_action(db_session, user_id="user-123", action="LOGIN")
        logs = AuditLogService.get_logs_by_user(db_session, "user-123")
        assert len(logs) >= 1

    def test_get_logs_by_nonexistent_user_returns_empty(self, db_session):
        logs = AuditLogService.get_logs_by_user(db_session, "nonexistent-uuid")
        assert len(logs) == 0

    def test_get_logs_by_entity(self, db_session):
        ticket_id = "ticket-uuid-123"
        AuditLogService.log_action(db_session, user_id="u1", action="CREATE", entity_type="ticket", entity_id=ticket_id)
        logs = AuditLogService.get_logs_by_entity(db_session, "ticket", ticket_id)
        assert len(logs) >= 1
```

- [ ] **Step 3: Run tests**

```
.venv/bin/python -m pytest tests/test_audit_log.py -v --tb=short
```

- [ ] **Step 4: Fix any import/fixture issues** — Common: missing `db_session` fixture, wrong service import path.

- [ ] **Step 5: Mark with `@pytest.mark.unit`**

### B.2: Create `tests/test_customer_type.py`

- [ ] **Step 1: Read `app/services/customerTypeService.py`**

- [ ] **Step 2: Create tests for `create_customer_type`, `get_customer_type`, `get_all_customer_types`, `update_customer_type`, `delete_customer_type`**

```python
import pytest
from app.services.customerTypeService import CustomerTypeService

class TestCustomerTypeCreation:
    def test_create_customer_type(self, db_session):
        result = CustomerTypeService.create_customer_type(
            db_session, name="VIP", description="Very important customer"
        )
        assert result.name == "VIP"
        assert result.is_active is True

    def test_create_customer_type_default_is_active(self, db_session):
        result = CustomerTypeService.create_customer_type(db_session, name="Regular")
        assert result.is_active is True

class TestCustomerTypeRetrieval:
    def test_get_customer_type(self, db_session):
        created = CustomerTypeService.create_customer_type(db_session, name="Standard")
        retrieved = CustomerTypeService.get_customer_type(db_session, created.id_customer_type)
        assert retrieved is not None
        assert retrieved.name == "Standard"

    def test_get_all_customer_types(self, db_session):
        CustomerTypeService.create_customer_type(db_session, name="Type1")
        CustomerTypeService.create_customer_type(db_session, name="Type2")
        all_types = CustomerTypeService.get_all_customer_types(db_session)
        assert len(all_types) >= 2
```

- [ ] **Step 3: Run and fix**

```
.venv/bin/python -m pytest tests/test_customer_type.py -v --tb=short
```

### B.3: Create `tests/test_department_assignment.py`

- [ ] **Step 1: Read `app/services/departmentAssignmentService.py`**

- [ ] **Step 2: Create tests for `assign_employee_to_department`, `remove_employee_from_department`, `get_department_employees`, `get_employee_departments`**

```python
import pytest
from app.services.departmentAssignmentService import DepartmentAssignmentService

class TestDepartmentAssignment:
    def test_assign_employee_to_department(self, db_session):
        result = DepartmentAssignmentService.assign_employee_to_department(
            db_session,
            employee_id="emp-uuid",
            department_id="dept-uuid",
            role="support"
        )
        assert result is not None

    def test_get_employee_departments(self, db_session):
        DeptAssignSvc = DepartmentAssignmentService
        DeptAssignSvc.assign_employee_to_department(db_session, "emp-uuid", "dept-uuid", "support")
        depts = DeptAssignSvc.get_employee_departments(db_session, "emp-uuid")
        assert len(depts) >= 1

    def test_remove_employee_from_department(self, db_session):
        DeptAssignSvc = DepartmentAssignmentService
        DeptAssignSvc.assign_employee_to_department(db_session, "emp-uuid", "dept-uuid", "support")
        result = DeptAssignSvc.remove_employee_from_department(db_session, "emp-uuid", "dept-uuid")
        assert result is True
```

- [ ] **Step 3: Run and fix**

```
.venv/bin/python -m pytest tests/test_department_assignment.py -v --tb=short
```

### B.4: Create `tests/test_ticket_category.py`

- [ ] **Step 1: Read `app/services/ticketCategoryService.py`**

- [ ] **Step 2: Create tests for `create_category`, `get_category`, `get_all_categories`, `update_category`, `delete_category`**

```python
import pytest
from app.services.ticketCategoryService import TicketCategoryService

class TestTicketCategoryCreation:
    def test_create_category(self, db_session):
        result = TicketCategoryService.create_category(
            db_session,
            name="Bug",
            description="Bug reports",
            id_department="dept-uuid",
            auto_assign=True
        )
        assert result.name == "Bug"
        assert result.is_active is True

    def test_create_category_default_auto_assign(self, db_session):
        result = TicketCategoryService.create_category(
            db_session, name="Feature", id_department="dept-uuid"
        )
        assert result.auto_assign is True

class TestTicketCategoryRetrieval:
    def test_get_category(self, db_session):
        created = TicketCategoryService.create_category(
            db_session, name="Support", id_department="dept-uuid"
        )
        retrieved = TicketCategoryService.get_category(db_session, created.id_category)
        assert retrieved is not None
        assert retrieved.name == "Support"
```

- [ ] **Step 3: Run and fix**

```
.venv/bin/python -m pytest tests/test_ticket_category.py -v --tb=short
```

### B.5: Create `tests/test_ticket_comment.py`

- [ ] **Step 1: Read `app/services/ticketCommentService.py`**

- [ ] **Step 2: Create tests for `add_comment`, `get_comment`, `get_ticket_comments`, `delete_comment`, `update_comment`**

```python
import pytest
from app.services.ticketCommentService import TicketCommentService

class TestTicketCommentCreation:
    def test_add_comment(self, db_session):
        result = TicketCommentService.add_comment(
            db_session,
            id_ticket="ticket-uuid",
            id_employee="emp-uuid",
            content="This is a test comment"
        )
        assert result.content == "This is a test comment"
        assert result.is_deleted is False

class TestTicketCommentRetrieval:
    def test_get_ticket_comments(self, db_session):
        TicketCommentService.add_comment(
            db_session, id_ticket="ticket-uuid", id_employee="emp-uuid", content="Comment 1"
        )
        comments = TicketCommentService.get_ticket_comments(db_session, "ticket-uuid")
        assert len(comments) >= 1

    def test_delete_comment(self, db_session):
        comment = TicketCommentService.add_comment(
            db_session, id_ticket="ticket-uuid", id_employee="emp-uuid", content="To delete"
        )
        result = TicketCommentService.delete_comment(db_session, comment.id_comment)
        assert result is True
```

- [ ] **Step 3: Run and fix**

```
.venv/bin/python -m pytest tests/test_ticket_comment.py -v --tb=short
```

### B.6: Create `tests/test_ticket_history.py`

- [ ] **Step 1: Read `app/services/ticketHistoryService.py`**

- [ ] **Step 2: Create tests for `record_change`, `get_ticket_history`, `get_entity_history`**

```python
import pytest
from app.services.ticketHistoryService import TicketHistoryService

class TestTicketHistoryRecording:
    def test_record_ticket_status_change(self, db_session):
        result = TicketHistoryService.record_change(
            db_session,
            id_ticket="ticket-uuid",
            changed_by="emp-uuid",
            field_name="status",
            old_value="New",
            new_value="In Progress"
        )
        assert result.field_name == "status"
        assert result.new_value == "In Progress"

    def test_get_ticket_history(self, db_session):
        TicketHistoryService.record_change(
            db_session, id_ticket="ticket-uuid", changed_by="emp-uuid",
            field_name="status", old_value="New", new_value="In Progress"
        )
        history = TicketHistoryService.get_ticket_history(db_session, "ticket-uuid")
        assert len(history) >= 1
```

- [ ] **Step 3: Run and fix**

```
.venv/bin/python -m pytest tests/test_ticket_history.py -v --tb=short
```

### B.7: Create `tests/test_token_blacklist.py`

- [ ] **Step 1: Read `app/services/tokenBlacklistService.py`**

- [ ] **Step 2: Create tests for `blacklist_token`, `is_blacklisted`, `cleanup_expired`**

```python
import pytest
from datetime import datetime, timezone, timedelta
from app.services.tokenBlacklistService import TokenBlacklistService

class TestTokenBlacklist:
    def test_blacklist_token(self, db_session):
        result = TokenBlacklistService.blacklist_token(
            db_session,
            token_jti="jti-123",
            token_type="access",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        assert result.token_jti == "jti-123"
        assert result.is_blacklisted is True

    def test_is_blacklisted_returns_true_for_blacklisted(self, db_session):
        TokenBlacklistService.blacklist_token(
            db_session, token_jti="jti-456", token_type="access",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        assert TokenBlacklistService.is_blacklisted(db_session, "jti-456") is True

    def test_is_blacklisted_returns_false_for_nonexistent(self, db_session):
        assert TokenBlacklistService.is_blacklisted(db_session, "nonexistent-jti") is False

    def test_cleanup_expired_removes_old_tokens(self, db_session):
        # Create expired token
        TokenBlacklistService.blacklist_token(
            db_session, token_jti="expired-jti", token_type="access",
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1)
        )
        removed = TokenBlacklistService.cleanup_expired(db_session)
        assert removed >= 1
        assert TokenBlacklistService.is_blacklisted(db_session, "expired-jti") is False
```

- [ ] **Step 3: Run and fix**

```
.venv/bin/python -m pytest tests/test_token_blacklist.py -v --tb=short
```

---

## Phase C: Complete Missing Integration Test Cases

### Target: Add integration tests for gaps: I_AUTH_06 (token refresh), I_CHAT_02 (chat pagination), I_SENT (sentiment), I_FILE (file upload).

**Files to modify:**
- `tests/test_integration_critical_flows.py` — add missing test cases

### C.1: Add I_AUTH_06 — Token refresh flow

- [ ] **Step 1: Check if `/refresh` endpoint exists in `app/api/v1/auth.py`**

```
grep -n "refresh" app/api/v1/auth.py
```

- [ ] **Step 2: If endpoint doesn't exist, implement it first**

```python
@router.post("/refresh")
def refresh_token(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Refresh access token using refresh token"""
    # Verify refresh token is not blacklisted
    if TokenBlacklistService.is_blacklisted(db, request.refresh_token):
        raise HTTPException(status_code=401, detail="Token has been revoked")

    # Decode and generate new access token
    payload = decode_token(request.refresh_token)
    new_access_token = create_access_token(
        data={"sub": payload["sub"], "type": "access"}
    )
    return {"access_token": new_access_token, "token_type": "bearer"}
```

- [ ] **Step 3: Add token refresh integration tests**

```python
class TestTokenRefresh:
    def test_refresh_token_success(self, client, test_customer):
        """I_AUTH_06: Token refresh flow"""
        # Login to get tokens
        login_resp = client.post("/api/v1/auth/login", json={
            "username": test_customer["username"],
            "password": "Test1234!"
        })
        assert login_resp.status_code == 200
        tokens = login_resp.json()
        access_token = tokens["access_token"]

        # Refresh token
        refresh_resp = client.post("/api/v1/auth/refresh", json={
            "refresh_token": tokens.get("refresh_token")
        })
        assert refresh_resp.status_code == 200
        new_tokens = refresh_resp.json()
        assert "access_token" in new_tokens
        assert new_tokens["access_token"] != access_token

    def test_refresh_token_with_blacklisted_token_fails(self, client, test_customer):
        """I_AUTH_06b: Cannot refresh a blacklisted token"""
        login_resp = client.post("/api/v1/auth/login", json={
            "username": test_customer["username"],
            "password": "Test1234!"
        })
        tokens = login_resp.json()

        # Blacklist the token
        client.post("/api/v1/auth/logout", headers={
            "Authorization": f"Bearer {tokens['access_token']}"
        })

        # Try to refresh — should fail
        refresh_resp = client.post("/api/v1/auth/refresh", json={
            "refresh_token": tokens.get("refresh_token")
        })
        assert refresh_resp.status_code in [401, 403]
```

- [ ] **Step 4: Run the new test**

```
.venv/bin/python -m pytest tests/test_integration_critical_flows.py::TestTokenRefresh -v --tb=short
```

### C.2: Add I_CHAT_02 — Chat session history pagination

- [ ] **Step 1: Check if chat message endpoint supports pagination**

```
grep -n "page\|limit\|offset" app/api/v1/chat.py app/api/v1/chatbot.py
```

- [ ] **Step 2: Add pagination test**

```python
def test_chat_session_message_pagination(self, client, test_employee, test_customer):
    """I_CHAT_02: Chat messages support pagination"""
    # Create a chat session
    session_resp = client.post(
        "/api/v1/chatbot/sessions",
        headers={"Authorization": f"Bearer {test_customer['token']}"},
        json={"customer_id": str(test_customer["id_customer"])}
    )
    assert session_resp.status_code == 201
    session_id = session_resp.json()["id_session"]

    # Add 11 messages (to test pagination at 10/page)
    for i in range(11):
        client.post(
            f"/api/v1/chatbot/sessions/{session_id}/messages",
            headers={"Authorization": f"Bearer {test_customer['token']}"},
            json={"message": f"Message {i+1}", "session_id": session_id}
        )

    # Get first page (should be 10)
    page1_resp = client.get(
        f"/api/v1/chatbot/sessions/{session_id}/messages?page=1&size=10",
        headers={"Authorization": f"Bearer {test_customer['token']}"}
    )
    assert page1_resp.status_code == 200
    page1_data = page1_resp.json()
    assert len(page1_data["messages"]) == 10
    assert page1_data.get("has_next") is True

    # Get second page (should be 1)
    page2_resp = client.get(
        f"/api/v1/chatbot/sessions/{session_id}/messages?page=2&size=10",
        headers={"Authorization": f"Bearer {test_customer['token']}"}
    )
    assert page2_resp.status_code == 200
    assert len(page2_resp.json()["messages"]) == 1
```

- [ ] **Step 3: Run test**

```
.venv/bin/python -m pytest tests/test_integration_critical_flows.py -k "pagination" -v --tb=short
```

### C.3: Add I_SENT — Sentiment analysis integration

- [ ] **Step 1: Check `app/services/sentimentService.py`** — Identify how sentiment analysis works.

- [ ] **Step 2: Add sentiment analysis integration test**

```python
def test_sentiment_analysis_on_ticket_feedback(self, client, test_customer, test_employee):
    """I_SENT: Sentiment analysis on ticket resolution feedback"""
    # Create a ticket and resolve it
    ticket_resp = client.post(
        "/api/v1/tickets",
        headers={"Authorization": f"Bearer {test_employee['token']}"},
        json={
            "title": "Feedback ticket",
            "id_customer": str(test_customer["id_customer"]),
            "id_category": str(test_customer["id_category"])
        }
    )
    ticket_id = ticket_resp.json()["id_ticket"]

    # Resolve the ticket
    client.put(
        f"/api/v1/tickets/{ticket_id}/resolve",
        headers={"Authorization": f"Bearer {test_employee['token']}"},
        json={"resolution_note": "Resolved with positive feedback"}
    )

    # Submit CSAT with text feedback
    csat_resp = client.post(
        "/api/v1/evaluations",
        headers={"Authorization": f"Bearer {test_customer['token']}"},
        json={
            "id_ticket": ticket_id,
            "rating": 5,
            "feedback_text": "Excellent support, very happy with the resolution!"
        }
    )
    assert csat_resp.status_code == 201

    # Verify sentiment was analyzed
    eval_data = csat_resp.json()
    assert "sentiment_score" in eval_data or "sentiment" in eval_data
    score = eval_data.get("sentiment_score") or eval_data.get("sentiment", {}).get("score")
    assert score is not None
```

- [ ] **Step 3: Run test**

```
.venv/bin/python -m pytest tests/test_integration_critical_flows.py -k "sentiment" -v --tb=short
```

### C.4: Add I_FILE — File attachment upload/download

- [ ] **Step 1: Check `app/api/v1/attachments.py`** — Identify `upload_file`, `download_file`, `delete_file` endpoints.

- [ ] **Step 2: Add file attachment integration tests**

```python
def test_upload_and_download_attachment(self, client, test_employee, test_ticket):
    """I_FILE: File attachment upload and download flow"""
    import io
    file_content = b"Test file attachment content"
    file_obj = io.BytesIO(file_content)

    upload_resp = client.post(
        "/api/v1/attachments",
        headers={"Authorization": f"Bearer {test_employee['token']}"},
        files={"file": ("test.txt", file_obj, "text/plain")},
        data={"id_ticket": str(test_ticket["id_ticket"])}
    )
    assert upload_resp.status_code == 201
    attachment_data = upload_resp.json()
    attachment_id = attachment_data["id_attachment"]

    # Download the file
    download_resp = client.get(
        f"/api/v1/attachments/{attachment_id}",
        headers={"Authorization": f"Bearer {test_employee['token']}"}
    )
    assert download_resp.status_code == 200
    assert download_resp.content == file_content

def test_upload_rejects_invalid_file_type(self, client, test_employee, test_ticket):
    """I_FILE: Upload rejects disallowed file types"""
    import io
    file_obj = io.BytesIO(b"malicious content")

    upload_resp = client.post(
        "/api/v1/attachments",
        headers={"Authorization": f"Bearer {test_employee['token']}"},
        files={"file": ("malware.exe", file_obj, "application/x-msdownload")},
        data={"id_ticket": str(test_ticket["id_ticket"])}
    )
    assert upload_resp.status_code in [400, 415]

def test_delete_attachment(self, client, test_employee, test_ticket):
    """I_FILE: Delete attachment"""
    import io
    file_obj = io.BytesIO(b"File to delete")
    upload_resp = client.post(
        "/api/v1/attachments",
        headers={"Authorization": f"Bearer {test_employee['token']}"},
        files={"file": ("delete_me.txt", file_obj, "text/plain")},
        data={"id_ticket": str(test_ticket["id_ticket"])}
    )
    attachment_id = upload_resp.json()["id_attachment"]

    delete_resp = client.delete(
        f"/api/v1/attachments/{attachment_id}",
        headers={"Authorization": f"Bearer {test_employee['token']}"}
    )
    assert delete_resp.status_code == 204

    # Verify cannot download deleted file
    get_resp = client.get(
        f"/api/v1/attachments/{attachment_id}",
        headers={"Authorization": f"Bearer {test_employee['token']}"}
    )
    assert get_resp.status_code == 404
```

- [ ] **Step 3: Run tests**

```
.venv/bin/python -m pytest tests/test_integration_critical_flows.py -k "attachment" -v --tb=short
```

---

## Phase D: Complete Missing System/E2E Tests

### Target: Add system tests for Socket.IO, file upload, scheduled jobs.

**Files to modify:**
- `tests/test_system_e2e.py` — add missing test cases

### D.1: Add Socket.IO real-time tests

- [ ] **Step 1: Check if there are Socket.IO tests currently**

```
grep -r "socket" tests/ --include="*.py" | head -20
```

- [ ] **Step 2: Read `app/websocket/socketio.py`** or relevant file to understand Socket.IO setup.

- [ ] **Step 3: Add Socket.IO connection tests**

```python
import socketio

class TestSocketIOConnection:
    def test_socketio_connection_authenticated(self):
        """SOCKET_IO_01: Socket.IO connection with valid token"""
        sio = socketio.Client()
        token = self.get_valid_token()  # helper using /login endpoint

        received = []

        @sio.on("connect")
        def on_connect():
            sio.emit("authenticate", {"token": token})

        @sio.on("authenticated")
        def on_auth(data):
            received.append(data)
            sio.disconnect()

        sio.connect("http://localhost:8000/socket.io/")
        sio.wait()
        assert len(received) == 1
        assert received[0].get("status") == "ok"

    def test_socketio_connection_invalid_token_rejected(self):
        """SOCKET_IO_02: Socket.IO rejects invalid token"""
        sio = socketio.Client()
        errors = []

        @sio.on("connect")
        def on_connect():
            sio.emit("authenticate", {"token": "invalid-token"})

        @sio.on("error")
        def on_error(data):
            errors.append(data)
            sio.disconnect()

        sio.connect("http://localhost:8000/socket.io/")
        sio.wait()
        assert len(errors) >= 1

    def test_socketio_ticket_update_event(self, client, test_employee, test_ticket):
        """SOCKET_IO_03: Ticket update event received by connected client"""
        # This requires a running server — mark as e2e
        pytest.skip("Requires running server with Socket.IO")
```

- [ ] **Step 4: Mark appropriately** — `@pytest.mark.e2e` for full server tests.

- [ ] **Step 5: Run non-e2e tests**

```
.venv/bin/python -m pytest tests/test_system_e2e.py -k "socketio" -v --tb=short
```

### D.2: Add scheduled jobs / background task tests

- [ ] **Step 1: Find scheduled job files**

```
find app -name "*job*" -o -name "*scheduler*" | head -10
```

- [ ] **Step 2: Check `app/services/emailService.py`** for background tasks (CSAT surveys).

- [ ] **Step 3: Add background job tests**

```python
class TestScheduledJobs:
    def test_csat_survey_job_sends_pending_surveys(self, db_session):
        """SCHEDULED_01: CSAT survey job processes pending surveys"""
        from app.models import Ticket
        from datetime import datetime, timezone

        # Create a resolved ticket without survey sent
        customer_id = "cust-survey-uuid"
        employee_id = "emp-survey-uuid"

        ticket = Ticket(
            title="Survey test",
            id_customer=customer_id,
            id_employee=employee_id,
            status="Resolved",
            survey_sent=False
        )
        db_session.add(ticket)
        db_session.commit()

        # Run the survey job
        from app.jobs.send_survey_job import send_pending_surveys
        result = send_pending_surveys(db_session)

        # Verify ticket now has survey_sent=True
        db_session.refresh(ticket)
        assert ticket.survey_sent is True

    def test_token_cleanup_job_removes_expired_blacklisted_tokens(self, db_session):
        """SCHEDULED_02: Token cleanup job removes expired tokens"""
        from datetime import datetime, timezone, timedelta
        from app.services.tokenBlacklistService import TokenBlacklistService

        # Create expired token
        TokenBlacklistService.blacklist_token(
            db_session,
            token_jti="expired-cleanup-jti",
            token_type="access",
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1)
        )

        # Run cleanup
        from app.jobs.token_cleanup_job import cleanup_expired_tokens
        removed = cleanup_expired_tokens(db_session)

        assert removed >= 1
        assert TokenBlacklistService.is_blacklisted(db_session, "expired-cleanup-jti") is False
```

- [ ] **Step 4: Run tests**

```
.venv/bin/python -m pytest tests/test_system_e2e.py -k "scheduled" -v --tb=short
```

### D.3: Add file upload E2E test

- [ ] **Step 1: Add file upload tests to `test_system_e2e.py`**

```python
class TestFileUploadEndToEnd:
    def test_upload_file_to_ticket(self, client, test_employee, test_ticket):
        """FILE_UPLOAD_01: Employee uploads file attachment to ticket"""
        import io
        file_content = b"Test attachment content for E2E"
        file_obj = io.BytesIO(file_content)

        response = client.post(
            "/api/v1/attachments",
            headers={"Authorization": f"Bearer {test_employee['token']}"},
            files={"file": ("e2e_test.txt", file_obj, "text/plain")},
            data={"id_ticket": str(test_ticket["id_ticket"])}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["file_name"] == "e2e_test.txt"
        assert "id_attachment" in data

    def test_upload_multiple_files_to_ticket(self, client, test_employee, test_ticket):
        """FILE_UPLOAD_02: Upload multiple files to same ticket"""
        files = [
            ("file1.txt", b"Content 1"),
            ("file2.txt", b"Content 2"),
            ("file3.txt", b"Content 3"),
        ]
        for name, content in files:
            file_obj = io.BytesIO(content)
            resp = client.post(
                "/api/v1/attachments",
                headers={"Authorization": f"Bearer {test_employee['token']}"},
                files={"file": (name, file_obj, "text/plain")},
                data={"id_ticket": str(test_ticket["id_ticket"])}
            )
            assert resp.status_code == 201

        # Verify all attachments exist
        list_resp = client.get(
            f"/api/v1/tickets/{test_ticket['id_ticket']}/attachments",
            headers={"Authorization": f"Bearer {test_employee['token']}"}
        )
        assert list_resp.status_code == 200
        attachments = list_resp.json()
        assert len(attachments) >= 3

    def test_upload_rejected_when_file_too_large(self, client, test_employee, test_ticket):
        """FILE_UPLOAD_03: Upload rejected if file exceeds size limit"""
        large_content = b"x" * (11 * 1024 * 1024)  # 11MB
        file_obj = io.BytesIO(large_content)

        resp = client.post(
            "/api/v1/attachments",
            headers={"Authorization": f"Bearer {test_employee['token']}"},
            files={"file": ("large.bin", file_obj, "application/octet-stream")},
            data={"id_ticket": str(test_ticket["id_ticket"])}
        )
        assert resp.status_code == 413 or resp.status_code == 400
```

- [ ] **Step 2: Run and verify**

```
.venv/bin/python -m pytest tests/test_system_e2e.py -k "file_upload" -v --tb=short
```

---

## Phase E: Stabilize PostgreSQL Test Layer

### Target: Reduce PostgreSQL test failures from ~68 to under 10.

**Files to modify:**
- `tests/conftest.py` — fix PostgreSQL-specific fixture issues
- `docker-compose.test.yml` — ensure PostgreSQL version/config is correct

### E.1: Investigate PostgreSQL failures

- [ ] **Step 1: Start PostgreSQL test container**

```bash
docker compose -f docker-compose.test.yml up -d postgres
sleep 3
```

- [ ] **Step 2: Run tests against PostgreSQL and capture failures**

```bash
TEST_DATABASE_URL="postgresql://testuser:testpass@localhost:5433/testdb" \
.venv/bin/python -m pytest tests/ -q --tb=no 2>&1 | grep "FAILED" | head -40
```

Count failures.

- [ ] **Step 3: Run one failure with full traceback**

```bash
TEST_DATABASE_URL="postgresql://testuser:testpass@localhost:5433/testdb" \
.venv/bin/python -m pytest tests/test_api_integration.py::TestAuthAPI::test_login_success -v --tb=short
```

- [ ] **Step 4: Categorize failures by root cause:**
   - UUID format issues (SQLite accepts strings, PostgreSQL requires UUID objects)
   - Foreign key constraint differences
   - `datetime.utcnow()` vs timezone-aware datetime
   - Missing tables/columns that exist in SQLite but not PostgreSQL schema
   - `NULL` vs empty string behavior

### E.2: Fix UUID handling in tests

- [ ] **Step 1: Search for raw UUID strings in test files**

```
grep -rn "uuid4()" tests/ | head -20
grep -rn "'uuid'" tests/ | head -20
```

- [ ] **Step 2: Ensure fixtures use proper UUID generation**

```python
import uuid
def create_test_employee(db, **kwargs):
    return Employee(
        id_employee=uuid.uuid4(),  # UUID object, not string
        username=kwargs.get("username", "testuser"),
        email=kwargs.get("email", "test@test.com"),
        password_hash=kwargs.get("password_hash", "hash"),
        ...
    )
```

- [ ] **Step 3: Update `tests/conftest.py`** to use UUID objects for all foreign keys.

- [ ] **Step 4: Re-run PostgreSQL tests**

```bash
TEST_DATABASE_URL="postgresql://testuser:testpass@localhost:5433/testdb" \
.venv/bin/python -m pytest tests/test_api_integration.py -q --tb=no
```

### E.3: Fix datetime timezone issues

- [ ] **Step 1: Replace `datetime.utcnow()` with `datetime.now(timezone.utc)` in all app and test files**

```
grep -rln "datetime.utcnow()" app/ tests/ | head -20
```

For each file, replace:
```python
from datetime import datetime, timezone
# Instead of:
created_at = datetime.utcnow()
# Use:
created_at = datetime.now(timezone.utc)
```

- [ ] **Step 2: Run PostgreSQL tests again and count failures**

```bash
TEST_DATABASE_URL="postgresql://testuser:testpass@localhost:5433/testdb" \
.venv/bin/python -m pytest tests/ -q --tb=no 2>&1 | tail -5
```

### E.4: Fix PostgreSQL schema differences

- [ ] **Step 1: Run pending migrations on PostgreSQL**

```bash
TEST_DATABASE_URL="postgresql://testuser:testpass@localhost:5433/testdb" \
.venv/bin/python -m alembic upgrade head
```

- [ ] **Step 2: Compare SQLite vs PostgreSQL schemas**

```bash
# SQLite schema
.venv/bin/python -c "
from sqlalchemy import create_engine, inspect
engine = create_engine('sqlite:///:memory:')
from app.db.base import Base
Base.metadata.create_all(engine)
inspector = inspect(engine)
for table in inspector.get_tables():
    print(table['name'])
    for col in inspector.get_columns(table['name']):
        print(f'  {col[\"name\"]}: {col[\"type\"]}')
"
```

- [ ] **Step 3: Identify and fix schema differences**

- [ ] **Step 4: Re-run PostgreSQL tests** — Target: <10 failures

```bash
TEST_DATABASE_URL="postgresql://testuser:testpass@localhost:5433/testdb" \
.venv/bin/python -m pytest tests/ -q --tb=no 2>&1 | tail -5
```

### E.5: Shut down PostgreSQL container

```bash
docker compose -f docker-compose.test.yml down
```

---

## Phase F: Add Redis Test Container

### Target: Enable Redis-dependent tests (rate limiting, caching) to run properly.

**Files to modify:**
- `docker-compose.test.yml` — add Redis service
- `tests/conftest.py` — add Redis fixture

### F.1: Add Redis to docker-compose.test.yml

- [ ] **Step 1: Read current `docker-compose.test.yml`**

- [ ] **Step 2: Add Redis service**

```yaml
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_USER: testuser
      POSTGRES_PASSWORD: testpass
      POSTGRES_DB: testdb
    ports:
      - "5433:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U testuser"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5
```

- [ ] **Step 3: Start Redis**

```bash
docker compose -f docker-compose.test.yml up -d redis postgres
sleep 5
```

- [ ] **Step 4: Verify Redis is accessible**

```bash
docker exec cfs-redis redis-cli ping
# Expected: PONG
```

### F.2: Update conftest.py for Redis

- [ ] **Step 1: Add `redis_client` fixture**

```python
import fakeredis

@pytest.fixture(scope="function")
def redis_client():
    """Redis client for tests. Uses fakeredis if REDIS_URL not set."""
    if os.environ.get("REDIS_URL"):
        import redis
        client = redis.from_url(os.environ["REDIS_URL"])
        yield client
        client.flushdb()
        client.close()
    else:
        # Use fakeredis for unit tests
        fake_redis = fakeredis.FakeRedis(decode_responses=True)
        yield fake_redis
```

- [ ] **Step 2: Update rate limiting tests to use Redis**

The chatbot rate limiting test and rate limit tests in system E2E need Redis. With fakeredis they can pass in unit mode.

- [ ] **Step 3: Run Redis-dependent tests**

```
.venv/bin/python -m pytest tests/test_chatbot.py::TestChatbotRateLimiting -v --tb=short
```

- [ ] **Step 4: Run system E2E rate limit tests with real Redis**

```
TEST_DATABASE_URL="postgresql://testuser:testpass@localhost:5433/testdb" \
REDIS_URL="redis://localhost:6379" \
.venv/bin/python -m pytest tests/test_system_e2e.py::TestRateLimitingEndToEnd -v --tb=short
```

---

## Phase G: Validate CI Workflow

### Target: Ensure CI workflow runs successfully on a real PR.

**Files to modify:**
- `.github/workflows/ci.yml` — fix any issues found when running on actual code

### G.1: Trigger CI on a test branch

- [ ] **Step 1: Create a test branch and push**

```bash
git checkout -b test/automation-validation
git push origin test/automation-validation
```

- [ ] **Step 2: Monitor CI run**

```bash
gh run list --branch test/automation-validation
```

- [ ] **Step 3: Check CI results**

```bash
gh run view <run-id> --log
```

### G.2: Fix any CI-specific issues

Common CI issues:
- **Timeout**: Increase timeout for slow tests in `pytest.ini` or workflow
- **Missing env vars**: Add `TEST_DATABASE_URL`, `REDIS_URL` to workflow
- **Coverage threshold too high**: Lower `--cov-fail-under` if tests are not fully stable
- **Wrong Python version**: Pin exact version in workflow
- **Docker not available in CI**: Use `services:` in workflow instead of `docker compose`

### G.3: Update workflow based on findings

```yaml
jobs:
  unit:
    runs-on: ubuntu-latest
    services:
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
    env:
      REDIS_URL: redis://localhost:6379
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.14'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run unit tests
        run: .venv/bin/python -m pytest tests/ -m "unit" -q --tb=short --timeout=120

  integration:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: testuser
          POSTGRES_PASSWORD: testpass
          POSTGRES_DB: testdb
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
    env:
      TEST_DATABASE_URL: postgresql://testuser:testpass@localhost:5432/testdb
      REDIS_URL: redis://localhost:6379
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.14'
      - name: Run integration tests
        run: .venv/bin/python -m pytest tests/ -m "integration" -q --tb=short --timeout=180
```

- [ ] **Step 4: Verify CI passes**

```bash
gh run view <run-id> --json status,conclusion
```

- [ ] **Step 5: Clean up test branch**

```bash
git checkout main
git branch -d test/automation-validation
```

---

## Verification Checklist

After all phases, run these commands to verify:

```
# Full suite — target: ~785+ passed, 0 failed
.venv/bin/python -m pytest tests/ -q --tb=no

# Unit tests — target: 100+ passed, 0 failed
.venv/bin/python -m pytest tests/ -m "unit" -q --tb=no

# Integration tests — target: 40+ passed, 0 failed
.venv/bin/python -m pytest tests/ -m "integration" -q --tb=no

# System tests — target: 30+ passed, 0 failed
.venv/bin/python -m pytest tests/ -m "system" -q --tb=no

# PostgreSQL — target: 750+ passed, <10 failed
TEST_DATABASE_URL="postgresql://testuser:testpass@localhost:5433/testdb" \
.venv/bin/python -m pytest tests/ -q --tb=no

# Coverage — target: 70%+
.venv/bin/python -m pytest tests/ --cov=app --cov-report=term-missing -q
```