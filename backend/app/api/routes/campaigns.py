from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.user import User
from app.schemas.campaign import (
    CampaignCreate,
    CampaignUpdate,
    CampaignResponse,
    CampaignListResponse,
    EmailJobListResponse,
    EmailJobResponse,
)
from app.services.campaign_service import (
    create_campaign,
    get_campaigns,
    get_campaign,
    update_campaign,
    delete_campaign,
    get_campaign_jobs,
    start_campaign,
    pause_campaign,
)
from app.core.exceptions import NotFoundException
from app.dependencies.auth import get_current_user


router = APIRouter(prefix="/campaigns", tags=["Campaigns"])


@router.get("", response_model=CampaignListResponse)
def list_campaigns(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items = get_campaigns(db, current_user.id)
    return CampaignListResponse(
        items=[CampaignResponse.model_validate(c) for c in items],
        total=len(items),
    )


@router.post(
    "",
    response_model=CampaignResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_new_campaign(
    payload: CampaignCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    campaign = create_campaign(db, current_user.id, payload)
    return CampaignResponse.model_validate(campaign)


@router.get("/{campaign_id}", response_model=CampaignResponse)
def retrieve_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    campaign = get_campaign(db, current_user.id, campaign_id)
    if not campaign:
        raise NotFoundException("Campaign not found.")
    return CampaignResponse.model_validate(campaign)


@router.put("/{campaign_id}", response_model=CampaignResponse)
def update_existing_campaign(
    campaign_id: int,
    payload: CampaignUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    campaign = update_campaign(db, current_user.id, campaign_id, payload)
    if not campaign:
        raise NotFoundException("Campaign not found.")
    return CampaignResponse.model_validate(campaign)


@router.delete("/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    success = delete_campaign(db, current_user.id, campaign_id)
    if not success:
        raise NotFoundException("Campaign not found.")
    return None


@router.post("/{campaign_id}/start", response_model=CampaignResponse)
def start_existing_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    campaign = start_campaign(db, current_user.id, campaign_id)
    return CampaignResponse.model_validate(campaign)


@router.post("/{campaign_id}/pause", response_model=CampaignResponse)
def pause_existing_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    campaign = pause_campaign(db, current_user.id, campaign_id)
    return CampaignResponse.model_validate(campaign)


@router.get("/{campaign_id}/jobs", response_model=EmailJobListResponse)
def list_campaign_jobs(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    jobs = get_campaign_jobs(db, current_user.id, campaign_id)
    items = []
    for j in jobs:
        item = EmailJobResponse.model_validate(j)
        if j.contact:
            item.contact_email = j.contact.email
            item.contact_name = (
                " ".join(filter(None, [j.contact.first_name, j.contact.last_name])).strip()
                or None
            )
        items.append(item)
    return EmailJobListResponse(items=items, total=len(items))