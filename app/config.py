from functools import lru_cache
from zoneinfo import ZoneInfo

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

TIMEZONE = ZoneInfo("Europe/Istanbul")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"
    log_level: str = "INFO"
    database_url: str = "sqlite:///./demobank.db"
    elevenlabs_api_key: SecretStr | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
