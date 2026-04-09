from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "QuizBlast V2"
    APP_ENV: str = "development"
    SECRET_KEY: str = "change-this-secret"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 720

    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/quizblast"
    REDIS_URL: str = "redis://localhost:6379/0"

    CORS_ORIGINS: str = "http://127.0.0.1:8000,http://localhost:8000"

    HOST_ADMIN_EMAIL: str = "admin@example.com"
    HOST_ADMIN_PASSWORD: str = "ChangeMe123!"

    COOKIE_SECURE: bool = False

    @property
    def cors_origins_list(self) -> list[str]:
        return [item.strip() for item in self.CORS_ORIGINS.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
