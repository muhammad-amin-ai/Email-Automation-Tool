from datetime import timedelta
from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.user import User
from app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenResponse,
    UserResponse,
    ProfileUpdateRequest,
)
from app.core.security import hash_password, verify_password, create_access_token
from app.core.exceptions import ConflictException, UnauthorizedException
from app.core.config import settings
from app.dependencies.auth import get_current_user


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(payload: UserRegisterRequest, db: Session = Depends(get_db)):
    email_normalized = payload.email.lower()
    existing = db.query(User).filter(User.email == email_normalized).first()
    if existing:
        raise ConflictException("An account with this email already exists.")

    user = User(
        email=email_normalized,
        password_hash=hash_password(payload.password),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(
        subject=user.id,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise UnauthorizedException("Invalid email or password.")
    if not user.is_active:
        raise UnauthorizedException("Account is inactive.")

    token = create_access_token(
        subject=user.id,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.post(
    "/login/form",
    response_model=TokenResponse,
    include_in_schema=False,
)
def login_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == form_data.username.lower()).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise UnauthorizedException("Invalid email or password.")
    if not user.is_active:
        raise UnauthorizedException("Account is inactive.")

    token = create_access_token(
        subject=user.id,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)


@router.patch("/me", response_model=UserResponse)
def update_profile(
    payload: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update the sender/business profile used to personalize outgoing
    emails (name, title, company, phone). Never put this info directly in
    email templates — it's pulled from here via {{sender_name}}, etc."""
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(current_user, key, value.strip() if isinstance(value, str) else value)
    db.commit()
    db.refresh(current_user)
    return UserResponse.model_validate(current_user)