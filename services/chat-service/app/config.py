"""Configuration settings for the Chat service."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Microsoft Foundry Configuration
    foundry_endpoint: str = ""  # e.g., https://aiproj-keiko-dev.westeurope.api.azureml.ms
    foundry_api_key: str = ""  # Optional: Only for local dev, use Managed Identity in production
    foundry_project_name: str = "aiproj-keiko-dev"
    foundry_default_model: str = "gpt-4o"  # Can be: gpt-4o, claude-sonnet-4.5, deepseek-v3, etc.

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
    use_legacy_openai: bool = False  # Set to True to use old Azure OpenAI instead of Foundry

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

