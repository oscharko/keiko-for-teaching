"""Configuration settings for the User service."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Redis Cache
    redis_url: str = "redis://localhost:6379"

    # Server
    host: str = "0.0.0.0"
    port: int = 8005
    debug: bool = False

    model_config = {"env_prefix": "", "case_sensitive": False}


settings = Settings()

