from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Neuro Assistant API"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    debug: bool = False

    database_url: str = "postgresql+asyncpg://neuro_user:YourStrongPassword123!@localhost/neuro_assistant"
    ollama_url: str = "http://localhost:11434/api/generate"
    model_name: str = "DistilQwen3-1.7B-uncensored:latest"
    ollama_timeout_seconds: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()