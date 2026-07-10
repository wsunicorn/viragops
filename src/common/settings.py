"""Application settings loaded from environment / .env file.

Single source of runtime configuration. No provider/model values here —
those live in config/*.yaml and are loaded via config_loader.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

APP_VERSION = "0.1.0"
APP_NAME = "viragops-api"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- App ---
    app_env: str = "local"
    app_port: int = 8000
    log_level: str = "INFO"

    # --- PostgreSQL ---
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "llmops"
    postgres_user: str = "admin"
    postgres_password: str = ""

    # --- Qdrant ---
    qdrant_url: str = "http://localhost:6333"

    # --- Valkey/Redis ---
    valkey_url: str = "redis://localhost:6379/0"

    # --- LiteLLM gateway ---
    litellm_base_url: str = "http://localhost:4000"
    litellm_master_key: str = ""

    # --- Langfuse ---
    langfuse_host: str = "http://localhost:3000"
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""

    @property
    def postgres_dsn(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
