"""Configuration settings for the Gateway BFF service."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Service URLs
    chat_service_url: str = "http://localhost:8001"
    search_service_url: str = "http://localhost:8002"
    document_service_url: str = "http://localhost:8003"
    auth_service_url: str = "http://localhost:8004"
    user_service_url: str = "http://localhost:8005"
    ingestion_service_url: str = "http://localhost:50051"

    # Redis
    redis_url: str = "redis://localhost:6379"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]

    # Rate limiting
    rate_limit_requests_per_minute: int = 60

    # Authentication
    enable_auth: bool = True  # Set to False to disable authentication

    model_config = {"env_prefix": "", "case_sensitive": False}


settings = Settings()

