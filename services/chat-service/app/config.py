"""Configuration settings for the Chat service."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Azure OpenAI
    azure_openai_endpoint: str = ""
    azure_openai_api_key: str = ""  # Optional: Only for local dev, use Managed Identity in production
    azure_openai_deployment: str = "gpt-4o"
    azure_openai_api_version: str = "2024-08-01-preview"

    # Azure Managed Identity
    azure_client_id: str = ""  # User-assigned managed identity client ID (optional)

    # Search Service
    search_service_url: str = "http://localhost:8002"

    # Redis Cache
    redis_url: str = "redis://localhost:6379"

    # Server
    host: str = "0.0.0.0"
    port: int = 8001
    debug: bool = False

    # Chat defaults
    default_temperature: float = 0.7
    default_max_tokens: int = 4096
    default_top_k: int = 5

    model_config = {"env_prefix": "", "case_sensitive": False}


settings = Settings()

