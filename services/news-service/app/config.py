from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    host: str = "0.0.0.0"
    port: int = 8003  # Running on port 8003 to avoid conflict
    debug: bool = False
    
    cors_origins: list[str] = ["*"]

    model_config = {"env_prefix": "NEWS_", "case_sensitive": False}

    # Azure Cosmos DB
    azure_cosmos_connection_string: str | None = None
    azure_news_database: str = "news-db"
    azure_news_container: str = "news-articles"
    azure_preferences_container: str = "user-preferences"

    # Azure OpenAI (for summarization)
    azure_openai_endpoint: str | None = None
    azure_openai_api_key: str | None = None
    azure_openai_chatgpt_deployment: str = "gpt-4"
    
    # Auth
    azure_tenant_id: str | None = None
    azure_client_id: str | None = None
    azure_client_secret: str | None = None

settings = Settings()
