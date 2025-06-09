from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ENVIRONMENT_NAME: str = "local"
    FILES_PROJECT_NAME: str
    FILES_VERSION: str
    FILES_API_PREFIX: str
    FILES_SERVICE_URL: str

    MINIO_HOST: str
    MINIO_ROOT_USER: str
    MINIO_ROOT_PASSWORD: str
    MINIO_BUCKET_NAME: str

    BACKEND_SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: str

    MAIN_SERVICE_URL: str
    MAIN_HEALTHCHECK_URL: str

    REDIS_HOST: str
    REDIS_PASSWORD: str

    DEBUG: bool
    LOG_LEVEL: str = "WARNING"
    LOG_PATH: str = "log"


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()
