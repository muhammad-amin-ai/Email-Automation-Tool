from pydantic import BaseModel, Field
from typing import Optional, List


class GenerateEmailRequest(BaseModel):
    purpose: str = Field(min_length=1, max_length=2000)
    recipient: Optional[str] = Field(default=None, max_length=1000)
    tone: Optional[str] = Field(default="professional", max_length=100)
    additional_instructions: Optional[str] = Field(default=None, max_length=2000)


class GenerateEmailResponse(BaseModel):
    subject: str
    body: str


class GenerateSubjectRequest(BaseModel):
    email_body: str = Field(min_length=1)
    context: Optional[str] = Field(default=None, max_length=1000)


class GenerateSubjectResponse(BaseModel):
    subject: str
    alternatives: List[str] = []


class PersonalizeEmailRequest(BaseModel):
    template_subject: str
    template_body: str
    contact_first_name: Optional[str] = None
    contact_last_name: Optional[str] = None
    contact_email: Optional[str] = None
    extra_context: Optional[str] = None


class PersonalizeEmailResponse(BaseModel):
    subject: str
    body: str
