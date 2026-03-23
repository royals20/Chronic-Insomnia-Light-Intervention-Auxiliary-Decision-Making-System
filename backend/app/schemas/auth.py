from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.user import UserRole


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=64, description="用户名")
    password: str = Field(..., min_length=6, max_length=128, description="密码")


class UserInfo(BaseModel):
    id: int
    username: str
    full_name: str
    role: UserRole
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserInfo
    message: str


class AuthMeResponse(BaseModel):
    user: UserInfo
    checked_at: datetime
