from backend.db.connection import get_pool


CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""

CREATE_USERS_EMAIL_INDEX = """
CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);
"""

ENABLE_PGCRYPTO = """
CREATE EXTENSION IF NOT EXISTS pgcrypto;
"""
ENABLE_VECTOR = "CREATE EXTENSION IF NOT EXISTS vector;"

CREATE_DOCUMENT_CHUNKS_TABLE = """
CREATE TABLE IF NOT EXISTS document_chunks (
    id SERIAL PRIMARY KEY,
    file_hash TEXT NOT NULL,
    file_name TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding vector(384) NOT NULL,
    user_id TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
"""

CREATE_CHUNKS_INDEX = """
CREATE INDEX IF NOT EXISTS idx_document_chunks_file_hash
ON document_chunks(file_hash, user_id);
"""

async def run_migrations():
    """
    Idempotent migration runner — safe to call on every startup.
    CREATE TABLE IF NOT EXISTS / CREATE INDEX IF NOT EXISTS means
    re-running this does nothing if the schema already exists.
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        # gen_random_uuid() requires pgcrypto on most Postgres setups
        # (Neon usually has it, but enable explicitly to be safe)
        await conn.execute(ENABLE_PGCRYPTO)
        await conn.execute(CREATE_USERS_TABLE)
        await conn.execute(CREATE_USERS_EMAIL_INDEX)
        print("[migrations] users table ready.")
        
        await conn.execute(ENABLE_VECTOR)
        await conn.execute(CREATE_DOCUMENT_CHUNKS_TABLE)
        await conn.execute(CREATE_CHUNKS_INDEX)
        print("[migrations] document chunks table ready.")