from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


engine: AsyncEngine = create_async_engine(
    settings.async_database_url,
    echo=False,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

class Base(DeclarativeBase):
    pass

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Yields an active database session per request and ensures cleanup.
    Transaction management (commit/rollback) is explicitly delegated to the Service/Repository layer.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()



from contextlib import asynccontextmanager

@asynccontextmanager
async def atomic_transaction(session: AsyncSession):
    """
    Guarantees safe transaction boundaries.
    Uses SAVEPOINT (begin_nested) if a transaction is already active,
    preventing 'transaction already begun' errors while auto-rolling back on exceptions.
    """
    if session.in_transaction():
        async with session.begin_nested():
            yield
    else:
        async with session.begin():
            yield
    await session.commit()