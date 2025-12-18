"""Configuration settings for the Document service."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Azure Blob Storage
    azure_storage_account_name: str = ""
    azure_storage_container_name: str = "documents"

    # Azure Managed Identity
    azure_client_id: str = ""  # User-assigned managed identity client ID (optional)

    # Ingestion Service
    ingestion_service_url: str = "http://localhost:50051"

    # Search Service
    search_service_url: str = "http://localhost:8002"

    # Redis Cache
    redis_url: str = "redis://localhost:6379"

    # Server
    host: str = "0.0.0.0"
    port: int = 8003
    debug: bool = False

    # Upload limits
    max_file_size: int = 104857600  # 100MB in bytes
    allowed_extensions: list[str] = ["pdf", "docx", "txt", "md", "html"]

    model_config = {"env_prefix": "", "case_sensitive": False}


settings = Settings()

