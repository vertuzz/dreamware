
import asyncio
import sys
import os

# Add the backend directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine
from app.models import Base

from sqlalchemy import text

async def reset_schema():
    print("Dropping all tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.execute(text("DROP TABLE IF EXISTS alembic_version"))
    print("Tables dropped.")

if __name__ == "__main__":
    asyncio.run(reset_schema())
