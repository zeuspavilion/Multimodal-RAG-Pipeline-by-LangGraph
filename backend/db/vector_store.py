import hashlib
import asyncio
from backend.db.connection import get_pool
from backend.config import get_embeddings, TEST_USER_ID
from backend.db.cache import is_document_indexed, mark_document_indexed


def _hash_file(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()


async def document_exists(file_hash: str, user_id: str) -> bool:
    """Redis-first check, falls back to Postgres."""
    # Fast path — Redis
    if await is_document_indexed(file_hash, user_id):
        return True

    # Slow path — Postgres (also warms Redis for next time)
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT 1 FROM document_chunks
            WHERE file_hash = $1 AND user_id = $2
            LIMIT 1
            """,
            file_hash, user_id
        )
    exists = row is not None

    # Warm Redis so next check is fast
    if exists:
        await mark_document_indexed(file_hash, user_id)

    return exists


async def store_document_chunks(
    content: str,
    file_name: str,
    user_id: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> str:
    file_hash = _hash_file(content)

    if await document_exists(file_hash, user_id):
        return file_hash

    def _chunk(text: str) -> list[str]:
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        return splitter.split_text(text)

    chunks = await asyncio.to_thread(_chunk, content)

    def _embed(texts: list[str]) -> list[list[float]]:
        return get_embeddings().embed_documents(texts)

    vectors = await asyncio.to_thread(_embed, chunks)

    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.executemany(
            """
            INSERT INTO document_chunks
                (file_hash, file_name, chunk_index, content, embedding, user_id)
            VALUES
                ($1, $2, $3, $4, $5::vector, $6)
            """,
            [
                (file_hash, file_name, i, chunk, f"[{','.join(map(str, vectors[i]))}]", user_id)
                for i, chunk in enumerate(chunks)
            ]
        )

    # Mark indexed in Redis after successful Postgres insert
    await mark_document_indexed(file_hash, user_id)

    return file_hash


async def retrieve_similar_chunks(
    query: str,
    file_hash: str,
    user_id: str,
    k: int = 5,
) -> list[str]:
    def _embed_query(text: str) -> list[float]:
        return get_embeddings().embed_query(text)

    query_vector = await asyncio.to_thread(_embed_query, query)

    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT content
            FROM document_chunks
            WHERE file_hash = $1 AND user_id = $2
            ORDER BY embedding <=> $3::vector
            LIMIT $4
            """,
            file_hash, user_id, f"[{','.join(map(str, query_vector))}]", k
        )

    return [row["content"] for row in rows]