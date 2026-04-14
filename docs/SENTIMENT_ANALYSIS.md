# Sentiment Analysis System

## Overview

Hệ thống phân tích cảm xúc khách hàng tự động sử dụng AI (Groq API) để phân tích các feedback từ 3 nguồn (messages, evaluations, comments) và tạo báo cáo theo tháng cho admin và từng department.

---

## Implementation Status: ✅ COMPLETE

| Component | Status |
|-----------|--------|
| Migration `s1t2u3v4w5x6_add_sentiment_tables` | ✅ Done |
| Model `app/models/sentiment.py` | ✅ Done |
| Schema `app/schemas/sentimentSchema.py` | ✅ Done |
| Repository `app/repositories/sentimentRepository.py` | ✅ Done |
| Service `app/services/sentimentService.py` | ✅ Done |
| Groq Service `app/services/groqService.py` (+analyze_sentiment) | ✅ Done |
| Admin Endpoints `app/api/v1/analytics.py` | ✅ Done |
| Department Endpoints `app/api/v1/department_analytics.py` | ✅ Done |
| Job `app/core/jobs.py` (SentimentAnalysisJob) | ✅ Done |
| Scheduler `app/core/scheduler.py` | ✅ Done |
| Constants `app/core/constants.py` | ✅ Done |
| Documentation `docs/SENTIMENT_ANALYSIS.md` | ✅ Done |

**All 9 API endpoints tested and passing.**

---

## Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        SENTIMENT ANALYSIS JOB                                │
│                           (Runs every 7 days)                                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 1: Query Data Sources (last 7 days)                                   │
│  ─────────────────────────────────────────────────                          │
│  • messages       → customer feedback via ticket messages                  │
│  • evaluations    → customer ratings & comments after ticket resolved        │
│  • ticket_comments → internal/external comments on tickets                   │
│                                                                              │
│  Query: created_at >= (now - 7 days) AND created_at < now                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 2: AI Sentiment Analysis (per item)                                   │
│  ─────────────────────────────────────────────────                          │
│  For each data item:                                                        │
│    → Call Groq API with sentiment prompt                                    │
│    → Get label: "positive" | "neutral" | "negative"                         │
│    → Get score: -1.0 to 1.0                                                  │
│                                                                              │
│  Sleep 1 second between batches to avoid rate limit                         │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 3: Save Sentiment Details                                             │
│  ─────────────────────────────────────────────────                          │
│  For each analyzed item:                                                     │
│    → Create sentiment_detail record                                         │
│      - source_type (message/evaluation/comment)                              │
│      - source_id (original record ID)                                       │
│      - sentiment_label                                                       │
│      - sentiment_score                                                       │
│      - id_customer, id_ticket, id_department                                 │
│      - original_content (first 500 chars)                                   │
│                                                                              │
│    → Update system sentiment_report counters                                 │
│      - positive_count, neutral_count, negative_count                          │
│      - total_interactions                                                    │
│      - by_source breakdown (message_*, evaluation_*, comment_*)               │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 4: Generate Reports                                                   │
│  ─────────────────────────────────────────────────                          │
│  Query ALL sentiment_details (no date filter)                               │
│                                                                              │
│  System Report:                                                             │
│    → Calculate avg_sentiment_score                                           │
│    → Calculate total_interactions                                            │
│    → Calculate by_source breakdown                                           │
│    → Update existing or create new                                           │
│                                                                              │
│  Department Reports (one per department with data):                         │
│    → Group details by id_department                                          │
│    → Calculate per-department stats                                          │
│    → Calculate by_source breakdown per department                            │
│    → Insert or update department reports                                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │     OUTPUT REPORTS             │
                    ├───────────────────────────────┤
                    │ sentiment_reports:             │
                    │   • System report (scope='system') │
                    │     - total counts              │
                    │     - by_source breakdown       │
                    │   • Department reports          │
                    │     (scope='department')        │
                    │     - total counts              │
                    │     - by_source breakdown       │
                    │                                 │
                    │ sentiment_details:              │
                    │   • Individual analyzed items   │
                    └───────────────────────────────┘

---

## Data Sources

### 1. messages
Customer feedback via ticket messages.
- Table: `messages`
- Department determined by: `ticket.id_employee → employee.id_department`

### 2. evaluations
Customer ratings & comments after ticket is resolved.
- Table: `evaluates`
- Department determined by: `ticket.id_employee → employee.id_department`

### 3. ticket_comments
Internal/external comments on tickets.
- Table: `ticket_comments`
- Department determined by: `ticket.id_employee → employee.id_department`

---

## Database Schema

### sentiment_reports

| Column | Type | Description |
|--------|------|-------------|
| id_report | UUID | Primary key |
| year | INT | Report year |
| month | INT | Report month (1-12) |
| scope | VARCHAR(20) | 'system' or 'department' |
| id_department | UUID | NULL for system report |
| positive_count | INT | Total positive sentiments |
| neutral_count | INT | Total neutral sentiments |
| negative_count | INT | Total negative sentiments |
| avg_sentiment_score | FLOAT | Average sentiment score (-1 to 1) |
| message_positive | INT | Positive from messages |
| message_neutral | INT | Neutral from messages |
| message_negative | INT | Negative from messages |
| evaluation_positive | INT | Positive from evaluations |
| evaluation_neutral | INT | Neutral from evaluations |
| evaluation_negative | INT | Negative from evaluations |
| comment_positive | INT | Positive from comments |
| comment_neutral | INT | Neutral from comments |
| comment_negative | INT | Negative from comments |
| total_interactions | INT | Total items analyzed |
| created_at | DATETIME | Creation timestamp |
| updated_at | DATETIME | Last update timestamp |

### sentiment_details

| Column | Type | Description |
|--------|------|-------------|
| id_detail | UUID | Primary key |
| id_report | UUID | FK to sentiment_reports |
| source_type | VARCHAR(20) | 'message' / 'evaluation' / 'comment' |
| source_id | UUID | ID of original record |
| sentiment_label | VARCHAR(20) | 'positive' / 'neutral' / 'negative' |
| sentiment_score | FLOAT | Score from -1.0 to 1.0 |
| id_customer | UUID | Customer who gave feedback |
| id_ticket | UUID | Related ticket (nullable) |
| id_department | UUID | Department handling the ticket |
| original_content | TEXT | Original text (first 500 chars) |
| created_at | DATETIME | When detail was created |

---

## API Endpoints

### Admin Endpoints (role = 'Admin')

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/analytics/sentiment` | Get system sentiment summary for month |
| GET | `/api/v1/analytics/sentiment/trends` | Get 12-month trend for system |
| GET | `/api/v1/analytics/sentiment/compare` | Compare sentiment between periods |
| GET | `/api/v1/analytics/sentiment/by-department` | Compare departments for month |

### Department Endpoints (employee sees own department only)

**Important**: Route ordering in FastAPI matters. `/me/...` routes MUST be defined BEFORE `/{dept_id}/...` routes in `department_analytics.py`, otherwise "me" gets matched as a UUID and causes 422 errors.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/department/me/sentiment` | Get current user's department |
| GET | `/api/v1/department/me/sentiment/trends` | Get current user's department trends |
| GET | `/api/v1/department/{dept_id}/sentiment` | Get department sentiment for month |
| GET | `/api/v1/department/{dept_id}/sentiment/trends` | Get department 12-month trend |
| GET | `/api/v1/department/{dept_id}/sentiment/compare` | Compare department periods |

---

## Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| year | int | Yes | 2020-2100 |
| month | int | Yes | 1-12 |
| from_year | int | For compare | Start year |
| from_month | int | For compare | Start month |
| to_year | int | For compare | End year |
| to_month | int | For compare | End month |

---

## Cronjob Configuration

| Setting | Value |
|---------|-------|
| Schedule | Every 7 days (Monday 2:00 AM) |
| Batch Size | 50 items per batch |
| Sleep Between Batches | 1 second |
| Data Range | Last 7 days |

---

## Department Assignment Logic

Department is determined by the **employee assigned to handle the ticket**:

```
data source → ticket → employee.id_department → sentiment_detail.id_department
                                ↓
                    sentiment_reports (department scope)
```

If ticket has no assigned employee, department will be NULL and won't create department report.

---

## Example Response

### GET /api/v1/analytics/sentiment?year=2026&month=4

```json
{
  "status": true,
  "code": 200,
  "message": "Sentiment data retrieved successfully",
  "data": {
    "year": 2026,
    "month": 4,
    "scope": "system",
    "id_department": null,
    "department_name": null,
    "sentiment_breakdown": {
      "positive": 45,
      "neutral": 30,
      "negative": 25
    },
    "avg_sentiment_score": 0.35,
    "total_interactions": 100,
    "by_source": {
      "messages": {"positive": 20, "neutral": 10, "negative": 5},
      "evaluations": {"positive": 15, "neutral": 10, "negative": 10},
      "comments": {"positive": 10, "neutral": 10, "negative": 10}
    },
    "metrics": {
      "avg_response_time_hours": 4.5,
      "resolution_rate": 0.85
    }
  }
}
```

### GET /api/v1/analytics/sentiment/trends?year=2026

```json
{
  "status": true,
  "code": 200,
  "data": {
    "labels": ["Tháng 1", "Tháng 2", "Tháng 3"],
    "positive_data": [45, 52, 61],
    "neutral_data": [30, 28, 25],
    "negative_data": [25, 20, 14],
    "avg_score_data": [0.35, 0.42, 0.51]
  }
}
```

### GET /api/v1/analytics/sentiment/compare?from_year=2026&from_month=1&to_year=2026&to_month=3

```json
{
  "status": true,
  "code": 200,
  "data": {
    "from_period": {"year": 2026, "month": 1, "positive": 45, "neutral": 30, "negative": 25, "avg_score": 0.35},
    "to_period": {"year": 2026, "month": 3, "positive": 61, "neutral": 25, "negative": 14, "avg_score": 0.51},
    "change_percentage": 8.5,
    "change_absolute": 16
  }
}
```

---

## Running Job Manually

To test sentiment analysis job one time (without waiting for cron):

```python
from app.db.session import SessionLocal
from app.core.jobs import run_sentiment_analysis

db = SessionLocal()
try:
    result = run_sentiment_analysis(db)
    print(f"Result: {result}")
finally:
    db.close()
```

**Note**: This uses real AI API calls and counts toward quota. Use sparingly for testing.

---

## Files Structure

```
app/
├── core/
│   ├── jobs.py              # SentimentAnalysisJob class
│   ├── scheduler.py         # APScheduler configuration (Monday 2AM, 7 days)
│   └── constants.py        # SentimentLabel, SentimentSourceType, SentimentConstants
├── models/
│   └── sentiment.py         # SentimentReport, SentimentDetail models
├── schemas/
│   └── sentimentSchema.py   # Pydantic schemas for API
├── services/
│   ├── sentimentService.py  # Business logic
│   └── groqService.py       # AI API integration (+analyze_sentiment)
├── repositories/
│   └── sentimentRepository.py
└── api/v1/
    ├── analytics.py              # 4 Admin endpoints
    └── department_analytics.py  # 5 Department endpoints (/me routes before /{dept_id})

migrations/versions/
└── s1t2u3v4w5x6_add_sentiment_tables.py  # Database migration (NO chatbot columns)
```

---

## by_source Breakdown

The `by_source` field in API response comes from `sentiment_reports` table columns:

| Column | Source | Meaning |
|--------|--------|---------|
| message_positive | messages | Positive sentiment from customer messages |
| message_neutral | messages | Neutral sentiment from customer messages |
| message_negative | messages | Negative sentiment from customer messages |
| evaluation_positive | evaluations | Positive from customer ratings/comments |
| evaluation_neutral | evaluations | Neutral from customer ratings/comments |
| evaluation_negative | evaluations | Negative from customer ratings/comments |
| comment_positive | ticket_comments | Positive from ticket comments |
| comment_neutral | ticket_comments | Neutral from ticket comments |
| comment_negative | ticket_comments | Negative from ticket comments |

These values are updated:
1. In `_save_detail()` when each item is processed
2. In `_generate_reports()` when aggregating department reports

---

## Maintenance Notes

### If AI Quota Exceeded
- Reduce BATCH_SIZE in jobs.py (default: 50)
- Increase SLEEP_SECONDS between batches (default: 1 second)

### If Report Data Incorrect
1. Clear sentiment_details and sentiment_reports tables:
   ```sql
   DELETE FROM sentiment_details;
   DELETE FROM sentiment_reports;
   ```
2. Run job manually to recreate
3. Check logs for processing errors

### If by_source Breakdown is Wrong

**Known Bug**: Previous implementation had a bug where `_save_detail()` and `_generate_reports()` were NOT updating the by_source fields (message_*, evaluation_*, comment_*), causing API to return all zeros for by_source breakdown.

The fix requires updating by_source fields in BOTH places:
1. `_save_detail()` - updates system report counters as each item is processed
2. `_generate_reports()` - updates department report counters when aggregating

The `by_source` breakdown (message_*, evaluation_*, comment_*) is calculated in `_generate_reports()`.
If these values are incorrect, delete and re-run the job:
```python
from app.core.jobs import run_sentiment_analysis
# This will recalculate all counts from sentiment_details
```

### Database Reset
If you need to recreate the tables:
```bash
alembic downgrade -1
alembic upgrade s1t2u3v4w5x6
```