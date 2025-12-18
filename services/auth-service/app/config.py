"""Configuration settings for the Auth service."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Azure AD B2C
    azure_ad_b2c_tenant_name: str = ""
    azure_ad_b2c_client_id: str = ""
    azure_ad_b2c_client_secret: str = ""
    azure_ad_b2c_policy_name: str = "B2C_1_signupsignin"

    # JWT
    jwt_secret_key: str = ""  # Secret key for signing JWT tokens
    jwt_algorithm: str = "RS256"
    jwt_expiration_minutes: int = 60

    # Redis Cache
    redis_url: str = "redis://localhost:6379"

    # Server
    host: str = "0.0.0.0"
    port: int = 8004
    debug: bool = False

    model_config = {"env_prefix": "", "case_sensitive": False}


settings = Settings()

