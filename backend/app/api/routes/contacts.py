from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, Query, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.user import User
from app.schemas.contact import (
    ContactCreate,
    ContactUpdate,
    ContactResponse,
    ContactListResponse,
    ContactImportResult,
)
from app.services.contact_service import (
    create_contact,
    get_contacts,
    get_contact,
    update_contact,
    delete_contact,
    import_contacts_from_csv,
)
from app.core.exceptions import BadRequestException, NotFoundException
from app.dependencies.auth import get_current_user


router = APIRouter(prefix="/contacts", tags=["Contacts"])


@router.get("", response_model=ContactListResponse)
def list_contacts(
    search: Optional[str] = Query(default=None, max_length=255),
    status_filter: Optional[str] = Query(default=None, alias="status", max_length=50),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items, total = get_contacts(
        db, current_user.id, search, status_filter, skip, limit
    )
    return ContactListResponse(
        items=[ContactResponse.model_validate(c) for c in items],
        total=total,
    )


@router.post(
    "",
    response_model=ContactResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_new_contact(
    payload: ContactCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    contact = create_contact(db, current_user.id, payload)
    return ContactResponse.model_validate(contact)


@router.get("/{contact_id}", response_model=ContactResponse)
def retrieve_contact(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    contact = get_contact(db, current_user.id, contact_id)
    if not contact:
        raise NotFoundException("Contact not found.")
    return ContactResponse.model_validate(contact)


@router.put("/{contact_id}", response_model=ContactResponse)
def update_existing_contact(
    contact_id: int,
    payload: ContactUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    contact = update_contact(db, current_user.id, contact_id, payload)
    if not contact:
        raise NotFoundException("Contact not found.")
    return ContactResponse.model_validate(contact)


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_contact(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    success = delete_contact(db, current_user.id, contact_id)
    if not success:
        raise NotFoundException("Contact not found.")
    return None


@router.post("/import", response_model=ContactImportResult)
async def import_contacts(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise BadRequestException("Please upload a CSV file.")

    content_bytes = await file.read()
    try:
        content = content_bytes.decode("utf-8")
    except UnicodeDecodeError:
        try:
            content = content_bytes.decode("latin-1")
        except Exception:
            raise BadRequestException("Could not decode CSV file. Please use UTF-8.")

    result = import_contacts_from_csv(db, current_user.id, content)
    return result
