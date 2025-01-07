from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app import settings

async_engine = create_async_engine(settings.postgres.get_url(driver="asyncpg"))
make_async_session = async_sessionmaker(async_engine, expire_on_commit=False)
