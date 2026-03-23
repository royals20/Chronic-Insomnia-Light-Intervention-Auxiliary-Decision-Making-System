from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User
from app.schemas.user import ResetPasswordRequest, UserCreate, UserRole, UserUpdate
from app.services.audit_service import add_audit_log


def list_users(db: Session) -> list[User]:
    return db.scalars(select(User).order_by(User.created_at.asc(), User.id.asc())).all()


def create_user(db: Session, payload: UserCreate, *, actor_name: str) -> User:
    existing = db.scalar(select(User).where(User.username == payload.username))
    if existing is not None:
        raise ValueError("用户名已存在")

    user = User(
        username=payload.username,
        full_name=payload.full_name,
        role=payload.role.value,
        is_active=payload.is_active,
        password_hash=hash_password(payload.password),
        password=None,
    )
    db.add(user)
    db.flush()
    add_audit_log(
        db,
        actor_name=actor_name,
        action_type="create_user",
        target_type="user",
        target_id=str(user.id),
        details={"username": user.username, "role": user.role},
        detail_text=f"创建用户 {user.username}",
    )
    db.commit()
    db.refresh(user)
    return user


def update_user(
    db: Session,
    user: User,
    payload: UserUpdate,
    *,
    actor_name: str,
    current_user: User,
) -> User:
    if payload.username and payload.username != user.username:
        existing = db.scalar(select(User).where(User.username == payload.username))
        if existing is not None and existing.id != user.id:
            raise ValueError("用户名已存在")
        user.username = payload.username

    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.role is not None:
        if current_user.id == user.id and payload.role != UserRole.ADMIN:
            raise ValueError("不能移除当前登录管理员的管理员角色")
        user.role = payload.role.value
    if payload.is_active is not None:
        if current_user.id == user.id and payload.is_active is False:
            raise ValueError("不能停用当前登录账号")
        user.is_active = payload.is_active

    add_audit_log(
        db,
        actor_name=actor_name,
        action_type="update_user",
        target_type="user",
        target_id=str(user.id),
        details={"username": user.username, "role": user.role, "is_active": user.is_active},
        detail_text=f"更新用户 {user.username}",
    )
    db.commit()
    db.refresh(user)
    return user


def reset_password(
    db: Session,
    user: User,
    payload: ResetPasswordRequest,
    *,
    actor_name: str,
) -> User:
    user.password_hash = hash_password(payload.new_password)
    user.password = None
    add_audit_log(
        db,
        actor_name=actor_name,
        action_type="reset_user_password",
        target_type="user",
        target_id=str(user.id),
        details={"username": user.username},
        detail_text=f"重置用户 {user.username} 的密码",
    )
    db.commit()
    db.refresh(user)
    return user


def toggle_user_active(
    db: Session,
    user: User,
    *,
    actor_name: str,
    current_user: User,
) -> User:
    if current_user.id == user.id and user.is_active:
        raise ValueError("不能停用当前登录账号")

    user.is_active = not user.is_active
    add_audit_log(
        db,
        actor_name=actor_name,
        action_type="toggle_user_active",
        target_type="user",
        target_id=str(user.id),
        details={"username": user.username, "is_active": user.is_active},
        detail_text=f"{'启用' if user.is_active else '停用'}用户 {user.username}",
    )
    db.commit()
    db.refresh(user)
    return user
