from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime
from typing import Optional


class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class ProfileUpdateRequest(BaseModel):
    sender_name: Optional[str] = Field(default=None, max_length=255)
    sender_title: Optional[str] = Field(default=None, max_length=255)
    company_name: Optional[str] = Field(default=None, max_length=255)
    sender_phone: Optional[str] = Field(default=None, max_length=50)
    website_url: Optional[str] = Field(default=None, max_length=255)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    is_active: bool
    sender_name: Optional[str] = None
    sender_title: Optional[str] = None
    company_name: Optional[str] = None
    sender_phone: Optional[str] = None
    website_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse