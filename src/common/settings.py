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

    # --- Langfuse (Phase 10) — Cloud (free tier), không self-host; xem
    # CHECKLIST Phase 10 cho lý do quyết định (máy dev hạn chế tài nguyên,
    # tránh thêm 4 container nặng langfuse-web/worker+clickhouse+minio).
    langfuse_host: str = "https://cloud.langfuse.com"
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""

    # --- Optimization/Routing (Phase 11) — mặc định TẮT, xem
    # config/optimization.yaml cho lý do (đo qua O1-O8 trước khi đổi mặc
    # định production, cùng nguyên tắc reranker/top_k_after).
    semantic_cache_enabled: bool = False
    context_compression_enabled: bool = False
    dynamic_top_k_enabled: bool = False

    @property
    def postgres_dsn(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
