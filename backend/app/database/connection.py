"""Database connection pool and session maker configurations."""

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

# Create async engine. Use SQLAlchemy 2.0+ patterns.
# settings.sqlalchemy_database_url already has the postgresql+psycopg:// scheme.
engine = create_async_engine(
    settings.sqlalchemy_database_url,
    pool_pre_ping=True,
    future=True,
)

# Async session factory
async_session_maker = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_db() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency to yield request-scoped async database sessions.

    Automatically handles session commit/rollback and cleanup.
    """
    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
