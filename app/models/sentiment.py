import uuid
from sqlalchemy import Column, Integer, String, DateTime, Float, Text, ForeignKey, Index, UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base


class SentimentReport(Base):
    __tablename__ = "sentiment_reports"

    id_report = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    scope = Column(String(20), nullable=False)
    id_department = Column(UUID(as_uuid=True), ForeignKey("departments.id_department", ondelete="SET NULL"), nullable=True)

    positive_count = Column(Integer, default=0)
    neutral_count = Column(Integer, default=0)
    negative_count = Column(Integer, default=0)
    avg_sentiment_score = Column(Float)

    message_positive = Column(Integer, default=0)
    message_neutral = Column(Integer, default=0)
    message_negative = Column(Integer, default=0)
    evaluation_positive = Column(Integer, default=0)
    evaluation_neutral = Column(Integer, default=0)
    evaluation_negative = Column(Integer, default=0)
    comment_positive = Column(Integer, default=0)
    comment_neutral = Column(Integer, default=0)
    comment_negative = Column(Integer, default=0)

    total_interactions = Column(Integer, default=0)
    avg_response_time_hours = Column(Float)
    resolution_rate = Column(Float)
    sentiment_change = Column(Float)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    details = relationship("SentimentDetail", back_populates="report", cascade="all, delete-orphan")

    __table_args__ = (
        Index('ix_sentiment_reports_year_month_scope', 'year', 'month', 'scope'),
        Index('ix_sentiment_reports_department', 'id_department'),
    )


class SentimentDetail(Base):
    __tablename__ = "sentiment_details"

    id_detail = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    id_report = Column(UUID(as_uuid=True), ForeignKey("sentiment_reports.id_report", ondelete="CASCADE"), nullable=False)
    source_type = Column(String(20), nullable=False)
    source_id = Column(UUID(as_uuid=True), nullable=False)
    sentiment_label = Column(String(20), nullable=False)
    sentiment_score = Column(Float, nullable=False)
    id_customer = Column(UUID(as_uuid=True), ForeignKey("customers.id_customer", ondelete="CASCADE"), nullable=False)
    id_ticket = Column(UUID(as_uuid=True), ForeignKey("tickets.id_ticket", ondelete="SET NULL"), nullable=True)
    id_department = Column(UUID(as_uuid=True), ForeignKey("departments.id_department", ondelete="CASCADE"), nullable=False)
    original_content = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)

    report = relationship("SentimentReport", back_populates="details")

    __table_args__ = (
        Index('ix_sentiment_details_report', 'id_report'),
        Index('ix_sentiment_details_source', 'source_type', 'source_id'),
    )