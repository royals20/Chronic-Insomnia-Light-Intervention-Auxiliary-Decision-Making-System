from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import build_expiration, decode_jwt, encode_jwt, verify_password
from app.models.user import User

settings = get_settings()


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    user = db.scalar(select(User).where(User.username == username))
    if user is None:
        return None

    password_matches = verify_password(password, user.password_hash)
    if not password_matches and user.password:
        password_matches = user.password == password

    if not password_matches:
        return None
    return user


def build_access_token(user: User) -> tuple[str, datetime]:
    expires_at = build_expiration(settings.jwt_access_token_expire_minutes)
    payload = {
        "sub": str(user.id),
        "username": user.username,
        "role": user.role,
        "exp": int(expires_at.timestamp()),
        "iat": int(datetime.now(UTC).timestamp()),
    }
    token = encode_jwt(payload, settings.jwt_secret_key, settings.jwt_algorithm)
    return token, expires_at


def decode_access_token(token: str) -> dict:
    return decode_jwt(token, settings.jwt_secret_key, settings.jwt_algorithm)


def mark_user_login(db: Session, user: User) -> None:
    user.last_login_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
