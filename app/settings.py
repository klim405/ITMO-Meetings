import secrets
from typing import List, Literal

from pydantic import AnyHttpUrl, EmailStr, PositiveInt
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class ServerSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="server_", extra="allow")
    # BACKEND_CORS_ORIGINS is a JSON-formatted list of origins
    # e.g: '["http://localhost", "http://localhost:4200", "http://localhost:3000", \
    # "http://localhost:8080", "http://local.dockertoolbox.tiangolo.com"]'
    cors_origins: List[AnyHttpUrl] = []
    host: str = "localhost"
    port: PositiveInt = 8000
    path_prefix: str = ""
    timezone: str = "UTC"


class AuthSettings(BaseSettings):
    jwt_secret: str = secrets.token_urlsafe(32)
    jwt_algorithm: str = "HS256"
    access_token_lifetime_in_min: int = 5
    refresh_token_lifetime_in_min: int = 30 * 24 * 60


class PostgresSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="postgres_", extra="allow")

    user: str
    password: str
    host: str
    port: PositiveInt = 5432
    db: str

    def get_url(self, driver: Literal["asyncpg", "psycopg2"] = "asyncpg"):
        return URL(
            drivername=f"postgresql+{driver}",
            username=self.user,
            password=self.password,
            host=self.host,
            port=self.port,
            database=self.db,
            query="",
        ).render_as_string(hide_password=False)


class EmailSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="email_", extra="allow")

    sender: EmailStr
    password: str
    smtp_host: str = "smtp.gmail.com"
    ssl_port: int = 465


class UtilsSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="utils_", extra="allow")

    simple_hash_pepper: str


server = ServerSettings()
auth = AuthSettings()
postgres = PostgresSettings()
email = EmailSettings()
utils = UtilsSettings()
