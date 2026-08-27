import csv
import io
import re
from typing import List, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.contact import Contact
from app.schemas.contact import ContactCreate, ContactUpdate, ContactImportResult
from app.core.exceptions import ConflictException


EMAIL_REGEX = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def validate_email(email: str) -> bool:
    if not email:
        return False
    return bool(EMAIL_REGEX.match(email.strip()))


def create_contact(db: Session, user_id: int, data: ContactCreate) -> Contact:
    existing = (
        db.query(Contact)
        .filter(Contact.user_id == user_id, Contact.email == _normalize_email(data.email))
        .first()
    )
    if existing:
        raise ConflictException("Contact with this email already exists.")

    contact = Contact(
        user_id=user_id,
        email=_normalize_email(data.email),
        first_name=(data.first_name or "").strip() or None,
        last_name=(data.last_name or "").strip() or None,
        status=data.status or "active",
        subscription_plan=data.subscription_plan,
        subscription_billing_cycle=data.subscription_billing_cycle,
        subscription_status=data.subscription_status,
    )
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


def get_contacts(
    db: Session,
    user_id: int,
    search: Optional[str] = None,
    status_filter: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> Tuple[List[Contact], int]:
    query = db.query(Contact).filter(Contact.user_id == user_id)

    if search:
        term = f"%{search.lower()}%"
        query = query.filter(
            or_(
                Contact.email.ilike(term),
                Contact.first_name.ilike(term),
                Contact.last_name.ilike(term),
            )
        )

    if status_filter:
        query = query.filter(Contact.status == status_filter)

    total = query.count()
    items = query.order_by(Contact.id.desc()).offset(skip).limit(limit).all()
    return items, total


def get_contact(db: Session, user_id: int, contact_id: int) -> Optional[Contact]:
    return (
        db.query(Contact)
        .filter(Contact.user_id == user_id, Contact.id == contact_id)
        .first()
    )


def update_contact(
    db: Session, user_id: int, contact_id: int, data: ContactUpdate
) -> Optional[Contact]:
    contact = get_contact(db, user_id, contact_id)
    if not contact:
        return None

    update_data = data.model_dump(exclude_unset=True)

    if "email" in update_data and update_data["email"]:
        new_email = _normalize_email(update_data["email"])
        if new_email != contact.email:
            existing = (
                db.query(Contact)
                .filter(
                    Contact.user_id == user_id,
                    Contact.email == new_email,
                    Contact.id != contact_id,
                )
                .first()
            )
            if existing:
                raise ConflictException("Another contact with this email already exists.")
            contact.email = new_email

    if "first_name" in update_data:
        contact.first_name = (update_data["first_name"] or "").strip() or None
    if "last_name" in update_data:
        contact.last_name = (update_data["last_name"] or "").strip() or None
    if "status" in update_data and update_data["status"]:
        contact.status = update_data["status"]

    db.commit()
    db.refresh(contact)
    return contact


def delete_contact(db: Session, user_id: int, contact_id: int) -> bool:
    contact = get_contact(db, user_id, contact_id)
    if not contact:
        return False
    db.delete(contact)
    db.commit()
    return True


def import_contacts_from_csv(db: Session, user_id: int, content: str) -> ContactImportResult:
    result = ContactImportResult(
        total_rows=0, imported=0, skipped=0, invalid=0, duplicates=0, errors=[]
    )

    if not content or not content.strip():
        return result

    try:
        reader = csv.DictReader(io.StringIO(content))
    except Exception as e:
        result.errors.append(f"Could not parse CSV: {e}")
        return result

    if not reader.fieldnames:
        result.errors.append("CSV file is empty or missing headers.")
        return result

    field_map = {}
    for f in reader.fieldnames:
        if not f:
            continue
        key = f.strip().lower().replace(" ", "_")
        field_map[key] = f

    if "email" not in field_map:
        result.errors.append("CSV must include an 'email' column.")
        return result

    email_col = field_map["email"]
    first_name_col = field_map.get("first_name") or field_map.get("firstname") or field_map.get("name")
    last_name_col = field_map.get("last_name") or field_map.get("lastname")

    existing_emails = {
        c.email
        for c in db.query(Contact).filter(Contact.user_id == user_id).all()
    }

    to_create = []
    seen_in_batch = set()

    for row_num, row in enumerate(reader, start=2):
        result.total_rows += 1
        try:
            raw_email = (row.get(email_col) or "").strip()
            if not raw_email:
                result.invalid += 1
                if len(result.errors) < 10:
                    result.errors.append(f"Row {row_num}: missing email.")
                continue

            email = _normalize_email(raw_email)
            if not validate_email(email):
                result.invalid += 1
                if len(result.errors) < 10:
                    result.errors.append(f"Row {row_num}: invalid email '{raw_email}'.")
                continue

            if email in existing_emails or email in seen_in_batch:
                result.duplicates += 1
                continue

            first_name = None
            last_name = None
            if first_name_col:
                first_name = (row.get(first_name_col) or "").strip() or None
            if last_name_col:
                last_name = (row.get(last_name_col) or "").strip() or None

            seen_in_batch.add(email)
            to_create.append(
                Contact(
                    user_id=user_id,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    status="active",
                )
            )
        except Exception as e:
            result.invalid += 1
            if len(result.errors) < 10:
                result.errors.append(f"Row {row_num}: {e}")

    if to_create:
        try:
            db.add_all(to_create)
            db.commit()
            result.imported = len(to_create)
        except Exception as e:
            db.rollback()
            result.errors.append(f"Database error during import: {e}")
            result.skipped = len(to_create)

    return result