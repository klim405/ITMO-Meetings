from app.database.base import Base
from app.database.core import engine

__all__ = ['engine', 'init_db', 'Base']


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
