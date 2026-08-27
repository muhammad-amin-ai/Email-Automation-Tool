from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database.connection import get_db
from app.models.user import User
from app.models.contact import Contact
from app.models.template import EmailTemplate
from app.models.campaign import Campaign
from app.models.email_job import EmailJob
from app.schemas.analytics import AnalyticsSummary
from app.dependencies.auth import get_current_user


router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/summary", response_model=AnalyticsSummary)
def get_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user_id = current_user.id

    total_contacts = (
        db.query(func.count(Contact.id))
        .filter(Contact.user_id == user_id)
        .scalar()
        or 0
    )
    active_contacts = (
        db.query(func.count(Contact.id))
        .filter(Contact.user_id == user_id, Contact.status == "active")
        .scalar()
        or 0
    )
    unsubscribed = (
        db.query(func.count(Contact.id))
        .filter(Contact.user_id == user_id, Contact.status == "unsubscribed")
        .scalar()
        or 0
    )
    bounced_contacts = (
        db.query(func.count(Contact.id))
        .filter(Contact.user_id == user_id, Contact.status == "bounced")
        .scalar()
        or 0
    )

    total_campaigns = (
        db.query(func.count(Campaign.id))
        .filter(Campaign.user_id == user_id)
        .scalar()
        or 0
    )
    active_campaigns = (
        db.query(func.count(Campaign.id))
        .filter(Campaign.user_id == user_id, Campaign.status == "active")
        .scalar()
        or 0
    )
    draft_campaigns = (
        db.query(func.count(Campaign.id))
        .filter(Campaign.user_id == user_id, Campaign.status == "draft")
        .scalar()
        or 0
    )
    paused_campaigns = (
        db.query(func.count(Campaign.id))
        .filter(Campaign.user_id == user_id, Campaign.status == "paused")
        .scalar()
        or 0
    )
    completed_campaigns = (
        db.query(func.count(Campaign.id))
        .filter(Campaign.user_id == user_id, Campaign.status == "completed")
        .scalar()
        or 0
    )

    total_templates = (
        db.query(func.count(EmailTemplate.id))
        .filter(EmailTemplate.user_id == user_id)
        .scalar()
        or 0
    )

    campaign_ids_subq = (
        db.query(Campaign.id).filter(Campaign.user_id == user_id).subquery()
    )

    total_sent = (
        db.query(func.count(EmailJob.id))
        .filter(
            EmailJob.campaign_id.in_(campaign_ids_subq),
            EmailJob.status == "sent",
        )
        .scalar()
        or 0
    )
    total_queued = (
        db.query(func.count(EmailJob.id))
        .filter(
            EmailJob.campaign_id.in_(campaign_ids_subq),
            EmailJob.status == "queued",
        )
        .scalar()
        or 0
    )
    total_processing = (
        db.query(func.count(EmailJob.id))
        .filter(
            EmailJob.campaign_id.in_(campaign_ids_subq),
            EmailJob.status == "processing",
        )
        .scalar()
        or 0
    )
    total_failed = (
        db.query(func.count(EmailJob.id))
        .filter(
            EmailJob.campaign_id.in_(campaign_ids_subq),
            EmailJob.status == "failed",
        )
        .scalar()
        or 0
    )
    total_bounced = (
        db.query(func.count(EmailJob.id))
        .filter(
            EmailJob.campaign_id.in_(campaign_ids_subq),
            EmailJob.status == "bounced",
        )
        .scalar()
        or 0
    )

    return AnalyticsSummary(
        total_contacts=total_contacts,
        active_contacts=active_contacts,
        unsubscribed_contacts=unsubscribed,
        bounced_contacts=bounced_contacts,
        total_campaigns=total_campaigns,
        active_campaigns=active_campaigns,
        draft_campaigns=draft_campaigns,
        paused_campaigns=paused_campaigns,
        completed_campaigns=completed_campaigns,
        total_templates=total_templates,
        total_sent=total_sent,
        total_queued=total_queued,
        total_processing=total_processing,
        total_failed=total_failed,
        total_bounced=total_bounced,
    )
