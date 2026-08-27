from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import datetime, timezone
from typing import Optional, List


class CampaignStepBase(BaseModel):
    template_id: int
    step_order: int = Field(ge=1)
    delay_hours: int = Field(default=0, ge=0)
    scheduled_at: Optional[datetime] = None

    @field_validator("scheduled_at")
    @classmethod
    def normalize_scheduled_at(cls, v: Optional[datetime]) -> Optional[datetime]:
        # Store everything as naive UTC (matches how the rest of the app
        # stores/compares datetimes). If the client sends a timezone-aware
        # value (e.g. an ISO string ending in "Z"), convert it to UTC and
        # drop the tzinfo; a naive value is assumed to already be UTC.
        if v is not None and v.tzinfo is not None:
            v = v.astimezone(timezone.utc).replace(tzinfo=None)
        return v


class CampaignStepCreate(CampaignStepBase):
    pass


class CampaignStepResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    campaign_id: int
    template_id: int
    step_order: int
    delay_hours: int
    scheduled_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class CampaignBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None


class CampaignCreate(CampaignBase):
    steps: List[CampaignStepCreate] = []


class CampaignUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[str] = None


class CampaignResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    name: str
    description: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime
    steps: List[CampaignStepResponse] = []


class CampaignListResponse(BaseModel):
    items: List[CampaignResponse]
    total: int


class EmailJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    campaign_id: int
    campaign_step_id: int
    contact_id: int
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    status: str
    scheduled_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    provider_message_id: Optional[str] = None
    error_message: Optional[str] = None
    subject: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class EmailJobListResponse(BaseModel):
    items: List[EmailJobResponse]
    total: int