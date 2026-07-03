import asyncpg
from backend.config import NEON_DATABASE_URL

_pool: asyncpg.Pool | None = None


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        raise RuntimeError("DB pool not initialized. Call init_pool() first.")
    return _pool


async def init_pool() -> asyncpg.Pool:
    global _pool

    # asyncpg needs the raw postgresql:// URL — not the +asyncpg variant
    url = NEON_DATABASE_URL

    _pool = await asyncpg.create_pool(
        dsn=url,
        min_size=2,
        max_size=10,
        command_timeout=30,
    )
    return _pool


async def close_pool():
    global _pool
    if _pool:
        await _pool.close()
        _pool = None