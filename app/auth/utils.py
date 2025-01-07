from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app import settings
from app.models import User


async def authenticate_user(db_session: AsyncSession, login: str, password: str) -> User:
    user = await User.get_by_login(db_session, login)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Wrong login",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def create_access_token(data: dict, expires_delta: timedelta) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.auth.jwt_secret, algorithm=settings.auth.jwt_algorithm)
    return encoded_jwt
