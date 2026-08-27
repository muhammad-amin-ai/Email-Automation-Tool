from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database.base import Base


class EmailTemplate(Base):
    __tablename__ = "email_templates"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String(255), nullable=False)
    subject = Column(String(500), nullable=False)
    html_body = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user = relationship("User", back_populates="templates")
    campaign_steps = relationship("CampaignStep", back_populates="template")
