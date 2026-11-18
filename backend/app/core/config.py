from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Vaultly"
    environment: str = "development"
    secret_key: str = "vaultly-super-secret-jwt-key-for-development-change-in-prod"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 30

    database_url: str = "sqlite:///./vaultly.db"
    redis_url: str = "redis://localhost:6379/0"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    upload_dir: str = str(Path(__file__).resolve().parent.parent.parent / "uploads")
    max_upload_size_bytes: int = 15 * 1024 * 1024  # 15 MB
    tesseract_cmd: str = "tesseract"


settings = Settings()
