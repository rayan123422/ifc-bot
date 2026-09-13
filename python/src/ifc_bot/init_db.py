from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy import text
from .db import engine
from .models import Base
import asyncio

async def init_db():
    # create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

if __name__ == '__main__':
    asyncio.run(init_db())
    print('DB initialized')
