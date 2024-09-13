from typing import Any, Optional, List, Self, Type

from fastapi import HTTPException, status
from pydantic import BaseModel
from sqlalchemy import ColumnExpressionArgument
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import DeclarativeBase, Session


class Base(DeclarativeBase):
    @classmethod
    def get(cls, db_session: Session, **pk) -> Optional[Self]:
        return db_session.query(cls).get(pk)

    @classmethod
    def get_all(cls, db_session: Session, *,
                offset: int = 0,
                limit: int | None = None) -> List[Self]:
        query = db_session.query(cls).offset(offset)
        if limit is not None:
            return query.limit(limit).all()
        return query.all()

    @classmethod
    def get_first_by_filter(cls, db_session: Session, *criterion: ColumnExpressionArgument[bool]) -> Optional[Self]:
        return db_session.query(cls).filter(*criterion).first()

    @classmethod
    def filter(cls, db_session: Session, *criterion: ColumnExpressionArgument[bool]) -> List[Self]:
        return db_session.query(cls).filter(*criterion).all()

    @classmethod
    def create(cls, db_session: Session, schema: BaseModel, *,
               include: dict[str, Any] | None = None,
               exclude: dict[str, Any] | None = None,
               exclude_unset: bool = False,
               exclude_defaults: bool = False) -> Self:
        creating_data = schema.model_dump(
            include=include, exclude=exclude, exclude_unset=exclude_unset, exclude_defaults=exclude_defaults)
        new_obj = cls(**creating_data)
        new_obj.save(db_session)
        return new_obj

    def update(self, db_session: Session, schema: BaseModel, *,
               include: dict[str, Any] | None = None,
               exclude: dict[str, Any] | None = None,
               exclude_unset: bool = True,
               exclude_defaults: bool = True) -> None:
        updating_data = schema.model_dump(include=include, exclude=exclude,
                                          exclude_unset=exclude_unset, exclude_defaults=exclude_defaults)
        for field, value in updating_data.items():
            setattr(self, field, value)
        self.save(db_session)

    def save(self, db_session: Session) -> None:
        try:
            db_session.add(self)
            db_session.commit()
            db_session.refresh(self)
        except IntegrityError as e:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f'{e.orig}')

    def delete(self, db_session: Session) -> None:
        db_session.delete(self)
        db_session.commit()

    def convert_to(self, schema: Type[BaseModel]) -> BaseModel:
        return schema.model_validate(self)
