from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = Field(default="dev", alias="APP_ENV")
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    database_url: str = Field(default="sqlite+aiosqlite:///./local.db", alias="DATABASE_URL")
    jwt_secret: str = Field(default="dev-secret", alias="JWT_SECRET")
    jwt_expires_minutes: int = Field(default=480, alias="JWT_EXPIRES_MINUTES")
    csrf_secret: str = Field(default="dev-csrf", alias="CSRF_SECRET")
    login_rate_limit_attempts: int = Field(default=5, alias="LOGIN_RATE_LIMIT_ATTEMPTS")
    login_rate_limit_window_minutes: int = Field(default=10, alias="LOGIN_RATE_LIMIT_WINDOW_MINUTES")
    bot_token: str = Field(default="123456:TEST_TOKEN", alias="BOT_TOKEN")
    manager_username: str = Field(default="manager_username", alias="MANAGER_USERNAME")
    admin_default_username: str = Field(default="admin", alias="ADMIN_DEFAULT_USERNAME")
    admin_default_password: str = Field(default="change-me", alias="ADMIN_DEFAULT_PASSWORD")
    upload_dir: str = Field(default="./uploads", alias="UPLOAD_DIR")
    max_upload_mb: int = Field(default=5, alias="MAX_UPLOAD_MB")
    backup_dir: str = Field(default="./backups", alias="BACKUP_DIR")
    timezone: str = Field(default="Europe/Moscow", alias="TIMEZONE")
    allowed_origins: str = Field(default="http://localhost:5173", alias="ALLOWED_ORIGINS")

    @property
    def cors_origins(self) -> List[str]:
        origins = [item.strip() for item in self.allowed_origins.split(",") if item.strip()]
        if self.app_env.lower() == "prod":
            return [item for item in origins if item.startswith("https://")]
        return origins


@lru_cache
def get_settings() -> Settings:
    return Settings()
