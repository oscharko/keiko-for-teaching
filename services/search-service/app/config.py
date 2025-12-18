"""Configuration settings for the Search service."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Azure AI Search
    azure_search_endpoint: str = ""
    azure_search_index_name: str = "keiko-documents"
    azure_search_api_version: str = "2024-07-01"

    # Azure Managed Identity
    azure_client_id: str = ""  # User-assigned managed identity client ID (optional)

    # Redis Cache
    redis_url: str = "redis://localhost:6379"

    # Server
    host: str = "0.0.0.0"
    port: int = 8002
    debug: bool = False

    # Search defaults
    default_top_k: int = 5
    default_semantic_configuration: str = "default"
    cache_ttl: int = 3600  # 1 hour

    model_config = {"env_prefix": "", "case_sensitive": False}


settings = Settings()

