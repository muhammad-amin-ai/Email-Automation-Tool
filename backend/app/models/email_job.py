from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    DateTime,
    Text,
    JSON,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database.base import Base


class EmailJob(Base):
    __tablename__ = "email_jobs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    campaign_id = Column(
        Integer,
        ForeignKey("campaigns.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    campaign_step_id = Column(
        Integer,
        ForeignKey("campaign_steps.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    contact_id = Column(
        Integer,
        ForeignKey("contacts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status = Column(String(50), default="queued", nullable=False, index=True)
    scheduled_at = Column(DateTime, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    provider_message_id = Column(String(255), nullable=True)
    error_message = Column(Text, nullable=True)
    subject = Column(String(500), nullable=True)
    body_snapshot = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    campaign = relationship("Campaign", back_populates="email_jobs")
    campaign_step = relationship("CampaignStep", back_populates="email_jobs")
    contact = relationship("Contact", back_populates="email_jobs")
    events = relationship(
        "EmailEvent", back_populates="email_job", cascade="all, delete-orphan"
    )


class EmailEvent(Base):
    __tablename__ = "email_events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email_job_id = Column(
        Integer,
        ForeignKey("email_jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type = Column(String(100), nullable=False, index=True)
    event_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    email_job = relationship("EmailJob", back_populates="events")
