from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.settings import settings

async_engine = create_async_engine(settings.ASYNC_DATABASE_URI)
make_async_session = async_sessionmaker(async_engine, expire_on_commit=False)
