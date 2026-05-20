# Analytics & Sentiment

## 1. Tổng quan

- **Sentiment Analysis**: Phân tích cảm xúc khách hàng từ tin nhắn, đánh giá, bình luận bằng AI (Groq LLM)
- **Dashboard Analytics**: Báo cáo sentiment theo tháng, xu hướng, so sánh kỳ, phân tích theo phòng ban
- **CSAT Evaluation**: Khách hàng đánh giá ticket (1-5 sao), tự động tính điểm CSAT cho nhân viên
- **Scheduled Jobs**: Kiểm tra SLA breach, gửi survey, chạy sentiment analysis định kỳ

---

## 2. Database Schema

### SentimentReport (`sentiment_reports`)
| Cột | Kiểu | Mô tả |
|-----|------|--------|
| id_report | UUID, PK | ID báo cáo |
| year / month | Integer | Năm/Tháng |
| scope | String(20) | "system" / "department" |
| id_department | UUID, FK (nullable) | Phòng ban (khi scope=department) |
| positive_count / neutral_count / negative_count | Integer | Tổng theo loại |
| avg_sentiment_score | Float | Điểm TB (-1.0 đến 1.0) |
| message_positive/neutral/negative | Integer | Phân loại theo nguồn: tin nhắn |
| evaluation_positive/neutral/negative | Integer | Phân loại theo nguồn: đánh giá |
| comment_positive/neutral/negative | Integer | Phân loại theo nguồn: bình luận |
| total_interactions | Integer | Tổng tương tác |
| avg_response_time_hours | Float | Thời gian phản hồi TB |
| resolution_rate | Float | Tỷ lệ giải quyết |
| sentiment_change | Float | Thay đổi so với kỳ trước |

### SentimentDetail (`sentiment_details`)
| Cột | Kiểu | Mô tả |
|-----|------|--------|
| id_detail | UUID, PK | ID |
| id_report | UUID, FK | Báo cáo |
| source_type | String(20) | message / evaluation / comment |
| source_id | UUID | ID nguồn gốc |
| sentiment_label | String(20) | positive / neutral / negative |
| sentiment_score | Float | Điểm (-1.0 đến 1.0) |
| id_customer / id_ticket / id_department | UUID | Liên kết |
| original_content | Text | Nội dung gốc (max 500 ký tự) |

### Evaluate (`evaluates`)
| Cột | Kiểu | Mô tả |
|-----|------|--------|
| id_evaluate | UUID, PK | ID đánh giá |
| id_ticket | UUID, FK | Ticket được đánh giá |
| id_customer | UUID, FK | Khách hàng đánh giá |
| star | Integer | Số sao (1-5) |
| comment | String (nullable) | Nhận xét |
| created_at / updated_at | DateTime | Timestamps |

---

## 3. API Endpoints

### Analytics (`/api/v1/analytics`) - Admin only

| Method | Path | Mô tả |
|--------|------|--------|
| GET | `/analytics/sentiment?year=&month=` | Tổng hợp sentiment theo tháng |
| GET | `/analytics/sentiment/trends?year=` | Xu hướng cả năm (12 tháng) |
| GET | `/analytics/sentiment/compare?from_year=&from_month=&to_year=&to_month=` | So sánh 2 kỳ |
| GET | `/analytics/sentiment/by-department?year=&month=` | Phân tích theo phòng ban |

### Evaluate (`/api/v1/evaluates`)

| Method | Path | Quyền | Mô tả |
|--------|------|-------|--------|
| POST | `/evaluates` | Customer | Tạo đánh giá (1-5 sao + comment) |
| GET | `/evaluates/ticket/{ticket_id}` | Public | Đánh giá của ticket |
| PATCH | `/evaluates/{id}` | Customer (chủ) | Cập nhật đánh giá |
| DELETE | `/evaluates/{id}` | Customer (chủ) | Xóa đánh giá |

---

## 4. Sentiment Analysis Flow

```
[Scheduled Job - 7 ngày/lần]
  │
  ├── Thu thập 7 ngày qua: Messages, Evaluations, Comments
  │
  ├── Xử lý batch (50 items/batch, sleep 1s):
  │   └── Gọi Groq AI → nhận label + score
  │
  ├── Lưu SentimentDetail cho mỗi item
  │
  └── Tạo/cập nhật SentimentReport:
      ├── scope="system" (toàn hệ thống)
      └── scope="department" (từng phòng ban)
```

**Quy tắc phân loại:**
- Positive: score >= 0.3
- Negative: score <= -0.3
- Neutral: -0.3 < score < 0.3

---

## 5. Groq AI Integration

### GroqService
- **API**: Groq Cloud (`https://api.groq.com/openai/v1/chat/completions`)
- **Multi-key rotation**: Hỗ trợ nhiều API key, tự động xoay khi lỗi 401/403/429/5xx
- **analyze_sentiment(text)**: Gửi text (max 1000 ký tự) → nhận JSON `{label, score}`
- **Fallback**: Trả neutral (score=0.0) nếu parse lỗi hoặc API fail
- **Timeout**: 60s, Temperature: 0.7

---

## 6. Scheduled Jobs

### SLABreachJob
- Quét ticket active (batch 100)
- Quá hạn → notify nhân viên + escalate lên manager
- Còn ≤ 24h → cảnh báo SLA warning
- Notification types: `SLA_WARNING`, `SLA_BREACHED`, `SLA_ESCALATED`

### SurveyJob
- Tìm ticket Resolved, chưa gửi survey, resolved > N giờ
- Gửi email CSAT survey → đánh dấu `survey_sent = True`

### SentimentAnalysisJob
- Chạy 7 ngày/lần
- Thu thập → phân tích AI → lưu detail → tạo report

---

## 7. CSAT Evaluation

### Luồng
```
Customer đánh giá (1-5 sao + comment)
  → Lưu evaluates
  → Notify nhân viên phụ trách
  → Cập nhật CSAT score: AVG(all star ratings) → employee.csat_score
```

### Tính CSAT Score
- Công thức: `AVG(star)` của tất cả đánh giá trên tickets mà NV được giao
- Cập nhật real-time mỗi khi có đánh giá mới
