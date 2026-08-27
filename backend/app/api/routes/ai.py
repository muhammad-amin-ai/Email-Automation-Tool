from fastapi import APIRouter, Depends

from app.models.user import User
from app.schemas.ai import (
    GenerateEmailRequest,
    GenerateEmailResponse,
    GenerateSubjectRequest,
    GenerateSubjectResponse,
    PersonalizeEmailRequest,
    PersonalizeEmailResponse,
)
from app.services.ollama_service import ollama_service
from app.dependencies.auth import get_current_user


router = APIRouter(prefix="/ai", tags=["AI"])


@router.post("/generate-email", response_model=GenerateEmailResponse)
async def generate_email(
    payload: GenerateEmailRequest,
    current_user: User = Depends(get_current_user),
):
    result = await ollama_service.generate_email(
        purpose=payload.purpose,
        recipient=payload.recipient,
        tone=payload.tone or "professional",
        additional_instructions=payload.additional_instructions,
    )
    return GenerateEmailResponse(**result)


@router.post("/generate-subject", response_model=GenerateSubjectResponse)
async def generate_subject(
    payload: GenerateSubjectRequest,
    current_user: User = Depends(get_current_user),
):
    result = await ollama_service.generate_subject(
        email_body=payload.email_body,
        context=payload.context,
    )
    return GenerateSubjectResponse(**result)


@router.post("/personalize-email", response_model=PersonalizeEmailResponse)
async def personalize_email(
    payload: PersonalizeEmailRequest,
    current_user: User = Depends(get_current_user),
):
    result = await ollama_service.personalize_email(
        template_subject=payload.template_subject,
        template_body=payload.template_body,
        contact_first_name=payload.contact_first_name,
        contact_last_name=payload.contact_last_name,
        contact_email=payload.contact_email,
        extra_context=payload.extra_context,
    )
    return PersonalizeEmailResponse(**result)
