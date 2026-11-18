from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Vaultly"
    database_url: str = "postgresql+psycopg://vaultly:vaultly@localhost:5432/vaultly"
    redis_url: str = "redis://localhost:6379/0"
    cors_origins: str = "http://localhost:3000"


settings = Settings()
