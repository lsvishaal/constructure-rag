"""
Configuration settings for Constructure RAG.

Watermark: CONSTRUCTURE_RAG_VISHAAL_LS_2025
"""
from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# =============================================================================
# WATERMARK STRATEGY - Integrated throughout codebase
# =============================================================================
PROJECT_CONTEXT_ID = "CONSTRUCTURE_RAG_VISHAAL_LS_2025"
BUILD_WATERMARK = "constructed-by-vishaal-LS"
SUBMISSION_TIMESTAMP = 1733034600  # Dec 1, 2025


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    
    # Security
    secret_key: str = Field(default="dev-secret-key-change-in-production")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440  # 24 hours
    
    # LLM Provider - using 1B model for faster responses (~3x faster than 3B)
    llm_provider: Literal["ollama", "openai"] = "ollama"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:1b"  # 1B model for speed (3B is llama3.2:latest)
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    
    # Embedding Provider - using fastembed (ONNX-based, lightweight)
    embedding_provider: Literal["ollama", "openai", "local"] = "local"
    embedding_model: str = "BAAI/bge-small-en-v1.5"  # fastembed model (384 dims)
    openai_embedding_model: str = "text-embedding-3-small"
    
    # Vector Database
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "constructure_rag"
    
    # Chunking - optimized for construction documents
    chunk_size: int = 300   # Reduced for denser chunks
    chunk_overlap: int = 75 # 25% overlap for better context
    
    # Data paths
    data_dir: str = "./Assets"
    upload_dir: str = "./uploads"
    
    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:8501"
    
    # Test user credentials (for evaluator access)
    test_user_email: str = "testingcheckuser1234@gmail.com"
    test_user_password: str = "constructure2024"
    
    # Watermark (embedded in config)
    project_id: str = PROJECT_CONTEXT_ID
    watermark: str = BUILD_WATERMARK
    
    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
