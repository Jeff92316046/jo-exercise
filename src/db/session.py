import asyncpg
from core.config import settings
from db.init_db import create_all_tables
from typing import AsyncGenerator

_db_pool: asyncpg.Pool | None = None


async def init_db_pool():
    global _db_pool
    _db_pool = await asyncpg.create_pool(
        user=settings.POSTGRES_USERNAME,
        password=settings.POSTGRES_PASSWORD,
        database=settings.POSTGRES_DB,
        host=settings.POSTGRES_SERVER,
        port=settings.POSTGRES_PORT,
        min_size=1,
        max_size=10,
    )
    async with _db_pool.acquire() as conn:
        await conn.execute(
            """
            CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
            """,
        )
        await create_all_tables(conn)


async def get_db() -> AsyncGenerator[asyncpg.Connection, None]:
    if _db_pool is None:
        raise RuntimeError(
            "Database pool is not initialized. Call init_db_pool() first."
        )
    async with _db_pool.acquire() as connection:
        async with connection.transaction():
            yield connection
