from backend.db.connection import get_pool


async def get_user_by_email(email: str) -> dict | None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, email, password_hash, name FROM users WHERE email = $1",
            email
        )
    return dict(row) if row else None


async def get_user_by_id(user_id: str) -> dict | None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, email, name FROM users WHERE id = $1",
            user_id
        )
    return dict(row) if row else None


async def create_user(email: str, password_hash: str, name: str) -> dict:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO users (email, password_hash, name)
            VALUES ($1, $2, $3)
            RETURNING id, email, name
            """,
            email, password_hash, name
        )
    return dict(row)