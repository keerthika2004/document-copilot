"""Application settings and configuration module.

This module is the single source of truth for environment variables across the backend service.
It uses pydantic-settings to validate required variables and fail fast on startup if anything is missing.
No load_dotenv or os.getenv calls are permitted in app code.
"""

import os
from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Single source of truth for backend configuration."""

    # Supabase (Auth + API)
    supabase_url: str = Field(..., description="Supabase project URL")
    supabase_anon_key: str = Field(..., description="Supabase anonymous public key")
    supabase_service_role_key: str = Field(
        ..., description="Supabase service role secret key"
    )

    # Postgres (Alembic + direct DB access)
    database_url: str = Field(..., description="Direct PostgreSQL connection string")

    # OpenAI / Gemini / LLM Configuration
    openai_api_key: str = Field("", description="OpenAI API key (optional)")
    gemini_api_key: str = Field("", description="Google Gemini API key (optional)")
    groq_api_key: str = Field("", description="Groq API key (optional)")
    llm_model: str = Field(
        "groq:llama-3.3-70b-versatile",
        description="LLM model string for PydanticAI (e.g. 'groq:llama-3.3-70b-versatile', 'google:gemini-2.0-flash')",
    )
    ollama_base_url: str = Field(
        "http://localhost:11434/v1",
        description="Base URL for local Ollama LLM server",
    )

    # Embeddings (local model by default, no API key needed)
    embedding_model: str = Field(
        "BAAI/bge-small-en-v1.5", description="HuggingFace embedding model name"
    )
    embedding_dimensions: int = Field(
        384, description="Embedding vector dimensions"
    )

    # Server
    allowed_origins: str = Field(
        "http://localhost:5173", description="Comma-separated browser CORS origins"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @computed_field
    @property
    def cors_origins(self) -> list[str]:
        """Parse ALLOWED_ORIGINS into a list of strings."""
        return [
            origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()
        ]

    @computed_field
    @property
    def sqlalchemy_database_url(self) -> str:
        """Ensure the database URL uses the psycopg (Psycopg 3) driver."""
        url = self.database_url
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+psycopg://", 1)
        return url


# Single source of truth for application settings.
# Instantiating this at import time fails fast if required environment variables are missing.
settings = Settings()

# Mirror required environment variables for third-party SDKs that read os.environ directly
# (e.g., OpenAI SDK / PydanticAI), without calling load_dotenv or sprinkling setdefault across app code.
if settings.openai_api_key:
    os.environ["OPENAI_API_KEY"] = settings.openai_api_key
if settings.gemini_api_key:
    os.environ["GEMINI_API_KEY"] = settings.gemini_api_key
if settings.groq_api_key:
    os.environ["GROQ_API_KEY"] = settings.groq_api_key
if settings.ollama_base_url:
    os.environ["OLLAMA_BASE_URL"] = settings.ollama_base_url
