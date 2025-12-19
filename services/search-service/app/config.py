"""Configuration settings for the Search service."""

import os
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
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str | None = None
    redis_url: str | None = None

    @property
    def redis_url_computed(self) -> str:
        """Construct Redis URL from components if not explicitly provided."""
        if self.redis_url:
            return self.redis_url

        # Use SSL for Azure Redis Cache (port 6380)
        if self.redis_port == 6380:
            auth_part = f":{self.redis_password}@" if self.redis_password else ""
            return f"rediss://{auth_part}{self.redis_host}:{self.redis_port}"

        auth_part = f":{self.redis_password}@" if self.redis_password else ""
        return f"redis://{auth_part}{self.redis_host}:{self.redis_port}"

    # Server
    host: str = "0.0.0.0"
    port: int = 8002
    debug: bool = False

    # Search defaults
    default_top_k: int = 5
    default_semantic_configuration: str = "default"
    cache_ttl: int = 3600  # 1 hour

    model_config = {"env_prefix": "", "case_sensitive": False}


# Create settings instance
settings = Settings()

# Override with uppercase environment variables (Azure Container Apps sets them as uppercase)
# This is necessary because Pydantic Settings doesn't automatically read uppercase env vars
if "REDIS_HOST" in os.environ:
    settings.redis_host = os.environ["REDIS_HOST"]
if "REDIS_PORT" in os.environ:
    settings.redis_port = int(os.environ["REDIS_PORT"])
if "REDIS_PASSWORD" in os.environ:
    settings.redis_password = os.environ["REDIS_PASSWORD"]
if "REDIS_URL" in os.environ:
    settings.redis_url = os.environ["REDIS_URL"]

