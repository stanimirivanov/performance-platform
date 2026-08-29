"""Application configuration using Pydantic Settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central application settings, loaded from env / .env file."""

    # Database
    database_url: str = "postgresql+asyncpg://test_user:test_password@localhost:5432/metadata"
    db_pool_size: int = 20
    db_max_overflow: int = 10

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


# Create a global settings instance (singleton)
settings = Settings()
