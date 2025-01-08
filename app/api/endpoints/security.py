from typing import Annotated

import jwt
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from starlette import status

from app.api.deps import AccessTokenDep
from app.database.deps import DBSessionDep
from app.models import RefreshToken, User
from app.schemas.token import RefreshTokenRequest, TokenResponse
from app.utils.security import create_access_token, create_refresh_token, decode_refresh_token

router = APIRouter()


@router.post("/token", name="Создать токен")
async def create_token(
    db_session: DBSessionDep, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> TokenResponse:
    user = await User.get_by_login(db_session, form_data.username)
    if user is None or not user.verify_password(form_data.password) or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Wrong login",
            headers={"WWW-Authenticate": "Bearer"},
        )
    refresh_token = RefreshToken(is_staff=user.is_staff, user_id=user.id)
    await refresh_token.save(db_session)
    return TokenResponse(
        access_token=create_access_token(user), refresh_token=create_refresh_token(refresh_token)
    )


@router.put(
    "/token",
    name="Обновить токен",
    description="Для выдачи нового токена доступа необходимо передать токен обновления. "
                "После обновления токен доступа, токен обновления перестает быть действительным."
)
async def refresh_access_token(db_session: DBSessionDep, data: RefreshTokenRequest) -> TokenResponse:
    try:
        refresh_payload = decode_refresh_token(data.refresh_token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Token was expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.UNAUTHORIZED, detail="Invalid token")

    refresh_token = await RefreshToken.get(db_session, id=refresh_payload.jti)
    if not refresh_token.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Token is deactivated")

    refresh_token.is_active = False
    await refresh_token.save(db_session)

    new_refresh_token = RefreshToken(is_staff=refresh_token.is_staff, user_id=refresh_token.user_id)
    await new_refresh_token.save(db_session)
    return TokenResponse(
        access_token=create_access_token(new_refresh_token),
        refresh_token=create_refresh_token(new_refresh_token),
    )


@router.delete(
    "/token",
    name="Отозвать токены обновления",
    description="После выполнения данной операции все токены будут отозваны. "
                "Операция возвращает новый токен доступа и обновления."
)
async def revoke_token(db_session: DBSessionDep, access_token: AccessTokenDep) -> TokenResponse:
    await RefreshToken.revoke_all(db_session, access_token.user_id)

    new_refresh_token = RefreshToken(is_staff=access_token.is_staff, user_id=access_token.user_id)
    await new_refresh_token.save(db_session)

    return TokenResponse(
        access_token=create_access_token(new_refresh_token),
        refresh_token=create_refresh_token(new_refresh_token),
    )
