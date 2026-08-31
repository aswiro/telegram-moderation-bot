import os

from pydantic import Field, PositiveInt
from pydantic_settings import BaseSettings, SettingsConfigDict

DOTENV = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=DOTENV,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    bot_token: str = Field(..., alias="BOT_TOKEN")
    superadmin_id: PositiveInt = Field(..., alias="SUPERADMIN_ID")

    use_webhook: bool = Field(False, alias="USE_WEBHOOK")
    webhook_base: str | None = Field(None, alias="WEBHOOK_BASE")
    webhook_path: str = Field("/bot", alias="WEBHOOK_PATH")
    webhook_secret: str | None = Field(None, alias="WEBHOOK_SECRET")
    webapp_host: str = Field("0.0.0.0", alias="WEBAPP_HOST")
    webapp_port: PositiveInt = Field(8002, alias="WEBAPP_PORT")

    postgres_user: str = Field(..., alias="POSTGRES_USER")
    postgres_password: str = Field(..., alias="POSTGRES_PASSWORD")
    postgres_db: str = Field(..., alias="POSTGRES_DB")
    postgres_host: str = Field(..., alias="POSTGRES_HOST")
    postgres_port: PositiveInt = Field(..., alias="POSTGRES_PORT")

    redis_host: str = Field(..., alias="REDIS_HOST")
    redis_port: PositiveInt = Field(..., alias="REDIS_PORT")


settings = Settings()
