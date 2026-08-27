from typing import List, Tuple, Optional
from sqlalchemy.orm import Session

from app.models.template import EmailTemplate
from app.schemas.template import TemplateCreate, TemplateUpdate


def create_template(db: Session, user_id: int, data: TemplateCreate) -> EmailTemplate:
    template = EmailTemplate(
        user_id=user_id,
        name=data.name.strip(),
        subject=data.subject.strip(),
        html_body=data.html_body,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


def get_templates(db: Session, user_id: int) -> Tuple[List[EmailTemplate], int]:
    query = db.query(EmailTemplate).filter(EmailTemplate.user_id == user_id)
    total = query.count()
    items = query.order_by(EmailTemplate.id.desc()).all()
    return items, total


def get_template(db: Session, user_id: int, template_id: int) -> Optional[EmailTemplate]:
    return (
        db.query(EmailTemplate)
        .filter(EmailTemplate.user_id == user_id, EmailTemplate.id == template_id)
        .first()
    )


def update_template(
    db: Session, user_id: int, template_id: int, data: TemplateUpdate
) -> Optional[EmailTemplate]:
    template = get_template(db, user_id, template_id)
    if not template:
        return None
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if isinstance(value, str):
            value = value.strip()
        setattr(template, key, value)
    db.commit()
    db.refresh(template)
    return template


def delete_template(db: Session, user_id: int, template_id: int) -> bool:
    template = get_template(db, user_id, template_id)
    if not template:
        return False
    db.delete(template)
    db.commit()
    return True
