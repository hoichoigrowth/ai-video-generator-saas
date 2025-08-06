from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache
import os

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # API Keys
    openai_api_key: str
    anthropic_api_key: str
    google_api_key: str
    piapi_key: str
    gotohuman_api_key: Optional[str] = None
    
    # Database (PostgreSQL - replacing MongoDB)
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"
    postgres_db: str = "ai_video_generator"
    
    # Legacy MongoDB (for migration period)
    mongodb_uri: str = "mongodb://localhost:27017/"
    mongodb_db_name: str = "ai_video_generator"
    
    # Redis (for caching and approval queues)
    redis_url: str = "redis://localhost:6379/0"
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_prefix: str = "/api/v1"
    
    # Celery
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"
    
    # MinIO/S3 Storage (replacing Google Docs file storage)
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket_name: str = "ai-video-generator"
    minio_secure: bool = False  # Use HTTPS
    
    # Environment
    environment: str = "development"
    debug: bool = True
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings():
    return Settings()

# Usage
settings = get_settings()