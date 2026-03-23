from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import AuthMeResponse, LoginRequest, LoginResponse, UserInfo
from app.services.auth_service import authenticate_user, build_access_token, mark_user_login

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/login", response_model=LoginResponse, summary="账号登录")
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    user = authenticate_user(db, payload.username, payload.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="当前账号已停用",
        )

    access_token, expires_at = build_access_token(user)
    mark_user_login(db, user)
    return LoginResponse(
        access_token=access_token,
        expires_in=max(int((expires_at - datetime.now(UTC)).total_seconds()), 0),
        user=UserInfo.model_validate(user),
        message="登录成功",
    )


@router.get("/me", response_model=AuthMeResponse, summary="获取当前登录用户")
def get_auth_me(current_user: User = Depends(get_current_user)) -> AuthMeResponse:
    return AuthMeResponse(
        user=UserInfo.model_validate(current_user),
        checked_at=datetime.utcnow(),
    )
