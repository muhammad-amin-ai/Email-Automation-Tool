import logging
from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.campaign import Campaign, CampaignStep
from app.models.contact import Contact
from app.models.email_job import EmailJob, EmailEvent
from app.models.template import EmailTemplate
from app.models.user import User
from app.schemas.campaign import CampaignCreate, CampaignUpdate
from app.services.email_service import email_service
from app.services import template_engine
from app.core.exceptions import NotFoundException, BadRequestException


logger = logging.getLogger(__name__)


def create_campaign(db: Session, user_id: int, data: CampaignCreate) -> Campaign:
    campaign = Campaign(
        user_id=user_id,
        name=data.name,
        description=data.description,
        status="draft",
    )
    db.add(campaign)
    db.flush()

    for step_data in data.steps:
        template = (
            db.query(EmailTemplate)
            .filter(
                EmailTemplate.id == step_data.template_id,
                EmailTemplate.user_id == user_id,
            )
            .first()
        )
        if not template:
            db.rollback()
            raise BadRequestException(
                f"Template with id {step_data.template_id} not found."
            )
        step = CampaignStep(
            campaign_id=campaign.id,
            template_id=step_data.template_id,
            step_order=step_data.step_order,
            delay_hours=step_data.delay_hours,
            scheduled_at=step_data.scheduled_at,
        )
        db.add(step)

    db.commit()
    db.refresh(campaign)
    return campaign


def get_campaigns(db: Session, user_id: int) -> List[Campaign]:
    return (
        db.query(Campaign)
        .filter(Campaign.user_id == user_id)
        .order_by(Campaign.id.desc())
        .all()
    )


def get_campaign(db: Session, user_id: int, campaign_id: int) -> Optional[Campaign]:
    return (
        db.query(Campaign)
        .filter(Campaign.user_id == user_id, Campaign.id == campaign_id)
        .first()
    )


def update_campaign(
    db: Session, user_id: int, campaign_id: int, data: CampaignUpdate
) -> Optional[Campaign]:
    campaign = get_campaign(db, user_id, campaign_id)
    if not campaign:
        return None

    update_data = data.model_dump(exclude_unset=True)

    if "status" in update_data and update_data["status"]:
        valid_statuses = {"draft", "active", "paused", "completed", "failed"}
        if update_data["status"] not in valid_statuses:
            raise BadRequestException(f"Invalid status: {update_data['status']}")

    for key, value in update_data.items():
        setattr(campaign, key, value)

    db.commit()
    db.refresh(campaign)
    return campaign


def delete_campaign(db: Session, user_id: int, campaign_id: int) -> bool:
    campaign = get_campaign(db, user_id, campaign_id)
    if not campaign:
        return False
    db.delete(campaign)
    db.commit()
    return True


def get_campaign_jobs(db: Session, user_id: int, campaign_id: int) -> List[EmailJob]:
    campaign = get_campaign(db, user_id, campaign_id)
    if not campaign:
        raise NotFoundException("Campaign not found.")
    return (
        db.query(EmailJob)
        .filter(EmailJob.campaign_id == campaign_id)
        .order_by(EmailJob.id.desc())
        .limit(500)
        .all()
    )


def start_campaign(db: Session, user_id: int, campaign_id: int) -> Campaign:
    campaign = get_campaign(db, user_id, campaign_id)
    if not campaign:
        raise NotFoundException("Campaign not found.")

    if not campaign.steps:
        raise BadRequestException("Campaign has no steps configured.")

    for step in campaign.steps:
        if not step.template:
            raise BadRequestException(
                f"Step {step.step_order} references a missing template."
            )

    if campaign.status == "active":
        raise BadRequestException("Campaign is already active.")

    contacts = (
        db.query(Contact)
        .filter(Contact.user_id == user_id, Contact.status == "active")
        .all()
    )

    if not contacts:
        raise BadRequestException("No active contacts to send to.")

    now = datetime.utcnow()
    jobs_created = 0

    for contact in contacts:
        for step in sorted(campaign.steps, key=lambda s: s.step_order):
            if step.scheduled_at:
                # Absolute date/time set on the step — send at that exact
                # moment, regardless of when the campaign was started.
                scheduled_at = step.scheduled_at
            else:
                # No absolute time set — fall back to the relative delay
                # counted from the moment the campaign was started.
                scheduled_at = now + timedelta(hours=step.delay_hours or 0)
            job = EmailJob(
                campaign_id=campaign.id,
                campaign_step_id=step.id,
                contact_id=contact.id,
                status="queued",
                scheduled_at=scheduled_at,
            )
            db.add(job)
            jobs_created += 1

    campaign.status = "active"
    db.commit()
    db.refresh(campaign)
    logger.info(f"Campaign {campaign.id} started with {jobs_created} queued jobs.")

    try:
        process_due_jobs(db, limit=100)
    except Exception as e:
        logger.error(f"Initial processing error for campaign {campaign.id}: {e}")

    return campaign


def pause_campaign(db: Session, user_id: int, campaign_id: int) -> Campaign:
    campaign = get_campaign(db, user_id, campaign_id)
    if not campaign:
        raise NotFoundException("Campaign not found.")

    campaign.status = "paused"

    db.query(EmailJob).filter(
        EmailJob.campaign_id == campaign_id,
        EmailJob.status == "queued",
    ).update({"status": "cancelled"}, synchronize_session=False)

    db.commit()
    db.refresh(campaign)
    return campaign


def process_due_jobs(db: Session, limit: int = 50) -> int:
    now = datetime.utcnow()

    jobs = (
        db.query(EmailJob)
        .filter(EmailJob.status == "queued", EmailJob.scheduled_at <= now)
        .order_by(EmailJob.scheduled_at.asc())
        .limit(limit)
        .all()
    )

    processed = 0
    for job in jobs:
        job_id = job.id
        try:
            job.status = "processing"
            db.commit()

            step = job.campaign_step
            template = step.template if step else None
            contact = job.contact
            campaign = job.campaign
            user = campaign.user if campaign else None

            if not template or not contact or not user:
                job.status = "failed"
                job.error_message = "Missing template, contact, or sender profile."
                db.commit()
                continue

            if contact.status != "active":
                job.status = "cancelled"
                job.error_message = f"Contact status is '{contact.status}'."
                db.commit()
                continue

            context = template_engine.build_context(user, contact)
            try:
                subject = template_engine.render_and_validate(
                    template.subject, context, escape_html=False
                )
                body = template_engine.render_and_validate(template.html_body, context)
            except ValueError as e:
                job.status = "failed"
                job.error_message = str(e)[:1000]
                db.commit()
                continue

            # Templates are authored as plain text (line breaks, blank lines
            # between paragraphs). Sent as-is inside an HTML email, clients
            # collapse those newlines into one run-on paragraph — convert to
            # <p>/<br> here so the sent email keeps its original formatting.
            html_out = template_engine.plain_text_to_html(body)

            job.subject = subject
            job.body_snapshot = html_out

            result = email_service.send_email(
                to_email=contact.email,
                subject=subject,
                html_body=html_out,
                text_body=body,
            )

            job.status = "sent"
            job.sent_at = datetime.utcnow()
            job.provider_message_id = result.get("id")
            job.error_message = None

            event = EmailEvent(
                email_job_id=job.id,
                event_type="sent",
                event_data={"provider_message_id": job.provider_message_id},
            )
            db.add(event)
            db.commit()
            processed += 1
        except Exception as e:
            db.rollback()
            try:
                fresh = db.query(EmailJob).filter(EmailJob.id == job_id).first()
                if fresh:
                    fresh.status = "failed"
                    fresh.error_message = str(e)[:1000]
                    db.commit()
            except Exception:
                db.rollback()
            logger.exception(f"Failed to process job {job_id}")

    return processed