from typing import Type, TypeVar

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.database import Base

_T = TypeVar('_T', bound=Base)


def get_or_404(model_cls: Type[_T], db_session: Session, **pk) -> _T:
    obj = model_cls.get(db_session, **pk)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'{model_cls.__name__} not found.')
    return obj
