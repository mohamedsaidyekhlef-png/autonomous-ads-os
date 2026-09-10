from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Autonomous Ads OS"
    app_env: str = "development"
    log_level: str = "INFO"
    dry_run: Literal[True] = True

    # Secrets are injected by the deployment environment. Local .env files are
    # intentionally never loaded by the application.
    app_secret_key: str = "development-only-change-me"
    token_encryption_key: str = "MDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDA="
    database_url: str = "sqlite:///./autonomous_ads.db"
    redis_url: str = "redis://localhost:6379/0"

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3.5:4b"
    llm_provider: str = "ollama"
    llm_base_url: str | None = None
    llm_api_key: str | None = None
    llm_model: str | None = None
    llm_timeout_seconds: float = 300
    dashboard_url: str = "http://localhost:3000"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    whop_api_key: str | None = None
    whop_app_id: str | None = None
    whop_product_id: str | None = None
    whop_webhook_secret: str | None = None
    whop_required_product_id: str | None = None

    google_ads_developer_token: str | None = None
    google_ads_manager_customer_id: str | None = None
    google_client_id: str | None = None
    google_client_secret: str | None = None
    google_redirect_uri: str = "http://localhost:8080/oauth/google/callback"
    meta_app_id: str | None = None
    meta_app_secret: str | None = None
    meta_redirect_uri: str = "http://localhost:8080/oauth/meta/callback"
    meta_graph_api_version: str = "v26.0"
    tiktok_app_id: str | None = None
    tiktok_app_secret: str | None = None
    tiktok_redirect_uri: str = "http://localhost:8080/oauth/tiktok/callback"

    model_config = SettingsConfigDict(case_sensitive=False, extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
