import logging
import inspect
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    wait_random,
    wait_combine,
    retry_if_exception,
    before_sleep_log,
    AsyncRetrying,
)

logger = logging.getLogger(__name__)


# ---------------------------------
# Error classification
# ---------------------------------

def is_retryable(exception: BaseException) -> bool:
    msg = str(exception).lower()

    retryable_codes = ["429", "500", "502", "503", "504"]
    if any(code in msg for code in retryable_codes):
        return True

    retryable_terms = ["timeout", "connection", "network", "temporarily"]
    if any(term in msg for term in retryable_terms):
        return True

    permanent_codes = ["400", "401", "403", "404"]
    if any(code in msg for code in permanent_codes):
        return False

    return True


# ---------------------------------
# Sync retry decorators
# (used only for sync functions in ThreadPoolExecutor)
# ---------------------------------

llm_retry = retry(
    retry=retry_if_exception(is_retryable),
    stop=stop_after_attempt(3),
    wait=wait_combine(
        wait_exponential(multiplier=1, min=1, max=8),
        wait_random(min=0, max=1)
    ),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True
)

api_retry = retry(
    retry=retry_if_exception(is_retryable),
    stop=stop_after_attempt(3),
    wait=wait_combine(
        wait_exponential(multiplier=1, min=2, max=10),
        wait_random(min=0, max=2)
    ),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True
)


# ---------------------------------
# TEMPORARY — prompt cache usage logging
# ---------------------------------

def _log_cache_usage(result, source: str = "llm") -> None:
    """
    Inspect a ChatGroq response for Groq's prompt-caching usage stats
    and log the cache hit rate. Safe no-op if metadata isn't present
    (e.g. non-Groq calls, or models that don't support caching).
    """
    print(f"[cache:{source}] RAW response_metadata = {getattr(result, 'response_metadata', None)}")
    print(f"[cache:{source}] RAW usage_metadata = {getattr(result, 'usage_metadata', None)}")
    try:
        metadata = getattr(result, "response_metadata", None)
        if not metadata:
            return

        usage = metadata.get("token_usage") or metadata.get("usage") or {}
        cached_tokens = usage.get("prompt_tokens_details", {}).get("cached_tokens", 0)
        total_prompt_tokens = usage.get("prompt_tokens", 0)

        if total_prompt_tokens:
            hit_rate = (cached_tokens / total_prompt_tokens) * 100
            logger.info(
                f"[cache:{source}] {cached_tokens}/{total_prompt_tokens} "
                f"prompt tokens cached ({hit_rate:.1f}%)"
            )
            print(
                f"[cache:{source}] {cached_tokens}/{total_prompt_tokens} "
                f"prompt tokens cached ({hit_rate:.1f}%)"
            )
    except Exception as e:
        # Never let logging break the actual call
        logger.debug(f"[cache:{source}] usage logging failed: {e}")


# ---------------------------------
# Async retry helpers
# (uses AsyncRetrying — correct for async functions)
# ---------------------------------

async def async_llm_retry(func, *args, **kwargs):
    """
    Async retry for LLM calls.
    Usage: result = await async_llm_retry(some_async_func, arg1, arg2)
    """
    async for attempt in AsyncRetrying(
        retry=retry_if_exception(is_retryable),
        stop=stop_after_attempt(3),
        wait=wait_combine(
            wait_exponential(multiplier=1, min=1, max=8),
            wait_random(min=0, max=1)
        ),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True
    ):
        with attempt:
            result = func(*args, **kwargs)
            if inspect.iscoroutine(result):
                result = await result
            _log_cache_usage(result, source="llm")
            return result


async def async_api_retry(func, *args, **kwargs):
    """
    Async retry for external APIs (Tavily, YouTube).
    Usage: result = await async_api_retry(some_async_func, arg1, arg2)
    """
    async for attempt in AsyncRetrying(
        retry=retry_if_exception(is_retryable),
        stop=stop_after_attempt(3),
        wait=wait_combine(
            wait_exponential(multiplier=1, min=2, max=10),
            wait_random(min=0, max=2)
        ),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True
    ):
        with attempt:
            result = func(*args, **kwargs)
            if inspect.iscoroutine(result):
                return await result
            return result