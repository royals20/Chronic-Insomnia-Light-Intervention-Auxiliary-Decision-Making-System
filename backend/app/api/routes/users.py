from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import ResetPasswordRequest, UserCreate, UserRead, UserRole, UserUpdate
from app.services.user_service import create_user, list_users, reset_password, toggle_user_active, update_user

router = APIRouter(prefix="/users", tags=["用户管理"])


@router.get("", response_model=list[UserRead], summary="用户列表")
def get_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
) -> list[User]:
    return list_users(db)


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED, summary="创建用户")
def create_user_endpoint(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
) -> User:
    try:
        return create_user(db, payload, actor_name=current_user.username)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.put("/{user_id}", response_model=UserRead, summary="更新用户")
def update_user_endpoint(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    try:
        return update_user(
            db,
            user,
            payload,
            actor_name=current_user.username,
            current_user=current_user,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/{user_id}/reset-password", response_model=UserRead, summary="重置密码")
def reset_password_endpoint(
    user_id: int,
    payload: ResetPasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    return reset_password(db, user, payload, actor_name=current_user.username)


@router.post("/{user_id}/toggle-active", response_model=UserRead, summary="启用或停用用户")
def toggle_active_endpoint(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    try:
        return toggle_user_active(
            db,
            user,
            actor_name=current_user.username,
            current_user=current_user,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
