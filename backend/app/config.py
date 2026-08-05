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
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
