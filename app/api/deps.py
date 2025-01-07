from typing import Annotated

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app import settings
from app.database.utils import get_or_404
from app.models import Channel, ChannelMember, User
from app.models.channel_member import Role
from app.utils.security import AccessTokenPayload

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


async def get_current_channel_member(
    db_session: AsyncSession, token: AccessTokenPayload, channel_id: int
) -> ChannelMember:
    member = await ChannelMember.get(db_session, user_id=token.user_id, channel_id=channel_id)
    if member is not None:
        return member
    channel = await get_or_404(Channel, db_session, id=channel_id)
    return ChannelMember(
        user_id=token.user_id,
        channel_id=channel_id,
        user=await User.get(db_session, id=token.user_id),
        channel=channel,
        permissions=Role.GUEST if channel.is_public else Role.ANONYMOUS,
    )


def get_access_token(token: Annotated[str, Depends(oauth2_scheme)]) -> AccessTokenPayload:
    token_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.auth.jwt_secret, algorithms=[settings.auth.jwt_algorithm])
        return AccessTokenPayload.parse_obj(payload)
    except jwt.InvalidTokenError:
        raise token_exception


LoginRequiredDep = Depends(get_access_token)
AccessTokenDep = Annotated[AccessTokenPayload, Depends(get_access_token)]
