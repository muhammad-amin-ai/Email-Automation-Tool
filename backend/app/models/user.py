from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Sender / business profile used to personalize outgoing emails
    # (never hardcode this info in templates — pull it from here instead).
    sender_name = Column(String(255), nullable=True)
    sender_title = Column(String(255), nullable=True)
    company_name = Column(String(255), nullable=True)
    sender_phone = Column(String(50), nullable=True)
    website_url = Column(String(255), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    contacts = relationship(
        "Contact", back_populates="user", cascade="all, delete-orphan"
    )
    templates = relationship(
        "EmailTemplate", back_populates="user", cascade="all, delete-orphan"
    )
    campaigns = relationship(
        "Campaign", back_populates="user", cascade="all, delete-orphan"
    )