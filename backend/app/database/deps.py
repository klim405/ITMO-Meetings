from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.database.core import SessionLocal


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


DBSessionDep = Annotated[Session, Depends(get_db)]
