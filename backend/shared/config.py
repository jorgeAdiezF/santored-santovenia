from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://invoices_user:invoices_pass@localhost:5432/invoices_db"

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # RabbitMQ
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"

    # MinIO
    minio_url: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin123"
    minio_bucket: str = "invoices"
    minio_secure: bool = False

    # JWT
    jwt_secret: str = "supersecretjwtkey_change_in_production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Service URLs
    auth_service_url: str = "http://localhost:8001"
    document_service_url: str = "http://localhost:8002"
    segmentation_service_url: str = "http://localhost:8003"
    ocr_service_url: str = "http://localhost:8004"
    materials_service_url: str = "http://localhost:8005"
    homologation_service_url: str = "http://localhost:8006"
    review_service_url: str = "http://localhost:8007"
    destinations_service_url: str = "http://localhost:8008"
    analytics_service_url: str = "http://localhost:8009"

    # App
    debug: bool = False
    log_level: str = "INFO"
    environment: str = "development"

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
