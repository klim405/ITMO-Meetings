from datetime import datetime, timezone

import jwt
from pydantic import BaseModel, PositiveInt

from app import settings
from app.models import User
from app.utils.time import add_delta_to_current_utc, datetime_to_int


class AccessTokenPayload(BaseModel):
    iat: PositiveInt
    exp: PositiveInt
    user_id: PositiveInt
    is_staff: bool


def create_access_token(user: User) -> str:
    payload = AccessTokenPayload(
        user_id=user.id,
        is_staff=user.is_staff,
        iat=datetime_to_int(datetime.now(timezone.utc)),
        exp=datetime_to_int(add_delta_to_current_utc(minutes=settings.auth.access_token_lifetime_in_min)),
    )
    return jwt.encode(payload.dict(), settings.auth.jwt_secret, settings.auth.jwt_algorithm)
