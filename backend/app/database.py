from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from typing import AsyncGenerator
from app.core.config import settings

# Database URL from settings - use async version
SQLALCHEMY_DATABASE_URL = settings.async_database_url

# Create async engine
engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=False,
)

# Determine dialect at startup (avoids issues with checking during async requests)
IS_POSTGRES = SQLALCHEMY_DATABASE_URL.startswith("postgresql")

# Create async session maker
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
