from fastapi import APIRouter

from app.schemas.recommendation import RecommendationConfig
from app.services.recommendation_config_service import load_recommendation_config, save_recommendation_config

router = APIRouter(prefix="/system-settings", tags=["系统设置"])


@router.get("/recommendation-rules", response_model=RecommendationConfig, summary="获取推荐规则配置")
def get_recommendation_rules() -> RecommendationConfig:
    return load_recommendation_config()


@router.put("/recommendation-rules", response_model=RecommendationConfig, summary="保存推荐规则配置")
def update_recommendation_rules(payload: RecommendationConfig) -> RecommendationConfig:
    return save_recommendation_config(payload)
