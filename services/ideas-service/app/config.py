from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    
    cors_origins: list[str] = ["*"]

    model_config = {"env_prefix": "IDEAS_", "case_sensitive": False}

    # Azure Cosmos DB
    azure_cosmos_connection_string: str | None = None
    azure_ideas_database: str = "ideas-db"
    azure_ideas_container: str = "ideas"
    azure_ideas_audit_container: str = "ideas-audit"

    # Azure AI Search
    azure_search_service: str | None = None
    azure_search_index: str = "ideas-index"
    azure_search_key: str | None = None

    # Azure OpenAI
    azure_openai_endpoint: str | None = None
    azure_openai_api_key: str | None = None
    azure_openai_chatgpt_deployment: str = "gpt-4"
    azure_openai_emb_deployment: str = "text-embedding-ada-002"
    
    # Auth
    azure_tenant_id: str | None = None
    azure_client_id: str | None = None
    azure_client_secret: str | None = None

settings = Settings()
