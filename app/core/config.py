from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str

    # JWT
    JWT_SECRET: str = Field(
        ..., validation_alias=AliasChoices("JWT_SECRET", "JWT_SERCERT")
    )
    JWT_ALGORITHM: str = Field(
        "HS256", validation_alias=AliasChoices("JWT_ALGORITHM", "JWT_ALGORTHIM")
    )
    JWT_EXPIRATION_MIN: int = 60

    # OpenRouter Configuration
    OPENROUTER_API_KEY: str
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    LLM_MODEL: str = "deepseek/deepseek-chat"  # OpenRouter format

    # Embeddings Configuration
    EMBEDDING_API_KEY: str = Field(
        ..., validation_alias=AliasChoices("EMBEDDING_API_KEY", "COHERE_API_KEY")
    )
    EMBEDDING_BASE_URL: str = "https://openrouter.ai/api/v1"  # OpenRouter for embeddings
    EMBEDDING_MODEL: str = ""
    VECTOR_DIMENSIONS: int = 1536

    # OpenRouter Headers (Required)
    OPENROUTER_HTTP_REFERER: str = "http://localhost:8000"
    OPENROUTER_APP_NAME: str = "AI-Support-Agent"

    # RAG
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    MAX_FILE_SIZE: int = 10

    # App
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = Path(__file__).resolve().parent.parent / ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"
        case_sensitive = False


settings = Settings()
