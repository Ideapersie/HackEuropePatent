from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        # Allow Railway to pass CORS_ORIGINS as a JSON array string
        # e.g. CORS_ORIGINS=["https://foo.vercel.app","http://localhost:3000"]
        env_parse_none_str="null",
        extra="ignore",
    )

    # Google Gemini
    google_api_key: str = ""
    gemini_model: str = "gemini-1.5-pro"
    gemini_embedding_model: str = "models/embedding-001"

    # Local ChromaDB vector store
    chroma_path: str = "backend/data/chroma"

    # EPO Open Patent Services
    epo_consumer_key: str = ""
    epo_consumer_secret: str = ""

    # App
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173", "http://localhost:4173"]
    vector_dimension: int = 768


@lru_cache()
def get_settings() -> Settings:
    return Settings()
