import secrets
from typing import List, Optional, Dict, Any

from pydantic.v1 import AnyHttpUrl, PostgresDsn, validator, BaseSettings


class Settings(BaseSettings):
    SECRET_KEY: str = secrets.token_urlsafe(32)
    TOKEN_CIPHER_ALGORITHM: str = "HS256"
    # 8 days * 24 hours * 60 minutes  = 8 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 8 * 24 * 60
    SERVER_NAME: str = 'ITMOMeetings'
    # BACKEND_CORS_ORIGINS is a JSON-formatted list of origins
    # e.g: '["http://localhost", "http://localhost:4200", "http://localhost:3000", \
    # "http://localhost:8080", "http://local.dockertoolbox.tiangolo.com"]'
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    SQLALCHEMY_DATABASE_URI: Optional[PostgresDsn] = None

    @validator("SQLALCHEMY_DATABASE_URI", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql",
            user=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER"),
            path=f"/{values.get('POSTGRES_DB') or ''}",
        )

    SERVER_TIMEZONE: str = 'UTC'

    class Config:
        case_sensitive = True


settings = Settings()
