from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "慢性失眠光干预科研辅助决策系统"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./app.db"
    demo_username: str = "research_demo"
    demo_password: str = "Demo@123456"
    demo_full_name: str = "科研演示账号"
    backend_cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    recommendation_rule_config_path: str = "app/config_data/recommendation_rules.json"
    model_artifact_dir: str = "app/model_artifacts"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="APP_",
        case_sensitive=False,
    )

    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.backend_cors_origins.split(",")
            if origin.strip()
        ]

    @property
    def recommendation_rule_path(self) -> Path:
        path = Path(self.recommendation_rule_config_path)
        if path.is_absolute():
            return path
        return Path(__file__).resolve().parents[2] / path

    @property
    def model_artifact_path(self) -> Path:
        path = Path(self.model_artifact_dir)
        if path.is_absolute():
            return path
        return Path(__file__).resolve().parents[2] / path


@lru_cache
def get_settings() -> Settings:
    return Settings()
