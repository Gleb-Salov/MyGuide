from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from infra.config.app_settings import settings
from sqlalchemy.orm import sessionmaker


engine = create_async_engine(settings.database_url)

SessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession) # type: ignore