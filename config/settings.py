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
    jwt_remember_expires_minutes: int = Field(default=43200, alias="JWT_REMEMBER_EXPIRES_MINUTES")
    csrf_secret: str = Field(default="dev-csrf", alias="CSRF_SECRET")
    login_rate_limit_attempts: int = Field(default=5, alias="LOGIN_RATE_LIMIT_ATTEMPTS")
    login_rate_limit_window_minutes: int = Field(default=30, alias="LOGIN_RATE_LIMIT_WINDOW_MINUTES")
    mailing_send_window_start_hour: int = Field(default=8, alias="MAILING_SEND_WINDOW_START_HOUR")
    mailing_send_window_end_hour: int = Field(default=21, alias="MAILING_SEND_WINDOW_END_HOUR")
    mailing_min_audience: int = Field(default=3, alias="MAILING_MIN_AUDIENCE")
    mailing_min_interval_minutes: int = Field(default=60, alias="MAILING_MIN_INTERVAL_MINUTES")
    bot_token: str = Field(default="123456:TEST_TOKEN", alias="BOT_TOKEN")
    manager_username: str = Field(default="manager_username", alias="MANAGER_USERNAME")
    admin_default_username: str = Field(default="admin", alias="ADMIN_DEFAULT_USERNAME")
    admin_default_password: str = Field(default="change-me", alias="ADMIN_DEFAULT_PASSWORD")
    upload_dir: str = Field(default="./uploads", alias="UPLOAD_DIR")
    upload_base_url: str = Field(
        default="http://localhost:8000/uploads",
        alias="UPLOAD_BASE_URL",
        description="Public URL for uploads when using local storage (bot sends media by this URL)",
    )
    # Если задан, бот подменяет localhost в URL медиа на этот адрес (чтобы Telegram мог скачать файл)
    upload_public_base_url: str | None = Field(
        default=None,
        alias="UPLOAD_PUBLIC_BASE_URL",
        description="Public URL to replace localhost in media URLs (required for bot in Docker; e.g. http://YOUR_IP:8000/uploads or http://YOUR_IP:9000/uploads for MinIO)",
    )
    max_upload_mb: int = Field(default=5, alias="MAX_UPLOAD_MB")
    # S3 (optional). If set, files are uploaded to S3 instead of local disk.
    s3_bucket: str | None = Field(default=None, alias="S3_BUCKET")
    s3_region: str | None = Field(default=None, alias="S3_REGION")
    s3_access_key_id: str | None = Field(default=None, alias="S3_ACCESS_KEY_ID")
    s3_secret_access_key: str | None = Field(default=None, alias="S3_SECRET_ACCESS_KEY")
    s3_endpoint_url: str | None = Field(
        default=None,
        alias="S3_ENDPOINT_URL",
        description="Custom endpoint, e.g. for MinIO: http://minio:9000",
    )
    s3_public_base_url: str | None = Field(
        default=None,
        alias="S3_PUBLIC_BASE_URL",
        description="Public base URL for S3 objects (e.g. https://cdn.example.com or https://bucket.s3.region.amazonaws.com)",
    )

    @property
    def use_s3(self) -> bool:
        return bool(self.s3_bucket and self.s3_access_key_id and self.s3_secret_access_key)
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
