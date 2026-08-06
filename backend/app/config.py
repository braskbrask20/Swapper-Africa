import os
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    environment: str = "development"
    database_url: str = "sqlite:///./swapper.db"
    jwt_secret: str = "development-only-secret"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 30
    allowed_origins: str = "http://localhost:8000"
    admin_email: str = "admin@example.com"
    admin_password: str = "change-this-before-deployment"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    @property
    def cors_origins(self) -> list[str]:
        raw = self.allowed_origins.strip()
        if raw == "*":
            return ["*"]
        return [origin.strip() for origin in raw.split(",") if origin.strip()]

    @property
    def resolved_database_url(self) -> str:
        raw = self.database_url.strip()
        if raw.startswith("sqlite:///"):
            db_path = raw[len("sqlite:///"):]
            if os.path.isabs(db_path):
                return raw
            cwd_path = os.path.abspath(os.path.join(os.getcwd(), db_path))
            if os.path.exists(cwd_path):
                return f"sqlite:///{cwd_path}"
            config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", db_path))
            return f"sqlite:///{config_path}"
        return raw


@lru_cache
def get_settings() -> Settings:
    return Settings()
