from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Autonomous Ads OS"
    app_env: str = "development"
    log_level: str = "INFO"

    dry_run: bool = True

    app_secret_key: str
    token_encryption_key: str

    database_url: str
    redis_url: str

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3.5:4b"
    llm_timeout_seconds: float = 300

    whop_api_key: str | None = None
    whop_app_id: str | None = None
    whop_product_id: str | None = None
    whop_webhook_secret: str | None = None

    google_ads_developer_token: str | None = None
    google_ads_manager_customer_id: str | None = None
    google_client_id: str | None = None
    google_client_secret: str | None = None
    google_redirect_uri: str

    meta_app_id: str | None = None
    meta_app_secret: str | None = None
    meta_redirect_uri: str
    meta_graph_api_version: str = "v26.0"

    tiktok_app_id: str | None = None
    tiktok_app_secret: str | None = None
    tiktok_redirect_uri: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
