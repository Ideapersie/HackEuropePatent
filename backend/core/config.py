from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Google Gemini
    google_api_key: str = ""
    gemini_model: str = "gemini-1.5-pro"
    gemini_embedding_model: str = "models/embedding-001"

    # Supabase
    supabase_url: str = ""
    supabase_service_key: str = ""

    # EPO Open Patent Services
    epo_consumer_key: str = ""
    epo_consumer_secret: str = ""

    # App
    cors_origins: list[str] = ["http://localhost:3000"]
    vector_dimension: int = 768

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
