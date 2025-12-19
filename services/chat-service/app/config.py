"""Configuration settings for the Chat service."""

import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Microsoft Foundry Configuration
    foundry_endpoint: str = ""  # e.g., https://aiproj-keiko-dev.westeurope.api.azureml.ms
    # Optional: Only for local dev, use Managed Identity in prod
    foundry_api_key: str = ""
    foundry_project_name: str = "aiproj-keiko-dev"
    # Options: gpt-4o, claude-sonnet-4.5, deepseek-v3
    foundry_default_model: str = "gpt-4o"

    # Azure Subscription & Resource Group (for Foundry Agent Service)
    azure_subscription_id: str = ""
    azure_resource_group: str = "rg-keiko-dev"

    # Azure Managed Identity
    azure_client_id: str = ""  # User-assigned managed identity client ID (optional)

    # Foundry Features
    enable_foundry_iq: bool = True  # Enable Foundry IQ for agentic RAG
    enable_model_router: bool = False  # Enable automatic model selection
    foundry_iq_retrieval_effort: str = "medium"  # low, medium, high

    # Legacy Azure OpenAI (for backward compatibility during migration)
    azure_openai_endpoint: str = ""
    azure_openai_api_key: str = ""
    azure_openai_deployment: str = "gpt-4o"
    azure_openai_api_version: str = "2024-08-01-preview"
    # Set to True to use old Azure OpenAI instead of Foundry
    use_legacy_openai: bool = False

    # Search Service
    search_service_url: str = "http://localhost:8002"

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
    port: int = 8001
    debug: bool = False

    # Chat defaults
    default_temperature: float = 0.7
    default_max_tokens: int = 4096
    default_top_k: int = 5

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

