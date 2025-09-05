from __future__ import annotations

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Настройки приложения, загружаемые из переменных окружения и .env файла.
    """

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    APP_NAME: str = "DocuCortex"
    LOG_LEVEL: str = "INFO"
    OPENAI_API_KEY: SecretStr


settings = Settings()
