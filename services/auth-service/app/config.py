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
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str | None = None
    redis_url: str | None = None

    @property
    def get_redis_url(self) -> str:
        """Construct Redis URL from components if not explicitly provided."""
        if self.redis_url:
            return self.redis_url
        
        auth_part = f":{self.redis_password}@" if self.redis_password else ""
        return f"redis://{auth_part}{self.redis_host}:{self.redis_port}"

    # Server
    host: str = "0.0.0.0"
    port: int = 8004
    debug: bool = False

    model_config = {"env_prefix": "", "case_sensitive": False}


settings = Settings()

