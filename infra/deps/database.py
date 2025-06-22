from sqlalchemy.ext.asyncio import AsyncSession
from infra.db.session import SessionLocal
from typing import AsyncGenerator


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session