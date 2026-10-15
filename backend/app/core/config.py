from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "nexus-workbench"
    app_env: str = "development"
    app_host: str = "127.0.0.1"
    app_port: int = 8000
    secret_key: str = Field(..., min_length=32)

    database_url: str = "sqlite+aiosqlite:///./data/nexus.db"

    keycloak_url: str = "http://127.0.0.1:8080"
    keycloak_realm: str = "nexus"
    keycloak_client_id: str = "nexus-workbench"
    keycloak_client_secret: str = "change-me"
    keycloak_admin_user: str = "admin"
    keycloak_admin_password: str = "admin"
    oidc_discovery_url: str = "http://127.0.0.1:8080/realms/nexus/.well-known/openid-configuration"
    oidc_redirect_uri: str = "http://127.0.0.1:3000/callback"
    oidc_logout_redirect_uri: str = "http://127.0.0.1:3000"

    llm_api_key: Optional[str] = None
    llm_provider: str = "openai-compatible"
    llm_model: str = "gpt-4o-mini"
    llm_base_url: str = "https://api.openai.com/v1"

    demo_mode: bool = True

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def oidc_issuer(self) -> str:
        return f"{self.keycloak_url}/realms/{self.keycloak_realm}"

    @property
    def oidc_jwks_uri(self) -> str:
        return f"{self.keycloak_url}/realms/{self.keycloak_realm}/protocol/openid-connect/certs"

    @property
    def oidc_authorization_endpoint(self) -> str:
        return f"{self.keycloak_url}/realms/{self.keycloak_realm}/protocol/openid-connect/auth"

    @property
    def oidc_token_endpoint(self) -> str:
        return f"{self.keycloak_url}/realms/{self.keycloak_realm}/protocol/openid-connect/token"

    @property
    def oidc_logout_endpoint(self) -> str:
        return f"{self.keycloak_url}/realms/{self.keycloak_realm}/protocol/openid-connect/logout"


@lru_cache
def get_settings() -> Settings:
    return Settings()