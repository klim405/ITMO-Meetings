from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.core import make_async_session


async def get_db() -> AsyncSession:
    async with make_async_session() as async_session:
        yield async_session


DBSessionDep = Annotated[AsyncSession, Depends(get_db)]
