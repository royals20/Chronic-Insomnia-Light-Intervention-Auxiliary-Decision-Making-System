from fastapi import APIRouter, Depends

from app.api.deps import require_roles
from app.models.user import User
from app.schemas.recommendation import RecommendationConfig
from app.schemas.user import UserRole
from app.services.recommendation_config_service import load_recommendation_config, save_recommendation_config

router = APIRouter(prefix="/system-settings", tags=["系统设置"])


@router.get("/recommendation-rules", response_model=RecommendationConfig, summary="获取推荐规则配置")
def get_recommendation_rules(
    _: User = Depends(require_roles(UserRole.ADMIN)),
) -> RecommendationConfig:
    return load_recommendation_config()


@router.put("/recommendation-rules", response_model=RecommendationConfig, summary="保存推荐规则配置")
def update_recommendation_rules(
    payload: RecommendationConfig,
    _: User = Depends(require_roles(UserRole.ADMIN)),
) -> RecommendationConfig:
    return save_recommendation_config(payload)
