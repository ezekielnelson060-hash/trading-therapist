from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    APP_NAME: str = "Trading Therapist"
    APP_VERSION: str = "0.2.0"
    DEBUG: bool = True

    DATABASE_URL: str = "sqlite+aiosqlite:///:memory:"

    SECRET_KEY: str = "change-me-in-production-use-openssl-rand-hex-32"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    ALGORITHM: str = "HS256"

    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None

    DEFAULT_SYNC_INTERVAL_MINUTES: int = 15

    RESEND_API_KEY: Optional[str] = None
    ALERT_FROM_EMAIL: str = "alerts@tiltshield.xyz"
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None
    STRIPE_PRICE_TRADER: Optional[str] = None
    STRIPE_PRICE_PRO: Optional[str] = None
    APP_URL: str = "https://trading-therapist.vercel.app"
    API_URL: str = "https://trading-therapist-production.up.railway.app"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
