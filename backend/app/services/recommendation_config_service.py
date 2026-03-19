import json

from app.core.config import get_settings
from app.schemas.recommendation import RecommendationConfig

settings = get_settings()


def load_recommendation_config() -> RecommendationConfig:
    path = settings.recommendation_rule_path
    payload = json.loads(path.read_text(encoding="utf-8"))
    return RecommendationConfig.model_validate(payload)


def save_recommendation_config(payload: RecommendationConfig) -> RecommendationConfig:
    path = settings.recommendation_rule_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        payload.model_dump_json(indent=2),
        encoding="utf-8",
    )
    return load_recommendation_config()
