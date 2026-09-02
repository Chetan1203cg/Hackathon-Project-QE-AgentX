"""
config/settings.py
==================
Centralised application settings loaded from environment variables.
No secrets are stored in code or committed config files.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ------------------------------------------------------------------ #
    # Azure OpenAI
    # ------------------------------------------------------------------ #
    azure_openai_endpoint: str = ""
    azure_openai_key: str = ""
    azure_openai_deployment: str = "gpt-4o"
    azure_openai_embedding_deployment: str = "text-embedding-3-large"
    azure_openai_api_version: str = "2024-08-01-preview"

    # ------------------------------------------------------------------ #
    # Jira
    # ------------------------------------------------------------------ #
    jira_base_url: str = ""
    jira_email: str = ""
    jira_api_token: str = ""

    # ------------------------------------------------------------------ #
    # Azure AI Search
    # ------------------------------------------------------------------ #
    azure_search_endpoint: str = ""
    azure_search_key: str = ""
    azure_search_index: str = "qe-agentx-patterns"

    # ------------------------------------------------------------------ #
    # Azure Blob Storage
    # ------------------------------------------------------------------ #
    azure_blob_conn_str: str = ""
    azure_blob_container: str = "qe-agentx-artifacts"

    # ------------------------------------------------------------------ #
    # Database
    # ------------------------------------------------------------------ #
    database_url: str = "postgresql+asyncpg://qeagentx:qeagentx@localhost:5432/qeagentx"

    # ------------------------------------------------------------------ #
    # Redis
    # ------------------------------------------------------------------ #
    redis_url: str = "redis://localhost:6379/0"

    # ------------------------------------------------------------------ #
    # Xray Cloud
    # ------------------------------------------------------------------ #
    xray_client_id: str = ""
    xray_client_secret: str = ""
    xray_base_url: str = "https://xray.cloud.getxray.app"

    # ------------------------------------------------------------------ #
    # Application
    # ------------------------------------------------------------------ #
    app_env: str = "development"
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    ui_port: int = 8501

    # ------------------------------------------------------------------ #
    # LangSmith
    # ------------------------------------------------------------------ #
    langchain_tracing_v2: bool = False
    langchain_api_key: str = ""
    langchain_project: str = "qe-agentx"

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def jira_auth(self) -> tuple[str, str]:
        return (self.jira_email, self.jira_api_token)


    @property
    def is_mock_mode(self) -> bool:
        """
        Return True if in Mock Mode (no Azure credentials configured).
        Mock Mode is used for demos and development without Azure services.
        """
        return not (self.azure_openai_key and self.azure_openai_endpoint)


@lru_cache
def get_settings() -> Settings:
    """Return cached singleton Settings instance."""
    return Settings()
