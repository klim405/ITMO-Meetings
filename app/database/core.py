from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.settings import settings

async_engine = create_async_engine(settings.ASYNC_DATABASE_URI)
make_async_session = async_sessionmaker(async_engine, expire_on_commit=False)
