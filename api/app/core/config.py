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
        Normalize DATABASE_URL for asyncpg:
        - postgres:// -> postgresql+asyncpg://
        - postgresql:// -> postgresql+asyncpg://
        - sslmode=require -> ssl=require (asyncpg uses 'ssl' not 'sslmode')
        """
        if not isinstance(v, str):
            return v
        if v.startswith("postgres://"):
            v = v.replace("postgres://", "postgresql+asyncpg://", 1)
        elif v.startswith("postgresql://"):
            v = v.replace("postgresql://", "postgresql+asyncpg://", 1)
        # asyncpg uses ssl=require, not sslmode=require
        v = v.replace("sslmode=require", "ssl=require")
        return v


settings = Settings()
