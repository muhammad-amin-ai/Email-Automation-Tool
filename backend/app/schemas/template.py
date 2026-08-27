from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional, List


class TemplateBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    subject: str = Field(min_length=1, max_length=500)
    html_body: str = Field(min_length=1)


class TemplateCreate(TemplateBase):
    pass


class TemplateUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    subject: Optional[str] = Field(default=None, min_length=1, max_length=500)
    html_body: Optional[str] = Field(default=None, min_length=1)


class TemplateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    name: str
    subject: str
    html_body: str
    created_at: datetime
    updated_at: datetime


class TemplateListResponse(BaseModel):
    items: List[TemplateResponse]
    total: int
