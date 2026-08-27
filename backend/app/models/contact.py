from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database.base import Base


class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    email = Column(String(255), nullable=False, index=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    status = Column(String(50), default="active", nullable=False, index=True)

    # Subscription info for this contact/customer, used to personalize
    # billing-related emails. All nullable — templates fall back gracefully
    # when a contact has no subscription data.
    subscription_plan = Column(String(100), nullable=True)
    subscription_billing_cycle = Column(String(50), nullable=True)
    subscription_status = Column(String(50), nullable=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user = relationship("User", back_populates="contacts")
    email_jobs = relationship(
        "EmailJob", back_populates="contact", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_contacts_user_email", "user_id", "email", unique=True),
    )