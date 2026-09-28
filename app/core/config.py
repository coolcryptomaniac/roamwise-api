from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    app_name: str = "RoamWise Developer API"
    version: str = "1.0.0"
    description: str = "AI-powered travel intelligence API for businesses"
    debug: bool = False

    # Security — no insecure default. If SECRET_KEY isn't set via env/.env,
    # startup fails loudly instead of silently signing JWTs with a value
    # that's sitting in plaintext in this repo's own history.
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Database
    database_url: str = "sqlite:///./roamwise_api.db"

    # Redis
    redis_url: Optional[str] = "redis://localhost:6379/0"

    # Stripe
    stripe_secret_key: Optional[str] = None
    stripe_webhook_secret: Optional[str] = None

    # Rate Limits (requests per minute)
    rate_limit_basic: int = 20
    rate_limit_pro: int = 100
    rate_limit_enterprise: int = 500

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()
