# Handles PostgreSQL connection pooling and ORM sessions.
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

# Database Engine (middle layer) - connection b/w py code and psql server-[ Python Code ]  --->  [ DB Engine (SQLAlchemy [write letter] (builds orm query to sql) + asyncpg (handles sql to psql))[sends letter to psql and recive results asynchrously ] ]  --->  [ PostgreSQL Server ]
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True
)

# session factory 
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

class Base(DeclarativeBase):
    pass

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

