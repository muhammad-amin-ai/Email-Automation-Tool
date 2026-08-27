from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.user import User
from app.core.security import decode_access_token
from app.core.exceptions import UnauthorizedException


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login/form", auto_error=False)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    if not token:
        raise UnauthorizedException("Authentication required.")

    user_id = decode_access_token(token)
    if not user_id:
        raise UnauthorizedException("Invalid or expired token.")

    try:
        user_id_int = int(user_id)
    except (ValueError, TypeError):
        raise UnauthorizedException("Invalid token payload.")

    user = db.query(User).filter(User.id == user_id_int).first()
    if not user:
        raise UnauthorizedException("User not found.")

    if not user.is_active:
        raise UnauthorizedException("User account is inactive.")

    return user