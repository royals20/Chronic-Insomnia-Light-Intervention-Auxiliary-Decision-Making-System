from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    user = db.scalar(select(User).where(User.username == username))
    if user is None or user.password != password:
        return None
    return user


def build_demo_token(username: str) -> str:
    return f"demo-token-{username}"
