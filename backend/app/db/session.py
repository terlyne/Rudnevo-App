from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from core.config import settings

# Создаем асинхронный движок
engine = create_async_engine(
    str(settings.SQLALCHEMY_DATABASE_URI), echo=settings.DB_ECHO, future=True
)

# Создаем фабрику асинхронных сессий
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency для получения асинхронной сессии БД."""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()
