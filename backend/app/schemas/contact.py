from pydantic import BaseModel, EmailStr, ConfigDict, Field
from datetime import datetime
from typing import Optional, List


class ContactBase(BaseModel):
    email: EmailStr
    first_name: Optional[str] = Field(default=None, max_length=100)
    last_name: Optional[str] = Field(default=None, max_length=100)
    status: Optional[str] = Field(default="active", max_length=50)
    subscription_plan: Optional[str] = Field(default=None, max_length=100)
    subscription_billing_cycle: Optional[str] = Field(default=None, max_length=50)
    subscription_status: Optional[str] = Field(default=None, max_length=50)


class ContactCreate(ContactBase):
    pass


class ContactUpdate(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(default=None, max_length=100)
    last_name: Optional[str] = Field(default=None, max_length=100)
    status: Optional[str] = Field(default=None, max_length=50)
    subscription_plan: Optional[str] = Field(default=None, max_length=100)
    subscription_billing_cycle: Optional[str] = Field(default=None, max_length=50)
    subscription_status: Optional[str] = Field(default=None, max_length=50)


class ContactResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    status: str
    subscription_plan: Optional[str] = None
    subscription_billing_cycle: Optional[str] = None
    subscription_status: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ContactListResponse(BaseModel):
    items: List[ContactResponse]
    total: int


class ContactImportResult(BaseModel):
    total_rows: int
    imported: int
    skipped: int
    invalid: int
    duplicates: int
    errors: List[str] = []