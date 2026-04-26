import json
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    mongodb_url: str = Field(default="mongodb://localhost:27017", alias="MONGODB_URL")
    mongodb_db_name: str = Field(default="statscout_db", alias="MONGODB_DB_NAME")

    secret_key: str = Field(default="change-me", alias="SECRET_KEY")
    algorithm: str = Field(default="HS256", alias="ALGORITHM")
    access_token_expire_minutes: int = Field(default=60, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    dev_login_enabled: bool = Field(default=True, alias="DEV_LOGIN_ENABLED")

    frontend_url: str = Field(default="http://localhost:5173", alias="FRONTEND_URL")
    allowed_origins: str = Field(default='["http://localhost:5173"]', alias="ALLOWED_ORIGINS")
    api_v1_prefix: str = Field(default="/api/v1", alias="API_V1_PREFIX")

    admin_api_key: str | None = Field(default=None, alias="ADMIN_API_KEY")

    def parsed_allowed_origins(self) -> list[str]:
        try:
            parsed = json.loads(self.allowed_origins)
            if isinstance(parsed, list):
                return [str(item) for item in parsed]
        except json.JSONDecodeError:
            pass
        return [self.frontend_url]


@lru_cache
def get_settings() -> Settings:
    return Settings()
