from typing import Any, Tuple, Type, TypeVar, Union

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Base

_T = TypeVar("_T", bound=Base)


async def get_or_404(
    model_cls: Type[_T], async_session: AsyncSession, **pk: Union[Any, Tuple[Any, ...]]
) -> _T:
    obj = await model_cls.get(async_session, **pk)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{model_cls.__name__} not found.")
    return obj
