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


settings = Settings()
