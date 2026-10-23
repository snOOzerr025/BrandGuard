from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Core Settings
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "info"
    SECRET_KEY: str = "replace_with_a_secure_random_key_for_production"

    # FastAPI Server
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # Database Configuration (Postgres + pgvector)
    POSTGRES_USER: str = "brandguard_admin"
    POSTGRES_PASSWORD: str = "brandguard_secure_password_123"
    POSTGRES_DB: str = "brandguard_db"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    # Redis Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_BROKER_URL: Optional[str] = None
    REDIS_BACKEND_URL: Optional[str] = None

    @property
    def broker_url(self) -> str:
        return self.REDIS_BROKER_URL or f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    @property
    def result_backend_url(self) -> str:
        return self.REDIS_BACKEND_URL or f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/1"

    # LLM APIs
    GEMINI_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None

    # ML Configuration
    MODEL_DEVICE: str = "cpu"
    MODEL_CACHE_DIR: str = "./models/cache"
    SENTIMENT_MODEL_NAME: str = "distilbert-base-uncased-finetuned-sst-2-english"
    SUMMARIZER_MODEL_NAME: str = "facebook/bart-large-cnn"

    # JIRA Configuration
    JIRA_DOMAIN: Optional[str] = None
    JIRA_EMAIL: Optional[str] = None
    JIRA_API_TOKEN: Optional[str] = None
    JIRA_PROJECT_KEY: str = "AXIS"
    JIRA_ENABLED: bool = False

    # Settings config
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    @property
    def database_url(self) -> str:
        """Helper to get full PostgreSQL connection string"""
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"


settings = Settings()
