from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.user import User
from app.schemas.template import (
    TemplateCreate,
    TemplateUpdate,
    TemplateResponse,
    TemplateListResponse,
)
from app.services.template_service import (
    create_template,
    get_templates,
    get_template,
    update_template,
    delete_template,
)
from app.core.exceptions import NotFoundException
from app.dependencies.auth import get_current_user


router = APIRouter(prefix="/templates", tags=["Templates"])


@router.get("", response_model=TemplateListResponse)
def list_templates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items, total = get_templates(db, current_user.id)
    return TemplateListResponse(
        items=[TemplateResponse.model_validate(t) for t in items],
        total=total,
    )


@router.post(
    "",
    response_model=TemplateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_new_template(
    payload: TemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    template = create_template(db, current_user.id, payload)
    return TemplateResponse.model_validate(template)


@router.get("/{template_id}", response_model=TemplateResponse)
def retrieve_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    template = get_template(db, current_user.id, template_id)
    if not template:
        raise NotFoundException("Template not found.")
    return TemplateResponse.model_validate(template)


@router.put("/{template_id}", response_model=TemplateResponse)
def update_existing_template(
    template_id: int,
    payload: TemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    template = update_template(db, current_user.id, template_id, payload)
    if not template:
        raise NotFoundException("Template not found.")
    return TemplateResponse.model_validate(template)


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    success = delete_template(db, current_user.id, template_id)
    if not success:
        raise NotFoundException("Template not found.")
    return None
