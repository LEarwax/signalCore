from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "postgresql+asyncpg://signalcore:signalcore@localhost:5432/signalcore"
    AUTH0_DOMAIN: str = ""
    AUTH0_AUDIENCE: str = ""
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    S3_BUCKET: str = "signalcore-files"
    WEB_URL: str = "http://localhost:3000"
    API_URL: str = "http://localhost:8000"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def fix_postgres_scheme(cls, v: str) -> str:
        """
        Render (and Heroku) provide DATABASE_URL as postgres://...
        asyncpg requires postgresql+asyncpg://...
        """
        if isinstance(v, str) and v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+asyncpg://", 1)
        return v


settings = Settings()
