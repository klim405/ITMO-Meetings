from typing import Any, Optional, Self, Type, Union, Tuple, Sequence

from fastapi import HTTPException, status
from pydantic import BaseModel
from sqlalchemy import ColumnExpressionArgument, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, AsyncAttrs
from sqlalchemy.orm import DeclarativeBase


class Base(AsyncAttrs, DeclarativeBase):
    @classmethod
    async def get(cls, async_session: AsyncSession, **pk: Union[Any, Tuple[Any, ...]]) -> Optional[Self]:
        return await async_session.get(cls, pk)

    @classmethod
    async def get_all(cls, async_session: AsyncSession, *, offset: int = 0, limit: int | None = None) -> Sequence[Self]:
        stmt = select(cls).offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await async_session.execute(stmt)
        return result.scalars().all()


    @classmethod
    async def get_first_by_filter(
        cls, async_session: AsyncSession, *criterion: ColumnExpressionArgument[bool]
    ) -> Optional[Self]:
        stmt = select(cls).filter(*criterion).limit(1)
        result = await async_session.execute(stmt)
        return result.scalars().first()


    @classmethod
    async def filter(cls, async_session: AsyncSession, *criterion: ColumnExpressionArgument[bool]) -> Sequence[Self]:
        stmt = select(cls).filter(*criterion)
        result = await async_session.execute(stmt)
        return result.scalars().all()


    @classmethod
    async def create(
        cls,
        async_session: AsyncSession,
        schema: BaseModel,
        *,
        include: dict[str, Any] | None = None,
        exclude: dict[str, Any] | None = None,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
    ) -> Self:
        creating_data = schema.model_dump(
            include=include,
            exclude=exclude,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
        )
        new_obj = cls(**creating_data)
        await new_obj.save(async_session)
        return new_obj


    async def update(
        self,
        session: AsyncSession,
        schema: BaseModel,
        *,
        include: dict[str, Any] | None = None,
        exclude: dict[str, Any] | None = None,
        exclude_unset: bool = True,
        exclude_defaults: bool = True,
    ) -> None:
        updating_data = schema.model_dump(
            include=include,
            exclude=exclude,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
        )
        for field, value in updating_data.items():
            setattr(self, field, value)
        await self.save(session)

    async def save(self, async_session: AsyncSession) -> None:
        try:
            async_session.add(self)
            await async_session.commit()
            await async_session.refresh(self)
        except IntegrityError as e:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"{e.orig}")

    async def delete(self, async_session: AsyncSession) -> None:
        await async_session.delete(self)
        await async_session.commit()

    def convert_to(self, schema: Type[BaseModel]) -> BaseModel:
        return schema.model_validate(self)
