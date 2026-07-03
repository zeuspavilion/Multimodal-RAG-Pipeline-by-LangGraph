import hashlib
import json
from upstash_redis import AsyncRedis
from backend.config import UPSTASH_REDIS_REST_URL, UPSTASH_REDIS_REST_TOKEN

# ---------------------------------
# TTLs
# ---------------------------------

TTL_LLM_RESPONSE = 60 * 60 * 24        # 24 hours — LLM responses
TTL_DOCUMENT_INDEXED = 60 * 60 * 24 * 7 

# ---------------------------------
# Client (lazy initialized)
# ---------------------------------

_redis: AsyncRedis | None = None


def is_redis_configured() -> bool:
    return bool(
        UPSTASH_REDIS_REST_URL
        and not UPSTASH_REDIS_REST_URL.startswith("your_upstash")
        and UPSTASH_REDIS_REST_URL != "None"
    )


def get_redis() -> AsyncRedis | None:
    global _redis
    if not is_redis_configured():
        return None
    if _redis is None:
        _redis = AsyncRedis(
            url=UPSTASH_REDIS_REST_URL,
            token=UPSTASH_REDIS_REST_TOKEN,
        )
    return _redis


# ---------------------------------
# Key builders
# ---------------------------------

def _llm_key(prompt_hash: str) -> str:
    return f"llm:response:{prompt_hash}"


def _doc_key(file_hash: str, user_id: str) -> str:
    return f"doc:indexed:{user_id}:{file_hash}"


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


# ---------------------------------
# LLM response cache
# ---------------------------------

async def get_cached_llm_response(prompt: str) -> str | None:
    """Return cached LLM response for this prompt, or None if not cached."""
    try:
        redis = get_redis()
        if not redis:
            return None
        key = _llm_key(_hash(prompt))
        result = await redis.get(key)
        return result if result else None
    except Exception as e:
        print(f"[Warning] Redis cache check failed: {e}")
        return None


async def set_cached_llm_response(prompt: str, response: str) -> None:
    """Cache an LLM response for 24 hours."""
    try:
        redis = get_redis()
        if not redis:
            return
        key = _llm_key(_hash(prompt))
        await redis.set(key, response, ex=TTL_LLM_RESPONSE)
    except Exception as e:
        print(f"[Warning] Redis cache set failed: {e}")


# ---------------------------------
# Document indexed cache
# ---------------------------------

async def is_document_indexed(file_hash: str, user_id: str) -> bool:
    """
    Fast Redis check before hitting Postgres.
    Returns True if this doc is already chunked and stored for this user.
    """
    try:
        redis = get_redis()
        if not redis:
            return False
        key = _doc_key(file_hash, user_id)
        result = await redis.get(key)
        return result is not None
    except Exception as e:
        print(f"[Warning] Redis document index check failed: {e}")
        return False


async def mark_document_indexed(file_hash: str, user_id: str) -> None:
    """Mark document as indexed in Redis after successful Postgres insert."""
    try:
        redis = get_redis()
        if not redis:
            return
        key = _doc_key(file_hash, user_id)
        await redis.set(key, "1", ex=TTL_DOCUMENT_INDEXED)
    except Exception as e:
        print(f"[Warning] Redis document index set failed: {e}")