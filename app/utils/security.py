from datetime import datetime

import jwt
from pydantic import BaseModel, Field, PositiveInt, AliasChoices

from app import settings
from app.models import RefreshToken, User
from app.utils.time import add_delta_to_current_utc, utc_now


class AccessTokenPayload(BaseModel):
    iat: PositiveInt | datetime
    exp: PositiveInt | datetime
    user_id: PositiveInt
    is_staff: bool


class RefreshTokenPayload(BaseModel):
    jti: str = Field(validation_alias=AliasChoices("id", "jti"))
    iat: PositiveInt | datetime = Field(validation_alias=AliasChoices("issues_at", "iat"))
    exp: PositiveInt | datetime = Field(validation_alias=AliasChoices("expires_at", "exp"))
    user_id: PositiveInt
    is_staff: bool = False

    class Config:
        from_attributes = True


def create_access_token(model: User | RefreshToken) -> str:
    payload = AccessTokenPayload(
        user_id=model.id if isinstance(model, User) else model.user_id,
        is_staff=model.is_staff,
        iat=utc_now(),
        exp=add_delta_to_current_utc(minutes=settings.auth.access_token_lifetime_in_min),
    )
    return jwt.encode(payload.dict(), settings.auth.jwt_secret, settings.auth.jwt_algorithm)


def create_refresh_token(model: RefreshToken) -> str:
    payload = model.convert_to(RefreshTokenPayload)
    return jwt.encode(payload.dict(), settings.auth.jwt_secret, settings.auth.jwt_algorithm)


def decode_refresh_token(token: str) -> RefreshTokenPayload:
    payload = jwt.decode(token, settings.auth.jwt_secret, algorithms=[settings.auth.jwt_algorithm])
    return RefreshTokenPayload(**payload)
