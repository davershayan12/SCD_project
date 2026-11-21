"""Application configuration using pydantic-settings."""

from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Server
    host: str = Field(default="0.0.0.0", description="Host to bind to")
    port: int = Field(default=8000, description="Port to bind to")

    # Database
    database_url: str = Field(
        default="sqlite:///./storage/researchradar.db",
        description="Database connection URL",
    )

    # Storage
    upload_dir: Path = Field(
        default=Path("./storage/uploads"),
        description="Directory for uploaded files",
    )
    max_file_size_mb: int = Field(
        default=50, ge=1, le=500, description="Maximum file size in MB"
    )
    max_page_count: int = Field(
        default=500, ge=1, le=10000, description="Maximum page count for PDFs"
    )

    # Processing
    chunk_size: int = Field(
        default=256,
        ge=50,
        le=1000,
        description="Target chunk size in tokens (approx)",
    )
    chunk_overlap: int = Field(
        default=50, ge=0, le=500, description="Chunk overlap in tokens (approx)"
    )

    # Hardware (for future phases)
    use_gpu: bool = Field(default=False, description="Use GPU for processing")
    embedding_device: str = Field(
        default="cpu", description="Device for embeddings: cpu or cuda"
    )
    ollama_url: str = Field(
        default="http://localhost:11434", description="Ollama API URL"
    )
    ollama_model: str = Field(
        default="qwen2.5:7b", description="Ollama model name"
    )
    ollama_num_ctx: int = Field(
        default=8192, description="Ollama context window size"
    )

    # Security
    secret_key: str = Field(
        default="change-me-in-production", description="Secret key for sessions"
    )

    @field_validator("upload_dir")
    @classmethod
    def create_upload_dir(cls, v: Path) -> Path:
        """Ensure upload directory exists."""
        v.mkdir(parents=True, exist_ok=True)
        return v

    @property
    def max_file_size_bytes(self) -> int:
        """Maximum file size in bytes."""
        return self.max_file_size_mb * 1024 * 1024


# Global settings instance
settings = Settings()
