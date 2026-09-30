"""Application configuration using pydantic-settings."""
import os
import secrets
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Central configuration — reads from environment / .env file."""

    # App
    APP_NAME: str = "AIFRE"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent

    # Database — computed as absolute path from BASE_DIR
    DATABASE_URL: str = ""

    def model_post_init(self, __context):
        if not self.DATABASE_URL:
            db_path = self.BASE_DIR / "data" / "aifre.db"
            db_path.parent.mkdir(parents=True, exist_ok=True)
            self.DATABASE_URL = f"sqlite+aiosqlite:///{db_path}"

    # Auth
    SECRET_KEY: str = Field(default_factory=lambda: os.getenv("SECRET_KEY", secrets.token_hex(32)))
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    # LLM
    LLM_PROVIDER: str = "mock"  # "mock" | "openai"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"
    LLM_MAX_TOKENS: int = 4096
    LLM_TEMPERATURE: float = 0.2

    # Embeddings
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_PROVIDER: str = "local"  # "local" | "openai"

    # ChromaDB
    CHROMA_PERSIST_DIR: str = "./data/chromadb"
    CHROMA_COLLECTION: str = "knowledge_base"

    # Security
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    MAX_UPLOAD_SIZE_MB: int = 50
    SENSITIVE_FIELDS: list[str] = [
        "ssn", "social_security", "account_number", "credit_card",
        "password", "secret", "token", "api_key"
    ]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    @property
    def DATA_DIR(self) -> Path:
        p = self.BASE_DIR / "data"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def UPLOAD_DIR(self) -> Path:
        p = self.DATA_DIR / "uploads"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def KNOWLEDGE_DIR(self) -> Path:
        p = self.BASE_DIR.parent / "knowledge_base"
        p.mkdir(parents=True, exist_ok=True)
        return p


settings = Settings()
