from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from app.models.ticket import Ticket
from app.models.human import Employee, Customer
from app.models.ticket import TicketCategory
from app.repositories.ticketRepository import TicketRepository
from app.repositories.employeeRepository import EmployeeRepository
from app.schemas.notificationSchema import NotificationCreate
from app.services.notificationService import NotificationService
from app.core.constants import TicketStatusConstants
from app.core.config import settings
from datetime import datetime, timedelta
import logging
import uuid

logger = logging.getLogger(__name__)

BATCH_SIZE = 100


class SLABreachJob:
    """Background job to check and handle SLA breaches"""

    def __init__(self, db: Session):
        self.db = db
        self.ticket_repo = TicketRepository(db)
        self.employee_repo = EmployeeRepository(db)
        self.noti_service = NotificationService(db)

    def check_overdue_tickets(self) -> dict:
        """
        Kiểm tra tất cả ticket đang active và xử lý quá hạn SLA.
        Trả về dict với số lượng tickets đã xử lý.
        Uses batch processing to avoid RAM overflow.
        """
        result = {
            "checked": 0,
            "overdue": 0,
            "warning": 0,
            "escalated": 0
        }

        try:
            offset = 0
            while True:
                batch = self.db.query(Ticket).filter(
                    Ticket.status.in_(TicketStatusConstants.ACTIVE_STATUSES)
                ).offset(offset).limit(BATCH_SIZE).all()

                if not batch:
                    break

                now = datetime.utcnow()

                for ticket in batch:
                    result["checked"] += 1

                    if not ticket.expired_date:
                        continue

                    if ticket.expired_date < now:
                        result["overdue"] += 1
                        self._handle_overdue_ticket(ticket)
                    elif self._is_within_warning_window(ticket.expired_date, now):
                        result["warning"] += 1
                        self._send_sla_warning(ticket)

                self.db.expire_all()
                offset += BATCH_SIZE

            return result

        except Exception as e:
            logger.error(f"Error checking overdue tickets: {e}")
            return result

    def _is_within_warning_window(self, expired_date: datetime, now: datetime, window_hours: int = 24) -> bool:
        time_diff = expired_date - now
        return 0 < time_diff.total_seconds() <= (window_hours * 3600)

    def _handle_overdue_ticket(self, ticket: Ticket):
        try:
            logger.warning(f"Ticket {ticket.id_ticket} is overdue! Escalating...")

            if ticket.id_employee:
                self._notify_employee_breach(ticket, ticket.id_employee)

                if ticket.id_category:
                    category = self.db.query(TicketCategory).filter(
                        TicketCategory.id_category == ticket.id_category
                    ).first()

                    if category and category.id_department:
                        manager = self.employee_repo.get_department_manager(category.id_department)
                        if manager and manager.id != ticket.id_employee:
                            self._notify_manager_breach(ticket, manager.id_employee)
                            logger.info(f"Escalated ticket {ticket.id_ticket} to manager {manager.id_employee}")

        except Exception as e:
            logger.error(f"Error handling overdue ticket {ticket.id_ticket}: {e}")

    def _send_sla_warning(self, ticket: Ticket):
        try:
            if not ticket.id_employee:
                return

            short_title = ticket.title[:30] + "..." if len(ticket.title) > 30 else ticket.title
            hours_remaining = self._get_hours_remaining(ticket.expired_date)

            noti_data = NotificationCreate(
                title=f"SLA cảnh báo - {hours_remaining:.1f}h còn lại",
                content=f"Ticket #{str(ticket.id_ticket)[:8]}: '{short_title}' sắp hết SLA. Vui lòng ưu tiên xử lý!",
                notification_type="SLA_WARNING",
                id_reference=ticket.id_ticket,
                id_receiver=ticket.id_employee
            )
            self.noti_service.create_and_send(noti_data)

        except Exception as e:
            logger.error(f"Error sending SLA warning for ticket {ticket.id_ticket}: {e}")

    def _notify_employee_breach(self, ticket: Ticket, employee_id: uuid.UUID):
        try:
            short_title = ticket.title[:30] + "..." if len(ticket.title) > 30 else ticket.title

            noti_data = NotificationCreate(
                title=f"SLA BREACHED - Ticket quá hạn!",
                content=f"Ticket #{str(ticket.id_ticket)[:8]}: '{short_title}' đã quá hạn SLA. Vui lòng xử lý ngay!",
                notification_type="SLA_BREACHED",
                id_reference=ticket.id_ticket,
                id_receiver=employee_id
            )
            self.noti_service.create_and_send(noti_data)
        except Exception as e:
            logger.error(f"Error notifying employee breach: {e}")

    def _notify_manager_breach(self, ticket: Ticket, manager_id: uuid.UUID):
        try:
            short_title = ticket.title[:30] + "..." if len(ticket.title) > 30 else ticket.title

            noti_data = NotificationCreate(
                title=f"Ticket bị quá hạn SLA - Cần escalation",
                content=f"Ticket #{str(ticket.id_ticket)[:8]}: '{short_title}' đã quá hạn. Nhân viên được giao chưa xử lý kịp.",
                notification_type="SLA_ESCALATED",
                id_reference=ticket.id_ticket,
                id_receiver=manager_id
            )
            self.noti_service.create_and_send(noti_data)
        except Exception as e:
            logger.error(f"Error notifying manager breach: {e}")

    def _get_hours_remaining(self, expired_date: datetime) -> float:
        now = datetime.utcnow()
        diff = expired_date - now
        return diff.total_seconds() / 3600


class SurveyJob:
    """Background job to send CSAT survey emails after ticket is resolved"""

    SURVEY_DELAY_HOURS = settings.SURVEY_DELAY_HOURS
    BATCH_SIZE = settings.SURVEY_BATCH_SIZE

    def __init__(self, db: Session):
        self.db = db
        self.ticket_repo = TicketRepository(db)

    def check_and_send_pending_surveys(self) -> dict:
        """
        Tìm các ticket đã resolved hơn 1 giờ và gửi survey email.
        Uses batch processing to avoid RAM overflow.
        """
        result = {
            "checked": 0,
            "sent": 0,
            "errors": 0
        }

        try:
            offset = 0
            while True:
                batch = self._fetch_pending_batch(offset)
                if not batch:
                    break

                for ticket in batch:
                    result["checked"] += 1
                    try:
                        self._send_survey(ticket)
                        ticket.survey_sent = True
                        result["sent"] += 1
                    except Exception as e:
                        logger.error(f"Error sending survey for ticket {ticket.id_ticket}: {e}")
                        result["errors"] += 1

                self.db.commit()
                self.db.expire_all()
                offset += self.BATCH_SIZE

            return result

        except Exception as e:
            logger.error(f"Error in check_and_send_pending_surveys: {e}")
            self.db.rollback()
            return result

    def _fetch_pending_batch(self, offset: int):
        """Fetch a batch of tickets ready for survey"""
        cutoff_time = datetime.utcnow() - timedelta(hours=self.SURVEY_DELAY_HOURS)

        return self.db.query(Ticket).filter(
            Ticket.status == "Resolved",
            Ticket.survey_sent == False,
            Ticket.resolved_at != None,
            Ticket.resolved_at < cutoff_time
        ).offset(offset).limit(self.BATCH_SIZE).all()

    def _send_survey(self, ticket: Ticket):
        """Send survey email for a single ticket"""
        try:
            from app.services.emailService import email_service

            customer = self.db.query(Customer).filter(
                Customer.id_customer == ticket.id_customer
            ).first()

            if not customer or not customer.email:
                logger.warning(f"No customer email for ticket {ticket.id_ticket}")
                return

            email_service.send_csat_survey(
                to_email=customer.email,
                ticket_id=str(ticket.id_ticket),
                ticket_title=ticket.title,
                ticket_status=ticket.status,
                ticket_severity=ticket.severity
            )
            logger.info(f"Survey sent for ticket {ticket.id_ticket}")

        except Exception as e:
            logger.error(f"Error sending survey email for ticket {ticket.id_ticket}: {e}")
            raise


def run_sla_breach_check(db: Session):
    """Standalone function to run SLA breach check"""
    job = SLABreachJob(db)
    result = job.check_overdue_tickets()
    logger.info(f"SLA breach check completed: {result}")
    return result


def run_survey_job(db: Session):
    """Standalone function to run survey job"""
    job = SurveyJob(db)
    result = job.check_and_send_pending_surveys()
    logger.info(f"Survey job completed: {result}")
    return result


class SentimentAnalysisJob:
    """Background job to analyze sentiment from all sources every 7 days"""

    BATCH_SIZE = 50
    SLEEP_SECONDS = 1.0

    def __init__(self, db: Session):
        self.db = db
        self.groq_service = None

    def _get_groq_service(self):
        if self.groq_service is None:
            from app.services.groqService import GroqService
            self.groq_service = GroqService()
        return self.groq_service

    def run_analysis(self) -> dict:
        """
        Phân tích sentiment cho tất cả data trong 7 ngày qua.
        Chạy batch processing để tránh tràn RAM.
        """
        result = {
            "processed": 0,
            "positive": 0,
            "neutral": 0,
            "negative": 0,
            "errors": 0
        }

        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=7)

            sources = ["message", "evaluation", "comment"]

            for source in sources:
                try:
                    source_result = self._process_source(source, start_date, end_date)
                    result["processed"] += source_result["processed"]
                    result["positive"] += source_result["positive"]
                    result["neutral"] += source_result["neutral"]
                    result["negative"] += source_result["negative"]
                    result["errors"] += source_result["errors"]
                except Exception as e:
                    logger.error(f"Error processing source {source}: {e}")

            self._generate_reports(start_date, end_date)

            return result

        except Exception as e:
            logger.error(f"Error in sentiment analysis: {e}")
            return result

    def _process_source(self, source_type: str, start_date: datetime, end_date: datetime) -> dict:
        """Xử lý 1 nguồn (messages/evaluations/comments)"""
        result = {"processed": 0, "positive": 0, "neutral": 0, "negative": 0, "errors": 0}

        if source_type == "message":
            data_items = self._get_messages(start_date, end_date)
        elif source_type == "evaluation":
            data_items = self._get_evaluations(start_date, end_date)
        elif source_type == "comment":
            data_items = self._get_comments(start_date, end_date)
        else:
            return result

        groq_service = self._get_groq_service()

        for i in range(0, len(data_items), self.BATCH_SIZE):
            batch = data_items[i:i + self.BATCH_SIZE]

            for item in batch:
                try:
                    content = item["content"]
                    sentiment = groq_service.analyze_sentiment(content)

                    label = sentiment.get("label", "neutral")
                    score = sentiment.get("score", 0.0)

                    self._save_detail(
                        source_type=source_type,
                        source_id=item["id"],
                        label=label,
                        score=score,
                        customer_id=item["customer_id"],
                        ticket_id=item.get("ticket_id"),
                        department_id=item["department_id"],
                        content=content[:500] if content else None
                    )

                    if label == "positive":
                        result["positive"] += 1
                    elif label == "neutral":
                        result["neutral"] += 1
                    else:
                        result["negative"] += 1

                    result["processed"] += 1

                except Exception as e:
                    logger.error(f"Error processing {source_type} {item['id']}: {e}")
                    result["errors"] += 1

            self.db.commit()

            import time
            time.sleep(self.SLEEP_SECONDS)

        return result

    def _get_messages(self, start_date: datetime, end_date: datetime) -> list:
        from sqlalchemy import text

        query = text("""
            SELECT m.id_message, m.message, m.id_ticket, t.id_customer, e.id_department
            FROM messages m
            JOIN tickets t ON m.id_ticket = t.id_ticket
            LEFT JOIN employees e ON t.id_employee = e.id_employee
            WHERE m.created_at >= :start_date AND m.created_at < :end_date
            AND m.is_deleted = false
        """)
        results = self.db.execute(query, {"start_date": start_date, "end_date": end_date}).fetchall()

        return [
            {
                "id": row[0],
                "content": row[1],
                "ticket_id": row[2],
                "customer_id": row[3],
                "department_id": row[4]
            }
            for row in results
        ]

    def _get_evaluations(self, start_date: datetime, end_date: datetime) -> list:
        from sqlalchemy import text

        query = text("""
            SELECT e.id_evaluate, e.comment, e.id_ticket, t.id_customer, emp.id_department
            FROM evaluates e
            JOIN tickets t ON e.id_ticket = t.id_ticket
            LEFT JOIN employees emp ON t.id_employee = emp.id_employee
            WHERE e.created_at >= :start_date AND e.created_at < :end_date
        """)
        results = self.db.execute(query, {"start_date": start_date, "end_date": end_date}).fetchall()

        return [
            {
                "id": row[0],
                "content": str(row[1]) if row[1] else "Star rating",
                "ticket_id": row[2],
                "customer_id": row[3],
                "department_id": row[4]
            }
            for row in results
        ]

    def _get_comments(self, start_date: datetime, end_date: datetime) -> list:
        from sqlalchemy import text

        query = text("""
            SELECT tc.id_comment, tc.content, tc.id_ticket, t.id_customer, e.id_department
            FROM ticket_comments tc
            JOIN tickets t ON tc.id_ticket = t.id_ticket
            LEFT JOIN employees e ON t.id_employee = e.id_employee
            WHERE tc.created_at >= :start_date AND tc.created_at < :end_date
        """)
        results = self.db.execute(query, {"start_date": start_date, "end_date": end_date}).fetchall()

        return [
            {
                "id": row[0],
                "content": row[1],
                "ticket_id": row[2],
                "customer_id": row[3],
                "department_id": row[4]
            }
            for row in results
        ]

    def _save_detail(self, source_type: str, source_id, label: str, score: float,
                     customer_id, ticket_id, department_id, content: str):
        from sqlalchemy import text

        target_date = datetime.utcnow() - timedelta(days=3)
        year = target_date.year
        month = target_date.month

        check_report = text("""
            SELECT id_report FROM sentiment_reports 
            WHERE year = :year AND month = :month AND scope = 'system' AND id_department IS NULL
        """)
        report_row = self.db.execute(check_report, {"year": year, "month": month}).fetchone()

        if not report_row:
            insert_report = text("""
                INSERT INTO sentiment_reports (id_report, year, month, scope, id_department, 
                    positive_count, neutral_count, negative_count, total_interactions, created_at)
                VALUES (gen_random_uuid(), :year, :month, 'system', NULL, 0, 0, 0, 0, NOW())
                RETURNING id_report
            """)
            result = self.db.execute(insert_report, {"year": year, "month": month})
            id_report = result.fetchone()[0]
        else:
            id_report = report_row[0]

        sentiment_counts = {"positive": 0, "neutral": 0, "negative": 0}
        if label == "positive":
            sentiment_counts["positive"] = 1
        elif label == "neutral":
            sentiment_counts["neutral"] = 1
        else:
            sentiment_counts["negative"] = 1

        source_field_map = {
            "message": f"message_{label}",
            "evaluation": f"evaluation_{label}",
            "comment": f"comment_{label}"
        }

        update_fields = {
            "positive_count": sentiment_counts["positive"],
            "neutral_count": sentiment_counts["neutral"],
            "negative_count": sentiment_counts["negative"],
            "total_interactions": 1
        }

        if source_type in source_field_map:
            update_fields[source_field_map[source_type]] = 1

        set_clauses = []
        params = {"id_report": id_report}
        for key, value in update_fields.items():
            if key == "total_interactions":
                set_clauses.append(f"{key} = {key} + :{key}")
            else:
                set_clauses.append(f"{key} = {key} + :{key}")
            params[key] = value

        set_clauses.append("updated_at = NOW()")

        update_report = text(f"""
            UPDATE sentiment_reports SET 
                {', '.join(set_clauses)}
            WHERE id_report = :id_report
        """)
        self.db.execute(update_report, params)

        insert_detail = text("""
            INSERT INTO sentiment_details (id_detail, id_report, source_type, source_id, sentiment_label, 
                sentiment_score, id_customer, id_ticket, id_department, original_content, created_at)
            VALUES (gen_random_uuid(), :id_report, :source_type, :source_id, :label, :score, 
                :customer_id, :ticket_id, :department_id, :content, NOW())
        """)
        self.db.execute(insert_detail, {
            "id_report": id_report,
            "source_type": source_type,
            "source_id": source_id,
            "label": label,
            "score": score,
            "customer_id": customer_id,
            "ticket_id": ticket_id,
            "department_id": department_id,
            "content": content
        })

    def _generate_reports(self, start_date: datetime, end_date: datetime):
        """Tạo/cập nhật sentiment_reports cho system và từng department"""
        from sqlalchemy import text

        target_date = end_date - timedelta(days=3)
        year = target_date.year
        month = target_date.month

        details_query = text("""
            SELECT id_detail, sentiment_label, sentiment_score, id_department, source_type
            FROM sentiment_details
        """)
        details = self.db.execute(details_query).fetchall()

        if not details:
            return

        total_score = sum(d[2] for d in details)
        avg_score = total_score / len(details) if details else 0.0

        update_system = text("""
            UPDATE sentiment_reports SET 
                avg_sentiment_score = :avg_score,
                total_interactions = :total,
                updated_at = NOW()
            WHERE year = :year AND month = :month AND scope = 'system' AND id_department IS NULL
        """)
        self.db.execute(update_system, {"avg_score": avg_score, "total": len(details), "year": year, "month": month})

        dept_stats = {}
        for detail in details:
            dept_id = detail[3]
            source_type = detail[4]
            label = detail[1]
            score = detail[2]

            if dept_id:
                if dept_id not in dept_stats:
                    dept_stats[dept_id] = {
                        "positive": 0, "neutral": 0, "negative": 0,
                        "total_score": 0.0, "count": 0,
                        "message_positive": 0, "message_neutral": 0, "message_negative": 0,
                        "evaluation_positive": 0, "evaluation_neutral": 0, "evaluation_negative": 0,
                        "comment_positive": 0, "comment_neutral": 0, "comment_negative": 0
                    }

                if label == "positive":
                    dept_stats[dept_id]["positive"] += 1
                elif label == "neutral":
                    dept_stats[dept_id]["neutral"] += 1
                else:
                    dept_stats[dept_id]["negative"] += 1

                dept_stats[dept_id]["total_score"] += score
                dept_stats[dept_id]["count"] += 1

                if source_type == "message":
                    if label == "positive":
                        dept_stats[dept_id]["message_positive"] += 1
                    elif label == "neutral":
                        dept_stats[dept_id]["message_neutral"] += 1
                    else:
                        dept_stats[dept_id]["message_negative"] += 1
                elif source_type == "evaluation":
                    if label == "positive":
                        dept_stats[dept_id]["evaluation_positive"] += 1
                    elif label == "neutral":
                        dept_stats[dept_id]["evaluation_neutral"] += 1
                    else:
                        dept_stats[dept_id]["evaluation_negative"] += 1
                elif source_type == "comment":
                    if label == "positive":
                        dept_stats[dept_id]["comment_positive"] += 1
                    elif label == "neutral":
                        dept_stats[dept_id]["comment_neutral"] += 1
                    else:
                        dept_stats[dept_id]["comment_negative"] += 1

        for dept_id, stats in dept_stats.items():
            dept_avg_score = stats["total_score"] / stats["count"] if stats["count"] > 0 else 0.0

            check_dept = text("""
                SELECT id_report FROM sentiment_reports 
                WHERE year = :year AND month = :month AND scope = 'department' AND id_department = :dept_id
            """)
            dept_row = self.db.execute(check_dept, {"year": year, "month": month, "dept_id": dept_id}).fetchone()

            if not dept_row:
                insert_dept = text("""
                    INSERT INTO sentiment_reports (id_report, year, month, scope, id_department, 
                        positive_count, neutral_count, negative_count, total_interactions, 
                        avg_sentiment_score, message_positive, message_neutral, message_negative,
                        evaluation_positive, evaluation_neutral, evaluation_negative,
                        comment_positive, comment_neutral, comment_negative, created_at)
                    VALUES (gen_random_uuid(), :year, :month, 'department', :dept_id,
                        :positive, :neutral, :negative, :total, :avg_score,
                        :msg_pos, :msg_neut, :msg_neg,
                        :eval_pos, :eval_neut, :eval_neg,
                        :com_pos, :com_neut, :com_neg, NOW())
                """)
                self.db.execute(insert_dept, {
                    "year": year, "month": month, "dept_id": dept_id,
                    "positive": stats["positive"],
                    "neutral": stats["neutral"],
                    "negative": stats["negative"],
                    "total": stats["count"],
                    "avg_score": dept_avg_score,
                    "msg_pos": stats["message_positive"],
                    "msg_neut": stats["message_neutral"],
                    "msg_neg": stats["message_negative"],
                    "eval_pos": stats["evaluation_positive"],
                    "eval_neut": stats["evaluation_neutral"],
                    "eval_neg": stats["evaluation_negative"],
                    "com_pos": stats["comment_positive"],
                    "com_neut": stats["comment_neutral"],
                    "com_neg": stats["comment_negative"]
                })
            else:
                update_dept = text("""
                    UPDATE sentiment_reports SET 
                        positive_count = :positive,
                        neutral_count = :neutral,
                        negative_count = :negative,
                        total_interactions = :total,
                        avg_sentiment_score = :avg_score,
                        message_positive = :msg_pos,
                        message_neutral = :msg_neut,
                        message_negative = :msg_neg,
                        evaluation_positive = :eval_pos,
                        evaluation_neutral = :eval_neut,
                        evaluation_negative = :eval_neg,
                        comment_positive = :com_pos,
                        comment_neutral = :com_neut,
                        comment_negative = :com_neg,
                        updated_at = NOW()
                    WHERE id_report = :id_report
                """)
                self.db.execute(update_dept, {
                    "positive": stats["positive"],
                    "neutral": stats["neutral"],
                    "negative": stats["negative"],
                    "total": stats["count"],
                    "avg_score": dept_avg_score,
                    "msg_pos": stats["message_positive"],
                    "msg_neut": stats["message_neutral"],
                    "msg_neg": stats["message_negative"],
                    "eval_pos": stats["evaluation_positive"],
                    "eval_neut": stats["evaluation_neutral"],
                    "eval_neg": stats["evaluation_negative"],
                    "com_pos": stats["comment_positive"],
                    "com_neut": stats["comment_neutral"],
                    "com_neg": stats["comment_negative"],
                    "id_report": dept_row[0]
                })

        self.db.commit()


def run_sentiment_analysis(db: Session):
    """Standalone function to run sentiment analysis job"""
    job = SentimentAnalysisJob(db)
    result = job.run_analysis()
    logger.info(f"Sentiment analysis completed: {result}")
    return result
