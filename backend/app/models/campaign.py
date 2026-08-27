from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database.base import Base


class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String(255), nullable=False)
    status = Column(String(50), default="draft", nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user = relationship("User", back_populates="campaigns")
    steps = relationship(
        "CampaignStep",
        back_populates="campaign",
        cascade="all, delete-orphan",
        order_by="CampaignStep.step_order",
    )
    email_jobs = relationship(
        "EmailJob", back_populates="campaign", cascade="all, delete-orphan"
    )


class CampaignStep(Base):
    __tablename__ = "campaign_steps"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    campaign_id = Column(
        Integer,
        ForeignKey("campaigns.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    template_id = Column(
        Integer,
        ForeignKey("email_templates.id", ondelete="RESTRICT"),
        nullable=False,
    )
    step_order = Column(Integer, nullable=False, default=1)
    delay_hours = Column(Integer, nullable=False, default=0)
    scheduled_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    campaign = relationship("Campaign", back_populates="steps")
    template = relationship("EmailTemplate", back_populates="campaign_steps")
    email_jobs = relationship("EmailJob", back_populates="campaign_step")